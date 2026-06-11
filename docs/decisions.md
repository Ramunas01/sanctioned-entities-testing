# Decision Records — Sanctions Add-on test campaign

Rulings by the Advisor (Claude Opus). Authoritative; the harness implements against
these. Posted here per the "GitHub is the single source of truth" discipline.

---

## DR-0 — Source identity (gates the merge sanity-check)

**Confirmed (PM, against `oracle/snapshot.json`):** the source is the
**trade.gov Consolidated Screening List** — the Commerce-hosted *aggregate* of
OFAC SDN + OFAC non-SDN + BIS Entity List + State Department lists. It is **not**
OFAC's own Consolidated (non-SDN) Sanctions List. Evidence:

- Manifest URL host = `data.trade.gov` (`.../downloadable_consolidated_screening_list/v1/consolidated.csv`).
- `source_sublist` spans **three agencies**: Treasury 19,511 · BIS 5,308 · State 948.
  An OFAC-only artifact would not carry BIS/State rows.

**Consequences:**
1. **Explains DR-D1.** The trade.gov CSL flattens its sources and drops OFAC's
   per-alias quality tagging. The strong/weak flag lives in the OFAC SDN
   *advanced XML*, never in this file. `strong_alias = unknown` is an inherent
   source property, not a parser gap.
2. **Sets the #3 reconciliation axis.** "All programs in place" spans multiple
   agencies. The census must reconcile by the CSL `source` column
   (OFAC-SDN / OFAC-NonSDN / BIS-Entity / State), because a realistic silent
   failure is ingesting OFAC rows and dropping BIS/State rows.

**Still owed by the human:** re-confirm with the Add-on owner that the Add-on
ingests *this same* trade.gov CSL file (README asserts it; pin it).

---

## DR-D1 — Alias strength: drop from oracle, enrich only the sample

**Decision:** Do **not** enrich the full 25,767-row oracle. Treat
`strong_alias = unknown` as a recorded source limitation.

- **Census (#3):** collapse the distinction entirely. Every primary name and
  every alias is match-eligible; a hit on any alias counts. `unknown` is fine —
  the census asks "did the record become matchable," not "with what confidence."
- **Behavioral (#4):** the weak-alias *precision* class is **OUT OF SCOPE**
  (ruled by PM/human, 2026-06-11). The trade.gov CSL does not label alias
  quality, and we are not enriching from OFAC SDN advanced XML. #4 will not
  measure weak-alias precision as a distinct class. This is an explicit scope
  declaration, not a silent collapse (which the Advisor forbids).
- **Policy for the record:** for a screening tool, correct behavior is *match on
  weak aliases and surface for human review* — a missed match is the catastrophic
  error. Wherever aliases are tested, **expected result = HIT**.

---

## DR-D2 — Hit definition + determinism prerequisite

**Prerequisite (must run before #3 trusts anything): determinism probe.**
Fire the same ~50 queries **K=5** times; check that bucket assignment
(`codes` vs `possible_codes`) is stable. If the *same query* lands a party in
`codes` on one run and `possible_codes` on another, that is an **Add-on defect**
and arguably the most significant finding so far — it makes the confidence
signal untrustworthy and invalidates behavioral threshold testing. Characterize
before building on it.

**Decision — hit definition:**
- **Census HIT = present in `codes` OR `possible_codes`.** Presence in either
  proves ingestion, which is what #3 measures. Bucket non-determinism therefore
  does not break the census.
- **Sub-finding to log (data, not a census failure):** any query of an *exact
  primary name from source* that lands **only** in `possible_codes`. An exact
  source name resolving as a weak match is a matching-calibration smell.
- **#4 gate:** the bucket split is the signal #4 tests, so **#4 cannot proceed
  until the probe shows bucketing is stable.** If unstable, #4 is blocked on an
  Add-on fix, not on us.

---

## DR-PR5 — Merge the oracle, but not on the author's say-so

PR #5 is the oracle, authored by Claude Code; the author must not be its sole
validator (oracle/checker separation). Clear to merge **after** an independent
pass that does **not** reuse the parser's logic:

1. Hand-verify ~25 rows spanning programs, entity types, scripts, and CSL
   sources against the official source/portal.
2. Confirm the 29→7 collapse lost no program codes for **multi-program parties**.
3. Sanity-check the 25,767 count against the published source magnitude *for the
   trade.gov CSL* (per DR-0).

**Advisor will perform (1) and (2)** given the routed sample
(`docs/oracle-review-sample.md` — 41 rows incl. multi-program parties up to 8
codes, each paired with its raw source row). Then merge.

---

## DR-REPRO — Pin the Add-on, not just the oracle

`version_date` is inert (Add-on serves "latest"); the oracle is frozen at
2026-06-10 with a hash guard. That asymmetry means mid-campaign Add-on data
updates cause drift and phantom misses. Harness requirements:

- Capture the Add-on's served-data date at the **start and end of every run**;
  abort/flag on change.
- Run the full census in **one tight window**.
- If the Add-on can be pinned to a date, pin it to **2026-06-10** to match the
  oracle.
