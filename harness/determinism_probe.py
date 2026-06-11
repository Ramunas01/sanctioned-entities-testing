#!/usr/bin/env python3
"""
Determinism probe for the Sanctions Add-on (DR-D2).

Goal
----
Characterize whether the Add-on assigns matched code IDs to ``output.codes``
(definite) vs ``output.possible_codes`` (fuzzy) *deterministically* across
repeated identical queries. Per DR-D2, bucket non-determinism is an Add-on
defect that would invalidate behavioral threshold testing (Issue #4): a query
that lands a party in ``codes`` on one run and ``possible_codes`` on another
makes the confidence signal untrustworthy.

We also verify ``processing.version_used`` is stable across the whole run
(reproducibility guard, DR-REPRO): if the served-data version changes mid-run,
the capture is contaminated.

What it does
------------
1. Deterministically select a stratified query set from ``oracle/expected.csv``
   (exact ``primary_name`` values), stratified across the three agencies
   (Treasury / BIS / State, derived from ``source_sublist``) and across entity
   types (Individual / Entity / Vessel / Aircraft / blank). Selection is
   seed + sort driven so a re-run picks the *same* names.
2. Append ~5 deliberate gibberish non-hit controls.
3. Fire each query K=5 times against the endpoint (concurrency capped at 4,
   each call runs a server-side LLM). Retry transient errors with backoff.
4. Write one JSON object per call to
   ``results/determinism-probe-<UTC-timestamp>.jsonl``.
5. Analyze per-query stability and write ``reports/determinism-probe.md``.

Stdlib only (urllib); no pip dependencies.

Endpoint (docs/addon-interface.md):
    POST https://fast.customsclear.net/api/sanctions_person_versions_regulations/match?query=<urlencoded name>
    - POST only; query in the query string (not body); no auth.
    - version_date is currently inert; we omit it.

Usage:
    python3 harness/determinism_probe.py            # full run (250-ish calls)
    python3 harness/determinism_probe.py --dry-run  # print selected query set, no calls
    python3 harness/determinism_probe.py --analyze-only <jsonl>  # re-analyze a capture
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# --------------------------------------------------------------------------- #
# Configuration                                                               #
# --------------------------------------------------------------------------- #

BASE_URL = (
    "https://fast.customsclear.net/api/"
    "sanctions_person_versions_regulations/match"
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED_CSV = os.path.join(REPO_ROOT, "oracle", "expected.csv")
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
REPORTS_DIR = os.path.join(REPO_ROOT, "reports")
REPORT_PATH = os.path.join(REPORTS_DIR, "determinism-probe.md")

K = 5                    # repeats per query
MAX_CONCURRENCY = 4      # cap: each call runs a server-side LLM
PER_STRATUM = 8          # listed names to draw per (agency, entity_type) stratum
SEED = 20260611          # fixed seed -> deterministic selection on re-run
HTTP_TIMEOUT = 45        # seconds per request
MAX_RETRIES = 2          # additional attempts after the first on transient error
BACKOFF_BASE = 1.5       # seconds; backoff = BACKOFF_BASE * (attempt+1)

# Deliberate gibberish non-hit controls (should yield codes == {}).
CONTROLS = [
    "Zxqwvbn Plokmijn Qwerasdf",
    "Flarbnax Qugglethorpe Wibbenstein",
    "Zzyzx Vorplenugget Throbblewick",
    "Klaxnorbit Drimblewedge Snorftacular",
    "Gribnaxle Pfutterworth Vexmondiac",
]

# Agencies we stratify across, with the entity types to sample for each.
# Per oracle: blank entity_type rows are exactly the BIS + State sublists
# (those sublists omit type); Treasury carries Individual/Entity/Vessel/Aircraft.
STRATA = [
    ("Treasury", "Individual"),
    ("Treasury", "Entity"),
    ("Treasury", "Vessel"),
    ("Treasury", "Aircraft"),
    ("BIS", ""),       # BIS rows have blank entity_type
    ("State", ""),     # State rows have blank entity_type
]


# --------------------------------------------------------------------------- #
# Query selection (deterministic)                                             #
# --------------------------------------------------------------------------- #

def _agency(sublist: str) -> str:
    """Map a CSL source_sublist label to its issuing agency."""
    if "Treasury" in sublist:
        return "Treasury"
    if "Bureau of Industry and Security" in sublist:
        return "BIS"
    if "State Department" in sublist:
        return "State"
    return "Other"


def _is_distinctive(name: str, entity_type: str) -> bool:
    """
    Heuristic to prefer names likely to MATCH cleanly (so they land in
    codes/possible_codes, which is the bucket-assignment we are testing).

    - Person/Entity/blank: multi-token, reasonable length. Multi-token, clearly
      structured names are far more likely to resolve to a definite party than a
      single common token.
    - Vessel/Aircraft: these are identifiers (vessel name / tail registration);
      single tokens are normal and distinctive, so we do not require 2+ tokens.
    """
    n = name.strip()
    if entity_type in ("Vessel", "Aircraft"):
        return 3 <= len(n) <= 40
    return len(n.split()) >= 2 and 8 <= len(n) <= 45


def load_rows() -> list[dict]:
    rows = []
    with open(EXPECTED_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def select_queries(rows: list[dict]) -> list[dict]:
    """
    Deterministically select a stratified set of listed-party names.

    Determinism guarantee: within each stratum we (1) filter to distinctive
    names, (2) DEDUPLICATE by name, (3) SORT by name, then (4) draw a
    seed-shuffled sample. Same frozen oracle + same SEED -> same names every run.

    Returns a list of selection records (dicts) carrying name + provenance.
    """
    by_stratum: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        key = (_agency(row["source_sublist"]), row["entity_type"])
        if key in STRATA and _is_distinctive(row["primary_name"], row["entity_type"]):
            by_stratum[key].append(row)

    selected: list[dict] = []
    seen_names: set[str] = set()

    for key in STRATA:
        agency, etype = key
        pool = by_stratum.get(key, [])
        # Deduplicate by exact name, keeping the first source row for provenance.
        dedup: dict[str, dict] = {}
        for row in pool:
            dedup.setdefault(row["primary_name"], row)
        # Sort by name for a stable, reproducible ordering before shuffling.
        ordered = [dedup[n] for n in sorted(dedup.keys())]
        # Seed per-stratum so adding/removing a stratum does not reshuffle others.
        rnd = random.Random(f"{SEED}:{agency}:{etype}")
        rnd.shuffle(ordered)

        picked = 0
        for row in ordered:
            if picked >= PER_STRATUM:
                break
            name = row["primary_name"]
            if name in seen_names:
                continue
            seen_names.add(name)
            selected.append({
                "name": name,
                "agency": agency,
                "entity_type": etype,
                "source_sublist": row["source_sublist"],
                "programs": row["programs"],
                "kind": "listed",
            })
            picked += 1

    # Append controls (deterministic order).
    for c in CONTROLS:
        selected.append({
            "name": c,
            "agency": "—",
            "entity_type": "—",
            "source_sublist": "—",
            "programs": "",
            "kind": "control",
        })

    return selected


# --------------------------------------------------------------------------- #
# HTTP                                                                          #
# --------------------------------------------------------------------------- #

def call_addon(query: str) -> dict:
    """POST one query; return parsed JSON. Raises on HTTP/transport error."""
    url = f"{BASE_URL}?{urllib.parse.urlencode({'query': query})}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        return json.load(r)


def call_with_retries(query: str) -> tuple[dict | None, str | None]:
    """
    Call with a couple of retries on transient error.
    Returns (response_json, None) on success or (None, error_string) on failure.
    """
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return call_addon(query), None
        except Exception as exc:  # urllib error, timeout, JSON decode, etc.
            last_err = f"{type(exc).__name__}: {exc}"
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE * (attempt + 1))
    return None, last_err


def extract_capture(query: str, run_idx: int, sel: dict,
                    resp: dict | None, err: str | None) -> dict:
    """Build the per-call capture record written to the JSONL."""
    rec = {
        "query": query,
        "run": run_idx,
        "kind": sel["kind"],
        "agency": sel["agency"],
        "entity_type": sel["entity_type"],
        "source_sublist": sel["source_sublist"],
        "ts_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "error": err,
    }
    if resp is not None:
        out = resp.get("output", {}) or {}
        proc = resp.get("processing", {}) or {}
        inp = resp.get("input", {}) or {}
        codes = out.get("codes") or {}
        possible = out.get("possible_codes") or {}
        rec.update({
            "codes": sorted(codes.keys()),
            "possible_codes": sorted(possible.keys()),
            "version_used": proc.get("version_used"),
            "version_date": inp.get("version_date"),
            "stage_used": proc.get("stage_used"),
            "processing_time": proc.get("processing_time"),
        })
    else:
        rec.update({
            "codes": None,
            "possible_codes": None,
            "version_used": None,
            "version_date": None,
            "stage_used": None,
            "processing_time": None,
        })
    return rec


# --------------------------------------------------------------------------- #
# Run                                                                          #
# --------------------------------------------------------------------------- #

def run_probe(selected: list[dict], jsonl_path: str) -> list[dict]:
    """
    Fire every (query, run) task with concurrency capped at MAX_CONCURRENCY.
    Stream captures to the JSONL as they complete. Return all captures.
    """
    tasks = []  # (sel, run_idx)
    for sel in selected:
        for run_idx in range(1, K + 1):
            tasks.append((sel, run_idx))

    captures: list[dict] = []
    total = len(tasks)
    done = 0

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(jsonl_path, "w", encoding="utf-8") as out_f:
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as pool:
            futures = {
                pool.submit(call_with_retries, sel["name"]): (sel, run_idx)
                for (sel, run_idx) in tasks
            }
            for fut in as_completed(futures):
                sel, run_idx = futures[fut]
                resp, err = fut.result()
                rec = extract_capture(sel["name"], run_idx, sel, resp, err)
                captures.append(rec)
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out_f.flush()
                done += 1
                status = "ERR" if err else "ok "
                print(f"[{done:3d}/{total}] {status} run{run_idx} "
                      f"{sel['name'][:48]}", file=sys.stderr)

    return captures


# --------------------------------------------------------------------------- #
# Analysis                                                                      #
# --------------------------------------------------------------------------- #

def classify_query(runs: list[dict]) -> dict:
    """
    Given the (<=K) capture records for a single query, classify stability.

    Returns a dict with:
      classification: STABLE | BUCKET-CHURN | UNION-CHURN | ERRORED
      n_runs, n_ok, n_err
      union: sorted list of all code IDs ever matched (across ok runs)
      union_stable: bool (same union every ok run)
      bucket_stable: bool (each code ID always in the same bucket)
      churn_codes: {code_id: detail} for any code that churned bucket/union
      version_used: sorted list of distinct version_used values seen
    """
    ok = [r for r in runs if r["error"] is None]
    err = [r for r in runs if r["error"] is not None]

    result = {
        "n_runs": len(runs),
        "n_ok": len(ok),
        "n_err": len(err),
        "union": [],
        "union_stable": None,
        "bucket_stable": None,
        "churn_codes": {},
        "version_used": sorted({r["version_used"] for r in ok if r["version_used"]}),
        "classification": None,
    }

    if not ok:
        result["classification"] = "ERRORED"
        return result

    # Per-run union and per-code bucket assignments.
    union_per_run = []
    # code_id -> set of buckets it appeared in across runs ("codes"/"possible")
    code_buckets: dict[str, set[str]] = defaultdict(set)
    # code_id -> number of ok runs it appeared in
    code_presence: dict[str, int] = defaultdict(int)

    for r in ok:
        codes = set(r["codes"] or [])
        possible = set(r["possible_codes"] or [])
        union_per_run.append(frozenset(codes | possible))
        for c in codes:
            code_buckets[c].add("codes")
            code_presence[c] += 1
        for c in possible:
            code_buckets[c].add("possible_codes")
            code_presence[c] += 1

    union_all = sorted(set().union(*union_per_run)) if union_per_run else []
    result["union"] = union_all
    result["union_stable"] = len(set(union_per_run)) == 1

    n_ok = len(ok)
    bucket_stable = True
    for c in union_all:
        appeared_everywhere = code_presence[c] == n_ok
        single_bucket = len(code_buckets[c]) == 1
        if not appeared_everywhere or not single_bucket:
            bucket_stable = False
            result["churn_codes"][c] = {
                "buckets": sorted(code_buckets[c]),
                "present_in_runs": code_presence[c],
                "of_ok_runs": n_ok,
                "type": ("union" if not appeared_everywhere else "bucket"),
            }
    result["bucket_stable"] = bucket_stable

    # Classify. Union instability is worse than bucket churn.
    if err:
        # Partial errors: still classify by the ok runs but note error.
        pass
    if not result["union_stable"]:
        result["classification"] = "UNION-CHURN"
    elif not bucket_stable:
        result["classification"] = "BUCKET-CHURN"
    else:
        result["classification"] = "STABLE"

    return result


def analyze(captures: list[dict]) -> dict:
    """Group captures by query, classify each, and aggregate run-wide facts."""
    by_query: dict[str, list[dict]] = defaultdict(list)
    for rec in captures:
        by_query[rec["query"]].append(rec)

    per_query = {}
    all_versions: set[str] = set()
    total_calls = 0
    total_errors = 0

    for q, runs in by_query.items():
        runs_sorted = sorted(runs, key=lambda r: r["run"])
        cls = classify_query(runs_sorted)
        # carry provenance from first record
        cls["kind"] = runs_sorted[0]["kind"]
        cls["agency"] = runs_sorted[0]["agency"]
        cls["entity_type"] = runs_sorted[0]["entity_type"]
        cls["source_sublist"] = runs_sorted[0]["source_sublist"]
        cls["runs"] = runs_sorted
        per_query[q] = cls
        for r in runs_sorted:
            total_calls += 1
            if r["error"]:
                total_errors += 1
            if r["version_used"]:
                all_versions.add(r["version_used"])

    return {
        "per_query": per_query,
        "versions_observed": sorted(all_versions),
        "total_calls": total_calls,
        "total_errors": total_errors,
    }


# --------------------------------------------------------------------------- #
# Reporting                                                                     #
# --------------------------------------------------------------------------- #

def write_report(analysis: dict, jsonl_path: str, selected: list[dict]) -> dict:
    per_query = analysis["per_query"]
    versions = analysis["versions_observed"]

    counts = defaultdict(int)
    for cls in per_query.values():
        counts[cls["classification"]] += 1

    listed = {q: c for q, c in per_query.items() if c["kind"] == "listed"}
    controls = {q: c for q, c in per_query.items() if c["kind"] == "control"}

    # Controls that unexpectedly produced a definite hit (codes non-empty on any run).
    dirty_controls = []
    for q, c in controls.items():
        hit = any((r["codes"] or []) for r in c["runs"] if r["error"] is None)
        if hit:
            dirty_controls.append(q)

    # Sub-finding (DR-D2): exact source name landing ONLY in possible_codes
    # (never in codes on any ok run) — a matching-calibration smell.
    only_possible = []
    for q, c in listed.items():
        ok = [r for r in c["runs"] if r["error"] is None]
        if not ok:
            continue
        ever_in_codes = any((r["codes"] or []) for r in ok)
        ever_matched = any((r["codes"] or []) or (r["possible_codes"] or []) for r in ok)
        if ever_matched and not ever_in_codes:
            only_possible.append(q)

    version_stable = len(versions) <= 1

    # Verdict on #4 gate.
    bucket_churn = counts["BUCKET-CHURN"]
    union_churn = counts["UNION-CHURN"]
    listed_total = len(listed)
    safe_for_4 = (bucket_churn == 0 and union_churn == 0)

    lines: list[str] = []
    lines.append("# Determinism Probe — Findings (DR-D2)\n")
    lines.append(f"_Generated: {_dt.datetime.now(_dt.timezone.utc).isoformat()}_  ")
    lines.append(f"_Raw capture: `{os.path.relpath(jsonl_path, REPO_ROOT)}`_  ")
    lines.append(f"_Probe: `harness/determinism_probe.py` "
                 f"(SEED={SEED}, K={K}, concurrency={MAX_CONCURRENCY}, "
                 f"per-stratum={PER_STRATUM})_\n")

    # Headline.
    if not version_stable:
        headline = (f"**HEADLINE: `version_used` is NOT stable across the run "
                    f"({', '.join(versions)}) — capture is contaminated; rerun in a "
                    f"tighter window before trusting any result.**")
    elif union_churn:
        headline = (f"**HEADLINE: {union_churn}/{listed_total} listed queries show "
                    f"UNION-CHURN — the set of matched code IDs changes across "
                    f"identical runs. This is worse than bucket churn and blocks "
                    f"#4 threshold testing.**")
    elif bucket_churn:
        headline = (f"**HEADLINE: {bucket_churn}/{listed_total} listed queries show "
                    f"BUCKET-CHURN — the same code ID lands in `codes` on one run and "
                    f"`possible_codes` on another. Per DR-D2 this is an Add-on defect "
                    f"that invalidates behavioral threshold testing; #4 is BLOCKED.**")
    else:
        headline = (f"**HEADLINE: bucketing is STABLE across all {listed_total} listed "
                    f"queries (K={K}); `version_used` constant at "
                    f"`{versions[0] if versions else 'n/a'}`. #4 threshold testing is "
                    f"safe to build on.**")
    lines.append(headline + "\n")

    # Verdict block.
    lines.append("## Verdict\n")
    lines.append(f"- **Bucketing stable enough for #4?** "
                 f"{'YES' if safe_for_4 else 'NO'} "
                 f"(BUCKET-CHURN={bucket_churn}, UNION-CHURN={union_churn}).")
    lines.append(f"- **`version_used` stable across the whole run (DR-REPRO)?** "
                 f"{'YES' if version_stable else 'NO'} — observed: "
                 f"{', '.join(f'`{v}`' for v in versions) if versions else 'none'}.")
    lines.append(f"- **Total calls:** {analysis['total_calls']} "
                 f"(errors: {analysis['total_errors']}).")
    if dirty_controls:
        lines.append(f"- **Control sanity:** WARNING — {len(dirty_controls)} gibberish "
                     f"control(s) produced a definite hit: "
                     f"{', '.join(repr(x) for x in dirty_controls)}.")
    else:
        lines.append(f"- **Control sanity:** OK — all {len(controls)} gibberish controls "
                     f"produced clean misses (empty `codes`).")
    if only_possible:
        lines.append(f"- **Sub-finding (DR-D2):** {len(only_possible)} exact source "
                     f"name(s) landed ONLY in `possible_codes` (never `codes`) — a "
                     f"matching-calibration smell: "
                     f"{', '.join(repr(x) for x in only_possible)}.")
    lines.append("")

    # Counts.
    lines.append("## Classification summary (listed queries)\n")
    lines.append("| Classification | Count |")
    lines.append("|----------------|------:|")
    for cl in ("STABLE", "BUCKET-CHURN", "UNION-CHURN", "ERRORED"):
        n = sum(1 for q, c in listed.items() if c["classification"] == cl)
        lines.append(f"| {cl} | {n} |")
    lines.append("")

    # Per-query table.
    lines.append("## Per-query classification\n")
    lines.append("| Query | Agency | Type | OK/Err | classification | "
                 "#union | version_used |")
    lines.append("|-------|--------|------|:------:|----------------|------:|------|")
    def _sortkey(item):
        q, c = item
        order = {"UNION-CHURN": 0, "BUCKET-CHURN": 1, "ERRORED": 2, "STABLE": 3}
        return (c["kind"] != "listed", order.get(c["classification"], 9), q)
    for q, c in sorted(per_query.items(), key=_sortkey):
        vu = ",".join(c["version_used"]) if c["version_used"] else "—"
        lines.append(
            f"| {q[:42]} | {c['agency']} | {c['entity_type'] or '∅'} | "
            f"{c['n_ok']}/{c['n_err']} | {c['classification']} | "
            f"{len(c['union'])} | {vu} |"
        )
    lines.append("")

    # Concrete instability examples.
    instabilities = [(q, c) for q, c in per_query.items()
                     if c["classification"] in ("BUCKET-CHURN", "UNION-CHURN")]
    lines.append("## Concrete instability examples\n")
    if not instabilities:
        lines.append("_None — no BUCKET-CHURN or UNION-CHURN observed._\n")
    else:
        for q, c in instabilities:
            lines.append(f"### `{q}` — {c['classification']}\n")
            lines.append(f"- agency={c['agency']}, type={c['entity_type'] or '∅'}, "
                         f"ok runs={c['n_ok']}, union={c['union']}")
            for code_id, detail in c["churn_codes"].items():
                lines.append(f"- code `{code_id}`: appeared in bucket(s) "
                             f"{detail['buckets']}, present in "
                             f"{detail['present_in_runs']}/{detail['of_ok_runs']} ok runs "
                             f"({detail['type']}-instability)")
            lines.append("\n  Per-run buckets:")
            for r in c["runs"]:
                if r["error"]:
                    lines.append(f"  - run {r['run']}: ERROR {r['error']}")
                else:
                    lines.append(f"  - run {r['run']}: codes={r['codes']} "
                                 f"possible={r['possible_codes']}")
            lines.append("")

    # Errored queries detail.
    errored = [(q, c) for q, c in per_query.items() if c["n_err"] > 0]
    if errored:
        lines.append("## Calls that errored\n")
        for q, c in errored:
            for r in c["runs"]:
                if r["error"]:
                    lines.append(f"- `{q}` run {r['run']}: {r['error']}")
        lines.append("")

    # Query set provenance.
    lines.append("## Query set chosen (and why)\n")
    lines.append("Stratified deterministically from `oracle/expected.csv` (exact "
                 "`primary_name`), across the three CSL agencies (Treasury/BIS/State, "
                 "from `source_sublist`) and entity types. Listed names were filtered "
                 "to *distinctive* candidates (multi-token persons/entities; "
                 "vessel/aircraft identifiers) likely to match, so the bucket "
                 "assignment is what gets exercised. Selection is seed+sort driven "
                 f"(SEED={SEED}); a re-run picks the same names.\n")
    lines.append("| Query | Kind | Agency | Type | sublist |")
    lines.append("|-------|------|--------|------|---------|")
    for sel in selected:
        lines.append(f"| {sel['name'][:42]} | {sel['kind']} | {sel['agency']} | "
                     f"{sel['entity_type'] or '∅'} | {sel['source_sublist'][:34]} |")
    lines.append("")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return {
        "counts": dict(counts),
        "version_stable": version_stable,
        "versions": versions,
        "safe_for_4": safe_for_4,
        "dirty_controls": dirty_controls,
        "only_possible": only_possible,
        "listed_total": listed_total,
    }


# --------------------------------------------------------------------------- #
# Main                                                                          #
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the selected query set and exit (no HTTP calls).")
    ap.add_argument("--analyze-only", metavar="JSONL",
                    help="Re-analyze an existing capture file instead of running.")
    args = ap.parse_args()

    rows = load_rows()
    selected = select_queries(rows)

    if args.dry_run:
        print(f"Selected {len(selected)} queries "
              f"({sum(1 for s in selected if s['kind']=='listed')} listed + "
              f"{sum(1 for s in selected if s['kind']=='control')} controls):")
        for sel in selected:
            print(f"  [{sel['kind']:7}] {sel['agency']:9} "
                  f"{(sel['entity_type'] or '∅'):11} {sel['name']}")
        print(f"\nTotal calls if run: {len(selected) * K}")
        return 0

    if args.analyze_only:
        captures = []
        with open(args.analyze_only, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    captures.append(json.loads(line))
        analysis = analyze(captures)
        summary = write_report(analysis, args.analyze_only, selected)
        print(json.dumps(summary, indent=2))
        return 0

    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    jsonl_path = os.path.join(RESULTS_DIR, f"determinism-probe-{ts}.jsonl")

    print(f"Firing {len(selected) * K} calls "
          f"({len(selected)} queries x K={K}), concurrency={MAX_CONCURRENCY}.",
          file=sys.stderr)
    captures = run_probe(selected, jsonl_path)
    analysis = analyze(captures)
    summary = write_report(analysis, jsonl_path, selected)

    print("\n=== SUMMARY ===")
    print(json.dumps(summary, indent=2))
    print(f"\nRaw: {jsonl_path}")
    print(f"Report: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
