#!/usr/bin/env python3
"""
Extract the latest additions to the UK Sanctions List snapshot.

    python3 harness/uk_latest.py --against data/UK-Sanctions-List.prev.xml   # true delta
    python3 harness/uk_latest.py --n 50                                      # newest by date
    python3 harness/uk_latest.py --since 2026-06-01

Emits the same 8-column CSV shape as the existing data/uk-sanctions-sample-50.csv:

    unique_id,type,primary_name,aliases,alias_count,date_designated_inclusion,last_updated,regime

Two different questions, two different flags -- do not conflate them:

  --against OLD.xml   Records present now and absent from OLD, by UniqueID. This
                      is "what was ADDED since that snapshot" and is the honest
                      answer for a refresh. Also reports removals (delistings) to
                      stderr, which a "newest N" query can never surface.

  --n N / --since D   Records by <DateDesignated>, newest first. This is "what was
                      most recently DESIGNATED", which is NOT the same set: a
                      record can be added to the published list days after its
                      designation date, and an amended old record keeps its old
                      DateDesignated.

  Sort key is DateDesignated, NOT LastUpdated. LastUpdated floats *amended*
  records (a 2012 designation edited last week) to the top; those are not
  additions. Getting this backwards is the same class of error as the retracted
  Finding #9 -- reading a date field as something it isn't.

BATCH BOUNDARIES. Designations arrive in same-day batches (e.g. 70 records dated
2026-06-16). A bare `--n 50` would cut such a batch in half, keeping 41 records
and silently dropping 29 that are indistinguishable from them. By default --n
therefore EXPANDS to the whole batch that straddles the cut and says so on
stderr. Pass --exact-n to force precisely N rows and accept the arbitrary split.

DERIVED COLUMNS. Only two fields are computed; everything else is verbatim.

  primary_name  The first non-empty <Name*> group whose NameType casefolds to
                "primary name". Individuals split the name across Name1..Name6
                (forename..surname); entities put the whole name in Name6. Parts
                are joined in numeric tag order with single spaces. Two records
                (BEL0174, IRN0249) carry a primary name whose parts are all
                empty -- hence "first NON-EMPTY", not "first".

  aliases       "; "-joined (the delimiter this repo already uses for the CSL's
                multi-value fields), built from NameType in {alias, primary name
                variation} plus any primary names after the first. Excludes
                entries equal to primary_name (the source frequently repeats it
                as its own alias) and de-duplicates, preserving source order.

                Both types are folded in because the source treats them as the
                same thing downstream: RUS3069's four "aliases" are all typed
                `Primary Name Variation`, while CAF0016's are typed `Alias`.

  NameType is matched CASEFOLDED. Upstream spellings are inconsistent
  ("Primary name") and one is a typo ("ALias", 1 occurrence). Casefolding reads
  them; it does not rewrite the source.

  <AliasStrength> exists on this list but is NOT emitted -- see the note in
  docs/uk-sanctions-refresh.md. It is the strong/weak flag the US CSL lacks (D1).

stdlib only; no dependencies.
"""

import argparse
import csv
import datetime
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
DEFAULT_XML = os.path.join(DATA, "UK-Sanctions-List.xml")

HEADER = [
    "unique_id", "type", "primary_name", "aliases", "alias_count",
    "date_designated_inclusion", "last_updated", "regime",
]

ALIAS_TYPES = {"alias", "primary name variation"}
PRIMARY_TYPE = "primary name"
_NAME_PART = re.compile(r"Name(\d+)$")


def parse_uk_date(s):
    """UK list dates are DD/MM/YYYY. Returns a date, or None if unparseable."""
    try:
        return datetime.datetime.strptime((s or "").strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def name_text(name_el):
    """Join Name1..Name6 in NUMERIC tag order (lexicographic would sort Name10
    before Name2). Empty parts are skipped; result may be ''."""
    parts = []
    for child in name_el:
        m = _NAME_PART.match(child.tag)
        if m:
            text = (child.text or "").strip()
            if text:
                parts.append((int(m.group(1)), text))
    return " ".join(text for _, text in sorted(parts))


def split_names(designation):
    """-> (primary_name, [aliases]) applying the rules in the module docstring."""
    primaries, aliases = [], []
    for name_el in designation.findall("Names/Name"):
        kind = (name_el.findtext("NameType") or "").strip().casefold()
        text = name_text(name_el)
        if not text:
            continue
        if kind == PRIMARY_TYPE:
            primaries.append(text)
        elif kind in ALIAS_TYPES:
            aliases.append(text)

    primary = primaries[0] if primaries else ""
    # Surplus primary names are real names for this party; keep them as aliases
    # rather than discard them. Order: extra primaries first, then the rest.
    candidates = primaries[1:] + aliases

    deduped, seen = [], {primary}
    for alias in candidates:
        if alias not in seen:
            seen.add(alias)
            deduped.append(alias)
    return primary, deduped


def to_row(designation):
    primary, aliases = split_names(designation)
    return [
        designation.findtext("UniqueID") or "",
        designation.findtext("IndividualEntityShip") or "",
        primary,
        "; ".join(aliases),
        str(len(aliases)),
        (designation.findtext("DateDesignated") or "").strip(),
        (designation.findtext("LastUpdated") or "").strip(),
        designation.findtext("RegimeName") or "",
    ]


def load(path):
    if not os.path.exists(path):
        sys.exit("ERROR: no snapshot at %s\nRun: python3 harness/fetch_uk_list.py" % path)
    root = ET.parse(path).getroot()
    return [d for d in root if d.tag == "Designation"], root.findtext("DateGenerated")


def sort_key(designation):
    """Newest DateDesignated first; UniqueID ascending breaks ties so the output
    is deterministic (same snapshot -> byte-identical CSV)."""
    designated = parse_uk_date(designation.findtext("DateDesignated"))
    return (designated or datetime.date.min, designation.findtext("UniqueID") or "")


def select_newest(designations, n, exact):
    """Newest n by DateDesignated, expanded to a whole same-date batch unless
    `exact`. Returns (selected, note_or_None)."""
    ordered = sorted(designations, key=sort_key, reverse=True)
    if n >= len(ordered):
        return ordered, None
    if exact:
        return ordered[:n], None

    cutoff = parse_uk_date(ordered[n - 1].findtext("DateDesignated"))
    selected = ordered[:n]
    extra = [d for d in ordered[n:] if parse_uk_date(d.findtext("DateDesignated")) == cutoff]
    if not extra:
        return selected, None
    selected += extra
    note = (
        "batch boundary: %d more record(s) share the cutoff date %s; expanded "
        "%d -> %d so the batch is not split. Use --exact-n for exactly %d."
        % (len(extra), cutoff.strftime("%d/%m/%Y"), n, len(selected), n)
    )
    return selected, note


def main():
    ap = argparse.ArgumentParser(
        description="Extract the latest additions to the UK Sanctions List.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--xml", default=DEFAULT_XML, help="snapshot to read (default: %(default)s)")
    ap.add_argument("--against", metavar="OLD_XML",
                    help="emit records added since OLD_XML (true delta, by UniqueID)")
    ap.add_argument("--n", type=int, default=50,
                    help="newest N by DateDesignated (default: %(default)s)")
    ap.add_argument("--exact-n", action="store_true",
                    help="with --n, allow splitting a same-date batch to return exactly N")
    ap.add_argument("--since", metavar="YYYY-MM-DD",
                    help="all records with DateDesignated on/after this date")
    ap.add_argument("-o", "--out", help="write CSV here (default: stdout)")
    args = ap.parse_args()

    designations, date_generated = load(args.xml)
    note = None

    if args.against:
        old, old_generated = load(args.against)
        old_ids = {d.findtext("UniqueID") for d in old}
        new_ids = {d.findtext("UniqueID") for d in designations}
        selected = sorted((d for d in designations if d.findtext("UniqueID") not in old_ids),
                          key=sort_key, reverse=True)

        removed = old_ids - new_ids
        print("comparing %s (DateGenerated %s) against %s (DateGenerated %s)"
              % (args.xml, date_generated, args.against, old_generated), file=sys.stderr)
        print("added: %d" % len(selected), file=sys.stderr)
        print("removed (delisted): %d" % len(removed), file=sys.stderr)
        for d in sorted(old, key=lambda d: d.findtext("UniqueID") or ""):
            if d.findtext("UniqueID") in removed:
                print("  - %-10s %s" % (d.findtext("UniqueID"), split_names(d)[0]), file=sys.stderr)

    elif args.since:
        try:
            since = datetime.datetime.strptime(args.since, "%Y-%m-%d").date()
        except ValueError:
            sys.exit("ERROR: --since must be YYYY-MM-DD, got %r" % args.since)
        selected = sorted(
            (d for d in designations
             if (parse_uk_date(d.findtext("DateDesignated")) or datetime.date.min) >= since),
            key=sort_key, reverse=True)
        print("designated on/after %s: %d record(s)" % (since, len(selected)), file=sys.stderr)

    else:
        selected, note = select_newest(designations, args.n, args.exact_n)
        if note:
            print(note, file=sys.stderr)

    if not selected:
        print("no records matched -- writing header only", file=sys.stderr)

    out = open(args.out, "w", newline="", encoding="utf-8") if args.out else sys.stdout
    try:
        writer = csv.writer(out)
        writer.writerow(HEADER)
        writer.writerows(to_row(d) for d in selected)
    finally:
        if args.out:
            out.close()
            print("wrote %d record(s) -> %s" % (len(selected), args.out), file=sys.stderr)


if __name__ == "__main__":
    main()
