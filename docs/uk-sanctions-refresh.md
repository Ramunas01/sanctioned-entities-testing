# UK Sanctions List — refresh & latest-additions extract

How to pull a current UK Sanctions List snapshot and extract what changed.
Previously undocumented: the UK XML in `data/` had been copied by hand from a
Windows folder and the 50-row sample hand-edited in `vi`, with no script, no URL,
and no manifest. This replaces that.

> **This is not the oracle.** `oracle/source/consolidated.csv` (US CSL) is a
> **frozen** snapshot: `parse_oracle.py` recomputes its sha256 and aborts on any
> mismatch, and it must never be re-downloaded mid-project. The UK list under
> `data/` is the opposite — a **refreshable working snapshot**. Nothing in this
> document touches `oracle/`. No census or ground-truth claim currently depends
> on the UK list.

## Source

| | |
|---|---|
| List | UK Sanctions List — OFSI/FCDO consolidated designations |
| XML | `https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.xml` |
| Landing page | `https://www.gov.uk/government/publications/the-uk-sanctions-list` |
| Snapshot | `data/UK-Sanctions-List.xml` (gitignored — ~21 MB; the manifest carries its hash) |
| Previous snapshot | `data/UK-Sanctions-List.prev.xml` (kept so the delta stays computable) |
| Manifest | `data/uk-snapshot.json` (url, `fetched_at_utc`, sha256, bytes, `DateGenerated`, count, + `history`) |

The FCDO path is stable — unlike the `assets.publishing.service.gov.uk` asset
links, it carries no per-publication hash, so it can be pinned in a script.

## Refresh

```bash
python3 harness/fetch_uk_list.py      # stdlib only; no dependencies
```

Downloads, **validates, then installs** — a bad download never replaces a good
snapshot. The gate: well-formed XML, root `<Designations>`, parseable
`<DateGenerated>`, ≥1 `<Designation>`, and every `NameType` recognised. Install
is atomic (`os.replace`), the prior snapshot moves to `.prev.xml`, and the fetch
is appended to the manifest.

If the sha256 matches what is already installed, the script prints `unchanged`
and writes **nothing** — it will not clobber `.prev.xml` and destroy your delta.
Re-running it is safe.

An unrecognised `NameType` is a **hard stop**, not a warning: the alias rule
below keys off that vocabulary, so a silent upstream change would corrupt every
extract. Update `KNOWN_NAMETYPES` in `fetch_uk_list.py` and the alias rule in
`uk_latest.py` together, or not at all.

## Extract the latest additions

```bash
# What was ADDED since the previous snapshot — the honest answer for a refresh.
python3 harness/uk_latest.py --against data/UK-Sanctions-List.prev.xml -o data/uk-latest-additions.csv

# What was most recently DESIGNATED — a different question (see below).
python3 harness/uk_latest.py --n 50
python3 harness/uk_latest.py --since 2026-06-01
```

Output is the same 8 columns as the old `data/uk-sanctions-sample-50.csv`:

```
unique_id,type,primary_name,aliases,alias_count,date_designated_inclusion,last_updated,regime
```

Deterministic: same snapshot → byte-identical CSV (sorted `DateDesignated`
descending, `UniqueID` ascending to break ties).

## Three traps this list sets

**1. "Latest 50" is not "the 50 added."** These are different sets, and the gap
is not theoretical. Refreshing 02/06/2026 → 07/07/2026 added **86** records, but
the newest 79 *by designation date* omit `GHR0191`–`GHR0197` — seven Global
Human Rights designations dated 09/06/2026 that were published *after* 79
later-dated records. A `--n 50` query misses them silently. Use `--against` for
a refresh; use `--n`/`--since` only when you genuinely mean "recently designated."

Only `--against` can report **removals** (delistings). The 07/07/2026 refresh
removed 3: `LIB0001`, `RUS2579`, `RUS2682`. No newest-N query can ever see those.

**2. Sort by `DateDesignated`, never `LastUpdated`.** Both exist on every record.
`LastUpdated` floats *amended* records to the top — a 2012 designation edited
last week outranks a designation made yesterday. Those are not additions.
This is the same class of error as the retracted Finding #9: reading a date field
as something it is not. (See `oracle/README.md` § the Finding #9 correction.)

**3. Same-day batches.** Designations land in same-date batches — 70 records on
16/06/2026 alone. A bare `--n 50` would keep 41 of them and drop 29 that are
indistinguishable from the ones kept. `--n` therefore **expands to the whole
batch** straddling the cut and reports it on stderr:

```
batch boundary: 29 more record(s) share the cutoff date 16/06/2026;
expanded 50 -> 79 so the batch is not split. Use --exact-n for exactly 50.
```

Pass `--exact-n` to force precisely N and accept the arbitrary split.

## Derived columns (everything else is verbatim)

Only two fields are computed. Both were reverse-engineered from the hand-made
`uk-sanctions-sample-50.csv` and reproduce all 50 of its rows **exactly**.

**`primary_name`** — the first *non-empty* `<Name*>` group whose `NameType`
casefolds to `primary name`. Individuals split the name across `Name1..Name6`
(forename … surname); entities put the whole name in `Name6`. Parts are joined in
**numeric** tag order (lexicographic would sort `Name10` before `Name2`). Five
records carry more than one primary name; two of those (`BEL0174`, `IRN0249`)
have a primary name whose parts are *all empty* — hence "first non-empty".

**`aliases`** — `"; "`-joined (the delimiter this repo already uses for the CSL's
multi-value fields), drawn from `NameType ∈ {alias, primary name variation}` plus
any primary names after the first. Entries equal to `primary_name` are dropped
and duplicates removed, preserving source order.

Both name types are folded together because the source uses them
interchangeably: `RUS3069`'s four "aliases" are all typed `Primary Name
Variation`, while `CAF0016`'s five are typed `Alias` — one of which repeats the
primary name verbatim (hence `alias_count = 4`, not 5).

**`NameType` is matched casefolded.** Upstream spelling is inconsistent
(`Primary Name`, `Primary name`, `Primary Name Variation`, `Primary name
variation`) and one value is a typo (`ALias`, 1 occurrence). Casefolding *reads*
the source; it does not rewrite it.

## Loose thread — `<AliasStrength>` (relevant to D1)

The UK XML carries an **`AliasStrength`** element on `<Name>`. The US CSL's flat
`alt_names` field has no such flag, which is exactly why `oracle/README.md`
records `strong_alias = unknown` for every aliased row and why **D1** is parked
on the Advisor ("drop the strong/weak distinction, or enrich from a secondary
source?").

`uk_latest.py` does **not** emit `AliasStrength` — the UK list is not the
Add-on's ingestion source for the US track, so importing it here would be
inventing ground truth. Flagged only because it is a live input to D1 if the
UK list ever becomes an oracle in its own right. Not a decision this script makes.

## Snapshot as of this writing

| | |
|---|---|
| `DateGenerated` | 07/07/2026 |
| Designations | 6,271 |
| sha256 | `09294883bee0e472558722211704b14f8380ea439f0b9232c5cef8b6fdbd646c` |
| Δ vs 02/06/2026 | **+86 added, −3 removed** |
| Added, by designation date | 06/07/2026 (9) · 16/06/2026 (70) · 09/06/2026 (7) |
| Added, by regime | Russia 70 · Chemical Weapons 9 · Global Human Rights 7 |
