# US CSL Integration — Sanctions Add-on Test Report

Owner: PM. Methodology: Advisor. Substance signed off by Advisor 2026-06-12.
Snapshot: oracle frozen at trade.gov CSL `2026-06-11` (sha256 in `oracle/snapshot.json`);
Add-on served version `2026-06-11` (`version_date` inert — DR-REPRO).

## 1. Summary / verdict
The US/CSL integration recalls **person records and entity records reliably across every
tested US sublist except one**. The **BIS Denied Persons List (DPL) ingestion path
is defective**: **280 currently-listed denied parties** (18.4% of DPL, disproportionately
companies) return **no match across 5 repeated queries**, all confirmed present in today's
source. The failure is **silent** — DPL works for persons and for the majority, so nothing
signals the gap. Entities are hit hardest (30.7% miss) but **persons are also missed (14.6%)**, so it is a DPL
**feed** defect, not entity-only. It is **DPL-scoped**: SDN, SSI, the BIS Entity List, MEU and
NS-MBS recall entities with 0 misses in 527 names (per-sublist 95% bounds in §5). **Severity:
Sev-1** — the DPL scope is a *fix-pointer*, not a severity discount; 280 silently-missed,
currently-listed denied parties is Sev-1 regardless. Two secondary Add-on defects
(non-determinism #6, generic-token false positives #8) are documented but do not change this
verdict.

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
### 3.1 Per-sublist recall
- Pilot (n≈26/sublist): 11 sublists 100% stable-definite; DPL the lone outlier (Finding #9).
- **Full DPL sweep — authoritative, all 1,520 unique DPL names × 5 (gate-4 verified,
  `version_used` stable `2026-06-11`):**

  | Class | n=1,520 | % |
  |---|--:|--:|
  | 5/5 definite | 730 | 48.0 |
  | flaky (1–4/5) | 266 | 17.5 |
  | `possible_codes`-only (weak/unverified) | 244 | 16.1 |
  | **0/5 MISS** | **280** | **18.4** |
  | **never stable-definite** | 790 | **52.0** |

  **Two findings within DPL.** DPL rows have no `entity_type`, so person/entity here is a
  **corporate-suffix heuristic** label, not ground truth (this matters for the cross-sublist
  comparison — see the like-for-like note in §5):
  - **Finding 9a — entities (primary):** **110 of 358** entity names miss (**30.7%**) /
    never-definite 68.2%.
  - **Finding 9b — persons (secondary, not negligible):** **170 of 1,162** person names miss
    (**14.6%**) / never-definite 47.0%. ~1 in 7 listed denied *persons* is also missed —
    versus ~0% on every other US feed (§5). The DPL feed is under-ingested for **both** record
    types, entities ~2.1× worse; a **feed** defect with an entity skew, not entity-only.
    **Upper-bound caveat:** DPL has no `entity_type`, so the heuristic person bucket is
    contaminated by suffix-less *entities* (e.g. `ABAN AIR`, `EMTRASUR`). Since those miss at
    the elevated entity rate, **14.6% is an *upper bound* on the true-person miss rate, and the
    real entity skew is likely *stronger* than 2.1×, not weaker** — the contamination sharpens
    the finding, it does not soften it.
  - **Reconciliation:** 110 entity misses + 170 person misses = **280** — the headline 0/5
    miss count (§3.3). (Earlier interim figures on partial sweeps differ; these are the final
    1,520-name numbers.)

  Persons-by-complexity (plain vs parenthetical/AKA/>3-token) miss **identically** (≈14–15%),
  so the gap is **not string-normalization** (corroborates gate 1's 0/10 formatting) — it is
  feed ingestion.

### 3.2 Root cause — whole-sublist omission vs record-level gap
**Verdict (A1, PM-verified): RECORD-LEVEL gap, not whole-sublist omission.** Of the 22
DPL pilot names that HIT, **20 are DPL-only** (appear under no non-DPL sublist), so their
matches cannot be leaking in via OFAC/DTC cross-listing — the Add-on demonstrably holds
*native* DPL records. Only 2 hits are cross-listed (both genuine DTC matches). The
decisive number **20** was reproduced independently by the PM with the pinned
normalization. ⇒ DPL data is ingested but coverage is **partial and unstable**, not
a missing sublist. (`reports/dpl_crosslist.csv`.)

### 3.3 Net defect list (defect vs stale-oracle)
**A3-full (all 280 DPL misses vs the current trade.gov source): 280/280 are real
DEFECTS, 0 stale. NET REAL-DEFECT COUNT = 280.** Every 0/5 miss is a *currently-listed*
party present in today's freshly downloaded CSL yet returned by the Add-on on no run.
The staleness confound is fully overturned at scale (A3-preview's 4/4 held across all
280). `reports/dpl_miss_active_status_full.csv`. (CSL search API unavailable — 401, no
key; current downloadable file is dispositive.)

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
(`reports/provenance_audit.md`.) **Scope caveat:** this is human-checkable provenance; if the
owner requires *machine-readable* legal-authority metadata, that is XML-only and not in
`consolidated.csv` — see Finding F-4 (§9.5).

## 5. Statistical assurance — is the entity defect DPL-only or systemic? (A5)
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

**Verdict: the defect is DPL-ONLY.** Zero entity misses on every other US sublist, reported
as **per-sublist 95% upper bounds** (rule of three, 0/n → ≤3/n), not pooled:

| Sublist | entity misses | 95% upper bound on entity-miss |
|---|---|---|
| SDN | 0 / 150 | ≤2.0% |
| SSI | 0 / 150 | ≤2.0% |
| EL | 0 / 150 | ≤2.0% |
| MEU | 0 / 66 | ≤4.5% (≈ full entity population of the sublist) |
| NS-MBS | 0 / 11 | ≤27% (full entity population — sublist is tiny) |

— versus **30.7% on DPL**, non-overlapping by a wide margin for SDN/SSI/EL.

**Like-for-like note:** DPL's 30.7% is **heuristic**-labeled (BIS rows have no `entity_type`)
while these bounds are mostly **ground-truth**. The comparison is therefore **shape-matched,
not definition-matched** — valid because the ground-truth recalling samples contain DPL's
exact name shapes (suffix-less, punctuated; next paragraph), not because the two labels share
a definition.

**SDN/SSI (ground-truth `entity_type`) carry the comparison; EL/MEU only corroborate.** The
ground-truth samples contain the *same name shapes DPL misses*: SDN entities are **75%
suffix-less** (e.g. `ADMINISTRADORA DE INMUEBLES VIDA, S.A. DE C.V.` — a company the
heuristic would mislabel as a person), SSI 25%, with punctuation throughout — yet recall at
100%. DPL misses are 61% suffix-less / 19% punctuated, so the recalling samples cover DPL's
hard cases. EL/MEU use the suffix-requiring heuristic and so cannot include suffix-less
names; they corroborate for suffix-bearing/punctuated entities (EL 35/150 punctuated, all
recalled) but do not themselves carry the claim. Either way the failure is the **DPL
ingestion path specifically**, not 'entities', 'BIS feeds', or name shape.
`reports/expanded_census.csv`.

> **Scope of the vessel/aircraft 100%:** this is **name-recall only** — vessels and aircraft
> are *findable by name*. It does **not** certify that the maritime/aircraft *blocking detail*
> the owner requires is present; that detail is an XML-only field absent from `consolidated.csv`
> (Finding F-4, §9.5).

## 6. Known Add-on defects (Behavior, partial — #4 blocked)
- Finding #6 (Sev-2): bucket-churn non-determinism (`codes`↔`possible_codes`). Blocks #4 threshold testing.
- Finding #8: generic-token false positives + masked recall (EXPORT MATERIALS).

## 7. Severity & recommendation
**Sev-1 (confirmed real, gate 1 cleared).** The DPL recall gap is a genuine Add-on
**ingestion** defect, not a harness artifact and not name-format sensitivity: retrieval
controls pass, and 10/10 tested misses stay missing under both verbatim and human-simplified
queries (`reports/dpl_harness_disconfirmation.md`). A screening tool that silently fails to
return live denied parties clears them by name.

**Final.** The US/CSL integration correctly recalls persons and entities across all tested
OFAC sublists **and the BIS Entity List**, but the **DPL feed is under-ingested**: **280
currently-listed denied parties (18.4% of DPL) return no match across repeated queries,
confirmed present in the current source.** Entities are hit hardest (30.7% miss) but
**persons are also affected (14.6%)**, so the gap is the DPL *feed*, not an entity-only
quirk. Because DPL works for the majority and for most persons, it **fails silently**.

**Severity: Sev-1.** The DPL scope is a **fix-pointer — where the bug is — not a severity
discount**: 280 silently-missed, currently-listed denied parties is Sev-1 regardless of how
many feeds are affected. **Remediation: the DPL source ingestion path (all record types;
entity records worst).** (Had A5 shown other sublists' entities also missing, this would have
escalated to a US integration-wide failure; it did not — the scope is narrow, the severity is
not.)

*Mechanism — probe-confirmed (PM, 2026-06-12): ingestion, not retrieval.* The pipeline is
two-stage (exact `keyword` → Meilisearch fuzzy @ `similarity_threshold` 0.7, `max_candidates`
5). For missed DPL entities, querying the record's **unique distinctive token** (`ALPHATRONX`,
`ADAERO`, `ROSENTHAL`) returns `no_match`/empty, while **generic tokens** (`CHEMICAL`,
`LOGISTICS`) reliably return 5 *unrelated* candidates — so the retrieval stages function and
the index is populated, but the missed records are **absent from the index**. An indexed
`ALPHATRONX` would be a 1.0 exact-keyword match (far above 0.7) yet returns nothing. This
isolates the defect to **ingestion** (records never loaded), not the 0.7/max-5 retrieval
threshold — gate 1's disconfirmation was consistent with either; this probe separates them.
(Direct index read-access would confirm definitively; this is strong inference.)

## 8. Caveats / limitations
- `version_date` inert — point-in-time queries unavailable; campaign run in one tight window.
- Alias census deferred to the #7 normalization fast-follow.
- DPL "hits" include `possible_codes`-only matches that may be spurious (generic-token, Finding #8).
- **Person/entity on DPL is a name heuristic** (no `entity_type` on BIS rows). The person bucket
  is contaminated by suffix-less entities, so Finding 9b's 14.6% is an **upper bound** and the
  entity concentration is **understated** (§3.1). Label-independent results (the 280 misses,
  DPL-only isolation, ingestion mechanism, active-defect confirmation) are unaffected.
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

## 9. Remediation handoff (for the Add-on team's PM / Advisor)

Owner confirmed (A0): the Add-on ingests **`consolidated.csv`** (the same file this oracle
froze — so the misses are genuine, not a source mismatch), the OFAC SDN advanced-XML extras
are required and used heavily, and **the low DPL recall is a new/unknown defect.**

### 9.1 What to reproduce
- **280 unique DPL `primary_name`s return 0/5** (both buckets empty across 5 identical queries).
  Full list: `reports/dpl_full_misslist.txt`. **Curated 100-example sample:
  `reports/dpl_defect_examples.csv`** (≈55/45 entity/person by `class_heuristic` — an
  **approximate** corporate-suffix name guess, *not* ground truth; the reliable fields are
  `primary_name` + `match_request_url`, with `name_shape` as the dependable structural label).
  Shapes span suffix-less, suffix-bearing and punctuated. All 280 are present in today's
  `consolidated.csv`.

### 9.2 Mechanism — ingestion, not retrieval (start here)
The pipeline is two-stage (`keyword` exact → Meilisearch fuzzy @ 0.7, max 5). Probing a missed
record's **unique distinctive token** (`ALPHATRONX`, `ADAERO`, `ROSENTHAL`) returns
`no_match`; **generic tokens** (`CHEMICAL`, `LOGISTICS`) return 5 unrelated candidates. The
retrieval stages work and the index is populated — **the missed records are absent from the
index.** Look at the **DPL ingestion/indexing path**, not the matcher or thresholds.

### 9.3 Diagnostic clues (these narrow the search a lot)
1. **DPL-specific.** Every other US sublist — including the BIS **Entity List** — recalls
   ~100% (§5). So it is not the whole `consolidated.csv` loader; it is DPL-source rows.
2. **DPL-vs-EL is the sharpest lever.** DPL and the Entity List are *both* BIS sub-lists with
   empty `entity_type`/`programs` columns — yet **EL recalls 100% and DPL fails.** So empty
   `entity_type` is **not** the cause. Diff how rows with `source = "Denied Persons List
   (DPL) …"` are parsed/loaded versus `source = "Entity List (EL) …"`; the differentiator
   lives there.
3. **Entity-skew within DPL** (entities 30.7% miss vs persons 14.6%) → a *partial/probabilistic
   drop* correlated with entity-shaped records, not a clean whole-source skip. Suggests a
   per-row parse/key condition that entity rows hit more often.
4. **Not name shape.** Gate-1 disconfirmation (10/10 misses stay missing under verbatim *and*
   simplified queries) and the persons-by-complexity result (plain ≈ complex) rule out
   punctuation / normalization.

### 9.4 Suggested steps (need the index/DB access we don't have)
1. **Confirm index absence** for the 280 (look them up directly in Meilisearch/DB). Expect absent.
2. **Trace DPL ingestion** of `consolidated.csv` and compare to EL ingestion (9.3 #2).
3. **Diff missing vs recalled DPL rows** field-by-field in `consolidated.csv` (the 280 missing
   vs the ~730 recalled DPL names) to find the entity-correlated dropping condition.
4. **Regression-gate the fix** with this repo: `harness/census.py` + the frozen oracle
   reproduce the result deterministically; after a fix, re-run the DPL census → the 280 should
   resolve. (`possible_codes`-only and flaky names should also firm up.)

### 9.5 Finding F-4 (GitHub #10) — required OFAC-XML extras are not ingestible from `consolidated.csv`
A **second, quieter coverage gap**, surfaced by the owner's own A0 #2 answer and distinct from
the DPL Sev-1. The owner states the **OFAC SDN advanced-XML extras** — legal-authority metadata
and **maritime/aircraft blocking detail** — are required and used heavily, but ingestion is
`consolidated.csv` (A0 #1), the flattened aggregate, which **does not carry those XML-only
fields** (nor per-alias strength, DR-D1). Two consequences land inside this report:
- **Bears on §4 (provenance "MET").** Provenance is MET via free-text `information`; but if the
  requirement is *machine-readable* legal-authority metadata, "MET" holds only in the
  human-checkable sense — the structured form is not ingestable from this file.
- **Bears on §5 (vessel/aircraft 100%).** That assurance is **name-recall only**; it does not
  certify the maritime/aircraft *blocking detail* is present, since that detail is XML-only and
  absent from `consolidated.csv`. Both "vessels/aircraft recall 100%" and "their blocking
  detail is missing" can be true simultaneously.

Independent of, and not blocking, the DPL recall fix — but it follows directly from the owner's
stated requirements, so it deserves its own track for their Advisor.

### 9.6 Reusable assets in this repo
`oracle/` (frozen source + deterministic parser) · `reports/dpl_full_misslist.txt` (all 280)
· `reports/dpl_defect_examples.csv` (100-example sample) · `harness/census.py` (regression
harness) · `reports/dpl_full_census.csv`, `reports/expanded_census.csv` (full per-class data).
