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
_(A4 numbers: full DPL census counts per class; pilot's 100% on the other 11 sublists; A5 bound.)_
- Pilot (n≈26/sublist): 11 sublists 100% stable-definite; **DPL 35% stable-definite** (Finding #9).
- Full DPL sweep (A4): _<fill: definite / flaky / possible-only / miss counts over 1,596>._

### 3.2 Root cause — whole-sublist omission vs record-level gap
**Verdict (A1, PM-verified): RECORD-LEVEL gap, not whole-sublist omission.** Of the 22
DPL pilot names that HIT, **20 are DPL-only** (appear under no non-DPL sublist), so their
matches cannot be leaking in via OFAC/DTC cross-listing — the Add-on demonstrably holds
*native* DPL records. Only 2 hits are cross-listed (both genuine DTC matches). The
decisive number **20** was reproduced independently by the PM with the pinned
normalization. ⇒ DPL data is ingested but coverage is **partial and unstable**, not
a missing sublist. (`reports/dpl_crosslist.csv`.)

### 3.3 Net defect list (defect vs stale-oracle)
**A3-preview (4 known pilot misses): all 4 are real DEFECTS, 0 stale.** Each is present in
a **freshly downloaded** trade.gov CSL (today) yet missed 0/5 by the Add-on. The plausible
staleness confound is overturned: although all four are *expired* denial orders
(end_dates 2003–2019), trade.gov still carries them, so expiry does not delist them.
(CSL search API unavailable — 401, no key; current file is dispositive.)
`reports/dpl_miss_active_status.csv`. _Full net-defect list pending A4 miss-list → A3-full._

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
_(resolves once §3.2 + §3.3 land: Sev-1 ingestion failure vs scope/staleness reclassification.)_

## 8. Caveats / limitations
- `version_date` inert — point-in-time queries unavailable; campaign run in one tight window.
- Alias census deferred to the #7 normalization fast-follow.
- DPL "hits" include `possible_codes`-only matches that may be spurious (generic-token, Finding #8).
