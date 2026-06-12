#!/usr/bin/env python3
"""Output-provenance audit (Advisor task A2).

Capture the FULL per-code `output` payload (ALL fields) for confirmed hits so we
can enumerate every field and judge whether any carries record SOURCE
(CSL vs OFAC) or a legal-authority / legislation reference.

Why fresh calls: the existing captures (census = code-ID lists only; identity
probe = slimmed to title/type/issuer/source) lack the full field set
(information, valid_*, envelope_*, meta). Spec-authorized small batch (<=15
calls). Serial, ~2s apart. stdlib urllib only.

Queries: 1 DPL definite hit + ~10 OFAC (SDN/SSI/CMIC/NS-MBS/CAP) hits, all
confirmed to return non-empty output.codes in the census pilot.
"""
import datetime
import json
import time
import urllib.parse
import urllib.request

BASE = "https://fast.customsclear.net/api/sanctions_person_versions_regulations/match"

# (query, sublist-label) — all confirmed definite-hit names from census-pilot.
QUERIES = [
    # DPL — Bureau of Industry and Security (Denied Persons List)
    ("ALI ABDULLAH AHMED ALHAY", "DPL"),
    # OFAC / Treasury lists
    ("DEMCHENKO, Ivan Ivanovich", "SDN"),
    ("KOKOREV, Sergei", "SDN"),
    ("MANA'A, Fares Mohammed", "SDN"),
    ("BENOIL SHIPPING INC", "SDN"),
    ("BANK OF KUNLUN CO LTD", "CAP"),
    ("Central Bank of the Russian Federation", "NS-MBS"),
    ("GAZPROM MEDIA HOLDING", "SSI"),
    ("PUBLIC JOINT STOCK COMPANY TRANSNEFT", "SSI"),
    ("CNOOC Limited", "CMIC"),
    ("China Mobile Limited", "CMIC"),
]


def match(query):
    url = f"{BASE}?{urllib.parse.urlencode({'query': query})}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def main():
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outpath = (
        "/home/ramunas/projects/sanctioned-entities-testing/results/"
        f"provenance-fullpayload-{ts}.jsonl"
    )
    with open(outpath, "w") as f:
        for i, (q, label) in enumerate(QUERIES, 1):
            rec = {
                "query": q,
                "list_label": label,
                "ts_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "error": None,
            }
            try:
                res = match(q)
                out = res.get("output", {})
                # Capture FULL codes & possible_codes payloads verbatim (all fields).
                rec["codes"] = out.get("codes")
                rec["possible_codes"] = out.get("possible_codes")
                rec["reasoning"] = out.get("reasoning")
                rec["processing"] = res.get("processing")
                rec["input"] = res.get("input")
            except Exception as e:  # noqa: BLE001
                rec["error"] = repr(e)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            ncodes = len(rec.get("codes") or {})
            print(f"{i:2d}. [{label}] {q[:40]:40s} codes={ncodes} err={rec.get('error')}")
            if i < len(QUERIES):
                time.sleep(2)
    print("\nWROTE:", outpath)


if __name__ == "__main__":
    main()
