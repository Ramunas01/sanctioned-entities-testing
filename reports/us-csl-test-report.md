# US CSL Integration — Sanctions Add-on Test Report (DRAFT)

Status: **skeleton — fill from task outputs.** Owner: PM. Methodology: Advisor.
Snapshot: oracle frozen at trade.gov CSL `2026-06-11` (sha256 in `oracle/snapshot.json`);
Add-on served version `2026-06-11` (`version_date` inert — DR-REPRO).

> Result-source map (which task fills which section):
> A1 → §3 root cause · A3 → §3 net defect list · A2 → §4 · A4 → §3 numbers · A5 → §5.

## 1. Summary / verdict
The US/CSL integration recalls **person records and entity records reliably across every
tested US sublist except one**. The **BIS Denied Persons List (DPL) entity-ingestion path
is defective**: **280 currently-listed denied parties** (18.4% of DPL, disproportionately
companies) return **no match across 5 repeated queries**, all confirmed present in today's
source. The failure is **silent** — DPL works for persons and for the majority, so nothing
signals the gap. It is **scoped to the DPL feed**: SDN, SSI, the BIS Entity List, MEU and
NS-MBS all recall entities at ~100% (0 misses in 527 entity names tested). **Severity: Sev-1,
scoped to DPL feed entity handling.** Two secondary Add-on defects (non-determinism #6,
generic-token false positives #8) are documented but do not change this verdict.

## 2. Method
Two-track: **Presence = census** (every primary name + strong alias → HIT/NO-HIT/ERROR),
**Behavior = sampled vectors**. HIT = `codes` ∪ `possible_codes` (DR-D2, census immune to
observed churn). Census run N=5× per name → per-name hit-rate. Reconcile by `source_sublist`
(F4). Reproducibility: `version_used` start/end guard (DR-REPRO).

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

  **Person/entity cross-tab** (DPL has no `entity_type`; corporate-suffix heuristic):
  PERSON (n=1,162) miss **14.6%** / never-definite 47.0%; ENTITY (n=358) miss **30.7%**
  / never-definite 68.2% — entities ~2.1× worse. Persons-by-complexity (plain vs
  parenthetical/AKA/>3-token) miss **identically** (≈14–15%), so the defect is
  entity-class, not string-normalization (corroborates gate 1's 0/10 formatting).

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
machine-parseable). (`reports/provenance_audit.md`. Verdict rests on the documented §3
payload + the live identity capture; agent's fresh calls were sandbox-blocked — operator
can run `harness/provenance_probe.py` to refresh the verbatim inventory.)

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

**Verdict: the entity-ingestion defect is DPL-ONLY.** Zero entity misses in 527 entity
names across five other sublists (rule of three → <0.6% entity-miss at 95% CI for the
527-name pool), versus **30.7% on DPL**. Critically, the **BIS Entity List recalls entities
at 100%** — so the failure is not "entities," "BIS feeds," or "the entity class," but the
**DPL ingestion path specifically**. `reports/expanded_census.csv`.

## 6. Known Add-on defects (Behavior, partial — #4 blocked)
- Finding #6 (Sev-2): bucket-churn non-determinism (`codes`↔`possible_codes`). Blocks #4 threshold testing.
- Finding #8: generic-token false positives + masked recall (EXPORT MATERIALS).

## 7. Severity & recommendation
**Sev-1 (confirmed real, gate 1 cleared).** The DPL recall gap is a genuine Add-on
**ingestion** defect, not a harness artifact and not name-format sensitivity: retrieval
controls pass, and 10/10 tested misses stay missing under both verbatim and human-simplified
queries (`reports/dpl_harness_disconfirmation.md`). A screening tool that silently fails to
return live denied parties clears them by name.

**Final (A5-scoped):** The US/CSL integration correctly recalls person records and all
tested OFAC sublists **and the BIS Entity List**, but the Denied Persons List
entity-ingestion path is defective: **280 currently-listed denied parties (18.4% of DPL,
disproportionately companies) return no match across repeated queries, confirmed present in
the current source.** Because the DPL check works for the majority and for persons, the gap
**fails silently**. **Sev-1, scoped to the DPL feed's entity handling. Remediation:
entity-record ingestion for the DPL source.** (Had A5 shown other sublists' entities also
missing, this would have escalated to a US integration-wide entity-ingestion failure; it did
not.)

## 8. Caveats / limitations
- `version_date` inert — point-in-time queries unavailable; campaign run in one tight window.
- Alias census deferred to the #7 normalization fast-follow.
- DPL "hits" include `possible_codes`-only matches that may be spurious (generic-token, Finding #8).
