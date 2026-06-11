# US CSL Integration — Sanctions Add-on Test Report (DRAFT)

Status: **skeleton — fill from task outputs.** Owner: PM. Methodology: Advisor.
Snapshot: oracle frozen at trade.gov CSL `2026-06-11` (sha256 in `oracle/snapshot.json`);
Add-on served version `2026-06-11` (`version_date` inert — DR-REPRO).

> Result-source map (which task fills which section):
> A1 → §3 root cause · A3 → §3 net defect list · A2 → §4 · A4 → §3 numbers · A5 → §5.

## 1. Summary / verdict
_(one paragraph: is the US/CSL integration fit for purpose? headline = DPL recall gap, pending A1+A3 severity resolution.)_

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

## 5. Statistical assurance (other sublists)
_(A5 overnight: ~300/sublist on SDN, SSI, EL, MEU, NS-MBS → ≤~1% miss bound at 95% (rule of three), vs the pilot's ~11% bound.)_

## 6. Known Add-on defects (Behavior, partial — #4 blocked)
- Finding #6 (Sev-2): bucket-churn non-determinism (`codes`↔`possible_codes`). Blocks #4 threshold testing.
- Finding #8: generic-token false positives + masked recall (EXPORT MATERIALS).

## 7. Severity & recommendation
**Sev-1 (confirmed real, gate 1 cleared).** The DPL recall gap is a genuine Add-on
**ingestion** defect, not a harness artifact and not name-format sensitivity: retrieval
controls pass, and 10/10 tested misses stay missing under both verbatim and human-simplified
queries (`reports/dpl_harness_disconfirmation.md`). A screening tool that silently fails to
return live denied parties clears them by name. _Final magnitude + the net real-defect count
(A3-full) fill in once the completed sweep merges; Advisor to finalize wording._

## 8. Caveats / limitations
- `version_date` inert — point-in-time queries unavailable; campaign run in one tight window.
- Alias census deferred to the #7 normalization fast-follow.
- DPL "hits" include `possible_codes`-only matches that may be spurious (generic-token, Finding #8).
