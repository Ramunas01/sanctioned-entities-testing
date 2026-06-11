#!/usr/bin/env python3
"""Emit a deterministic stratified review sample for independent oracle audit.

Pairs each sampled expected.csv row with its raw source row (same index — the
oracle preserves source order, no dedup) so a reviewer who did NOT author the
parser can audit it cell-by-cell against the raw CSL (oracle/checker separation).

Deterministic: fixed strata, fixed in-stratum index rule, no random/clock input.
Run: python3 oracle/sample_for_review.py  -> docs/oracle-review-sample.md
"""
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = ROOT / "oracle" / "expected.csv"
SOURCE = ROOT / "oracle" / "source" / "consolidated.csv"
OUT = ROOT / "docs" / "oracle-review-sample.md"

csv.field_size_limit(10 * 1024 * 1024)

# expected col -> source col it was copied from (strong_alias is derived)
COL_MAP = {
    "primary_name": "name", "aliases": "alt_names", "entity_type": "type",
    "programs": "programs", "start_date": "start_date", "source_sublist": "source",
}

def load(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def main():
    exp = load(EXPECTED)
    src = load(SOURCE)
    if len(exp) != len(src):
        sys.exit(f"ABORT: row-count mismatch exp={len(exp)} src={len(src)} (pairing by index invalid)")

    picks = []  # (reason, index)
    seen = set()
    def add(reason, i):
        if 0 <= i < len(exp) and i not in seen:
            picks.append((reason, i)); seen.add(i)

    # 1) Every sub-list: first + a spaced interior + last occurrence.
    sublists = {}
    for i, r in enumerate(exp):
        sublists.setdefault(r["source_sublist"], []).append(i)
    for name in sorted(sublists):
        idxs = sublists[name]
        for i in (idxs[0], idxs[len(idxs)//2], idxs[-1]):
            add(f"sublist:{name.split('(')[-1].split(')')[0].strip() or name[:24]}", i)

    # 2) Every entity_type (incl. blank).
    types = {}
    for i, r in enumerate(exp):
        types.setdefault(r["entity_type"], i)
    for t, i in types.items():
        add(f"entity_type:{t or 'BLANK'}", i)

    # 3) Aliased vs non-aliased, and a multi-alias row.
    for i, r in enumerate(exp):
        if r["aliases"]:
            add("has-aliases", i); break
    for i, r in enumerate(exp):
        if not r["aliases"]:
            add("no-aliases", i); break
    for i, r in enumerate(exp):
        if r["aliases"].count("; ") >= 3:
            add("multi-alias(>=4)", i); break

    # 4) Multi-program parties — the 29->7 collapse is exactly where program
    #    codes could silently vanish (Advisor review check #2). Pick a few with
    #    the most program codes so the verbatim copy is auditable.
    multi = sorted((i for i, r in enumerate(exp) if r["programs"].count("; ") >= 1),
                   key=lambda i: exp[i]["programs"].count("; "), reverse=True)
    for i in multi[:4]:
        add(f"MULTI-PROGRAM({exp[i]['programs'].count('; ')+1} codes)", i)

    # 5) The one known date anomaly (must survive verbatim, leading space).
    for i, r in enumerate(exp):
        if "MENDOZA-ESQUIVEL" in r["primary_name"].upper():
            add("DATE-ANOMALY", i); break

    picks.sort(key=lambda p: p[1])

    lines = [
        "# Oracle PR #5 — Independent Review Sample",
        "",
        f"Deterministic stratified sample of **{len(picks)}** rows from "
        f"`oracle/expected.csv` ({len(exp):,} rows), each paired with its raw "
        "source row for cell-by-cell audit. Index = data-row position; the oracle "
        "preserves source order with no dedup, so expected[i] <-> source[i].",
        "",
        "For each row: confirm the 6 verbatim columns equal the named raw source "
        "column, and that `strong_alias` = `unknown` iff aliases is non-empty "
        "(D1 placeholder).",
        "",
    ]
    for reason, i in picks:
        e, s = exp[i], src[i]
        lines.append(f"## row {i}  —  _{reason}_")
        lines.append("")
        lines.append("| expected column | oracle value | raw source col | raw source value |")
        lines.append("|---|---|---|---|")
        def cell(v):
            v = (v or "").replace("|", "\\|").replace("\n", " ")
            return v if len(v) <= 160 else v[:157] + "..."
        for ec in ["primary_name", "aliases", "strong_alias", "entity_type", "programs", "start_date", "source_sublist"]:
            sc = COL_MAP.get(ec, "(derived)")
            sv = s.get(sc, "") if sc != "(derived)" else "—"
            lines.append(f"| `{ec}` | {cell(e[ec])} | `{sc}` | {cell(sv)} |")
        lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} — {len(picks)} rows.")

if __name__ == "__main__":
    main()
