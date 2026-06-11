#!/usr/bin/env python3
"""
Issue #2 -- Oracle parser for the US Consolidated Screening List (CSL).

Deterministic, pure parse. Reads the FROZEN source snapshot
(oracle/source/consolidated.csv -- downloaded once, never re-fetched per run)
and emits the ground-truth table the rest of the test harness diffs against:

    oracle/expected.csv   one row per listed party, 7 normalized columns
    oracle/unparsed.csv   any row that cannot be parsed cleanly, + a reason
    oracle/snapshot.json   reproducibility manifest (sha256, row_count, time)

Design rules (non-negotiable -- see oracle/README.md for the full spec):

  * PURE PARSE. No fuzzy logic, no matching, no inference, no guessing.
  * The column SCHEMA is normalized (29 messy source columns -> 7 documented
    columns). Column VALUES are copied VERBATIM from the source: no
    case-folding, no whitespace trimming, no date reformatting, no alias
    de-duplication or reordering, no unicode normalization. "No hidden
    normalization" -- every transformation lives in this file and the README.
  * DETERMINISTIC. Rows are emitted in source order; no sorting, no dedup.
    Same frozen input -> byte-identical outputs on every run.
  * AUDITABLE. The oracle author is not its sole validator (oracle/checker
    separation): a human/Advisor reviews expected.csv against the raw CSV, so
    the mapping below is explicit and commented.

Blocked on Advisor ruling -- DO NOT resolve here, parse around:

  TODO(D1): The CSL `alt_names` field is a flat list with no strong/weak alias
            quality flag (unlike the OFAC SDN XML). We therefore emit
            strong_alias = "unknown" for every row that has at least one alias.
            The strong/weak distinction the equivalence design assumed is not
            derivable from this source alone; the Advisor will rule whether to
            drop it or enrich from a secondary OFAC SDN source.

  TODO(D2): No hit / match / threshold definition is implemented in this oracle.
            Defining what counts as a HIT is the harness's job in Issue #3.
"""

import csv
import datetime
import hashlib
import json
import os
import sys

# --- paths (resolved relative to this file so the script runs from anywhere) --
HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_CSV = os.path.join(HERE, "source", "consolidated.csv")
EXPECTED_CSV = os.path.join(HERE, "expected.csv")
UNPARSED_CSV = os.path.join(HERE, "unparsed.csv")
SNAPSHOT_JSON = os.path.join(HERE, "snapshot.json")

# --- the 29 columns the CSL source is documented/observed to carry -----------
# Used to detect structurally broken rows (wrong field count). If the upstream
# schema ever changes, this list is the single place that must be updated.
SOURCE_FIELDNAMES = [
    "_id", "source", "entity_number", "type", "programs", "name", "title",
    "addresses", "federal_register_notice", "start_date", "end_date",
    "standard_order", "license_requirement", "license_policy", "call_sign",
    "vessel_type", "gross_tonnage", "gross_registered_tonnage", "vessel_flag",
    "vessel_owner", "remarks", "source_list_url", "alt_names", "citizenships",
    "dates_of_birth", "nationalities", "places_of_birth",
    "source_information_url", "ids",
]

# --- the 7 normalized output columns -----------------------------------------
# (output column  <-  source column)        verbatim copy unless noted
#  primary_name   <-  name
#  aliases        <-  alt_names             CSL joins aliases with "; "
#  strong_alias   <-  (derived)             "unknown" if aliases else ""  [D1]
#  entity_type    <-  type                  "" preserved (BIS lists omit it)
#  programs       <-  programs              CSL joins programs with "; "
#  start_date     <-  start_date            "" preserved; verbatim, not reparsed
#  source_sublist <-  source                the CSL sub-list label
EXPECTED_HEADER = [
    "primary_name", "aliases", "strong_alias", "entity_type",
    "programs", "start_date", "source_sublist",
]

# Sentinels used to spot rows whose field count != len(SOURCE_FIELDNAMES).
_EXTRA = "__EXTRA_FIELDS__"
_MISSING = "__MISSING_FIELD__"


def sha256_of(path):
    """SHA-256 of the source file, streamed (the file is ~16 MB)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_row(row):
    """
    Map one source row to (expected_row, unparsed_reason).

    Returns (list, None)  -> goes to expected.csv
            (None, str)   -> goes to unparsed.csv with that reason

    A row is "unparseable" ONLY when it is structurally broken or unidentifiable
    -- never because a value looks odd. Odd-but-present values are preserved
    verbatim and flagged in the README, not dropped (dropping a listed party
    would manufacture a false census miss downstream).
    """
    # 1. Structural integrity: csv.DictReader puts surplus cells under the
    #    _EXTRA restkey and short rows get _MISSING for absent columns.
    if _EXTRA in row:
        return None, "extra fields: row has more columns than the 29-column CSL schema"
    if any(v == _MISSING for v in row.values()):
        return None, "missing fields: row has fewer columns than the 29-column CSL schema"

    # 2. Identity: every listed party must have a primary name to be queryable.
    #    (Observed 0 such rows in the snapshot; this is a guard, not a guess.)
    if not row["name"].strip():
        return None, "empty primary name: source `name` field is blank"

    aliases = row["alt_names"]
    # [D1] strong_alias is unknown for aliased rows; blank when there are no
    # aliases (the flag describes aliases -- "unknown" on a row with none would
    # be misleading, so we leave it empty rather than invent a value).
    strong_alias = "unknown" if aliases.strip() else ""

    expected_row = [
        row["name"],        # primary_name   -- verbatim
        aliases,            # aliases        -- verbatim ("; "-joined by source)
        strong_alias,       # strong_alias   -- "unknown" | ""  [D1]
        row["type"],        # entity_type    -- verbatim ("" preserved)
        row["programs"],    # programs       -- verbatim ("; "-joined by source)
        row["start_date"],  # start_date     -- verbatim, NOT reparsed
        row["source"],      # source_sublist -- verbatim
    ]
    return expected_row, None


def main():
    if not os.path.exists(SOURCE_CSV):
        sys.exit(
            "ERROR: frozen source not found at %s\n"
            "Download it ONCE (see oracle/README.md); it must never be "
            "re-downloaded per run." % SOURCE_CSV
        )

    # --- reproducibility guard: the frozen file must not change between runs --
    digest = sha256_of(SOURCE_CSV)
    snapshot = {}
    if os.path.exists(SNAPSHOT_JSON):
        with open(SNAPSHOT_JSON, encoding="utf-8") as f:
            snapshot = json.load(f)
    src_entry = snapshot["sources"][0]
    if src_entry.get("sha256") and src_entry["sha256"] != digest:
        sys.exit(
            "ERROR: source sha256 changed since it was frozen.\n"
            "  recorded: %s\n  current:  %s\n"
            "The snapshot must be immutable -- do not re-download mid-project."
            % (src_entry["sha256"], digest)
        )

    # --- parse -----------------------------------------------------------------
    # utf-8-sig tolerates a UTF-8 BOM (none observed, harmless if absent).
    # newline="" lets the csv module handle embedded newlines/quotes itself.
    expected_rows = []
    unparsed_rows = []
    data_row_count = 0
    with open(SOURCE_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, restkey=_EXTRA, restval=_MISSING)
        # Pin the schema so a silent upstream column change is caught, not absorbed.
        if reader.fieldnames != SOURCE_FIELDNAMES:
            sys.exit(
                "ERROR: source header does not match the pinned 29-column CSL schema.\n"
                "  expected: %s\n  got:      %s" % (SOURCE_FIELDNAMES, reader.fieldnames)
            )
        for row in reader:
            data_row_count += 1
            expected_row, reason = parse_row(row)
            if reason is None:
                expected_rows.append(expected_row)
            else:
                # Preserve the full original row (in schema order) + the reason,
                # so unparsed.csv is self-contained and auditable on its own.
                original = [row.get(name, "") for name in SOURCE_FIELDNAMES]
                unparsed_rows.append(original + [reason])

    # --- write expected.csv (source order, deterministic) ----------------------
    with open(EXPECTED_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(EXPECTED_HEADER)
        w.writerows(expected_rows)

    # --- write unparsed.csv (header always present; may be empty) --------------
    with open(UNPARSED_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(SOURCE_FIELDNAMES + ["reason"])
        w.writerows(unparsed_rows)

    # --- maintain snapshot.json (hashes computed, never hand-edited) -----------
    # downloaded_at_utc is set ONCE from the frozen file's mtime and then
    # preserved -- snapshot discipline: once frozen it never changes.
    if not src_entry.get("downloaded_at_utc"):
        mtime = os.path.getmtime(SOURCE_CSV)
        src_entry["downloaded_at_utc"] = (
            datetime.datetime.fromtimestamp(mtime, datetime.timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        )
    src_entry["sha256"] = digest
    src_entry["row_count"] = data_row_count
    with open(SNAPSHOT_JSON, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
        f.write("\n")

    print("source rows:      %d" % data_row_count)
    print("expected.csv:     %d rows" % len(expected_rows))
    print("unparsed.csv:     %d rows" % len(unparsed_rows))
    print("snapshot sha256:  %s" % digest)


if __name__ == "__main__":
    main()
