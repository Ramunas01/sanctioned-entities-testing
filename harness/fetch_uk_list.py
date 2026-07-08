#!/usr/bin/env python3
"""
Refresh the UK Sanctions List snapshot (OFSI/FCDO consolidated designations).

    python3 harness/fetch_uk_list.py

Downloads the current UK-Sanctions-List.xml, validates it, and -- only if it
actually changed -- installs it at data/UK-Sanctions-List.xml, moving the
previous copy aside to data/UK-Sanctions-List.prev.xml so the additions/
removals delta stays computable (see harness/uk_latest.py --against).

Every fetch is recorded in data/uk-snapshot.json: url, fetched_at_utc, sha256,
byte size, the list's own <DateGenerated>, and the designation count. Prior
entries are pushed onto `history`, never overwritten.

  ! THIS IS NOT THE FROZEN ORACLE SNAPSHOT.
    oracle/source/consolidated.csv (US CSL) is frozen: parse_oracle.py aborts on
    a sha256 mismatch, and it must never be re-downloaded mid-project. The UK
    list under data/ is deliberately the opposite -- a refreshable working
    snapshot, not ground truth for any census. Nothing here touches oracle/.

Validation before install (a bad download must never silently replace a good
snapshot): well-formed XML, root <Designations>, a parseable <DateGenerated>,
at least one <Designation>, and every NameType recognised. Unknown NameTypes
are a hard stop, not a warning -- uk_latest.py's alias rule keys off them, so an
upstream vocabulary change would silently corrupt the extract.

stdlib only; no dependencies.
"""

import datetime
import hashlib
import json
import os
import shutil
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET

# --- source ------------------------------------------------------------------
# The XML is served directly by FCDO at a stable path (no per-publication hash
# in the URL, unlike the gov.uk asset links). LANDING_PAGE is the human page
# that documents it.
URL = "https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.xml"
LANDING_PAGE = "https://www.gov.uk/government/publications/the-uk-sanctions-list"

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")
TARGET = os.path.join(DATA, "UK-Sanctions-List.xml")
PREV = os.path.join(DATA, "UK-Sanctions-List.prev.xml")
MANIFEST = os.path.join(DATA, "uk-snapshot.json")

# The complete NameType vocabulary, casefolded. Observed spellings vary in case
# ("Primary name") and one is a typo ("ALias") -- both are upstream, both are
# preserved by casefolding rather than "corrected". An unlisted value aborts.
KNOWN_NAMETYPES = {"primary name", "primary name variation", "alias"}

TIMEOUT = 300
USER_AGENT = "sanctioned-entities-testing/1.0 (+refresh; contact via repo)"


def sha256_of(path):
    """SHA-256, streamed (the file is ~21 MB)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def current_umask():
    """Read the umask without leaving it changed (os.umask only ever swaps)."""
    mask = os.umask(0)
    os.umask(mask)
    return mask


def parse_uk_date(s):
    """UK list dates are DD/MM/YYYY. Returns a date, or None if unparseable."""
    try:
        return datetime.datetime.strptime((s or "").strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        if resp.status != 200:
            sys.exit("ERROR: HTTP %s fetching %s" % (resp.status, url))
        last_modified = resp.headers.get("Last-Modified", "")
        with open(dest, "wb") as f:
            shutil.copyfileobj(resp, f, length=1 << 20)
    return last_modified


def validate(path):
    """Structural gate. Returns (date_generated_raw, designation_count).

    Aborts on anything that would make a downstream extract untrustworthy.
    """
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        sys.exit("ERROR: downloaded file is not well-formed XML: %s" % e)

    if root.tag != "Designations":
        sys.exit("ERROR: unexpected root element <%s>, expected <Designations>" % root.tag)

    date_generated = root.findtext("DateGenerated")
    if not parse_uk_date(date_generated):
        sys.exit("ERROR: missing or unparseable <DateGenerated>: %r" % date_generated)

    designations = [d for d in root if d.tag == "Designation"]
    if not designations:
        sys.exit("ERROR: no <Designation> elements -- refusing to install an empty list")

    seen = {
        (n.findtext("NameType") or "").strip().casefold()
        for d in designations
        for n in d.findall("Names/Name")
    }
    unknown = seen - KNOWN_NAMETYPES
    if unknown:
        sys.exit(
            "ERROR: unknown NameType(s) upstream: %s\n"
            "harness/uk_latest.py derives `aliases` from this vocabulary; a new "
            "value must be classified (name? alias? neither?) before it is\n"
            "silently absorbed. Update KNOWN_NAMETYPES here and the alias rule "
            "in uk_latest.py together." % sorted(unknown)
        )

    return date_generated.strip(), len(designations)


def unique_ids(path):
    """UniqueID set of an existing snapshot, for the delta summary."""
    if not os.path.exists(path):
        return None
    root = ET.parse(path).getroot()
    return {d.findtext("UniqueID") for d in root if d.tag == "Designation"}


def load_manifest():
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            return json.load(f)
    return {
        "source": {
            "list": "UK Sanctions List (OFSI/FCDO consolidated designations)",
            "url": URL,
            "landing_page": LANDING_PAGE,
            "note": "Refreshable working snapshot. NOT the frozen oracle source.",
        },
        "current": None,
        "history": [],
    }


def main():
    os.makedirs(DATA, exist_ok=True)
    manifest = load_manifest()

    # Download to a temp file in DATA (same filesystem -> atomic os.replace).
    fd, tmp = tempfile.mkstemp(dir=DATA, prefix=".uk-fetch-", suffix=".xml")
    os.close(fd)
    try:
        print("fetching %s" % URL)
        last_modified = download(URL, tmp)
        date_generated, count = validate(tmp)
        digest = sha256_of(tmp)
        size = os.path.getsize(tmp)

        current = manifest.get("current") or {}
        if current.get("sha256") == digest:
            print(
                "unchanged: sha256 identical to the installed snapshot\n"
                "  DateGenerated: %s\n  designations:  %d\n"
                "Nothing written." % (date_generated, count)
            )
            return

        old_ids = unique_ids(TARGET)

        # mkstemp creates 0600 and os.replace preserves it, which would leave the
        # snapshot unreadable to every other user. Restore normal file perms
        # (0644 & ~umask) before it becomes the installed file.
        os.chmod(tmp, 0o644 & ~current_umask())

        # Install: previous snapshot moves aside (enables --against), new one lands.
        if os.path.exists(TARGET):
            os.replace(TARGET, PREV)
        os.replace(tmp, TARGET)
        tmp = None  # consumed

        if current:
            manifest["history"].append(current)
        manifest["source"]["url"] = URL
        manifest["source"]["landing_page"] = LANDING_PAGE
        manifest["current"] = {
            "fetched_at_utc": utcnow(),
            "sha256": digest,
            "bytes": size,
            "date_generated": date_generated,
            "designation_count": count,
            "last_modified_header": last_modified,
        }
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")

        print("installed %s" % TARGET)
        print("  DateGenerated: %s" % date_generated)
        print("  designations:  %d" % count)
        print("  sha256:        %s" % digest)
        if old_ids is not None:
            new_ids = unique_ids(TARGET)
            added, removed = new_ids - old_ids, old_ids - new_ids
            print("  previous copy: %s" % PREV)
            print("  delta:         +%d added, -%d removed (by UniqueID)"
                  % (len(added), len(removed)))
            print("\nExtract the additions:\n"
                  "  python3 harness/uk_latest.py --against %s" % os.path.relpath(PREV))
        else:
            print("\nFirst snapshot -- no previous copy to diff against.\n"
                  "Extract the newest designations:\n"
                  "  python3 harness/uk_latest.py --n 50")
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)


if __name__ == "__main__":
    main()
