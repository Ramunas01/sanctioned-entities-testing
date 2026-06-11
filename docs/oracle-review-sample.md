# Oracle PR #5 — Independent Review Sample

Deterministic stratified sample of **41** rows from `oracle/expected.csv` (25,767 rows), each paired with its raw source row for cell-by-cell audit. Index = data-row position; the oracle preserves source order with no dedup, so expected[i] <-> source[i].

For each row: confirm the 6 verbatim columns equal the named raw source column, and that `strong_alias` = `unknown` iff aliases is non-empty (D1 placeholder).

## row 0  —  _sublist:CMIC_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | China Telecom Corporation Limited | `name` | China Telecom Corporation Limited |
| `aliases` | CHINA TELECOM; CHINA TELECOM CO., LTD; CHINA TELECOM CORP LTD | `alt_names` | CHINA TELECOM; CHINA TELECOM CO., LTD; CHINA TELECOM CORP LTD |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | CMIC-EO13959 | `programs` | CMIC-EO13959 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department | `source` | Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department |

## row 1  —  _sublist:EL_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Abdul Satar Ghoura | `name` | Abdul Satar Ghoura |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` | 2011-11-21 | `start_date` | 2011-11-21 |
| `source_sublist` | Entity List (EL) - Bureau of Industry and Security | `source` | Entity List (EL) - Bureau of Industry and Security |

## row 2  —  _sublist:MEU_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Academy of Aerospace Solid Propulsion Technology (AASPT) | `name` | Academy of Aerospace Solid Propulsion Technology (AASPT) |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` | 2020-12-23 | `start_date` | 2020-12-23 |
| `source_sublist` | Military End User (MEU) List - Bureau of Industry and Security | `source` | Military End User (MEU) List - Bureau of Industry and Security |

## row 3  —  _sublist:PLC_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Ismail Abdul Salah HANIYA | `name` | Ismail Abdul Salah HANIYA |
| `aliases` | Ismail HANIYA; Ismaeel HANIYYA | `alt_names` | Ismail HANIYA; Ismaeel HANIYYA |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Individual | `type` | Individual |
| `programs` | NS-PLC | `programs` | NS-PLC |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Palestinian Legislative Council List (PLC) - Treasury Department | `source` | Palestinian Legislative Council List (PLC) - Treasury Department |

## row 4  —  _sublist:CAP_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | BANK OF KUNLUN CO LTD | `name` | BANK OF KUNLUN CO LTD |
| `aliases` | KARAMAY URBAN CREDIT COOPERATIVES; KARAMAY CITY COMMERCIAL BANK CO LTD. | `alt_names` | KARAMAY URBAN CREDIT COOPERATIVES; KARAMAY CITY COMMERCIAL BANK CO LTD. |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | 561-Related | `programs` | 561-Related |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Capta List (CAP) - Treasury Department | `source` | Capta List (CAP) - Treasury Department |

## row 5  —  _sublist:DTC_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | A & C International Trade, Inc. | `name` | A & C International Trade, Inc. |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` |  | `start_date` |  |
| `source_sublist` | ITAR Debarred (DTC) - State Department | `source` | ITAR Debarred (DTC) - State Department |

## row 6  —  _sublist:NS-MBS List_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Joint Stock Company Russian Agricultural Bank | `name` | Joint Stock Company Russian Agricultural Bank |
| `aliases` | Russian Agricultural Bank; Russian Agricultural Bank Open Joint Stock Company; Rosselkhozbank; Russian Agricultural Bank OJSC; RusAg | `alt_names` | Russian Agricultural Bank; Russian Agricultural Bank Open Joint Stock Company; Rosselkhozbank; Russian Agricultural Bank OJSC; RusAg |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | UKRAINE-EO13662; RUSSIA-EO14024 | `programs` | UKRAINE-EO13662; RUSSIA-EO14024 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department | `source` | Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department |

## row 7  —  _sublist:SDN_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | AEROCARIBBEAN AIRLINES | `name` | AEROCARIBBEAN AIRLINES |
| `aliases` | AERO-CARIBBEAN | `alt_names` | AERO-CARIBBEAN |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | CUBA | `programs` | CUBA |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Specially Designated Nationals (SDN) - Treasury Department | `source` | Specially Designated Nationals (SDN) - Treasury Department |

## row 8  —  _sublist:UVL_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Atlas Sanatgaran | `name` | Atlas Sanatgaran |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Unverified List (UVL) - Bureau of Industry and Security | `source` | Unverified List (UVL) - Bureau of Industry and Security |

## row 9  —  _sublist:DPL_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | SEMICONDUCTOR SYSTEMS INTL., INC. (SSI) | `name` | SEMICONDUCTOR SYSTEMS INTL., INC. (SSI) |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` | 1992-03-20 | `start_date` | 1992-03-20 |
| `source_sublist` | Denied Persons List (DPL) - Bureau of Industry and Security | `source` | Denied Persons List (DPL) - Bureau of Industry and Security |

## row 10  —  _sublist:SSI_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | VTB BANK PUBLIC JOINT STOCK COMPANY | `name` | VTB BANK PUBLIC JOINT STOCK COMPANY |
| `aliases` | VTB Bank PAO; VTB Bank PJSC; Bank VTB Publichnoe Aktsionernoe Obshchestvo; VTB Bank; Bank VTB PAO; JSC VTB Bank New Delhi Branch; VTB Bank PJSC Shanghai Bran... | `alt_names` | VTB Bank PAO; VTB Bank PJSC; Bank VTB Publichnoe Aktsionernoe Obshchestvo; VTB Bank; Bank VTB PAO; JSC VTB Bank New Delhi Branch; VTB Bank PJSC Shanghai Bran... |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | UKRAINE-EO13662; RUSSIA-EO14024 | `programs` | UKRAINE-EO13662; RUSSIA-EO14024 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Sectoral Sanctions Identifications List (SSI) - Treasury Department | `source` | Sectoral Sanctions Identifications List (SSI) - Treasury Department |

## row 11  —  _sublist:ISN_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | SPC Supachoke  | `name` | SPC Supachoke  |
| `aliases` | Super Trade | `alt_names` | Super Trade |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` | Chemical and Biological Weapons Act | `programs` | Chemical and Biological Weapons Act |
| `start_date` | 1994-02-08 | `start_date` | 1994-02-08 |
| `source_sublist` | Nonproliferation Sanctions (ISN) - State Department | `source` | Nonproliferation Sanctions (ISN) - State Department |

## row 330  —  _sublist:ISN_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Korean Committee for Space Technology  | `name` | Korean Committee for Space Technology  |
| `aliases` | DPRK Committee for Space Technology, Department of Space Technology of North Korea, Committee for Space Technology, KCST | `alt_names` | DPRK Committee for Space Technology, Department of Space Technology of North Korea, Committee for Space Technology, KCST |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` | E.O. 13382 | `programs` | E.O. 13382 |
| `start_date` | 2013-01-24 | `start_date` | 2013-01-24 |
| `source_sublist` | Nonproliferation Sanctions (ISN) - State Department | `source` | Nonproliferation Sanctions (ISN) - State Department |

## row 444  —  _sublist:ISN_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Ri Su'ung-ch'o'l (Ri Sung Chol) (DPRK national) | `name` | Ri Su'ung-ch'o'l (Ri Sung Chol) (DPRK national) |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` | INKSNA | `programs` | INKSNA |
| `start_date` | 2024-11-20 | `start_date` | 2024-11-20 |
| `source_sublist` | Nonproliferation Sanctions (ISN) - State Department | `source` | Nonproliferation Sanctions (ISN) - State Department |

## row 512  —  _sublist:PLC_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Hamid Jabir KHUDAIR | `name` | Hamid Jabir KHUDAIR |
| `aliases` | Hamid Sulieman Jabir KHUDAIR | `alt_names` | Hamid Sulieman Jabir KHUDAIR |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Individual | `type` | Individual |
| `programs` | NS-PLC | `programs` | NS-PLC |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Palestinian Legislative Council List (PLC) - Treasury Department | `source` | Palestinian Legislative Council List (PLC) - Treasury Department |

## row 567  —  _sublist:PLC_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Qais Abdul KARIM | `name` | Qais Abdul KARIM |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` | Individual | `type` | Individual |
| `programs` | NS-PLC | `programs` | NS-PLC |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Palestinian Legislative Council List (PLC) - Treasury Department | `source` | Palestinian Legislative Council List (PLC) - Treasury Department |

## row 658  —  _sublist:DTC_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Barbara Jo Luque | `name` | Barbara Jo Luque |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` |  | `start_date` |  |
| `source_sublist` | ITAR Debarred (DTC) - State Department | `source` | ITAR Debarred (DTC) - State Department |

## row 1119  —  _sublist:UVL_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Universe Market Limited | `name` | Universe Market Limited |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Unverified List (UVL) - Bureau of Industry and Security | `source` | Unverified List (UVL) - Bureau of Industry and Security |

## row 1229  —  _sublist:UVL_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Identiparts Ltd. | `name` | Identiparts Ltd. |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Unverified List (UVL) - Bureau of Industry and Security | `source` | Unverified List (UVL) - Bureau of Industry and Security |

## row 1279  —  _sublist:DTC_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | VTA Telecom Corporation | `name` | VTA Telecom Corporation |
| `aliases` | [] | `alt_names` | [] |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` |  | `start_date` |  |
| `source_sublist` | ITAR Debarred (DTC) - State Department | `source` | ITAR Debarred (DTC) - State Department |

## row 1421  —  _sublist:SSI_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | GAZPROM DOBYCHA KUZNETSK, OOO | `name` | GAZPROM DOBYCHA KUZNETSK, OOO |
| `aliases` | GAZPROM DOBYCHA KUZNETSK; OBSHCHESTVO S OGRANICHENNOI OTVETSTVENNOSTYU 'GAZPROM DOBYCHA KUZNETSK' | `alt_names` | GAZPROM DOBYCHA KUZNETSK; OBSHCHESTVO S OGRANICHENNOI OTVETSTVENNOSTYU 'GAZPROM DOBYCHA KUZNETSK' |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | UKRAINE-EO13662 | `programs` | UKRAINE-EO13662 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Sectoral Sanctions Identifications List (SSI) - Treasury Department | `source` | Sectoral Sanctions Identifications List (SSI) - Treasury Department |

## row 1563  —  _sublist:SSI_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | TNK Trading International S.A. | `name` | TNK Trading International S.A. |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | VENEZUELA-EO13850; UKRAINE-EO13662 | `programs` | VENEZUELA-EO13850; UKRAINE-EO13662 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Sectoral Sanctions Identifications List (SSI) - Treasury Department | `source` | Sectoral Sanctions Identifications List (SSI) - Treasury Department |

## row 1597  —  _sublist:MEU_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Harbin General Aircraft Industry Co., Ltd. | `name` | Harbin General Aircraft Industry Co., Ltd. |
| `aliases` | Harbin Hafei Aviation Industry Co. Ltd. | `alt_names` | Harbin Hafei Aviation Industry Co. Ltd. |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` | 2020-12-23 | `start_date` | 2020-12-23 |
| `source_sublist` | Military End User (MEU) List - Bureau of Industry and Security | `source` | Military End User (MEU) List - Bureau of Industry and Security |

## row 1631  —  _sublist:MEU_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Beijing Skyrizon Aviation Industry Investment Co., Ltd. | `name` | Beijing Skyrizon Aviation Industry Investment Co., Ltd. |
| `aliases` | Beijing Tianjiao Aviation Industry Investment Company | `alt_names` | Beijing Tianjiao Aviation Industry Investment Company |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` | 2021-01-14 | `start_date` | 2021-01-14 |
| `source_sublist` | Military End User (MEU) List - Bureau of Industry and Security | `source` | Military End User (MEU) List - Bureau of Industry and Security |

## row 1719  —  _sublist:NS-MBS List_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Central Bank of the Russian Federation | `name` | Central Bank of the Russian Federation |
| `aliases` | Bank Rossi, Federal State Budgetary Institution; Bank of Russia; Bank of Russia, Central Bank; Tsentralny Bank Rossiskoi Federatsii; Central Bank of Russia | `alt_names` | Bank Rossi, Federal State Budgetary Institution; Bank of Russia; Bank of Russia, Central Bank; Tsentralny Bank Rossiskoi Federatsii; Central Bank of Russia |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | RUSSIA-EO14024 | `programs` | RUSSIA-EO14024 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department | `source` | Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department |

## row 1724  —  _sublist:NS-MBS List_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Michel Martelly | `name` | Michel Martelly |
| `aliases` | Michael Martelly;  | `alt_names` | Michael Martelly;  |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Individual | `type` | Individual |
| `programs` | ILLICIT-DRUGS-EO14059 | `programs` | ILLICIT-DRUGS-EO14059 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department | `source` | Non-SDN Menu-Based Sanctions List (NS-MBS List) - Treasury Department |

## row 2527  —  _entity_type:Vessel_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | MAR AZUL | `name` | MAR AZUL |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` | Vessel | `type` | Vessel |
| `programs` | CUBA | `programs` | CUBA |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Specially Designated Nationals (SDN) - Treasury Department | `source` | Specially Designated Nationals (SDN) - Treasury Department |

## row 2655  —  _sublist:DPL_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | DAVOUD BANIAMERI | `name` | DAVOUD BANIAMERI |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` | 2012-05-03 | `start_date` | 2012-05-03 |
| `source_sublist` | Denied Persons List (DPL) - Bureau of Industry and Security | `source` | Denied Persons List (DPL) - Bureau of Industry and Security |

## row 3102  —  _DATE-ANOMALY_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | FRANCISCO JAVIER MENDOZA-ESQUIVEL | `name` | FRANCISCO JAVIER MENDOZA-ESQUIVEL |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` |  8/11/2015 | `start_date` |  8/11/2015 |
| `source_sublist` | Denied Persons List (DPL) - Bureau of Industry and Security | `source` | Denied Persons List (DPL) - Bureau of Industry and Security |

## row 4061  —  _MULTI-PROGRAM(8 codes)_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | ISLAMIC REVOLUTIONARY GUARD CORPS | `name` | ISLAMIC REVOLUTIONARY GUARD CORPS |
| `aliases` | IRGC; THE IRANIAN REVOLUTIONARY GUARDS; IRG; THE ARMY OF THE GUARDIANS OF THE ISLAMIC REVOLUTION; AGIR; SEPAH-E PASDARAN-E ENQELAB-E ESLAMI; PASDARN-E ENGHEL... | `alt_names` | IRGC; THE IRANIAN REVOLUTIONARY GUARDS; IRG; THE ARMY OF THE GUARDIANS OF THE ISLAMIC REVOLUTION; AGIR; SEPAH-E PASDARAN-E ENQELAB-E ESLAMI; PASDARN-E ENGHEL... |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | NPWMD; IRGC; IRAN-HR; HRIT-IR; IFSR; SDGT; FTO; ELECTION-EO13848 | `programs` | NPWMD; IRGC; IRAN-HR; HRIT-IR; IFSR; SDGT; FTO; ELECTION-EO13848 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Specially Designated Nationals (SDN) - Treasury Department | `source` | Specially Designated Nationals (SDN) - Treasury Department |

## row 4074  —  _MULTI-PROGRAM(6 codes)_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | ISLAMIC REVOLUTIONARY GUARD CORPS (IRGC)-QODS FORCE | `name` | ISLAMIC REVOLUTIONARY GUARD CORPS (IRGC)-QODS FORCE |
| `aliases` | PASDARAN-E ENGHELAB-E ISLAMI (PASDARAN); SEPAH-E QODS (JERUSALEM FORCE); IRGC-QF; IRGC-QUDS FORCE; ISLAMIC REVOLUTIONARY GUARD CORPS-QODS FORCE; QODS FORCE; ... | `alt_names` | PASDARAN-E ENGHELAB-E ISLAMI (PASDARAN); SEPAH-E QODS (JERUSALEM FORCE); IRGC-QF; IRGC-QUDS FORCE; ISLAMIC REVOLUTIONARY GUARD CORPS-QODS FORCE; QODS FORCE; ... |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | IRGC; SDGT; IFSR; IRAN-HR; FTO; ELECTION-EO13848 | `programs` | IRGC; SDGT; IFSR; IRAN-HR; FTO; ELECTION-EO13848 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Specially Designated Nationals (SDN) - Treasury Department | `source` | Specially Designated Nationals (SDN) - Treasury Department |

## row 5328  —  _MULTI-PROGRAM(6 codes)_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | ISLAMIC REVOLUTIONARY GUARD CORPS AIR FORCE | `name` | ISLAMIC REVOLUTIONARY GUARD CORPS AIR FORCE |
| `aliases` | SEPAH PASDARAN AIR FORCE; IRGC AIR FORCE; ISLAMIC REVOLUTION GUARDS CORPS AIR FORCE; ISLAMIC REVOLUTIONARY GUARDS CORPS AIR FORCE; IRGCAF; AIR FORCE, IRGC (P... | `alt_names` | SEPAH PASDARAN AIR FORCE; IRGC AIR FORCE; ISLAMIC REVOLUTION GUARDS CORPS AIR FORCE; ISLAMIC REVOLUTIONARY GUARDS CORPS AIR FORCE; IRGCAF; AIR FORCE, IRGC (P... |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | NPWMD; IRGC; IFSR; SDGT; FTO; RUSSIA-EO14024 | `programs` | NPWMD; IRGC; IFSR; SDGT; FTO; RUSSIA-EO14024 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Specially Designated Nationals (SDN) - Treasury Department | `source` | Specially Designated Nationals (SDN) - Treasury Department |

## row 5332  —  _MULTI-PROGRAM(6 codes)_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | NAQDI, Mohammad Reza | `name` | NAQDI, Mohammad Reza |
| `aliases` | NAGHDI, Mohammad Reza; SHAMS, Mohammad Reza; NAQDI, Muhammad; NAQDI, Mohammad-Reza; NAGHDI, Mohammedreza; NAQDI, Gholamreza; NAQDI, Gholam-reza | `alt_names` | NAGHDI, Mohammad Reza; SHAMS, Mohammad Reza; NAQDI, Muhammad; NAQDI, Mohammad-Reza; NAGHDI, Mohammedreza; NAQDI, Gholamreza; NAQDI, Gholam-reza |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Individual | `type` | Individual |
| `programs` | NPWMD; IRGC; IRAN-HR; IFSR; SDGT; IRAN-EO13876 | `programs` | NPWMD; IRGC; IRAN-HR; IFSR; SDGT; IRAN-EO13876 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Specially Designated Nationals (SDN) - Treasury Department | `source` | Specially Designated Nationals (SDN) - Treasury Department |

## row 5989  —  _sublist:DPL_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | MARCO SANTILLAN, JR | `name` | MARCO SANTILLAN, JR |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` | 2025-12-15 | `start_date` | 2025-12-15 |
| `source_sublist` | Denied Persons List (DPL) - Bureau of Industry and Security | `source` | Denied Persons List (DPL) - Bureau of Industry and Security |

## row 6101  —  _sublist:CMIC_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | CHINA SATELLITE COMMUNICATIONS CO., LTD. | `name` | CHINA SATELLITE COMMUNICATIONS CO., LTD. |
| `aliases` | CHINA SATCOM | `alt_names` | CHINA SATCOM |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | CMIC-EO13959 | `programs` | CMIC-EO13959 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department | `source` | Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department |

## row 6168  —  _sublist:CMIC_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Xiamen Meiya Pico Information Co., Ltd. | `name` | Xiamen Meiya Pico Information Co., Ltd. |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` | Entity | `type` | Entity |
| `programs` | CMIC-EO13959 | `programs` | CMIC-EO13959 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department | `source` | Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) - Treasury Department |

## row 6855  —  _sublist:EL_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Innovation and Technologies LLC | `name` | Innovation and Technologies LLC |
| `aliases` | Intekh; INTEKH OOO | `alt_names` | Intekh; INTEKH OOO |
| `strong_alias` | unknown | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` | 2023-02-27 | `start_date` | 2023-02-27 |
| `source_sublist` | Entity List (EL) - Bureau of Industry and Security | `source` | Entity List (EL) - Bureau of Industry and Security |

## row 9076  —  _sublist:EL_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | Huawei Technologies Bahrain | `name` | Huawei Technologies Bahrain |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` |  | `type` |  |
| `programs` |  | `programs` |  |
| `start_date` | 2019-08-21 | `start_date` | 2019-08-21 |
| `source_sublist` | Entity List (EL) - Bureau of Industry and Security | `source` | Entity List (EL) - Bureau of Industry and Security |

## row 9142  —  _entity_type:Aircraft_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | EP-GOL | `name` | EP-GOL |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` | Aircraft | `type` | Aircraft |
| `programs` | SDGT | `programs` | SDGT |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Specially Designated Nationals (SDN) - Treasury Department | `source` | Specially Designated Nationals (SDN) - Treasury Department |

## row 16234  —  _sublist:SDN_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | KAZAKOVA, Olga Mikhailovna | `name` | KAZAKOVA, Olga Mikhailovna |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` | Individual | `type` | Individual |
| `programs` | RUSSIA-EO14024 | `programs` | RUSSIA-EO14024 |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Specially Designated Nationals (SDN) - Treasury Department | `source` | Specially Designated Nationals (SDN) - Treasury Department |

## row 25766  —  _sublist:SDN_

| expected column | oracle value | raw source col | raw source value |
|---|---|---|---|
| `primary_name` | AHADZADEH, Sajjad | `name` | AHADZADEH, Sajjad |
| `aliases` |  | `alt_names` |  |
| `strong_alias` |  | `(derived)` | — |
| `entity_type` | Individual | `type` | Individual |
| `programs` | IFSR; IRAN-CON-ARMS-EO | `programs` | IFSR; IRAN-CON-ARMS-EO |
| `start_date` |  | `start_date` |  |
| `source_sublist` | Specially Designated Nationals (SDN) - Treasury Department | `source` | Specially Designated Nationals (SDN) - Treasury Department |
