# US CSL Integration — Sanctions Add-on Test Report

Owner: PM. Methodology: Advisor.
Snapshot: oracle frozen at trade.gov CSL `2026-06-11` (sha256 in `oracle/snapshot.json`);
Add-on served version `2026-06-11` (`version_date` inert — DR-REPRO).

> ### ⚠️ Retraction / correction notice (2026-06-15)
> An earlier version of this report (filed 2026-06-11) called the DPL result a **Sev-1
> ingestion defect** — *"280 currently-listed denied parties silently missed."* **That finding
> is withdrawn.** After Add-on-team pushback and verification, the 280 are **expired denial
> orders** the Add-on **correctly excludes**. **Root cause of the error:** the oracle did not
> apply `end_date` validity (the column flagged in §8 but never used), so expired orders were
> counted as expected hits. With `end_date` applied, **active-DPL recall is 100%** and the
> integration is correct. Audit trail: filed Sev-1 2026-06-11 → reclassified 2026-06-15.
> Finding #9 is reclassified to a **product recommendation for the integration owner** (§7b/§9),
> not a builder bug. Finding F-4 (#10) is **withdrawn** (OFAC-XML extras confirmed ingested).

## 1. Summary / verdict
**The US/CSL integration is functioning correctly.** Across all tested US sublists — SDN, SSI,
BIS Entity List, MEU, NS-MBS, **and DPL** — active person and entity records recall at ~100%
(0 active misses; per-sublist bounds in §5). For DPL specifically, with listing validity
applied (`end_date`), **active-DPL recall = 454/454 = 100% (all stable-definite)**; the 280
"no-match" results are **expired BIS denial orders the Add-on correctly excludes** (date
validity), not silent misses. The Add-on's **active-only filter is the correct default.**
*One product question remains for the integration owner* — whether to optionally surface
**expired/historical** debarments as a clearly-labeled flag for trade due-diligence (§7b/§9) —
a feature decision, not a defect. Two real but secondary Add-on defects stand: non-determinism
(#6, Sev-2) and generic-token false positives (#8).

## 2. Method
Two-track: **Presence = census**, **Behavior = sampled vectors**. This report covers the
**primary-name census**: every listed party's `primary_name` → HIT/NO-HIT/ERROR. The
**alias-based census is deferred** to the #7 alias-normalization fast-follow (the CSL has no
strong/weak alias flag — `strong_alias` is `unknown` for every row, DR-D1 — and alias
normalization is itself a reviewed transform; see §8), so no alias was pushed to the Add-on
here. HIT = `codes` ∪ `possible_codes` (DR-D2, census immune to observed churn). Census run
N=5× per name → per-name hit-rate. Reconcile by `source_sublist` (F4). Reproducibility:
`version_used` start/end guard (DR-REPRO).

## 3. Coverage findings (Presence)
### 3.1 Per-sublist recall — active records recall everywhere
With listing validity applied (oracle `end_date` → derived `active`), **every active US
record recalls — DPL included.**
- 11 non-DPL sublists: 100% stable-definite (pilot + A5, §5).
- **DPL, active-only: 454 / 454 active names = 100% HIT, 100% stable-definite. Zero active
  DPL records missed.**

The full DPL census over all 1,520 names (before applying validity) was:

  | Class | n=1,520 | note |
  |---|--:|---|
  | 5/5 definite | 730 | |
  | flaky (1–4/5) | 266 | |
  | `possible_codes`-only | 244 | |
  | **0/5 "no match"** | **280** | **all expired denial orders — correctly excluded (§3.2)** |

The 280 "no-match" results are **not misses** — they are expired BIS denial orders the Add-on
correctly date-filters (next).

### 3.2 The 280 are expired denial orders, correctly excluded (corrects Finding #9)
Joining the 280 to `consolidated.csv` `end_date`: **280 / 280 have a past `end_date`
(expired); 0 are active.** The Add-on applies an **active-only date filter** — the correct
default for a blocking screen. Confirmed three independent ways:
- **The DPL feed *is* ingested:** active DPL records hit from the DPL envelope
  (`reg-us-csl-dpl.json`) with future `valid_to` — THANE-COAT 2027, YURI I. MONTGOMERY 2040,
  TETRABAL 2056 (10/10 sampled active records hit definite).
- **Expired records that still recall** do so via **cross-listed active envelopes** (EL/ITAR,
  `valid_to=2099`), not their expired DPL record.
- **Expired-only records** (e.g. `ALPHATRONX`, a 2012-expired denial) are absent from the
  *served* index → `no_match`. That is correct exclusion, not a missing feed — the §9.2
  "index-absence" observation was right, but its earlier "ingestion defect" interpretation was
  wrong.

**Error root cause:** the oracle dropped the source `end_date` column, so the census expected
expired orders to hit and scored their (correct) exclusion as misses. The oracle now carries
`end_date` + a derived `active` flag (`oracle/parse_oracle.py`); with it applied, active-DPL
recall is 100% (§3.1).

### 3.3 The entity "skew" is an expiry artifact, not an entity-class defect
The earlier "entities miss ~2.1× persons" reconciles completely: among DPL records, **entity
orders are 83.3% expired vs 67.0% for persons.** Entities produced more "no-match" results
because their denial orders expire more often — not because entity records are mishandled. The
earlier cross-listing (A1) and "net-defect" (A3) analyses are **superseded** by this
validity-aware reading; their raw data stands, the defect interpretation does not.

## 4. Output provenance (spec requirement)
**Verdict (A2): requirement MET.** A hit-response code payload carries record provenance
redundantly: **`meta.issuer`** (e.g. `US`), **`envelope_filename`** (source dataset +
program, e.g. `reg-us-russia-eo14024.json`), and **`information`** (inline legal authority,
e.g. `Listed: 2022-02-25 (EO 14024)`). Spec asks for source **or** a legal reference; the
Add-on supplies both. Caveat: the legal reference is free-text (human-checkable, not
machine-parseable). **Verified live (PM, 2026-06-12)** against two hits — DPL
`ADRIAN MANUEL HERNANDEZ` → code 1155166, `meta.issuer=US`,
`envelope_filename=reg-us-csl-itar.json`, `information` carries Federal Register Notice
`83 FR 18112`; SDN `GRACHEV, Pavel Sergeyevich` → code 1139334, `meta.issuer=US`,
`envelope_filename=reg-us-russia-eo14024.json`, party-specific aliases/birthdate. Both
party-specific, so **MET is confirmed on live captures, not the documented payload alone**.
(`reports/provenance_audit.md`.)

## 5. Statistical assurance — active entity recall across sublists (A5)
Entity-oversampled census of the trade-critical sublists, 832 names × 5 = **4,160 calls,
0 errors, `version_used` stable `2026-06-11`**. Classes labeled by **ground-truth
`entity_type`** where present (SDN/SSI/NS-MBS); corporate-suffix **heuristic** only where
empty (EL/MEU). Vessel/aircraft kept on their own lines.

| Sublist | class | method | n | definite | miss |
|---|---|---|--:|--:|--:|
| SDN | entity | entity_type | 150 | 100% | 0% |
| SDN | vessel | entity_type | 50 | 100% | 0% |
| SDN | aircraft | entity_type | 50 | 100% | 0% |
| SDN | person | entity_type | 100 | 99% | 0% |
| SSI | entity | entity_type | 150 | 100% | 0% |
| EL | entity | heuristic | 150 | 100% | 0% |
| EL | person | heuristic | 100 | 100% | 0% |
| MEU | entity | heuristic | 66 | 100% | 0% |
| MEU | person | heuristic | 4 | 100% | 0% |
| NS-MBS | entity | entity_type | 11 | 100% | 0% |
| NS-MBS | person | entity_type | 1 | 100% | 0% |

**Verdict: active records recall across every sublist.** Per-sublist 95% upper bounds on the
entity-miss rate (rule of three, 0/n → ≤3/n):

| Sublist | entity misses | 95% upper bound |
|---|---|---|
| SDN | 0 / 150 | ≤2.0% |
| SSI | 0 / 150 | ≤2.0% |
| EL | 0 / 150 | ≤2.0% |
| MEU | 0 / 66 | ≤4.5% (≈ full entity population) |
| NS-MBS | 0 / 11 | ≤27% (full entity population — tiny) |

Together with **DPL active-recall = 100%** (§3.1), active entity recall is ~100% on every US
sublist. The ground-truth SDN/SSI samples deliberately include suffix-less and punctuated
entity names (SDN **75% suffix-less**, e.g. `ADMINISTRADORA DE INMUEBLES VIDA, S.A. DE C.V.`;
SSI 25%), so recall is confirmed across the full range of name shapes, not just clean
corporate suffixes. `reports/expanded_census.csv`.

> Vessel/aircraft recall is by name; the OFAC advanced-XML blocking detail is confirmed
> ingested by the Add-on team, so the earlier F-4 concern here is withdrawn.

## 6. Known Add-on defects (Behavior, partial — #4 blocked)
- Finding #6 (Sev-2): bucket-churn non-determinism (`codes`↔`possible_codes`). Blocks #4 threshold testing.
- Finding #8: generic-token false positives + masked recall (EXPORT MATERIALS).

## 7. Conclusion & recommendation
**The integration is functioning correctly.** Active person and entity records recall at
~100% on every US sublist, DPL included (§3, §5). With listing validity applied, **active-DPL
recall = 454/454 = 100%**; the 280 "no-match" results were **expired BIS denial orders the
Add-on correctly excludes.**

**7a — The active-only date filter is the correct default.** A denial order past its
`end_date` is no longer a legal basis to block; returning it as a hit would be a false
positive. Excluding expired orders is the right behaviour for a blocking screen, and the
Add-on does it consistently — active records served from `reg-us-csl-dpl.json`, expired
DPL-only records excluded. **No defect; no change to the default is required.**

**7b — Product recommendation for the integration owner (not a builder bug).** Expired ≠
never-listed. For trade due-diligence a *lapsed* debarment is materially different from a
party that was never listed — prior debarment is a risk signal even when it is no legal basis
to block. We recommend the owner consider **on-demand, clearly-labelled surfacing of
expired/historical listings** — a *labelled flag* (e.g. "formerly listed: BIS DPL, order
expired 2015-09-22"), **not** a blocking hit, **off by default**. This is a product decision
for our owner, not a fix for the Add-on team. Candidate scope: the ~1,066 expired DPL records
(`reports/dpl_full_misslist.txt`; labelled sample in §9).

*Mechanism note (corrected):* the probe finding that expired records are "absent from the
served index" (unique-token queries → `no_match`) was **factually correct** — but it is the
**intended date exclusion**, not an ingestion defect. The active DPL feed *is* ingested
(active records hit from `reg-us-csl-dpl.json`); only expired records are withheld.

## 8. Caveats / limitations
- `version_date` inert — point-in-time queries unavailable; campaign run in one tight window.
- Alias census deferred to the #7 normalization fast-follow.
- DPL "hits" include `possible_codes`-only matches that may be spurious (generic-token, Finding #8).
- **Person/entity on DPL is a name heuristic** (no `entity_type` on BIS rows); used only for
  the §3.3 expiry breakdown and the §9 sample's `class_heuristic` column. The headline result
  (active-DPL recall 100%; the 280 = expired orders) is label-independent.
- **Record-level `valid_from` is inconsistently populated (source-specific).** Empty for
  State-Dept **ITAR/DTC** records (`reg-us-csl-itar.json`, e.g. `ADRIAN MANUEL HERNANDEZ`),
  but populated for OFAC records (`GRACHEV` 2023-05-19, `HANIYA` 2006-04-12, China Telecom
  2021-01-08). The endpoint advertises `valid_from`/`valid_to` date-range filtering; for the
  ITAR/DTC source that filter has no record-level basis and would fall back to the batch
  (`envelope`) date. **Owner question.** (Note: corrects an initial "all records empty" read —
  only the ITAR/DTC envelope is affected among those checked.)
- **Endpoint labeled "EU Sanctions Person (Regulations)" but serves US records.** The connector
  header reads "EU" yet returns US data (`meta.issuer=US`, `reg-us-csl-itar.json`), keyed by
  `version_date` — almost certainly a shared EU/US endpoint with a cosmetic label. Loose thread,
  not a finding: if the chatbot wrapper routes by that label, a US query could in principle hit
  an EU-scoped path. **Owner question:** confirm US/EU share this endpoint and the label is cosmetic.

## 9. Product recommendation — optional historical-listing surfacing (for the integration owner)

*This section replaces an earlier "DPL defect remediation handoff." There is **no Add-on
defect to remediate** (see the retraction notice and §7) — what remains is a product question
for our owner.*

### 9.1 The artifact
The 280 DPL "no-match" results are **expired denial orders the Add-on correctly excludes**
(active-only filter) — specifically the expired DPL records with no active cross-listing, i.e.
the records that legitimately return nothing today. Reference:
`reports/dpl_full_misslist.txt` (all 280) and `reports/dpl_expired_examples.csv` (100-row
labelled sample — each row: `primary_name`, `end_date`, `class_heuristic`, `name_shape`,
`match_request_url`). The full expired DPL population is ~1,066 records; the other ~786 already
surface via an active cross-listing (SDN / EL / ITAR).

### 9.2 The decision (see §7b)
Should the integration **optionally** surface expired/historical listings for trade
due-diligence?
- **For:** prior debarment is a real risk signal; "formerly listed — order expired 2015-09-22"
  is materially different from "never listed."
- **Guardrail:** it must never read as an active hit — a **clearly-labelled, off-by-default
  flag** carrying the expiry date, distinct from a blocking match, so lawful trade is not
  over-blocked.

A feature decision for our owner; the Add-on team need do nothing unless the owner asks for it.

### 9.3 If surfacing is pursued
The Add-on would serve expired records under a distinct field (e.g. `historical_codes`, with
the past `valid_to`) rather than withholding them, so the wrapper can render a labelled flag;
the active hit path stays unchanged. The oracle now carries `end_date` + a derived `active`
flag, so the active-vs-expired expectation is reproducible for regression.

### 9.4 Finding F-4 (#10) — WITHDRAWN
The Add-on team confirmed the OFAC SDN advanced-XML extras **are** ingested, so §4 "MET" and
§5's vessel/aircraft recall stand without qualification. F-4 is withdrawn (audit trail on #10).

### 9.5 Reusable assets
`oracle/` (frozen source + deterministic parser, now `end_date`/`active`-aware) ·
`reports/dpl_full_misslist.txt` · `reports/dpl_expired_examples.csv` · `harness/census.py`
(regression harness) · `reports/dpl_full_census.csv`, `reports/expanded_census.csv`.
