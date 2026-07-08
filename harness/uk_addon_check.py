#!/usr/bin/env python3
"""
Do the Add-on's UK data include the newest UK Sanctions List designations?

    python3 harness/uk_addon_check.py                # full run (~97 names x 5)
    python3 harness/uk_addon_check.py --limit 10     # smoke test

Reads data/uk-latest-additions.csv (the +86 delta produced by harness/uk_latest.py),
queries each primary_name against the Add-on, and classifies each record.

WHY THIS IS NOT A PLAIN CENSUS
------------------------------
Two failure modes make "did any code come back?" a useless question here.

1. FALSE NEIGHBOURS. The endpoint returns fuzzy neighbours even for names that are
   not in the list at all: `query="Jonas Petraitis Nobody Random"` -> codes {} but
   possible_codes = 3 unrelated people. DR-D2's census rule (HIT = codes u
   possible_codes) would score that nonsense string as a HIT. It is the right rule
   for "did ingestion happen at all" on a list we know is loaded; it is the WRONG
   rule for "is THIS new record present". So a hit here requires IDENTITY: a
   returned record whose title matches the queried party's primary name or one of
   its aliases under the pinned normalization. Everything else is a neighbour.

2. FRESHNESS IS PER-ENVELOPE, NOT GLOBAL. `processing.version_used` is a single
   global date, but the Add-on serves one envelope per regulation, each with its
   own `envelope_valid_from`. A record designated 06/07/2026 cannot be matched by
   an envelope cut before that date -- and that is CORRECT behaviour, not a defect.
   Scoring such a no-match as a miss is exactly the error that produced the
   retracted Finding #9 (see oracle/README.md). So this harness harvests
   envelope_valid_from per envelope_filename from the control hits and reports the
   Add-on's UK data cut alongside every miss. A miss is only interpretable against
   the envelope date of its own regime.

CONTROLS (a run without these proves nothing)
---------------------------------------------
  control_pos   Long-standing records (designated <= 2024) in EACH affected regime
                (CHW / RUS / GHR). If these miss, the harness or the regime's
                envelope is broken and NO conclusion may be drawn about additions.
  control_neg   Nonsense names. Must produce zero IDENTITY hits. If they "hit",
                the identity rule is too loose.
  delisted      The 3 records removed by this refresh. Informational: does the
                Add-on still match parties the UK has delisted?

METHOD
------
  * N = 5 queries per name (Finding #6: bucketing is non-deterministic; a single
    call is noise -- `Putin` returned 0 definite codes on one call and 3 on the
    next). Runs are NEVER collapsed before recording; the per-name hit rate is
    the signal.
  * Classification per record, over the N runs:
        STABLE_DEFINITE  identity match in `codes` on every run
        FLAKY            identity match on some runs, not all
        POSSIBLE_ONLY    identity match, but only ever in `possible_codes`
        NEIGHBOUR_ONLY   codes/possible returned, never an identity match
        MISS             nothing returned on any run
  * Ships are reported on their own line, never folded into the headline: this is
    a person/entity matcher, and vessel handling is name-recall-only (Finding F-4).
  * version_used captured on EVERY call; start/end recorded; a mid-run change
    invalidates the run (DR-REPRO).

Identity normalization is the rule pinned in A1: NFKC -> casefold -> collapse
non-alphanumerics. Two names are the same party when their normalized token
MULTISETS are equal (so "Putin Vladimir Vladimirovich" == "Vladimir Vladimirovich
PUTIN"). Strict subset relations are recorded as `partial`, never counted as hits.

Stdlib only. Concurrency 4 (each call runs a server-side LLM). ~485 calls, ~4 min.
"""

import argparse
import collections
import csv
import datetime
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

BASE = "https://fast.customsclear.net/api/sanctions_person_versions_regulations/match"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ADDITIONS = os.path.join(ROOT, "data", "uk-latest-additions.csv")
PREV_XML = os.path.join(ROOT, "data", "UK-Sanctions-List.prev.xml")
RESULTS = os.path.join(ROOT, "results")
REPORTS = os.path.join(ROOT, "reports")

N_RUNS = 5
WORKERS = 4
TIMEOUT = 60
RETRIES = 3

# Long-standing designations (<= 2024) in each regime touched by the additions.
# Chosen from the PREVIOUS snapshot, so they predate every record under test.
CONTROL_POS = [
    ("CHW0001", "Firas Ahmed"),
    ("CHW0002", "Walid Zughaib"),
    ("RUS0001", "Dmitry Konstantinovich Kiselyov"),
    ("RUS0002", "Andrei Aleksandrovich Klishas"),
    ("GHR0001", "Dmitry Borisovich KRATOV"),
    ("GHR0002", "Aleksey Vasilyevich ANICHIN"),
]
CONTROL_NEG = [
    ("NEG0001", "Jonas Petraitis Nobody Random"),
    ("NEG0002", "Zxqvwlk Brintofferson Nonexistent"),
]


# --- identity ----------------------------------------------------------------

def normalize(s):
    """A1's pinned rule: NFKC -> casefold -> collapse non-alphanumerics."""
    s = unicodedata.normalize("NFKC", s or "").casefold()
    return re.sub(r"[^0-9a-z]+", " ", s).strip()


def tokens(s):
    return tuple(sorted(normalize(s).split()))


def identity(returned_title, names):
    """'exact' | 'tokenset' | 'partial' | None, against the party's own names."""
    rt_norm, rt_tok = normalize(returned_title), tokens(returned_title)
    if not rt_tok:
        return None
    best = None
    for name in names:
        if not name:
            continue
        if rt_norm == normalize(name):
            return "exact"
        n_tok = tokens(name)
        if rt_tok == n_tok:
            best = "tokenset"
        elif best is None and (set(rt_tok) < set(n_tok) or set(n_tok) < set(rt_tok)):
            best = "partial"
    return best


HIT_KINDS = ("exact", "tokenset")


# --- endpoint ----------------------------------------------------------------

def match(query):
    url = "%s?%s" % (BASE, urllib.parse.urlencode({"query": query}))
    last = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, method="POST")
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return json.load(r), None
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            last = repr(e)
            time.sleep(1.5 * (attempt + 1))
    return None, last


def probe(record, run_idx):
    """One call. Returns a raw dict suitable for the jsonl capture."""
    resp, err = match(record["primary_name"])
    row = {
        "unique_id": record["unique_id"],
        "role": record["role"],
        "run": run_idx,
        "query": record["primary_name"],
        "error": err,
    }
    if resp is None:
        return row

    out = resp.get("output", {})
    row["version_used"] = resp.get("processing", {}).get("version_used")
    row["stage_used"] = resp.get("processing", {}).get("stage_used")

    names = [record["primary_name"]] + [
        a.strip() for a in (record.get("aliases") or "").split(";") if a.strip()
    ]
    # Collect EVERY identity match, not the first one found. A party can be listed
    # by several regimes at once (CHW0037 matches both the EU 2018/1542 record and
    # the UK chemical-weapons record); taking whichever the dict yielded first made
    # the issuer breakdown an artifact of iteration order. `matches` is the record
    # of what the Add-on actually returned, and the aggregation decides afterwards.
    matches, saw_any = [], False
    for bucket in ("codes", "possible_codes"):
        for code, rec in (out.get(bucket) or {}).items():
            saw_any = True
            kind = identity(rec.get("title", ""), names)
            if kind in HIT_KINDS:
                matches.append({
                    "bucket": bucket, "code": code, "title": rec.get("title"), "kind": kind,
                    "issuer": (rec.get("meta") or {}).get("issuer"),
                    "envelope_filename": rec.get("envelope_filename"),
                    "envelope_valid_from": rec.get("envelope_valid_from"),
                    "envelope_valid_to": rec.get("envelope_valid_to"),
                    "valid_from": rec.get("valid_from"),
                    "valid_to": rec.get("valid_to"),
                })

    if any(m["bucket"] == "codes" for m in matches):
        verdict = "definite"
    elif matches:
        verdict = "possible"
    elif saw_any:
        verdict = "neighbour"
    else:
        verdict = "empty"

    row["verdict"] = verdict
    row["matches"] = matches
    row["n_codes"] = len(out.get("codes") or {})
    row["n_possible"] = len(out.get("possible_codes") or {})
    return row


# --- inputs ------------------------------------------------------------------

def load_records(limit):
    records = []
    with open(ADDITIONS, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            role = "ship_addition" if r["type"] == "Ship" else "addition"
            records.append({
                "unique_id": r["unique_id"], "type": r["type"], "role": role,
                "primary_name": r["primary_name"], "aliases": r["aliases"],
                "regime": r["regime"], "date_designated": r["date_designated_inclusion"],
            })
    if limit:
        records = records[:limit]

    for uid, name in CONTROL_POS:
        records.append({"unique_id": uid, "type": "", "role": "control_pos",
                        "primary_name": name, "aliases": "", "regime": "", "date_designated": ""})
    for uid, name in CONTROL_NEG:
        records.append({"unique_id": uid, "type": "", "role": "control_neg",
                        "primary_name": name, "aliases": "", "regime": "", "date_designated": ""})

    # The 3 delisted parties, pulled from the previous snapshot by UniqueID.
    if os.path.exists(PREV_XML) and not limit:
        cur_ids = {r["unique_id"] for r in records}
        sys.path.insert(0, HERE)
        from uk_latest import split_names  # same derivation as the extract
        root = ET.parse(PREV_XML).getroot()
        cur = {d.findtext("UniqueID") for d in ET.parse(
            os.path.join(ROOT, "data", "UK-Sanctions-List.xml")).getroot() if d.tag == "Designation"}
        for d in root:
            if d.tag != "Designation":
                continue
            uid = d.findtext("UniqueID")
            if uid not in cur and uid not in cur_ids:
                primary, aliases = split_names(d)
                records.append({"unique_id": uid, "type": d.findtext("IndividualEntityShip") or "",
                                "role": "delisted", "primary_name": primary,
                                "aliases": "; ".join(aliases),
                                "regime": d.findtext("RegimeName") or "", "date_designated": ""})
    return records


# --- classification ----------------------------------------------------------

def classify(runs):
    n = len(runs)
    definite = sum(1 for r in runs if r.get("verdict") == "definite")
    possible = sum(1 for r in runs if r.get("verdict") == "possible")
    neighbour = sum(1 for r in runs if r.get("verdict") == "neighbour")
    empty = sum(1 for r in runs if r.get("verdict") == "empty")
    errors = sum(1 for r in runs if r.get("error"))

    if errors == n:
        label = "ERROR"
    elif definite == n:
        label = "STABLE_DEFINITE"
    elif definite + possible == 0 and neighbour == 0:
        label = "MISS"
    elif definite + possible == 0:
        label = "NEIGHBOUR_ONLY"
    elif definite == 0:
        label = "POSSIBLE_ONLY"
    else:
        label = "FLAKY"
    return label, definite, possible, neighbour, empty, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="only the first N additions (smoke test)")
    ap.add_argument("--runs", type=int, default=N_RUNS)
    args = ap.parse_args()

    os.makedirs(RESULTS, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_path = os.path.join(RESULTS, "uk-additions-addon-%s.jsonl" % stamp)

    records = load_records(args.limit)
    jobs = [(rec, i) for rec in records for i in range(args.runs)]
    print("names: %d  runs/name: %d  calls: %d" % (len(records), args.runs, len(jobs)))
    print("raw -> %s" % raw_path)

    rows, done = [], 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as pool, open(raw_path, "w", encoding="utf-8") as raw:
        for row in pool.map(lambda j: probe(*j), jobs):
            raw.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows.append(row)
            done += 1
            if done % 50 == 0 or done == len(jobs):
                print("  %d/%d  (%.0fs)" % (done, len(jobs), time.time() - t0), flush=True)

    # DR-REPRO: version_used must be stable across the whole window.
    versions = [r["version_used"] for r in rows if r.get("version_used")]
    version_set = sorted(set(versions))
    errors = [r for r in rows if r.get("error")]

    by_id = collections.defaultdict(list)
    for r in rows:
        by_id[r["unique_id"]].append(r)
    meta = {r["unique_id"]: r for r in records}

    # envelope_valid_from is a per-RECORD field, so the same envelope_filename can
    # legitimately appear with different values. Keep every value seen per envelope
    # rather than letting the last write win (which invented a false contradiction:
    # a "2026-06-02" Russia envelope apparently holding 16/06 designations).
    envelopes = collections.defaultdict(set)
    out_rows = []
    for uid, runs in by_id.items():
        rec = meta[uid]
        label, definite, possible, neighbour, empty, errs = classify(runs)

        all_matches = [m for r in runs for m in (r.get("matches") or [])]
        for m in all_matches:
            if m.get("envelope_filename"):
                envelopes[m["envelope_filename"]].add(m.get("envelope_valid_from"))

        # Report the UK-issued record when one exists -- that is the question being
        # asked ("is the new UK designation present?"). A same-party match issued by
        # the EU/US is a different list's copy and must not be allowed to stand in.
        uk = next((m for m in all_matches if m.get("issuer") == "UK"), None)
        chosen = uk or (all_matches[0] if all_matches else {})
        issuers = sorted({m.get("issuer") or "?" for m in all_matches})

        # Does the served listing validity agree with the source designation date?
        vf, dd = chosen.get("valid_from") or "", rec["date_designated"]
        agree = ""
        if vf and dd:
            try:
                agree = "yes" if datetime.datetime.strptime(vf, "%Y-%m-%d").date() == \
                    datetime.datetime.strptime(dd, "%d/%m/%Y").date() else "no"
            except ValueError:
                agree = "unparseable"

        out_rows.append({
            "unique_id": uid, "role": rec["role"], "type": rec["type"],
            "primary_name": rec["primary_name"], "regime": rec["regime"],
            "date_designated": dd, "class": label,
            "definite_runs": definite, "possible_runs": possible,
            "neighbour_runs": neighbour, "empty_runs": empty, "error_runs": errs,
            "n_runs": len(runs),
            "uk_match": "yes" if uk else ("no" if all_matches else ""),
            "issuers_matched": "|".join(issuers),
            "matched_code": chosen.get("code", ""), "matched_title": chosen.get("title", ""),
            "identity_kind": chosen.get("kind", ""), "issuer": chosen.get("issuer", ""),
            "valid_from": vf, "valid_to": chosen.get("valid_to", ""),
            "valid_from_matches_designation": agree,
            "envelope_filename": chosen.get("envelope_filename", ""),
            "envelope_valid_from": chosen.get("envelope_valid_from", ""),
        })

    order = {"addition": 0, "ship_addition": 1, "control_pos": 2, "control_neg": 3, "delisted": 4}
    out_rows.sort(key=lambda r: (order.get(r["role"], 9), r["unique_id"]))
    csv_path = os.path.join(REPORTS, "uk_additions_addon_check.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    # --- summary --------------------------------------------------------------
    print("\n" + "=" * 72)
    print("version_used: %s   %s" % (version_set, "STABLE" if len(version_set) == 1 else "*** CHANGED MID-RUN: RUN INVALID ***"))
    print("errors: %d/%d calls" % (len(errors), len(rows)))
    print("=" * 72)

    for role in ("control_pos", "control_neg", "addition", "ship_addition", "delisted"):
        group = [r for r in out_rows if r["role"] == role]
        if not group:
            continue
        counts = collections.Counter(r["class"] for r in group)
        print("\n%s  (n=%d)" % (role.upper(), len(group)))
        for k, v in counts.most_common():
            print("    %-16s %3d  (%.0f%%)" % (k, v, 100.0 * v / len(group)))
        if role in ("addition", "ship_addition"):
            uk = sum(1 for r in group if r["uk_match"] == "yes")
            eu_only = [r["unique_id"] for r in group if r["uk_match"] == "no"]
            agree = sum(1 for r in group if r["valid_from_matches_designation"] == "yes")
            print("    -- matched by a UK-issued record: %d/%d" % (uk, len(group)))
            if eu_only:
                print("    -- NON-UK issuer only (a different list's copy!): %s" % eu_only)
            print("    -- served valid_from == source DateDesignated: %d/%d" % (agree, len(group)))
        if role == "delisted":
            for r in group:
                print("    %-9s %-16s valid_to=%s  env_from=%s"
                      % (r["unique_id"], r["class"], r["valid_to"], r["envelope_valid_from"]))

    print("\nAdd-on envelope cuts observed (envelope_valid_from values per envelope):")
    for env, vfs in sorted(envelopes.items()):
        print("    %-68s %s" % (env[:68], sorted(v for v in vfs if v)))

    print("\ncsv -> %s" % csv_path)
    print("raw -> %s" % raw_path)


if __name__ == "__main__":
    main()
