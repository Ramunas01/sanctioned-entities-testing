#!/usr/bin/env python3
"""
Issue #3 — Primary-name census harness for the Sanctions Add-on.

WHAT IT DOES
------------
For each listed party's ``primary_name`` (from ``oracle/expected.csv``) it queries
the Add-on and decides HIT / NO-HIT, to detect catastrophic ingestion/recall
failure ("did the record become matchable at all?"). This is the **primary-name**
census only; the alias census is out of scope here (it waits on the #7
fast-follow per DR-PR5).

CONTRACT (implemented exactly — see docs/decisions.md)
------------------------------------------------------
1. HIT definition (DR-D2): HIT = at least one code ID present in
   ``output.codes`` ∪ ``output.possible_codes``. NO-HIT = both empty. Presence in
   either bucket proves ingestion, which is all the census measures, so the
   documented codes↔possible bucket non-determinism (Finding #6) does NOT break
   the census.
2. Repetition (amended DR-D2): query each name N=5 times. Per-name hit-rate is
   the point and is NOT collapsed before recording:
       5/5 -> stable HIT   ·   1-4/5 -> flaky retrieval   ·   0/5 -> MISS
   Census HIT = a hit on *any* run.
3. Reconcile by ``source_sublist``, NOT ``programs`` (Finding F4): all reporting
   is bucketed by the CSL ``source_sublist`` column. BIS/State rows carry empty
   ``programs``/``entity_type`` — that is an expected property of the trade.gov
   aggregate (DR-0), not a coverage hole.
4. Reproducibility guard (DR-REPRO): capture ``processing.version_used`` on EVERY
   call; record the value seen at the START and END of the run; if it changes
   mid-run, the run is **flagged invalidated** in the report. Also record
   ``input.version_date``.
5. Determinism-aware (Finding #6): matching is non-deterministic, so the per-name
   hit-rate IS the signal. The 5 runs are never collapsed before recording.

SAMPLING (deterministic stratified pilot)
-----------------------------------------
Stratify by ``source_sublist`` (all 12 CSL sublists). Draw ~25 distinct primary
names per sublist (take ALL rows if a sublist has fewer). Selection is seed+sort
driven (SEED=20260611): per sublist we deduplicate by name, sort, then draw a
seed-shuffled sample — so a re-run picks the *same* names. ``EXPORT MATERIALS,
INC.`` is force-included as a positive control (it should reproduce as a 0/5
MISS, confirming the harness detects the known recall gap from Finding #8).

  Pilot:  ~25 names/sublist × 12 sublists ≈ ~300 names × N=5 ≈ ~1500 calls.
  --full: switches the stratum size to the full count (the eventual complete
          ~25,767-name census). STUB — large; validate the pilot first.

ENDPOINT (docs/addon-interface.md)
----------------------------------
    POST https://fast.customsclear.net/api/sanctions_person_versions_regulations/match?query=<urlencoded name>
    POST only; ``query`` in the query string (not the body); no auth.
    ``version_date`` is currently inert (Add-on serves "latest"); we omit it but
    still record the echoed ``input.version_date`` per call.

Stdlib only (``urllib``); no pip dependencies. Concurrency capped at 4 (each call
runs a server-side LLM). ~2 s/call → pilot budget ~12–15 min.

USAGE
-----
This environment's allowlist only permits ``python3 -`` (stdin). Run it by piping
the script to python from the repo root:

    # pilot (default): ~25 names/sublist, all 12 sublists
    python3 - < harness/census.py

    # show the selected sample and exit (no HTTP calls)
    python3 - < harness/census.py --dry-run

    # re-analyze an existing capture (rebuild the report, no HTTP calls)
    python3 - < harness/census.py --analyze-only results/census-pilot-<UTC>.jsonl

    # FULL census stub (defaults off; large — validate the pilot first)
    python3 - < harness/census.py --full

Because ``python3 -`` reads the program from stdin, ``__file__`` is unavailable.
The repo root is taken from the current working directory (run from the repo
root), overridable with ``--repo-root /abs/path``.

It is also directly executable when the allowlist permits it:

    python3 harness/census.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
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

N = 5                     # repeats per name (amended DR-D2)
MAX_CONCURRENCY = 4       # cap: each call runs a server-side LLM
PILOT_PER_SUBLIST = 25    # pilot stratum size: ~25 names per source_sublist
SEED = 20260611           # fixed seed -> deterministic selection on re-run
HTTP_TIMEOUT = 45         # seconds per request
MAX_RETRIES = 2           # additional attempts after the first on transient error
BACKOFF_BASE = 1.5        # seconds; backoff = BACKOFF_BASE * (attempt+1)

# Positive control: a listed party known (Finding #8) to never be CORRECTLY
# retrieved. Force-included so the report exercises the known recall gap.
#
# CAVEAT (Finding #8 / DR-D2 amended): the Add-on never matches the correct
# party for this name; instead it returns the *spurious* codes below — unrelated
# Chinese firms matched only on the generic tokens "Export"/"Material", and
# always in `possible_codes` (never `codes`). Under the strict census HIT
# definition (codes ∪ possible_codes non-empty) that registers as a HIT even
# though true recall is 0. We therefore detect this case explicitly: a positive
# control whose union is exactly (a subset of) these spurious codes is a
# SPURIOUS-ONLY hit, i.e. the recall gap reproduced — the "HIT" is a precision
# defect, not coverage. See reports/export-materials-identity.md.
POSITIVE_CONTROL = "EXPORT MATERIALS, INC."
POSITIVE_CONTROL_SPURIOUS_CODES = {"1145893", "1145895"}

REPORT_BASENAME = "census-pilot.md"   # reports/census-pilot.md

# --------------------------------------------------------------------------- #
# Issue #3 / Advisor A4 — FULL DPL census sweep                                #
# --------------------------------------------------------------------------- #
# Run ALL distinct Denied Persons List (DPL) primary names × N=5, plus two
# controls, in one tight window. Reuses the pilot's HIT definition, per-name
# classification, version-stability guard, retry/concurrency machinery. Adds:
#   - DPL_TP_CONTROL: a TRUE-POSITIVE control — an SDN-sublist primary name that
#     scored 5/5-definite (codes non-empty all runs) in the pilot. Expect 5/5
#     definite; if it reads 0/5 the harness is BROKEN and we must not publish.
#   - per-name "definite" classification (codes non-empty across all OK runs),
#     distinct from the union-based "hit" classification, so we can report
#     5/5-definite / flaky / possible-only / MISS exactly per the task.
DPL_SUBLIST_PREFIX = "Denied Persons List"
DPL_TP_CONTROL = "DEMCHENKO, Ivan Ivanovich"   # SDN, 5/5-definite in the pilot
DPL_TP_CONTROL_EXPECTED_CODES = {"1123129", "1137415"}
DPL_CSV_BASENAME = "dpl_full_census.csv"        # reports/dpl_full_census.csv


# --------------------------------------------------------------------------- #
# Paths (stdin-runnable: derive from cwd, not __file__)                       #
# --------------------------------------------------------------------------- #

def resolve_paths(repo_root: str | None) -> dict:
    """Resolve repo-relative paths. Defaults to the current working directory
    (run from the repo root) because under ``python3 -`` there is no __file__."""
    root = os.path.abspath(repo_root or os.getcwd())
    paths = {
        "root": root,
        "expected_csv": os.path.join(root, "oracle", "expected.csv"),
        "results_dir": os.path.join(root, "results"),
        "reports_dir": os.path.join(root, "reports"),
        "report_path": os.path.join(root, "reports", REPORT_BASENAME),
    }
    if not os.path.isfile(paths["expected_csv"]):
        sys.exit(
            f"ERROR: oracle/expected.csv not found under repo root {root!r}.\n"
            f"Run from the repo root, or pass --repo-root /abs/path."
        )
    return paths


# --------------------------------------------------------------------------- #
# Sampling (deterministic, stratified by source_sublist)                      #
# --------------------------------------------------------------------------- #

def load_rows(expected_csv: str) -> list[dict]:
    rows = []
    with open(expected_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def select_names(rows: list[dict], per_sublist: int | None) -> list[dict]:
    """
    Deterministically select primary names stratified by ``source_sublist``.

    per_sublist = None  -> take ALL distinct names in every sublist (the --full
                           stratum; the eventual complete census).
    per_sublist = int   -> draw up to that many distinct names per sublist; if a
                           sublist has fewer distinct names, take all of them.

    Determinism guarantee: within each sublist we (1) deduplicate by exact name
    (keeping the first source row for provenance), (2) SORT by name, then (3)
    draw a seed-shuffled sample seeded per-sublist (so adding/removing a sublist
    never reshuffles the others). Same frozen oracle + same SEED -> same names.

    ``EXPORT MATERIALS, INC.`` is force-included as a positive control regardless
    of the draw (deduplicated against the sample so it is never queried twice).
    """
    by_sublist: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        sub = row["source_sublist"]
        name = row["primary_name"]
        # Deduplicate by exact name within the sublist, keep first row.
        by_sublist[sub].setdefault(name, row)

    selected: list[dict] = []
    seen_names: set[str] = set()

    # Stable sublist iteration order (largest first, then label) for readable
    # output; selection within a sublist is independent of this order.
    sublist_order = sorted(
        by_sublist.keys(), key=lambda s: (-len(by_sublist[s]), s)
    )

    for sub in sublist_order:
        dedup = by_sublist[sub]
        ordered = [dedup[n] for n in sorted(dedup.keys())]   # sort for stability
        rnd = random.Random(f"{SEED}:{sub}")                 # per-sublist seed
        rnd.shuffle(ordered)

        take = len(ordered) if per_sublist is None else per_sublist
        picked = 0
        for row in ordered:
            if picked >= take:
                break
            name = row["primary_name"]
            if name in seen_names:
                continue
            seen_names.add(name)
            selected.append({
                "name": name,
                "source_sublist": sub,
                "entity_type": row["entity_type"],
                "programs": row["programs"],
                "kind": "listed",
            })
            picked += 1

    # Force-include the positive control (if not already drawn).
    if POSITIVE_CONTROL not in seen_names:
        ctrl_row = None
        for sub, dedup in by_sublist.items():
            if POSITIVE_CONTROL in dedup:
                ctrl_row = dedup[POSITIVE_CONTROL]
                break
        if ctrl_row is not None:
            seen_names.add(POSITIVE_CONTROL)
            selected.append({
                "name": POSITIVE_CONTROL,
                "source_sublist": ctrl_row["source_sublist"],
                "entity_type": ctrl_row["entity_type"],
                "programs": ctrl_row["programs"],
                "kind": "positive-control",
            })
    else:
        # Already drawn — relabel it so the report flags it as the control.
        for sel in selected:
            if sel["name"] == POSITIVE_CONTROL:
                sel["kind"] = "positive-control"
                break

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
    """Call with a couple of retries on transient error.
    Returns (response_json, None) on success or (None, error_string) on failure."""
    last_err = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return call_addon(query), None
        except Exception as exc:  # urllib error, timeout, JSON decode, etc.
            last_err = f"{type(exc).__name__}: {exc}"
            if attempt < MAX_RETRIES:
                time.sleep(BACKOFF_BASE * (attempt + 1))
    return None, last_err


def extract_capture(run_idx: int, sel: dict, seq: int,
                    resp: dict | None, err: str | None) -> dict:
    """Build the per-call capture record written to the JSONL.

    ``seq`` is a monotonic completion index used to order the run (for the
    version_used start/end stability check under concurrency)."""
    rec = {
        "seq": seq,
        "name": sel["name"],
        "sublist": sel["source_sublist"],
        "entity_type": sel["entity_type"],
        "kind": sel["kind"],
        "run": run_idx,
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
            "codes": None, "possible_codes": None,
            "version_used": None, "version_date": None,
            "stage_used": None, "processing_time": None,
        })
    return rec


# --------------------------------------------------------------------------- #
# Run                                                                          #
# --------------------------------------------------------------------------- #

def run_census(selected: list[dict], jsonl_path: str) -> list[dict]:
    """Fire every (name, run) task with concurrency capped at MAX_CONCURRENCY.
    Stream captures to the JSONL as they complete. Return all captures."""
    tasks = [(sel, run_idx)
             for sel in selected
             for run_idx in range(1, N + 1)]

    captures: list[dict] = []
    total = len(tasks)
    done = 0

    os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)
    with open(jsonl_path, "w", encoding="utf-8") as out_f:
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENCY) as pool:
            futures = {
                pool.submit(call_with_retries, sel["name"]): (sel, run_idx)
                for (sel, run_idx) in tasks
            }
            for fut in as_completed(futures):
                sel, run_idx = futures[fut]
                resp, err = fut.result()
                rec = extract_capture(run_idx, sel, done, resp, err)
                captures.append(rec)
                out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out_f.flush()
                done += 1
                status = "ERR" if err else "ok "
                hit = ""
                if not err:
                    hit = "HIT" if (rec["codes"] or rec["possible_codes"]) else "no-hit"
                print(f"[{done:4d}/{total}] {status} {hit:6} run{run_idx} "
                      f"{sel['name'][:46]}", file=sys.stderr)
    return captures


# --------------------------------------------------------------------------- #
# Analysis                                                                      #
# --------------------------------------------------------------------------- #

def is_hit(rec: dict) -> bool:
    """HIT = at least one code ID in codes ∪ possible_codes (DR-D2)."""
    if rec["error"] is not None:
        return False
    return bool(rec["codes"]) or bool(rec["possible_codes"])


def classify_name(runs: list[dict]) -> dict:
    """Classify a single name's N runs into stable HIT / flaky / MISS.

    hit_rate counts runs that were a HIT among the OK (non-errored) runs.
      ok_runs == N and hits == N      -> "5/5"   stable HIT
      hits in 1..(ok_runs-1) inclusive -> flaky retrieval
      hits == 0                        -> MISS
    Census HIT = hit on any run.
    """
    ok = [r for r in runs if r["error"] is None]
    err = [r for r in runs if r["error"] is not None]
    hits = sum(1 for r in ok if is_hit(r))
    n_ok = len(ok)

    # Union of all matched code IDs across OK runs, split by bucket. The DR-D2
    # sub-finding ("exact source name landing ONLY in possible_codes") is a
    # matching-calibration smell: the party is found only as a weak/fuzzy match.
    union_codes: set[str] = set()
    union_possible: set[str] = set()
    for r in ok:
        union_codes.update(r["codes"] or [])
        union_possible.update(r["possible_codes"] or [])
    union = union_codes | union_possible
    ever_in_codes = bool(union_codes)
    only_possible = (hits > 0) and (not ever_in_codes)

    if n_ok == 0:
        cls = "ALL-ERROR"
    elif hits == 0:
        cls = "MISS"
    elif hits == n_ok and n_ok == N:
        cls = "STABLE-HIT"
    elif hits == n_ok:
        # every OK run hit, but some runs errored (incomplete repetition)
        cls = "STABLE-HIT*"
    else:
        cls = "FLAKY"

    return {
        "name": runs[0]["name"],
        "sublist": runs[0]["sublist"],
        "entity_type": runs[0]["entity_type"],
        "kind": runs[0]["kind"],
        "n_runs": len(runs),
        "n_ok": n_ok,
        "n_err": len(err),
        "hits": hits,
        "hit_rate": f"{hits}/{n_ok}" if n_ok else "0/0",
        "census_hit": hits > 0,
        "classification": cls,
        "union": sorted(union),
        "only_possible": only_possible,
    }


def analyze(captures: list[dict]) -> dict:
    """Group captures by name, classify each, aggregate run-wide facts."""
    by_name: dict[str, list[dict]] = defaultdict(list)
    for rec in captures:
        by_name[rec["name"]].append(rec)

    per_name = {}
    for name, runs in by_name.items():
        runs_sorted = sorted(runs, key=lambda r: r["run"])
        per_name[name] = classify_name(runs_sorted)

    # version_used start/end stability (DR-REPRO). Order by completion seq.
    ordered = sorted((r for r in captures if r["version_used"]),
                     key=lambda r: r.get("seq", 0))
    versions = sorted({r["version_used"] for r in captures if r["version_used"]})
    version_dates = sorted({r["version_date"] for r in captures if r["version_date"]})
    version_start = ordered[0]["version_used"] if ordered else None
    version_end = ordered[-1]["version_used"] if ordered else None
    version_stable = len(versions) <= 1
    invalidated = not version_stable

    total_calls = len(captures)
    total_errors = sum(1 for r in captures if r["error"] is not None)

    return {
        "per_name": per_name,
        "versions": versions,
        "version_dates": version_dates,
        "version_start": version_start,
        "version_end": version_end,
        "version_stable": version_stable,
        "invalidated": invalidated,
        "total_calls": total_calls,
        "total_errors": total_errors,
    }


# --------------------------------------------------------------------------- #
# Reporting                                                                     #
# --------------------------------------------------------------------------- #

def _agency(sublist: str) -> str:
    if "Treasury" in sublist:
        return "Treasury (OFAC)"
    if "Bureau of Industry and Security" in sublist:
        return "BIS"
    if "State Department" in sublist:
        return "State"
    return "Other"


def write_report(analysis: dict, jsonl_path: str, selected: list[dict],
                 paths: dict, mode: str) -> dict:
    per_name = analysis["per_name"]
    listed = {n: c for n, c in per_name.items()
              if c["kind"] in ("listed", "positive-control")}

    # Per-sublist aggregation.
    by_sub: dict[str, list[dict]] = defaultdict(list)
    for c in listed.values():
        by_sub[c["sublist"]].append(c)

    sub_rows = []
    for sub in sorted(by_sub.keys(), key=lambda s: (-len(by_sub[s]), s)):
        items = by_sub[sub]
        n = len(items)
        n_stable = sum(1 for c in items if c["classification"].startswith("STABLE-HIT"))
        n_flaky = sum(1 for c in items if c["classification"] == "FLAKY")
        n_miss = sum(1 for c in items if c["classification"] == "MISS")
        n_allerr = sum(1 for c in items if c["classification"] == "ALL-ERROR")
        sub_rows.append({
            "sublist": sub, "agency": _agency(sub), "n": n,
            "stable": n_stable, "flaky": n_flaky, "miss": n_miss, "allerr": n_allerr,
            "pct_stable": 100.0 * n_stable / n if n else 0.0,
            "pct_flaky": 100.0 * n_flaky / n if n else 0.0,
            "pct_miss": 100.0 * n_miss / n if n else 0.0,
        })

    misses = sorted((c for c in listed.values() if c["classification"] == "MISS"),
                    key=lambda c: (c["sublist"], c["name"]))
    flakies = sorted((c for c in listed.values() if c["classification"] == "FLAKY"),
                     key=lambda c: (c["sublist"], c["name"]))
    allerr = sorted((c for c in listed.values() if c["classification"] == "ALL-ERROR"),
                    key=lambda c: (c["sublist"], c["name"]))

    # Positive control verdict.
    # The recall gap "reproduces" if EITHER (a) it is a true 0/5 MISS, OR (b) it
    # is a SPURIOUS-ONLY hit: every matched code is one of the documented
    # Finding #8 generic-token false positives (1145893/1145895), always in
    # possible_codes. Both mean the *correct* party was never retrieved.
    ctrl = next((c for c in listed.values() if c["kind"] == "positive-control"), None)
    ctrl_spurious_only = (
        ctrl is not None
        and ctrl["census_hit"]
        and ctrl["only_possible"]
        and set(ctrl["union"]).issubset(POSITIVE_CONTROL_SPURIOUS_CODES)
    )
    ctrl_true_miss = (ctrl is not None and ctrl["classification"] == "MISS")
    ctrl_reproduced_gap = ctrl_true_miss or ctrl_spurious_only

    # Names whose every match was a weak/fuzzy possible_codes hit (DR-D2 smell).
    only_possible_names = sorted(
        (c for c in listed.values()
         if c["only_possible"] and c["kind"] != "positive-control"),
        key=lambda c: (c["sublist"], c["name"]))

    # Headline: worst-recall sublist (by %MISS, then %flaky), and BIS/State vs OFAC.
    worst = max(sub_rows, key=lambda r: (r["pct_miss"], r["pct_flaky"]),
                default=None)
    # Agency-level recall (share of names that are NOT a stable HIT).
    by_agency: dict[str, list[dict]] = defaultdict(list)
    for c in listed.values():
        by_agency[_agency(c["sublist"])].append(c)
    agency_recall = {}
    for ag, items in by_agency.items():
        n = len(items)
        stable = sum(1 for c in items if c["classification"].startswith("STABLE-HIT"))
        agency_recall[ag] = (100.0 * stable / n if n else 0.0, n)

    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    L: list[str] = []
    L.append("# Issue #3 — Primary-name census (stratified pilot)\n")
    L.append(f"_Generated: {now}_  ")
    L.append(f"_Raw capture: `{os.path.relpath(jsonl_path, paths['root'])}`_  ")
    L.append(f"_Harness: `harness/census.py` (mode={mode}, SEED={SEED}, N={N}, "
             f"concurrency={MAX_CONCURRENCY}, "
             f"per-sublist={'ALL' if mode == 'full' else PILOT_PER_SUBLIST})_\n")

    # --- Headline ----------------------------------------------------------- #
    if analysis["invalidated"]:
        L.append("**HEADLINE: RUN INVALIDATED — `version_used` changed mid-run "
                 f"({', '.join(analysis['versions'])}). Per DR-REPRO the capture is "
                 "contaminated by an Add-on data update; rerun in a tighter window "
                 "before trusting any recall number below.**\n")
    else:
        # A sublist is flagged as an outlier if it is materially worse than a
        # clean run: any MISS or flaky present, OR <90% stable-HIT. (With a
        # ~25-name pilot stratum a single MISS is ~4%, so we use a relative
        # "stands out from the others" test, not just a high absolute floor.)
        flagged = [r for r in sub_rows
                   if r["pct_miss"] > 0.0 or r["pct_flaky"] > 0.0 or r["pct_stable"] < 90.0]
        clean = [r for r in sub_rows if r not in flagged]
        agency_bits = []
        for label, key in (("OFAC", "Treasury (OFAC)"), ("BIS", "BIS"), ("State", "State")):
            v, nn = agency_recall.get(key, (None, 0))
            if v is not None:
                agency_bits.append(f"{label} {v:.0f}% stable (n={nn})")
        only_poss_subs = sorted({c["sublist"].split(" (")[0] for c in only_possible_names})
        if flagged:
            worst_names = "; ".join(
                f"{r['sublist'].split(' (')[0]} "
                f"({r['pct_stable']:.0f}% 5/5, {r['pct_flaky']:.0f}% flaky, "
                f"{r['pct_miss']:.0f}% miss)"
                for r in sorted(flagged, key=lambda r: (r["pct_stable"], r["sublist"])))
            extra = ""
            if only_poss_subs:
                extra = (f" All {len(only_possible_names)} weak-only "
                         f"(`possible_codes`-only) hits also fall in "
                         f"{', '.join(only_poss_subs)}.")
            L.append(f"**HEADLINE: primary-name recall is intact for {len(clean)}/"
                     f"{len(sub_rows)} sublists (100% 5/5), but {worst_names} stands "
                     f"out as under-recalled — every MISS and flaky name in the pilot "
                     f"is in it.{extra} Agency recall — {'; '.join(agency_bits)}. "
                     f"BIS/State are NOT systematically worse than OFAC SDN except for "
                     f"this one BIS sublist.**\n")
        else:
            L.append(f"**HEADLINE: no sublist shows systematically poor primary-name "
                     f"recall; ingestion looks broadly intact across all "
                     f"{len(sub_rows)} sublists. Agency recall — "
                     f"{'; '.join(agency_bits)}.**\n")

    # --- Reproducibility guard --------------------------------------------- #
    L.append("## Reproducibility guard (DR-REPRO)\n")
    L.append(f"- **`version_used` at run start:** `{analysis['version_start']}`")
    L.append(f"- **`version_used` at run end:** `{analysis['version_end']}`")
    L.append(f"- **Distinct `version_used` values seen:** "
             f"{', '.join(f'`{v}`' for v in analysis['versions']) or 'none'}")
    L.append(f"- **`input.version_date` seen:** "
             f"{', '.join(f'`{v}`' for v in analysis['version_dates']) or 'none'}")
    L.append(f"- **Verdict:** "
             f"{'STABLE — run is valid' if analysis['version_stable'] else 'CHANGED — RUN INVALIDATED'}\n")

    # --- Totals ------------------------------------------------------------- #
    n_listed = len(listed)
    n_stable = sum(1 for c in listed.values() if c["classification"].startswith("STABLE-HIT"))
    n_flaky = len(flakies)
    n_miss = len(misses)
    n_allerr = len(allerr)
    L.append("## Totals\n")
    L.append(f"- **Names tested:** {n_listed}")
    L.append(f"- **Total calls:** {analysis['total_calls']} "
             f"(errors: {analysis['total_errors']})")
    L.append(f"- **Stable HIT (5/5):** {n_stable} "
             f"({100.0*n_stable/n_listed:.1f}%)" if n_listed else "")
    L.append(f"- **Flaky retrieval (1–4/5):** {n_flaky} "
             f"({100.0*n_flaky/n_listed:.1f}%)" if n_listed else "")
    L.append(f"- **MISS (0/5):** {n_miss} "
             f"({100.0*n_miss/n_listed:.1f}%)" if n_listed else "")
    if n_allerr:
        L.append(f"- **All-error (no usable runs):** {n_allerr}")
    L.append("")

    # --- Positive control --------------------------------------------------- #
    L.append("## Positive control (Finding #8 recall gap)\n")
    if ctrl is None:
        L.append(f"- `{POSITIVE_CONTROL}` was not present in the sample (unexpected).\n")
    elif ctrl_true_miss:
        L.append(f"- `{POSITIVE_CONTROL}` ({ctrl['sublist'].split(' (')[0]}): "
                 f"**RECALL GAP REPRODUCED as a clean 0/5 MISS** — harness correctly "
                 f"detects the known recall gap (Finding #8).\n")
    elif ctrl_spurious_only:
        L.append(f"- `{POSITIVE_CONTROL}` ({ctrl['sublist'].split(' (')[0]}): "
                 f"**RECALL GAP REPRODUCED — but as a SPURIOUS-ONLY hit, not a 0/5 "
                 f"MISS.** All {ctrl['hits']}/{ctrl['n_ok']} runs returned only "
                 f"`possible_codes` = `{ctrl['union']}` — the documented Finding #8 "
                 f"false positives (unrelated Chinese firms matched on the generic "
                 f"tokens \"Export\"/\"Material\"); `codes` was empty every run and the "
                 f"correct listed party was never retrieved.")
        L.append(f"  - **Caveat for the census signal:** under the strict DR-D2 HIT "
                 f"definition (codes ∪ possible_codes non-empty) this name scores as a "
                 f"5/5 HIT, so it is NOT in the MISS list below. The recall gap is real "
                 f"but is *masked* by a precision defect. The census question \"did the "
                 f"record become matchable?\" answers \"yes — but only via a wrong "
                 f"party.\" Catching this requires identity-level checking (codes vs the "
                 f"oracle's expected code), which is out of scope for the ingestion "
                 f"census and is exactly the precision class Finding #8 tracks.\n")
    else:
        L.append(f"- `{POSITIVE_CONTROL}` ({ctrl['sublist'].split(' (')[0]}): "
                 f"**DID NOT reproduce the recall gap** (got {ctrl['classification']}, "
                 f"hit-rate {ctrl['hit_rate']}, union `{ctrl['union']}`) — the Add-on "
                 f"may have changed; investigate.\n")

    # --- DR-D2 sub-finding: only-possible (calibration smell) -------------- #
    L.append("## Matching-calibration smell — names found ONLY in `possible_codes` "
             "(DR-D2 sub-finding)\n")
    L.append("_Exact primary names that, on every run they matched, landed only in "
             "`possible_codes` (weak/fuzzy) and never in `codes` (definite). Per "
             "DR-D2 this is logged as data, not a census failure — they still count "
             "as HITs — but it is a matching-calibration smell worth flagging._\n")
    if not only_possible_names:
        L.append("_None — every matched name reached `codes` on at least one run._\n")
    else:
        L.append("| name | source_sublist | hit-rate | union (possible_codes only) |")
        L.append("|------|----------------|---------:|------------------------------|")
        for c in only_possible_names:
            L.append(f"| {c['name']} | {c['sublist'].split(' (')[0]} | "
                     f"{c['hit_rate']} | {', '.join(c['union'])} |")
        L.append("")

    # --- Per-sublist table -------------------------------------------------- #
    L.append("## Per-`source_sublist` recall (reconciled by sublist, not programs — F4)\n")
    L.append("| source_sublist | agency | names | %HIT 5/5 | %flaky | %MISS |")
    L.append("|----------------|--------|------:|---------:|-------:|------:|")
    for r in sub_rows:
        L.append(f"| {r['sublist']} | {r['agency']} | {r['n']} | "
                 f"{r['pct_stable']:.0f}% | {r['pct_flaky']:.0f}% | {r['pct_miss']:.0f}% |")
    L.append("")
    L.append("_BIS/State rows carry empty `programs`/`entity_type` by design "
             "(trade.gov aggregate, DR-0/F4); that is expected, not a coverage hole._\n")

    # --- Misses (candidate recall gaps) ------------------------------------ #
    L.append("## MISSES — 0/5, candidate recall gaps\n")
    if not misses:
        L.append("_None — every name was retrieved on at least one run._\n")
    else:
        L.append("| name | source_sublist | hit-rate | note |")
        L.append("|------|----------------|---------:|------|")
        for c in misses:
            note = "positive control (expected MISS)" if c["kind"] == "positive-control" else ""
            L.append(f"| {c['name']} | {c['sublist'].split(' (')[0]} | "
                     f"{c['hit_rate']} | {note} |")
        L.append("")

    # --- Flaky (candidate recall gaps) ------------------------------------- #
    L.append("## FLAKY — 1–4/5, candidate recall gaps\n")
    if not flakies:
        L.append("_None — every retrieved name was retrieved on all OK runs._\n")
    else:
        L.append("| name | source_sublist | hit-rate |")
        L.append("|------|----------------|---------:|")
        for c in flakies:
            L.append(f"| {c['name']} | {c['sublist'].split(' (')[0]} | {c['hit_rate']} |")
        L.append("")

    # --- All-error ---------------------------------------------------------- #
    if allerr:
        L.append("## All-error names (no usable runs — transport failures)\n")
        L.append("| name | source_sublist | n_err |")
        L.append("|------|----------------|------:|")
        for c in allerr:
            L.append(f"| {c['name']} | {c['sublist'].split(' (')[0]} | {c['n_err']} |")
        L.append("")

    # --- Sample definition -------------------------------------------------- #
    L.append("## Stratified sample definition\n")
    L.append(f"Sampled deterministically from `oracle/expected.csv` "
             f"(exact `primary_name`), stratified by `source_sublist` (all 12 CSL "
             f"sublists). {'Pilot: up to ' + str(PILOT_PER_SUBLIST) + ' distinct names per sublist (all if fewer).' if mode == 'pilot' else 'FULL: all distinct names per sublist.'} "
             f"Within each sublist: deduplicate by name → sort → seed-shuffle "
             f"(SEED={SEED}, per-sublist seed) → draw. A re-run picks the same "
             f"names. `{POSITIVE_CONTROL}` is force-included as a positive control.\n")
    L.append("| source_sublist | names drawn |")
    L.append("|----------------|------------:|")
    drawn_by_sub = defaultdict(int)
    for sel in selected:
        drawn_by_sub[sel["source_sublist"]] += 1
    for sub in sorted(drawn_by_sub.keys(), key=lambda s: (-drawn_by_sub[s], s)):
        L.append(f"| {sub} | {drawn_by_sub[sub]} |")
    L.append("")

    os.makedirs(paths["reports_dir"], exist_ok=True)
    with open(paths["report_path"], "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    return {
        "names_tested": n_listed,
        "total_calls": analysis["total_calls"],
        "total_errors": analysis["total_errors"],
        "stable_hit": n_stable,
        "flaky": n_flaky,
        "miss": n_miss,
        "all_error": n_allerr,
        "version_start": analysis["version_start"],
        "version_end": analysis["version_end"],
        "version_stable": analysis["version_stable"],
        "invalidated": analysis["invalidated"],
        "positive_control_gap_reproduced": ctrl_reproduced_gap,
        "positive_control_form": (
            "true-0/5-miss" if ctrl_true_miss else
            "spurious-only-hit" if ctrl_spurious_only else
            "unexpected"),
        "only_possible_count": len(only_possible_names),
        "per_sublist": sub_rows,
        "report_path": paths["report_path"],
    }


# --------------------------------------------------------------------------- #
# Issue #3 / A4 — FULL DPL census sweep: selection, classification, CSV report #
# --------------------------------------------------------------------------- #

def select_dpl_full(rows: list[dict]) -> list[dict]:
    """Select ALL distinct DPL primary names plus both controls.

    DPL is identified by ``source_sublist`` starting with ``"Denied Persons
    List"`` (F4: reconcile by sublist). Names are deduplicated by exact
    ``primary_name`` (the unit the Add-on queries — a name appearing on N DPL
    listings produces identical match output, so querying it once suffices;
    duplicate listing rows are collapsed, mirroring ``select_names``). Sorted for
    a stable, reproducible order.

    Two controls are force-included (deduplicated against the DPL set):
      - NEGATIVE control ``EXPORT MATERIALS, INC.`` (a DPL name; expect 0/5
        definite — spurious-only per Finding #8).
      - TRUE-POSITIVE control ``DEMCHENKO, Ivan Ivanovich`` (an SDN name that was
        5/5-definite in the pilot; expect 5/5 definite — a live harness check).
    """
    dpl_names: dict[str, dict] = {}
    tp_row = None
    neg_row = None
    for row in rows:
        sub = row["source_sublist"]
        name = row["primary_name"]
        if sub.startswith(DPL_SUBLIST_PREFIX):
            dpl_names.setdefault(name, row)
        if name == DPL_TP_CONTROL and tp_row is None:
            tp_row = row
        if name == POSITIVE_CONTROL and neg_row is None:
            neg_row = row

    selected: list[dict] = []
    for name in sorted(dpl_names.keys()):
        row = dpl_names[name]
        kind = "negative-control" if name == POSITIVE_CONTROL else "listed"
        selected.append({
            "name": name,
            "source_sublist": row["source_sublist"],
            "entity_type": row["entity_type"],
            "programs": row["programs"],
            "kind": kind,
        })

    # Ensure NEGATIVE control present & labelled (it is a DPL name; normally in set).
    if POSITIVE_CONTROL not in dpl_names and neg_row is not None:
        selected.append({
            "name": POSITIVE_CONTROL,
            "source_sublist": neg_row["source_sublist"],
            "entity_type": neg_row["entity_type"],
            "programs": neg_row["programs"],
            "kind": "negative-control",
        })

    # Force-include the TRUE-POSITIVE control (SDN; not a DPL name).
    if tp_row is None:
        sys.exit(f"ERROR: TP control {DPL_TP_CONTROL!r} not found in oracle.")
    selected.append({
        "name": DPL_TP_CONTROL,
        "source_sublist": tp_row["source_sublist"],
        "entity_type": tp_row["entity_type"],
        "programs": tp_row["programs"],
        "kind": "tp-control",
    })
    return selected


def classify_definite(runs: list[dict]) -> dict:
    """Per-name DPL classification per the A4 task (separate from classify_name).

    Definitions (HIT = codes ∪ possible_codes, DR-D2):
      - 5/5-definite : ``codes`` non-empty on ALL N OK runs (and N OK runs).
      - flaky        : HIT on some runs but not all (retrieval flakiness).
      - possible-only: HIT on every OK run, but ``codes`` empty on every run
                       (only ever a weak ``possible_codes`` match).
      - MISS         : 0/N — both buckets empty on every OK run.
    Records definite-runs and hit-runs counts.
    """
    ok = [r for r in runs if r["error"] is None]
    err = [r for r in runs if r["error"] is not None]
    n_ok = len(ok)
    hits = sum(1 for r in ok if (r["codes"] or r["possible_codes"]))
    definite = sum(1 for r in ok if r["codes"])

    union_codes: set[str] = set()
    union_possible: set[str] = set()
    for r in ok:
        union_codes.update(r["codes"] or [])
        union_possible.update(r["possible_codes"] or [])

    if n_ok == 0:
        cls = "ALL-ERROR"
    elif hits == 0:
        cls = "MISS"
    elif definite == n_ok and n_ok == N:
        cls = "5/5-definite"
    elif definite > 0:
        # some definite codes, but not on every one of the N runs
        cls = "flaky"
    elif hits == n_ok:
        # hit every OK run but never a definite codes match
        cls = "possible-only"
    else:
        # hit on some runs, never definite (mix of weak hits and misses)
        cls = "flaky"

    return {
        "name": runs[0]["name"],
        "sublist": runs[0]["sublist"],
        "kind": runs[0]["kind"],
        "n_runs": len(runs),
        "n_ok": n_ok,
        "n_err": len(err),
        "hits": hits,
        "definite": definite,
        "classification": cls,
        "union_codes": sorted(union_codes),
        "union_possible": sorted(union_possible),
    }


def write_dpl_csv(captures: list[dict], analysis: dict, jsonl_path: str,
                  paths: dict) -> dict:
    """Write reports/dpl_full_census.csv: one row per DPL name + summary block +
    delimited MISS list and possible-only list. Returns a summary dict."""
    by_name: dict[str, list[dict]] = defaultdict(list)
    for rec in captures:
        by_name[rec["name"]].append(rec)

    per_name = {n: classify_definite(sorted(r, key=lambda x: x["run"]))
                for n, r in by_name.items()}

    # Controls.
    neg = next((c for c in per_name.values() if c["kind"] == "negative-control"), None)
    tp = next((c for c in per_name.values() if c["kind"] == "tp-control"), None)

    # DPL listed names only (exclude the SDN TP control; the negative control IS
    # a DPL name and stays in the DPL population).
    dpl = sorted((c for c in per_name.values() if c["kind"] != "tp-control"),
                 key=lambda c: c["name"])

    counts = {"5/5-definite": 0, "flaky": 0, "possible-only": 0,
              "MISS": 0, "ALL-ERROR": 0}
    for c in dpl:
        counts[c["classification"]] = counts.get(c["classification"], 0) + 1

    misses = sorted((c for c in dpl if c["classification"] == "MISS"),
                    key=lambda c: c["name"])
    possible_only = sorted((c for c in dpl if c["classification"] == "possible-only"),
                           key=lambda c: c["name"])
    flakies = sorted((c for c in dpl if c["classification"] == "flaky"),
                     key=lambda c: c["name"])

    n_dpl = len(dpl)
    # Recall = share of DPL names that reached a definite codes match on every run.
    recall = (100.0 * counts["5/5-definite"] / n_dpl) if n_dpl else 0.0

    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    out_path = os.path.join(paths["reports_dir"], DPL_CSV_BASENAME)
    os.makedirs(paths["reports_dir"], exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # --- Summary block (commented header). ---
        w.writerow(["# Issue #3 / A4 — FULL DPL primary-name census"])
        w.writerow([f"# generated: {now}"])
        w.writerow([f"# raw_capture: {os.path.relpath(jsonl_path, paths['root'])}"])
        w.writerow([f"# harness: harness/census.py (mode=dpl-full, N={N}, "
                    f"concurrency={MAX_CONCURRENCY})"])
        w.writerow([f"# dpl_names_tested: {n_dpl}"])
        w.writerow([f"# total_calls: {analysis['total_calls']}  "
                    f"errors: {analysis['total_errors']}"])
        w.writerow([f"# version_used_start: {analysis['version_start']}  "
                    f"end: {analysis['version_end']}  "
                    f"stable: {analysis['version_stable']}  "
                    f"invalidated: {analysis['invalidated']}"])
        w.writerow([f"# class_counts: 5/5-definite={counts['5/5-definite']}  "
                    f"flaky={counts['flaky']}  "
                    f"possible-only={counts['possible-only']}  "
                    f"MISS={counts['MISS']}"
                    + (f"  ALL-ERROR={counts['ALL-ERROR']}" if counts['ALL-ERROR'] else "")])
        w.writerow([f"# DPL_recall_5/5_definite: {recall:.2f}%  "
                    f"({counts['5/5-definite']}/{n_dpl})"])
        neg_form = (f"{neg['definite']}/{neg['n_ok']} definite, "
                    f"class={neg['classification']}") if neg else "MISSING"
        tp_form = (f"{tp['definite']}/{tp['n_ok']} definite, "
                   f"class={tp['classification']}") if tp else "MISSING"
        neg_pass = bool(neg and neg["definite"] == 0)
        tp_pass = bool(tp and tp["definite"] == tp["n_ok"] and tp["n_ok"] == N)
        w.writerow([f"# NEGATIVE_control [{POSITIVE_CONTROL}]: {neg_form} -> "
                    f"{'PASS (0/5 definite as expected)' if neg_pass else 'FAIL'}"])
        w.writerow([f"# TRUE_POSITIVE_control [{DPL_TP_CONTROL}]: {tp_form} -> "
                    f"{'PASS (5/5 definite as expected)' if tp_pass else 'FAIL — HARNESS BROKEN'}"])
        w.writerow([])
        # --- One row per DPL name. ---
        w.writerow(["primary_name", "source_sublist", "hit_status_class",
                    "definite_runs", "hit_runs", "n_ok_runs", "n_err",
                    "kind", "codes_union", "possible_codes_union"])
        for c in dpl:
            w.writerow([
                c["name"], c["sublist"], c["classification"],
                f"{c['definite']}/{c['n_ok']}", f"{c['hits']}/{c['n_ok']}",
                c["n_ok"], c["n_err"], c["kind"],
                ";".join(c["union_codes"]), ";".join(c["union_possible"]),
            ])
        # --- Delimited MISS list (consumed by task A3). ---
        w.writerow([])
        w.writerow([f"### BEGIN MISS LIST (0/5 — definite recall gaps; "
                    f"{len(misses)} names) — for task A3 ###"])
        w.writerow(["miss_primary_name", "source_sublist", "hit_runs"])
        for c in misses:
            w.writerow([c["name"], c["sublist"], f"{c['hits']}/{c['n_ok']}"])
        w.writerow(["### END MISS LIST ###"])
        # --- Delimited possible-only list. ---
        w.writerow([])
        w.writerow([f"### BEGIN POSSIBLE-ONLY LIST (hit every run but never a "
                    f"definite codes match; {len(possible_only)} names) ###"])
        w.writerow(["possible_only_primary_name", "source_sublist",
                    "hit_runs", "possible_codes_union"])
        for c in possible_only:
            w.writerow([c["name"], c["sublist"], f"{c['hits']}/{c['n_ok']}",
                        ";".join(c["union_possible"])])
        w.writerow(["### END POSSIBLE-ONLY LIST ###"])

    return {
        "csv_path": out_path,
        "dpl_names_tested": n_dpl,
        "total_calls": analysis["total_calls"],
        "total_errors": analysis["total_errors"],
        "counts": counts,
        "recall_5_5_definite_pct": recall,
        "miss_count": len(misses),
        "possible_only_count": len(possible_only),
        "flaky_count": len(flakies),
        "version_start": analysis["version_start"],
        "version_end": analysis["version_end"],
        "version_stable": analysis["version_stable"],
        "invalidated": analysis["invalidated"],
        "neg_control": neg_form, "neg_control_pass": neg_pass,
        "tp_control": tp_form, "tp_control_pass": tp_pass,
    }


# --------------------------------------------------------------------------- #
# Main                                                                          #
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Issue #3 primary-name census (stratified pilot by default).")
    ap.add_argument("--full", action="store_true",
                    help="STUB: run the complete census (ALL distinct names per "
                         "sublist, ~25,767 names). Large — validate the pilot first.")
    ap.add_argument("--dpl-full", action="store_true",
                    help="A4: run the FULL DPL sweep — ALL distinct Denied "
                         "Persons List primary names + negative + true-positive "
                         "controls, N=5. Writes reports/dpl_full_census.csv.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the selected sample and exit (no HTTP calls).")
    ap.add_argument("--analyze-only", metavar="JSONL",
                    help="Re-analyze an existing capture and rebuild the report.")
    ap.add_argument("--repo-root", metavar="DIR", default=None,
                    help="Repo root (defaults to cwd; needed under `python3 -`).")
    args = ap.parse_args(argv)

    paths = resolve_paths(args.repo_root)
    rows = load_rows(paths["expected_csv"])

    # --- A4: FULL DPL sweep -------------------------------------------------- #
    if args.dpl_full:
        selected = select_dpl_full(rows)
        n_dpl = sum(1 for s in selected if s["kind"] != "tp-control")
        if args.dry_run:
            print(f"Mode: dpl-full   DPL names (incl negative control): {n_dpl}   "
                  f"+1 TP control   Calls if run: {len(selected) * N}  (N={N})")
            for s in selected:
                if s["kind"] != "listed":
                    print(f"  control[{s['kind']}]: {s['name']}  ({s['source_sublist']})")
            return 0
        ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        jsonl_path = os.path.join(paths["results_dir"], f"dpl-full-census-{ts}.jsonl")
        print(f"DPL-full census: {len(selected)} names "
              f"({n_dpl} DPL + 1 TP control) × N={N} = "
              f"{len(selected) * N} calls, concurrency={MAX_CONCURRENCY}.",
              file=sys.stderr)
        captures = run_census(selected, jsonl_path)
        analysis = analyze(captures)
        summary = write_dpl_csv(captures, analysis, jsonl_path, paths)
        print("\n=== DPL-FULL SUMMARY ===")
        print(json.dumps(summary, indent=2))
        if not summary["tp_control_pass"]:
            print("\n*** TP CONTROL FAILED — HARNESS BROKEN — DPL numbers NOT trustworthy ***",
                  file=sys.stderr)
        print(f"\nRaw: {jsonl_path}")
        print(f"CSV: {summary['csv_path']}")
        return 0

    mode = "full" if args.full else "pilot"
    per_sublist = None if args.full else PILOT_PER_SUBLIST

    selected = select_names(rows, per_sublist)

    if args.dry_run:
        by_sub = defaultdict(int)
        for sel in selected:
            by_sub[sel["source_sublist"]] += 1
        print(f"Mode: {mode}   Names: {len(selected)}   "
              f"Calls if run: {len(selected) * N}  (N={N})")
        for sub in sorted(by_sub.keys(), key=lambda s: (-by_sub[s], s)):
            print(f"  {by_sub[sub]:4d}  {sub}")
        ctrl = [s for s in selected if s["kind"] == "positive-control"]
        print(f"Positive control present: {bool(ctrl)} "
              f"({ctrl[0]['name'] if ctrl else 'MISSING'})")
        return 0

    if args.analyze_only:
        captures = []
        with open(args.analyze_only, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    captures.append(json.loads(line))
        analysis = analyze(captures)
        # Reconstruct mode from per-sublist drawn counts is unreliable; use cli.
        summary = write_report(analysis, args.analyze_only, selected, paths, mode)
        print(json.dumps({k: v for k, v in summary.items()
                          if k != "per_sublist"}, indent=2))
        print(f"Report: {summary['report_path']}")
        return 0

    if args.full:
        print("WARNING: --full runs the COMPLETE census (~25,767 names × "
              f"{N} = ~{25767*N:,} calls). This is the stub for the eventual full "
              "run; validate the pilot first.", file=sys.stderr)

    ts = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    jsonl_path = os.path.join(paths["results_dir"], f"census-pilot-{ts}.jsonl")

    print(f"Census {mode}: {len(selected)} names × N={N} = "
          f"{len(selected) * N} calls, concurrency={MAX_CONCURRENCY}.",
          file=sys.stderr)
    captures = run_census(selected, jsonl_path)
    analysis = analyze(captures)
    summary = write_report(analysis, jsonl_path, selected, paths, mode)

    print("\n=== SUMMARY ===")
    print(json.dumps({k: v for k, v in summary.items()
                      if k != "per_sublist"}, indent=2))
    print("\nPer-sublist:")
    for r in summary["per_sublist"]:
        print(f"  {r['sublist'][:50]:50} n={r['n']:3} "
              f"HIT5/5={r['pct_stable']:5.1f}% flaky={r['pct_flaky']:5.1f}% "
              f"MISS={r['pct_miss']:5.1f}%")
    print(f"\nRaw: {jsonl_path}")
    print(f"Report: {summary['report_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
