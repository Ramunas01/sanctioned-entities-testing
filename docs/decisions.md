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

> **AMENDED 2026-06-11 (post-probe).** The probe disproved the "presence-in-either-
> bucket" immunity claim: a known-listed party (`EXPORT MATERIALS, INC.`) returned
> **both buckets empty** on 1 of 5 identical runs — a whole-result *dropout*, not a
> reshuffle. "HIT = codes ∪ possible_codes" does not save that case.
> - **Census is NOT immune.** A single-pass census can fabricate a miss.
> - **Fix — run the census with repetition:** query each name **N=5** times;
>   HIT = hit on *any* run (union over runs); record per-name **hit-rate**
>   (5/5 stable · 4/5 "present, flaky retrieval" · 0/5 true miss). Converts the
>   instability from a confound into a measured reliability number.
> - **The dropout is a Severity-1 Add-on defect on its own** (Finding #6) — a
>   screening tool that intermittently returns nothing for a listed party will, by
>   timing alone, clear a sanctioned counterparty.
> - **#4 stays blocked** until the dropout rate is quantified and bucketing
>   characterized. Measured so far: empty-result rate = **1/240 (0.42%)** of
>   known-listed (name,run) pairs, confined to one name; identity fork (true
>   dropout vs spurious fuzzy hit) under investigation
>   (`reports/export-materials-identity.md`).

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

> **AMENDED 2026-06-11 (Advisor review complete — CLEARED TO MERGE).** All 41
> sample rows verified: (1) cell-for-cell fidelity on all 6 verbatim columns;
> (2) multi-program collapse lossless (the 8-code row 4061 and all three 6-code
> rows preserve every code in source order); (3) index alignment holds at row 0
> and row 25766 (no off-by-one across the span); `strong_alias` invariant
> self-consistent. **The verbatim parse is approved to merge.**
>
> **Fast-follow required BEFORE alias consumption (see Findings F1/F2):** the
> oracle must emit a *normalized alias list* via a documented, **sublist-aware**
> split — semicolon default, **comma for ISN / State-Nonproliferation** — that
> strips empty-equivalents (`[]`, whitespace-only, trailing tokens). Keep the
> verbatim string alongside for audit. This split is now the riskiest
> deterministic transform in the oracle → it gets its own independent review pass.
>
> **Decomposition (nothing stalls):** **#3 primary-name census may start
> immediately** (`primary_name` has none of these hazards); **#3 alias census
> waits** on the fast-follow.

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

---

## Findings from the PR #5 review (F1–F4)

Raised by the Advisor while reviewing `docs/oracle-review-sample.md`. These are
**not** parse infidelities (the verbatim parse passed) — they are hazards in how
#3/#4 *consume* the data.

- **F1 — Alias delimiter is not uniform across sublists. (Top finding.)** Most
  sublists semicolon-delimit aliases, but **State-Dept Nonproliferation (ISN)**
  rows comma-delimit them (sample row 330). And semicolon values contain internal
  commas (`CHINA TELECOM CO., LTD`). So no single split is safe: split on `;` only
  → every ISN row collapses into one un-queryable mega-alias (real aliases like
  `KCST` never tested → false NO-HITs); also split on `,` → `CO., LTD` shreds into
  junk queries. A naive split under-queries the State/nonprolif sublist and
  over-queries the rest. **→ Drives the alias-normalization fast-follow; a hard
  #3 acceptance criterion.**
- **F2 — Empty-equivalent alias tokens corrupt `strong_alias` and become junk
  vectors.** Row 1279 stores the literal `[]`; row 1724 is `Michael Martelly; `
  with a trailing empty token. Both are semantically empty but counted non-empty,
  so they get `strong_alias = unknown` wrongly and would push the query `[]` to
  the census. The invariant "non-empty string ⇒ has aliases" is the flaw.
  **→ Fixed in the same fast-follow (strip empty-equivalents).**
- **F3 — `start_date` format inconsistent (verbatim-correct, unsafe to consume).**
  Almost all ISO; DPL row 3102 is ` 8/11/2015` (leading space, US M/D/YYYY).
  Verbatim is right for the oracle — just don't parse `start_date` as ISO until a
  normalization pass runs. Low impact (not a match field). Already noted as the
  oracle's known date anomaly.
- **F4 — BIS/State rows carry no `programs` or `entity_type`** (expected for the
  trade.gov aggregate). Consequence (confirms DR-0): **the census must reconcile
  by `source_sublist`, not by `programs`**, or the entire BIS/State half looks
  like a coverage hole that isn't one. **A hard #3 acceptance criterion.**
