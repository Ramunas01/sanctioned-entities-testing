# Determinism Probe — Findings (DR-D2)

_Generated: 2026-06-11T17:25:16.859897+00:00_  
_Raw capture: `results/determinism-probe-20260611T172417Z.jsonl`_  
_Probe: `harness/determinism_probe.py` (SEED=20260611, K=5, concurrency=4, per-stratum=8)_

**HEADLINE: 1/48 listed queries show UNION-CHURN — the set of matched code IDs changes across identical runs. This is worse than bucket churn and blocks #4 threshold testing.**

## Verdict

- **Bucketing stable enough for #4?** NO (BUCKET-CHURN=2, UNION-CHURN=1).
- **`version_used` stable across the whole run (DR-REPRO)?** YES — observed: `2026-06-11`.
- **Total calls:** 265 (errors: 0).
- **Control sanity:** OK — all 5 gibberish controls produced clean misses (empty `codes`).
- **Sub-finding (DR-D2):** 2 exact source name(s) landed ONLY in `possible_codes` (never `codes`) — a matching-calibration smell: 'THOMAS LIM', 'EXPORT MATERIALS, INC.'.

## Classification summary (listed queries)

| Classification | Count |
|----------------|------:|
| STABLE | 45 |
| BUCKET-CHURN | 2 |
| UNION-CHURN | 1 |
| ERRORED | 0 |

## Per-query classification

| Query | Agency | Type | OK/Err | classification | #union | version_used |
|-------|--------|------|:------:|----------------|------:|------|
| EXPORT MATERIALS, INC. | BIS | ∅ | 5/0 | UNION-CHURN | 2 | 2026-06-11 |
| ACHEKZAI, Maulawi Adam Khan | Treasury | Individual | 5/0 | BUCKET-CHURN | 3 | 2026-06-11 |
| AL-KHAFAJI, Muhsin Khadr | Treasury | Individual | 5/0 | BUCKET-CHURN | 3 | 2026-06-11 |
| 3A-MGU | Treasury | Aircraft | 5/0 | STABLE | 2 | 2026-06-11 |
| 5th Shipyard | BIS | ∅ | 5/0 | STABLE | 1 | 2026-06-11 |
| AAJ | Treasury | Vessel | 5/0 | STABLE | 3 | 2026-06-11 |
| AL-WATFA, Ali Ibrahim | Treasury | Individual | 5/0 | STABLE | 1 | 2026-06-11 |
| ASSOCIATES OF PARTNERS SAL OFF-SHORE | Treasury | Entity | 5/0 | STABLE | 1 | 2026-06-11 |
| Aerospace Industries Organization (AIO) | State | ∅ | 5/0 | STABLE | 1 | 2026-06-11 |
| Alejandro Reyes-Baez | State | ∅ | 5/0 | STABLE | 1 | 2026-06-11 |
| Avin Electronics Technology Co., Ltd. (AET | BIS | ∅ | 5/0 | STABLE | 1 | 2026-06-11 |
| BOREY G | Treasury | Vessel | 5/0 | STABLE | 2 | 2026-06-11 |
| BRYAN VILLANUEVA-VALLES | BIS | ∅ | 5/0 | STABLE | 1 | 2026-06-11 |
| EP-IBZ | Treasury | Aircraft | 5/0 | STABLE | 1 | 2026-06-11 |
| EP-ICF | Treasury | Aircraft | 5/0 | STABLE | 1 | 2026-06-11 |
| EP-ITD | Treasury | Aircraft | 5/0 | STABLE | 1 | 2026-06-11 |
| ESTANCIA INFANTIL NINO FELIZ S.C. | Treasury | Entity | 5/0 | STABLE | 1 | 2026-06-11 |
| Ernesto Hernandez | State | ∅ | 5/0 | STABLE | 1 | 2026-06-11 |
| FU YUAN YU 8651 | Treasury | Vessel | 5/0 | STABLE | 1 | 2026-06-11 |
| GRACHEV, Pavel Sergeyevich | Treasury | Individual | 5/0 | STABLE | 1 | 2026-06-11 |
| Gerardo Domingo Rodriguez-Rivera | State | ∅ | 5/0 | STABLE | 1 | 2026-06-11 |
| HONG XUN | Treasury | Vessel | 5/0 | STABLE | 1 | 2026-06-11 |
| Hector De Jesus Garcia | State | ∅ | 5/0 | STABLE | 1 | 2026-06-11 |
| KASMA | Treasury | Vessel | 5/0 | STABLE | 3 | 2026-06-11 |
| Kepler Corporation | BIS | ∅ | 5/0 | STABLE | 1 | 2026-06-11 |
| LIA | Treasury | Vessel | 5/0 | STABLE | 3 | 2026-06-11 |
| LIMITED LIABILITY COMPANY SOVRUDNIK | Treasury | Entity | 5/0 | STABLE | 1 | 2026-06-11 |
| M SOPHIA | Treasury | Vessel | 5/0 | STABLE | 3 | 2026-06-11 |
| MASAKI, Toshio | Treasury | Individual | 5/0 | STABLE | 1 | 2026-06-11 |
| MELLADO CRUZ, Galdino | Treasury | Individual | 5/0 | STABLE | 1 | 2026-06-11 |
| MOSKVICHEV, Evgeny Sergeyevich | Treasury | Individual | 5/0 | STABLE | 2 | 2026-06-11 |
| ORBITAL HORIZONS CORP. | Treasury | Entity | 5/0 | STABLE | 1 | 2026-06-11 |
| Oben Cabalceta | State | ∅ | 5/0 | STABLE | 2 | 2026-06-11 |
| Orelmetallpolimer LLC | BIS | ∅ | 5/0 | STABLE | 2 | 2026-06-11 |
| POLARIS 1 | Treasury | Vessel | 5/0 | STABLE | 1 | 2026-06-11 |
| Public Joint Stock Company Gazprom Neft | Treasury | Entity | 5/0 | STABLE | 5 | 2026-06-11 |
| RA-86496 | Treasury | Aircraft | 5/0 | STABLE | 1 | 2026-06-11 |
| RA-86539 | Treasury | Aircraft | 5/0 | STABLE | 1 | 2026-06-11 |
| SUTARIA, Satishkumar Hareshbhai | Treasury | Individual | 5/0 | STABLE | 1 | 2026-06-11 |
| SWISSTEC 3D AKUS AG | Treasury | Entity | 5/0 | STABLE | 1 | 2026-06-11 |
| Shahid Hemmat Industrial Group (SHIG) | State | ∅ | 5/0 | STABLE | 3 | 2026-06-11 |
| Shenzhen Mingxinyuan Co., Ltd. | BIS | ∅ | 5/0 | STABLE | 1 | 2026-06-11 |
| THOMAS LIM | BIS | ∅ | 5/0 | STABLE | 2 | 2026-06-11 |
| TSARGRAD PARK OOO | Treasury | Entity | 5/0 | STABLE | 1 | 2026-06-11 |
| VOSTOKINTERPROM LIMITED LIABILITY COMPANY | Treasury | Entity | 5/0 | STABLE | 1 | 2026-06-11 |
| YV2716 | Treasury | Aircraft | 5/0 | STABLE | 1 | 2026-06-11 |
| YV3071 | Treasury | Aircraft | 5/0 | STABLE | 1 | 2026-06-11 |
| Yasser Ahmad Obeid | State | ∅ | 5/0 | STABLE | 1 | 2026-06-11 |
| Flarbnax Qugglethorpe Wibbenstein | — | — | 5/0 | STABLE | 0 | 2026-06-11 |
| Gribnaxle Pfutterworth Vexmondiac | — | — | 5/0 | STABLE | 0 | 2026-06-11 |
| Klaxnorbit Drimblewedge Snorftacular | — | — | 5/0 | STABLE | 0 | 2026-06-11 |
| Zxqwvbn Plokmijn Qwerasdf | — | — | 5/0 | STABLE | 0 | 2026-06-11 |
| Zzyzx Vorplenugget Throbblewick | — | — | 5/0 | STABLE | 0 | 2026-06-11 |

## Concrete instability examples

### `ACHEKZAI, Maulawi Adam Khan` — BUCKET-CHURN

- agency=Treasury, type=Individual, ok runs=5, union=['1073001', '1120907', '1143831']
- code `1073001`: appeared in bucket(s) ['codes', 'possible_codes'], present in 5/5 ok runs (bucket-instability)
- code `1120907`: appeared in bucket(s) ['codes', 'possible_codes'], present in 5/5 ok runs (bucket-instability)

  Per-run buckets:
  - run 1: codes=['1143831'] possible=['1073001', '1120907']
  - run 2: codes=['1143831'] possible=['1073001', '1120907']
  - run 3: codes=['1143831'] possible=['1073001', '1120907']
  - run 4: codes=['1073001', '1120907', '1143831'] possible=[]
  - run 5: codes=['1143831'] possible=['1073001', '1120907']

### `AL-KHAFAJI, Muhsin Khadr` — BUCKET-CHURN

- agency=Treasury, type=Individual, ok runs=5, union=['1000416', '1122397', '1134686']
- code `1000416`: appeared in bucket(s) ['codes', 'possible_codes'], present in 5/5 ok runs (bucket-instability)
- code `1122397`: appeared in bucket(s) ['codes', 'possible_codes'], present in 5/5 ok runs (bucket-instability)

  Per-run buckets:
  - run 1: codes=['1122397', '1134686'] possible=['1000416']
  - run 2: codes=['1134686'] possible=['1000416', '1122397']
  - run 3: codes=['1000416', '1122397', '1134686'] possible=[]
  - run 4: codes=['1000416', '1122397', '1134686'] possible=[]
  - run 5: codes=['1000416', '1122397', '1134686'] possible=[]

### `EXPORT MATERIALS, INC.` — UNION-CHURN

- agency=BIS, type=∅, ok runs=5, union=['1145893', '1145895']
- code `1145893`: appeared in bucket(s) ['possible_codes'], present in 4/5 ok runs (union-instability)
- code `1145895`: appeared in bucket(s) ['possible_codes'], present in 2/5 ok runs (union-instability)

  Per-run buckets:
  - run 1: codes=[] possible=['1145893', '1145895']
  - run 2: codes=[] possible=['1145893']
  - run 3: codes=[] possible=[]
  - run 4: codes=[] possible=['1145893', '1145895']
  - run 5: codes=[] possible=['1145893']

## Query set chosen (and why)

Stratified deterministically from `oracle/expected.csv` (exact `primary_name`), across the three CSL agencies (Treasury/BIS/State, from `source_sublist`) and entity types. Listed names were filtered to *distinctive* candidates (multi-token persons/entities; vessel/aircraft identifiers) likely to match, so the bucket assignment is what gets exercised. Selection is seed+sort driven (SEED=20260611); a re-run picks the same names.

| Query | Kind | Agency | Type | sublist |
|-------|------|--------|------|---------|
| ACHEKZAI, Maulawi Adam Khan | listed | Treasury | Individual | Specially Designated Nationals (SD |
| MELLADO CRUZ, Galdino | listed | Treasury | Individual | Specially Designated Nationals (SD |
| AL-WATFA, Ali Ibrahim | listed | Treasury | Individual | Specially Designated Nationals (SD |
| GRACHEV, Pavel Sergeyevich | listed | Treasury | Individual | Specially Designated Nationals (SD |
| MOSKVICHEV, Evgeny Sergeyevich | listed | Treasury | Individual | Specially Designated Nationals (SD |
| MASAKI, Toshio | listed | Treasury | Individual | Specially Designated Nationals (SD |
| SUTARIA, Satishkumar Hareshbhai | listed | Treasury | Individual | Specially Designated Nationals (SD |
| AL-KHAFAJI, Muhsin Khadr | listed | Treasury | Individual | Specially Designated Nationals (SD |
| ORBITAL HORIZONS CORP. | listed | Treasury | Entity | Specially Designated Nationals (SD |
| Public Joint Stock Company Gazprom Neft | listed | Treasury | Entity | Sectoral Sanctions Identifications |
| ASSOCIATES OF PARTNERS SAL OFF-SHORE | listed | Treasury | Entity | Specially Designated Nationals (SD |
| ESTANCIA INFANTIL NINO FELIZ S.C. | listed | Treasury | Entity | Specially Designated Nationals (SD |
| LIMITED LIABILITY COMPANY SOVRUDNIK | listed | Treasury | Entity | Specially Designated Nationals (SD |
| SWISSTEC 3D AKUS AG | listed | Treasury | Entity | Specially Designated Nationals (SD |
| VOSTOKINTERPROM LIMITED LIABILITY COMPANY | listed | Treasury | Entity | Specially Designated Nationals (SD |
| TSARGRAD PARK OOO | listed | Treasury | Entity | Specially Designated Nationals (SD |
| LIA | listed | Treasury | Vessel | Specially Designated Nationals (SD |
| KASMA | listed | Treasury | Vessel | Specially Designated Nationals (SD |
| BOREY G | listed | Treasury | Vessel | Specially Designated Nationals (SD |
| POLARIS 1 | listed | Treasury | Vessel | Specially Designated Nationals (SD |
| FU YUAN YU 8651 | listed | Treasury | Vessel | Specially Designated Nationals (SD |
| AAJ | listed | Treasury | Vessel | Specially Designated Nationals (SD |
| M SOPHIA | listed | Treasury | Vessel | Specially Designated Nationals (SD |
| HONG XUN | listed | Treasury | Vessel | Specially Designated Nationals (SD |
| YV3071 | listed | Treasury | Aircraft | Specially Designated Nationals (SD |
| RA-86496 | listed | Treasury | Aircraft | Specially Designated Nationals (SD |
| RA-86539 | listed | Treasury | Aircraft | Specially Designated Nationals (SD |
| EP-ITD | listed | Treasury | Aircraft | Specially Designated Nationals (SD |
| EP-ICF | listed | Treasury | Aircraft | Specially Designated Nationals (SD |
| EP-IBZ | listed | Treasury | Aircraft | Specially Designated Nationals (SD |
| 3A-MGU | listed | Treasury | Aircraft | Specially Designated Nationals (SD |
| YV2716 | listed | Treasury | Aircraft | Specially Designated Nationals (SD |
| 5th Shipyard | listed | BIS | ∅ | Entity List (EL) - Bureau of Indus |
| THOMAS LIM | listed | BIS | ∅ | Denied Persons List (DPL) - Bureau |
| Kepler Corporation | listed | BIS | ∅ | Entity List (EL) - Bureau of Indus |
| EXPORT MATERIALS, INC. | listed | BIS | ∅ | Denied Persons List (DPL) - Bureau |
| Orelmetallpolimer LLC | listed | BIS | ∅ | Entity List (EL) - Bureau of Indus |
| Shenzhen Mingxinyuan Co., Ltd. | listed | BIS | ∅ | Unverified List (UVL) - Bureau of  |
| BRYAN VILLANUEVA-VALLES | listed | BIS | ∅ | Denied Persons List (DPL) - Bureau |
| Avin Electronics Technology Co., Ltd. (AET | listed | BIS | ∅ | Entity List (EL) - Bureau of Indus |
| Shahid Hemmat Industrial Group (SHIG) | listed | State | ∅ | Nonproliferation Sanctions (ISN) - |
| Ernesto Hernandez | listed | State | ∅ | ITAR Debarred (DTC) - State Depart |
| Hector De Jesus Garcia | listed | State | ∅ | ITAR Debarred (DTC) - State Depart |
| Aerospace Industries Organization (AIO) | listed | State | ∅ | Nonproliferation Sanctions (ISN) - |
| Gerardo Domingo Rodriguez-Rivera | listed | State | ∅ | ITAR Debarred (DTC) - State Depart |
| Oben Cabalceta | listed | State | ∅ | ITAR Debarred (DTC) - State Depart |
| Yasser Ahmad Obeid | listed | State | ∅ | ITAR Debarred (DTC) - State Depart |
| Alejandro Reyes-Baez | listed | State | ∅ | ITAR Debarred (DTC) - State Depart |
| Zxqwvbn Plokmijn Qwerasdf | control | — | — | — |
| Flarbnax Qugglethorpe Wibbenstein | control | — | — | — |
| Zzyzx Vorplenugget Throbblewick | control | — | — | — |
| Klaxnorbit Drimblewedge Snorftacular | control | — | — | — |
| Gribnaxle Pfutterworth Vexmondiac | control | — | — | — |
