# Test Plan — Sanctions Add-on (US/CSL integration)

Status: DRAFT. Owner of methodology = Advisor. Owner of tracking = PM. Human = integration point.

## 0. Snapshot pinning (reproducibility contract)

- **Add-on served version:** `2026-06-10` (latest). Owner confirms ~1-day ingestion lag
  vs. source publish, i.e. the 2026-06-10 snapshot reflects source data published ~2026-06-09.
- **`version_date` query param is currently INERT** — every value normalizes to latest.
  Point-in-time queries are not yet selectable. Reproducibility therefore relies on:
  1. Running the census while the served version is stable at `2026-06-10`, AND
  2. The harness recording `processing.version_used` on **every** response and asserting it
     does not change mid-run. Any change invalidates the run.
- **Source of record:** Consolidated Screening List (CSL), single merged CSV:
  `https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.csv`
  Download once, freeze under `oracle/source/`, hash into `oracle/snapshot.json`.

> NOTE: The CSL is the merged US list across OFAC SDN, OFAC non-SDN, BIS Entity List,
> BIS Denied Persons, State Dept (ISN/DTC), etc. This is the file the Add-on ingests, so
> it is also our oracle source. It replaces the OFAC SDN+Consolidated XML originally
> assumed in the Issue #2 brief.

## 1. Two-track method

| Track | Question | Method | Output |
|-------|----------|--------|--------|
| Presence | Did every listed party load? | Full census: push every primary name + strong alias, check HIT/NO-HIT/ERROR | `reports/census.csv` |
| Behavior | Does matching behave correctly? | ~60-70 designed + ~300 random stratified vectors | `reports/behavioral-diff.csv` |

Presence is a certainty check for catastrophic failure (missing program/batch). Behavior is
sampled and measured as recall + precision **separately**.

## 2. Issue ordering / dependencies

- **#1 Interface discovery** — DONE (`docs/addon-interface.md`).
- **#2 Oracle** — parse CSL CSV into `oracle/expected.csv`. Unblocked. Gates #3, #4.
- **#3 Census harness** — needs #1 + #2 + stable served version. Gated.
- **#4 Behavioral vectors** — needs #2 + Advisor equivalence matrix (`docs/equivalence-classes.md`). Gated.

## 3. Open decisions (route to Advisor — `decision-needed`)

- **D1 — Alias strength.** CSL `alt_names` is a flat list with no strong/weak quality flag
  (unlike OFAC SDN XML). The "strong vs weak alias" distinction the equivalence design assumed
  may not be derivable from the CSL CSV alone. Advisor to rule: drop the distinction, or
  enrich from a secondary OFAC SDN source?
- **D2 — Hit definition.** Add-on splits results between `output.codes` and
  `output.possible_codes` non-deterministically. Proposed: hit = code ID present in
  `codes ∪ possible_codes`. Does a `possible_codes`-only match count as a census HIT and/or
  affect precision? Advisor to rule.

## 4. Interface essentials (see docs/addon-interface.md)

- `POST https://fast.customsclear.net/api/sanctions_person_versions_regulations/match?query=<name>&version_date=2026-06-10`
- No auth. ~1.8-2.6 s wall/query (LLM stage dominates). No rate limit observed.
- Match on stable numeric **code IDs**, not on the codes/possible_codes split.
