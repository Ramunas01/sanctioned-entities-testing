# Oracle — US Consolidated Screening List (CSL)

Ground truth for the test harness. `parse_oracle.py` reads the **frozen** source
snapshot and emits `expected.csv` (the table every later check diffs against),
`unparsed.csv` (rows that could not be parsed cleanly), and maintains
`snapshot.json` (the reproducibility manifest).

This is a **pure, deterministic parse**: no fuzzy logic, no matching, no
inference, no guessing. The column *schema* is normalized (29 messy source
columns → 9 documented columns); column *values* are copied **verbatim** so the
oracle can be audited cell-by-cell against the raw CSV by a human/Advisor who is
not the parser's author (oracle/checker separation).

## Source (pinned)

| | |
|---|---|
| List | Consolidated Screening List (CSL) — the single merged US list across OFAC SDN, OFAC non-SDN, BIS Entity List, BIS Denied Persons, State Dept (ISN/DTC), etc. |
| URL | `https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.csv` |
| Frozen at | `oracle/source/consolidated.csv` (gitignored — large; the manifest carries its hash) |
| Downloaded | once; **never** re-fetched per run |
| sha256 | `63b6a9aa7b257879ef0afb4bef8e3dc739040521934c8e7c6302b0cd669e1485` |
| Rows | 25,767 data rows (29 columns) |

This is the file the Add-on ingests (confirmed by the Add-on owner). It is **not**
the OFAC SDN/Consolidated XML — that source is deliberately not used here.

`parse_oracle.py` recomputes the sha256 on every run and **aborts** if it differs
from the value recorded in `snapshot.json` — a guard against the snapshot
silently drifting (e.g. an accidental re-download). It also pins the 29-column
header, so an upstream schema change is caught rather than absorbed.

## How to run

```bash
python3 oracle/parse_oracle.py          # stdlib only; no dependencies
```

To re-create the frozen source from scratch (only if it is lost — this changes
nothing if upstream is unchanged, and changes the hash if upstream moved):

```bash
curl -sSL -o oracle/source/consolidated.csv \
  "https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.csv"
```

## `expected.csv` — columns

One row per **listed party**, in **source order** (no sorting, no de-duplication).
All four party kinds are retained (Individual / Entity / Vessel / Aircraft, plus
rows with a blank type) — the oracle mirrors the whole list faithfully; deciding
which rows the census actually queries is the harness's job, not the oracle's.

| # | Column | Source column | Rule |
|---|--------|---------------|------|
| 1 | `primary_name`   | `name`      | Verbatim. Every row has one (0 blanks observed). |
| 2 | `aliases`        | `alt_names` | Verbatim. The CSL joins multiple aliases with `"; "` (semicolon-space). Empty when the source has none. No de-duplication, case-folding, or reordering. |
| 3 | `strong_alias`   | *(derived)* | **`unknown`** when the row has ≥1 alias; **empty** when it has none. See **D1** below. |
| 4 | `entity_type`    | `type`      | Verbatim: `Individual`, `Entity`, `Vessel`, `Aircraft`, or **empty**. Empty is a genuine source value (BIS sub-lists omit type); it is preserved, never inferred. |
| 5 | `programs`       | `programs`  | Verbatim. The CSL joins multiple program codes with `"; "`. Empty when the source has none. |
| 6 | `start_date`     | `start_date`| Verbatim — **not** reparsed or reformatted. Mostly ISO `YYYY-MM-DD`; mostly empty. See the date anomaly below. |
| 7 | `end_date`       | `end_date`  | Verbatim — listing expiry (e.g. a BIS denial-order term). Empty = no expiry. **Added 2026-06-15** (the Finding #9 correction — see below). |
| 8 | `active`         | *(derived)* | `yes` if the listing is active as of `SNAPSHOT_DATE` (empty `end_date`, or `end_date` ≥ snapshot), `no` if expired, `unknown` if the date can't be parsed. The one downstream-applied validity rule. |
| 9 | `source_sublist` | `source`    | Verbatim. The CSL sub-list label (one of the 12 below). |

### Normalization rules applied (the complete list)

Everything the parser does to a value is here — nothing is hidden:

1. **Schema only.** 29 source columns → the 7 above. The dropped columns
   (addresses, titles, IDs, vessel particulars, remarks, URLs, citizenships,
   DOB/POB, etc.) are intentionally out of scope for this oracle.
2. **Verbatim values.** No whitespace trimming, no case-folding, no unicode
   normalization, no date reformatting, no list re-encoding. The multi-value
   fields (`aliases`, `programs`) keep the source's own `"; "` delimiter; a
   downstream consumer that needs the individual items splits on `"; "`.
3. **`strong_alias` derivation (the only computed column).** `"unknown"` if
   `alt_names` is non-empty, else `""`. This is the **D1** placeholder, not a
   judgement about alias strength.
4. **File encoding.** Read as `utf-8-sig` (tolerates a UTF-8 BOM; none present).
   This touches the byte stream, not cell contents.

### Source sub-lists present (column 7)

| Rows | Sub-list |
|-----:|----------|
| 19,066 | Specially Designated Nationals (SDN) — Treasury Department |
| 3,420 | Entity List (EL) — Bureau of Industry and Security |
| 1,596 | Denied Persons List (DPL) — Bureau of Industry and Security |
| 787 | ITAR Debarred (DTC) — State Department |
| 286 | Sectoral Sanctions Identifications List (SSI) — Treasury Department |
| 222 | Unverified List (UVL) — Bureau of Industry and Security |
| 161 | Nonproliferation Sanctions (ISN) — State Department |
| 78 | Palestinian Legislative Council List (PLC) — Treasury Department |
| 70 | Military End User (MEU) List — Bureau of Industry and Security |
| 68 | Non-SDN Chinese Military-Industrial Complex Companies List (CMIC) — Treasury Department |
| 12 | Non-SDN Menu-Based Sanctions List (NS-MBS List) — Treasury Department |
| 1 | Capta List (CAP) — Treasury Department |

### `end_date` / `active` — the Finding #9 correction (2026-06-15)

The original oracle dropped the source `end_date`. The DPL census then expected **expired**
denial orders to match and scored their (correct) exclusion by the Add-on as 280 "misses" —
the basis of a withdrawn Sev-1 finding. The Add-on applies an **active-only date filter**
(correct for a blocking screen): with `end_date`/`active` applied, **active-DPL recall is
100%**. The parser now emits `end_date` (verbatim) and a derived `active` flag against
`SNAPSHOT_DATE = 2026-06-11`. Downstream presence checks should treat only `active = yes`
records as expected hits. See the report's retraction notice and §7.

### Known data anomaly (preserved, not "fixed")

Exactly **one** row carries a non-ISO `start_date`:

```
FRANCISCO JAVIER MENDOZA-ESQUIVEL  (Denied Persons List)  start_date = " 8/11/2015"
```

It is a leading-space, `M/D/YYYY`-or-`D/M/YYYY`-ambiguous value. Per the verbatim
rule it is kept **exactly as the source wrote it** (leading space included) and
the row stays in `expected.csv` — it is a legitimately listed party, and dropping
it would manufacture a false census miss in Issue #3. We do **not** guess the
month/day order. Flagged here so the reviewer/Advisor sees it; if a canonical
date is required, that is a downstream decision, not a silent oracle edit.

## `unparsed.csv` — rows that could not be parsed cleanly

Columns = the 29 source columns + a trailing `reason`. **Currently empty**
(header only): every source row parsed cleanly. A row is routed here, never
guessed, only when it is:

- **structurally broken** — more or fewer than 29 columns; or
- **unidentifiable** — a blank primary `name` (0 observed; guard retained).

An odd-but-present *value* (e.g. the date above) is **not** grounds for unparsing
— that would drop a real party. Unparsing is reserved for rows we genuinely
cannot map.

## Blocked on Advisor — parsed around, not resolved

- **TODO(D1) — alias strength.** The CSL `alt_names` field has no strong/weak
  quality flag (unlike the OFAC SDN XML). `strong_alias` is therefore `unknown`
  for every aliased row. The Advisor will rule whether to drop the strong/weak
  distinction or enrich it from a secondary OFAC SDN source. Until then, no
  alias is treated as strong or weak here.
- **TODO(D2) — hit definition.** This oracle implements **no** hit / match /
  threshold logic. Defining what counts as a HIT (and how `output.codes` vs
  `output.possible_codes` factor in) is the harness's job in Issue #3.

## Reproducibility

- Same frozen input → **byte-identical** `expected.csv` / `unparsed.csv` every
  run (source order, no clock/random/network input).
- `snapshot.json` records `downloaded_at_utc`, `sha256`, and `row_count`. Hashes
  are computed by the parser, never hand-edited; `downloaded_at_utc` is set once
  from the frozen file and then preserved.
