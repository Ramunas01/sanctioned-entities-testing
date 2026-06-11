# Issue #3 — Primary-name census (stratified pilot)

_Generated: 2026-06-11T18:21:37.644518+00:00_  
_Raw capture: `results/census-pilot-20260611T181238Z.jsonl`_  
_Harness: `harness/census.py` (mode=pilot, SEED=20260611, N=5, concurrency=4, per-sublist=25)_

**HEADLINE: primary-name recall is intact for 11/12 sublists (100% 5/5), but Denied Persons List (65% 5/5, 19% flaky, 15% miss) stands out as under-recalled — every MISS and flaky name in the pilot is in it. All 11 weak-only (`possible_codes`-only) hits also fall in Denied Persons List. Agency recall — OFAC 100% stable (n=111); BIS 91% stable (n=101); State 100% stable (n=50). BIS/State are NOT systematically worse than OFAC SDN except for this one BIS sublist.**

## Reproducibility guard (DR-REPRO)

- **`version_used` at run start:** `2026-06-11`
- **`version_used` at run end:** `2026-06-11`
- **Distinct `version_used` values seen:** `2026-06-11`
- **`input.version_date` seen:** `2026-06-11`
- **Verdict:** STABLE — run is valid

## Totals

- **Names tested:** 262
- **Total calls:** 1310 (errors: 0)
- **Stable HIT (5/5):** 253 (96.6%)
- **Flaky retrieval (1–4/5):** 5 (1.9%)
- **MISS (0/5):** 4 (1.5%)

## Positive control (Finding #8 recall gap)

- `EXPORT MATERIALS, INC.` (Denied Persons List): **RECALL GAP REPRODUCED — but as a SPURIOUS-ONLY hit, not a 0/5 MISS.** All 5/5 runs returned only `possible_codes` = `['1145893', '1145895']` — the documented Finding #8 false positives (unrelated Chinese firms matched on the generic tokens "Export"/"Material"); `codes` was empty every run and the correct listed party was never retrieved.
  - **Caveat for the census signal:** under the strict DR-D2 HIT definition (codes ∪ possible_codes non-empty) this name scores as a 5/5 HIT, so it is NOT in the MISS list below. The recall gap is real but is *masked* by a precision defect. The census question "did the record become matchable?" answers "yes — but only via a wrong party." Catching this requires identity-level checking (codes vs the oracle's expected code), which is out of scope for the ingestion census and is exactly the precision class Finding #8 tracks.

## Matching-calibration smell — names found ONLY in `possible_codes` (DR-D2 sub-finding)

_Exact primary names that, on every run they matched, landed only in `possible_codes` (weak/fuzzy) and never in `codes` (definite). Per DR-D2 this is logged as data, not a census failure — they still count as HITs — but it is a matching-calibration smell worth flagging._

| name | source_sublist | hit-rate | union (possible_codes only) |
|------|----------------|---------:|------------------------------|
| DAVID IRWIN PORTNOY | Denied Persons List | 1/5 | 1124070, 1136701, 1149400, 1150255, 1150766 |
| DMITRY N. CHERNYSHENKO | Denied Persons List | 1/5 | 1067132, 1112414, 1112471, 1112640, 1141704 |
| EDSONS WORLDWIDE SERVICES, INC | Denied Persons List | 5/5 | 1151178 |
| IAN ACE | Denied Persons List | 2/5 | 1128224, 1131763, 1147278, 1148047, 1155626 |
| KATSUTA KEISUKE | Denied Persons List | 4/5 | 1032427, 1122628, 1127585, 1133330 |
| KHALDOUN HEJAZI | Denied Persons List | 5/5 | 1126447, 1136704 |
| MAN CHUNG TONG | Denied Persons List | 5/5 | 1128507 |
| MUHAMMAD KAMRAN WALI | Denied Persons List | 5/5 | 1072950, 1120789 |
| SAMMY SMITH | Denied Persons List | 5/5 | 1150084, 1150095, 1150129 |
| SUSAN Y.GIMM | Denied Persons List | 4/5 | 1129924, 1129945, 1147403 |
| WEN ENTERPRISES | Denied Persons List | 5/5 | 1132524, 1135620 |

## Per-`source_sublist` recall (reconciled by sublist, not programs — F4)

| source_sublist | agency | names | %HIT 5/5 | %flaky | %MISS |
|----------------|--------|------:|---------:|-------:|------:|
| Denied Persons List (DPL) - Bureau of Industry and Security | BIS | 26 | 65% | 19% | 15% |
| Entity List (EL) - Bureau of Industry and Security | BIS | 25 | 100% | 0% | 0% |
| ITAR Debarred (DTC) - State Department | State | 25 | 100% | 0% | 0% |
| Military End User (MEU) List - Bureau of Industry and Security | BIS | 25 | 100% | 0% | 0% |
| Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department | Treasury (OFAC) | 25 | 100% | 0% | 0% |
| Nonproliferation Sanctions (ISN) - State Department | State | 25 | 100% | 0% | 0% |
| Palestinian Legislative Council List (PLC) - Treasury Department | Treasury (OFAC) | 25 | 100% | 0% | 0% |
| Sectoral Sanctions Identifications List (SSI) - Treasury Department | Treasury (OFAC) | 25 | 100% | 0% | 0% |
| Specially Designated Nationals (SDN) - Treasury Department | Treasury (OFAC) | 25 | 100% | 0% | 0% |
| Unverified List (UVL) - Bureau of Industry and Security | BIS | 25 | 100% | 0% | 0% |
| Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department | Treasury (OFAC) | 10 | 100% | 0% | 0% |
| Capta List (CAP) - Treasury Department | Treasury (OFAC) | 1 | 100% | 0% | 0% |

_BIS/State rows carry empty `programs`/`entity_type` by design (trade.gov aggregate, DR-0/F4); that is expected, not a coverage hole._

## MISSES — 0/5, candidate recall gaps

| name | source_sublist | hit-rate | note |
|------|----------------|---------:|------|
| BLACK, SIVALLS & BRYSON (UK) LTD | Denied Persons List | 0/5 |  |
| ITEX-WAVE FZCO | Denied Persons List | 0/5 |  |
| KOLOKOL (AKA: ALDRICH AMES) | Denied Persons List | 0/5 |  |
| TATOS, FRED | Denied Persons List | 0/5 |  |

## FLAKY — 1–4/5, candidate recall gaps

| name | source_sublist | hit-rate |
|------|----------------|---------:|
| DAVID IRWIN PORTNOY | Denied Persons List | 1/5 |
| DMITRY N. CHERNYSHENKO | Denied Persons List | 1/5 |
| IAN ACE | Denied Persons List | 2/5 |
| KATSUTA KEISUKE | Denied Persons List | 4/5 |
| SUSAN Y.GIMM | Denied Persons List | 4/5 |

## Stratified sample definition

Sampled deterministically from `oracle/expected.csv` (exact `primary_name`), stratified by `source_sublist` (all 12 CSL sublists). Pilot: up to 25 distinct names per sublist (all if fewer). Within each sublist: deduplicate by name → sort → seed-shuffle (SEED=20260611, per-sublist seed) → draw. A re-run picks the same names. `EXPORT MATERIALS, INC.` is force-included as a positive control.

| source_sublist | names drawn |
|----------------|------------:|
| Denied Persons List (DPL) - Bureau of Industry and Security | 26 |
| Entity List (EL) - Bureau of Industry and Security | 25 |
| ITAR Debarred (DTC) - State Department | 25 |
| Military End User (MEU) List - Bureau of Industry and Security | 25 |
| Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department | 25 |
| Nonproliferation Sanctions (ISN) - State Department | 25 |
| Palestinian Legislative Council List (PLC) - Treasury Department | 25 |
| Sectoral Sanctions Identifications List (SSI) - Treasury Department | 25 |
| Specially Designated Nationals (SDN) - Treasury Department | 25 |
| Unverified List (UVL) - Bureau of Industry and Security | 25 |
| Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department | 10 |
| Capta List (CAP) - Treasury Department | 1 |
