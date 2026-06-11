#!/usr/bin/env python3
"""Re-query EXPORT MATERIALS, INC. 10x and capture full code identities.

Resolves Advisor fork on Finding #6: are 1145893/1145895 the real entity
(true dropout on run 3) or a different party (spurious-hit)?

Captures, per code in codes & possible_codes: title, type, meta.issuer, source.
Also captures output.reasoning and processing.stage_used. Serial, ~2s apart.
"""
import datetime
import json
import time
import urllib.parse
import urllib.request

BASE = "https://fast.customsclear.net/api/sanctions_person_versions_regulations/match"
QUERY = "EXPORT MATERIALS, INC."
N = 10


def match(query):
    url = f"{BASE}?{urllib.parse.urlencode({'query': query})}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def slim(bucket):
    out = {}
    for code, d in (bucket or {}).items():
        out[code] = {
            "title": d.get("title"),
            "type": d.get("type"),
            "issuer": (d.get("meta") or {}).get("issuer"),
            "source": d.get("source"),
        }
    return out


def main():
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outpath = (
        "/home/ramunas/projects/sanctioned-entities-testing/results/"
        f"export-materials-identity-{ts}.jsonl"
    )
    with open(outpath, "w") as f:
        for i in range(1, N + 1):
            rec = {
                "query": QUERY,
                "run": i,
                "ts_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "error": None,
            }
            try:
                res = match(QUERY)
                out = res.get("output", {})
                proc = res.get("processing", {})
                rec["codes"] = slim(out.get("codes"))
                rec["possible_codes"] = slim(out.get("possible_codes"))
                rec["reasoning"] = out.get("reasoning")
                rec["stage_used"] = proc.get("stage_used")
                rec["version_used"] = proc.get("version_used")
                rec["processing_time"] = proc.get("processing_time")
            except Exception as e:  # noqa: BLE001
                rec["error"] = repr(e)
            f.write(json.dumps(rec) + "\n")
            f.flush()
            print(
                f"run {i}: codes={list((rec.get('codes') or {}).keys())} "
                f"possible={list((rec.get('possible_codes') or {}).keys())} "
                f"stage={rec.get('stage_used')} err={rec.get('error')}"
            )
            if i < N:
                time.sleep(2)
    print("\nWROTE:", outpath)


if __name__ == "__main__":
    main()
