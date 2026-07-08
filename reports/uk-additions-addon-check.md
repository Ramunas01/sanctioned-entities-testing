# Does the Add-on identify the newest UK Sanctions List designations?

**Verdict: YES — 86/86 new UK designations are correctly identified, all by UK-issued
records, all at 5/5 runs.** No misses, no flakiness, no false positives on controls.

Run 2026-07-08. Endpoint `POST /api/sanctions_person_versions_regulations/match`
(`docs/addon-interface.md`). Harness `harness/uk_addon_check.py`. Raw capture
`results/uk-additions-addon-20260708T073002Z.jsonl`. Per-record table
`reports/uk_additions_addon_check.csv`.

## Scope

The 86 records added to the UK Sanctions List between the snapshots generated
02/06/2026 and 07/07/2026 (`data/uk-latest-additions.csv`, produced by
`harness/uk_latest.py --against`). 59 Individual/Entity + 27 Ship.

This measures **presence** (is the new record matchable?), not precision, not
alias recall, not the ranking of `codes` vs `possible_codes`.

## Result

| Group | n | Result |
|---|---:|---|
| **Additions** (Individual/Entity) | 59 | **59 STABLE_DEFINITE (100%)** |
| **Additions** (Ship) | 27 | **27 STABLE_DEFINITE (100%)** |
| Control: long-standing records, one pair per affected regime | 6 | 6 STABLE_DEFINITE |
| Control: nonsense names | 2 | 0 identity matches (as required) |
| Delisted by this refresh | 3 | 3 still match — see below |

- `version_used = 2026-07-08`, **stable** across all 485 calls (DR-REPRO satisfied).
- **0 errors** in 485 calls.
- Every addition matched at **5/5 runs**. No flaky retrieval.
- Every addition matched by a record with `meta.issuer = UK` — not a copy of the
  same party from the EU or US list. (4 parties are listed by multiple regimes;
  all 4 have a UK record among their matches.)
- Every addition's served `valid_from` **equals its source `DateDesignated`**, 86/86.
- Every match was `exact` under the pinned normalization; **none** relied on the
  looser token-set rule. The result does not depend on how permissive the identity
  rule is.

Coverage is uniform across the three designation batches: 06/07/2026 (9),
16/06/2026 (70), 09/06/2026 (7) — all STABLE_DEFINITE.

## Why this is not a bare census

Two things would have made "did any code come back?" the wrong question.

**1. The endpoint returns fuzzy neighbours for names that are not listed at all.**
`query="Jonas Petraitis Nobody Random"` → `codes {}` but three unrelated
`possible_codes`. DR-D2's census rule (`HIT = codes ∪ possible_codes`) would score
that nonsense string as a hit. Correct for "did ingestion happen at all" on a list
known to be loaded; wrong for "is *this* record present". So a hit here required
**identity**: a returned record whose title matches the queried party's primary name
or an alias under the A1 normalization (NFKC → casefold → collapse non-alphanumerics),
compared as token multisets. Everything else is a neighbour. Both negative controls
produced zero identity matches across 10 calls.

**2. Freshness is per-envelope, not global.** `processing.version_used` is one global
date, but the Add-on serves one envelope per regulation, each with its own validity.
A record designated 06/07/2026 cannot be matched by an envelope cut before that date
— and that would be **correct behaviour, not a defect**. Scoring such a no-match as a
miss is precisely the error that produced the retracted Finding #9. So the harness
records the envelope of every match and reports it alongside.

Observed UK envelope cuts (`envelope_valid_from`):

| Envelope | Cut |
|---|---|
| `reg-uk-the-chemical-weapons-sanctions-eu-exit-regulations-2019.json` | 2026-07-06 |
| `reg-uk-the-global-human-rights-sanctions-regulations-2020.json` | 2026-07-06 |
| `reg-uk-the-russia-sanctions-eu-exit-regulations-2019.json` | 2026-06-02, 2026-07-06 |
| `reg-uk-the-libya-sanctions-eu-exit-regulations-2020.json` | 2026-06-02 |

The three regimes carrying additions (CHW, GHR, RUS) are all cut **2026-07-06** —
one day behind the source list's `DateGenerated` of 07/07/2026, and on/after every
designation date under test. So the additions *could* be present, and they are.

Note `envelope_valid_from` is a **per-record** field: the same envelope filename
appears with different values. An earlier version of this harness let the last write
win and reported the Russia envelope as `2026-06-02`, manufacturing an apparent
contradiction (a June-2 envelope holding June-16 designations). It was a reporting
bug, not a finding. Both are now retained per envelope.

## Open question, NOT a defect — delisted parties still match

All 3 parties removed by this refresh still return `STABLE_DEFINITE`, each with
`valid_to = 2099-12-31` — i.e. served as **active** listings:

| UniqueID | Party | Envelope cut of the served record |
|---|---|---|
| `LIB0001` | Libyan Arab African Investment Company | 2026-06-02 |
| `RUS2682` | LLC "RBRU Specialized depository" | 2026-06-02 |
| `RUS2579` | ZANGAZUR | **2026-07-06** |

`LIB0001` and `RUS2682` are served from envelopes cut **2026-06-02**, when both were
still listed. Retaining them is **correct for that cut**.

`RUS2579` is served from the freshest Russia envelope (**2026-07-06**) yet was removed
by the list generated 07/07/2026. Whether that is a retention bug or simply one
publication of lag depends on **when OFSI actually delisted it** — a date the XML does
not carry (removed records leave no tombstone). This cannot be adjudicated from the
list alone.

**This is deliberately not filed as a finding.** Calling it a defect without the
delisting date would repeat the Finding #9 mistake: treating "absent from today's
source" as "should have been absent from the Add-on's snapshot". Resolve by asking the
Add-on owner for their UK ingestion cadence, or OFSI for the delisting date of
`RUS2579`.

## Caveats

1. **Ships are reported on their own line and excluded from the headline person/entity
   figure.** This is a person/entity matcher; vessel handling is name-recall-only
   (Finding F-4). That all 27 matched is a stronger result than expected, but a ship
   name matching (`IMO 9379301 ("VERSA")`) says nothing about vessel-particular
   handling (IMO number, flag, tonnage).
2. **`stage_used` was `keyword` on 305/485 calls.** The additions are queried with the
   source's exact primary-name string, which short-circuits the pipeline before the
   LLM stage — where Finding #6's non-determinism lives. **The 5/5 stability therefore
   partly reflects easy inputs**, not a resolution of Finding #6. `Putin` still returned
   0 definite codes on one call and 3 on the next during this session. A behavioural
   test with perturbed names would exercise the LLM stage and should be expected to be
   far less stable.
3. **Presence, not precision.** No claim is made about false positives on the wider
   corpus, alias recall (blocked on #7), or the `codes`/`possible_codes` split (#6).
4. **Primary names only.** Aliases were used for identity confirmation, never queried.
5. The identity rule permits token-multiset equality (word-order permutation). In this
   run it was never needed — all 86 were `exact` — so the headline is insensitive to it.

## Reproduce

```bash
python3 harness/fetch_uk_list.py                                                  # refresh
python3 harness/uk_latest.py --against data/UK-Sanctions-List.prev.xml -o data/uk-latest-additions.csv
python3 harness/uk_addon_check.py                                                 # 97 names x 5 = 485 calls, ~3.5 min
```

The controls are not optional. A run whose `control_pos` group is not 6/6, or whose
`control_neg` group shows any identity match, proves nothing about the additions and
must be discarded.
