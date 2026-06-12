#!/usr/bin/env python3
"""A5 — assurance census, entity-oversampled, per-sublist class cross-tab.

Advisor question: is the entity-ingestion defect (Finding #9, confirmed on DPL)
DPL-only, or does it span every US sublist? We deliberately oversample ENTITY
names per sublist (random draw under-samples them) and report recall as a
per-sublist, per-CLASS cross-tab — never pooled.

Class labeling (Advisor-pinned):
  - Use the oracle's `entity_type` field DIRECTLY wherever populated (OFAC
    sublists): Individual->person, Entity->entity, Vessel->vessel, Aircraft->
    aircraft. Vessel and Aircraft are their OWN lines, never folded into entity.
  - Fall back to the corporate-suffix name heuristic ONLY where entity_type is
    empty (BIS sublists EL/MEU, per F4).
  - Record `label_method` (entity_type | heuristic) per row so OFAC ground-truth
    and DPL/BIS heuristic numbers are never silently conflated.

Deterministic: source-order, first-N per class. stdlib only;
run via `python3 - < harness/a5_assurance.py`.
"""
import csv, json, re, urllib.parse, urllib.request, time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

csv.field_size_limit(10**7)
BASE = "https://fast.customsclear.net/api/sanctions_person_versions_regulations/match"
RUNS, CONC = 5, 4
CAPS = {"entity": 150, "person": 100, "vessel": 50, "aircraft": 50}

SUBLISTS = {  # short key -> source_sublist prefix
    "SDN": "Specially Designated Nationals",
    "SSI": "Sectoral Sanctions",
    "EL": "Entity List",
    "MEU": "Military End User",
    "NS-MBS": "Non-SDN Menu-Based",
}
ENT = re.compile(r"\b(LTD|LIMITED|INC|INCORPORATED|CORP|CORPORATION|CO|COMPANY|LLC|GMBH|PTY|"
    r"LLP|PLC|AG|SA|BV|NV|SRL|FZCO|FZE|DMCC|JSC|OOO|TRADING|TECHNOLOG\w*|SYSTEMS|INDUSTR\w*|"
    r"INTERNATIONAL|INTL|IMPORT|EXPORT|ENTERPRISE\w*|GROUP|HOLDING\w*|ELECTRONIC\w*|ENGINEERING|"
    r"MANUFACTUR\w*|SHIPPING|LOGISTIC\w*|SERVICES|SOLUTIONS|BANK|SHIPYARD|AVIATION|AIRLINE\w*|"
    r"SEMICONDUCTOR\w*|MACHINER\w*|EQUIPMENT|MATERIAL\w*|METAL\w*|CHEMICAL\w*|TRADE|FACTORY|"
    r"INSTITUTE|UNIVERSITY|LABORATOR\w*|AEROSPACE|DEFENSE|OPTICS|PRECISION|PUBLIC JOINT|"
    r"JOINT STOCK|OAO|PAO|ZAO)\b", re.I)

def label_row(entity_type, name):
    """-> (label, method). Ground-truth entity_type wins; heuristic only if empty."""
    et = (entity_type or "").strip()
    if et:
        return {"Individual": "person", "Entity": "entity", "Vessel": "vessel",
                "Aircraft": "aircraft"}.get(et, et.lower()), "entity_type"
    return ("entity" if ENT.search(name) else "person"), "heuristic"

def select():
    seen = {k: set() for k in SUBLISTS}
    buckets = {k: {c: [] for c in CAPS} for k in SUBLISTS}  # key -> class -> [(name, method)]
    for r in csv.DictReader(open("oracle/expected.csv", newline="", encoding="utf-8")):
        sl = r["source_sublist"]
        for k, pref in SUBLISTS.items():
            if sl.startswith(pref):
                n = r["primary_name"]
                if n in seen[k]:
                    break
                seen[k].add(n)
                lab, meth = label_row(r["entity_type"], n)
                if lab in buckets[k] and len(buckets[k][lab]) < CAPS[lab]:
                    buckets[k][lab].append((n, meth))
                break
    chosen = []
    for k in SUBLISTS:
        for lab in CAPS:
            for n, meth in buckets[k][lab]:
                chosen.append((k, lab, meth, n))
    return chosen

def call(item):
    k, lab, meth, name = item
    url = f"{BASE}?{urllib.parse.urlencode({'query': name})}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="POST"), timeout=40) as resp:
                d = json.load(resp)
            o = d.get("output", {}) or {}; p = d.get("processing", {}) or {}; inp = d.get("input", {}) or {}
            return {"sublist": k, "label": lab, "label_method": meth, "name": name,
                    "codes": list((o.get("codes") or {}).keys()),
                    "possible_codes": list((o.get("possible_codes") or {}).keys()),
                    "version_used": p.get("version_used"), "version_date": inp.get("version_date"),
                    "stage_used": p.get("stage_used"), "error": None,
                    "ts_utc": datetime.now(timezone.utc).isoformat()}
        except Exception as e:
            if attempt == 2:
                return {"sublist": k, "label": lab, "label_method": meth, "name": name,
                        "codes": [], "possible_codes": [], "version_used": None, "version_date": None,
                        "stage_used": None, "error": f"{type(e).__name__}:{e}",
                        "ts_utc": datetime.now(timezone.utc).isoformat()}
            time.sleep(1.5 * (attempt + 1))

def main():
    chosen = select()
    out = f"results/a5-assurance-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.jsonl"
    tasks = [it for it in chosen for _ in range(RUNS)]
    print(f"A5 names={len(chosen)} calls={len(tasks)} out={out}", flush=True)
    n = 0
    with open(out, "w", encoding="utf-8") as fh, ThreadPoolExecutor(max_workers=CONC) as ex:
        for fut in as_completed([ex.submit(call, t) for t in tasks]):
            fh.write(json.dumps(fut.result()) + "\n"); fh.flush()
            n += 1
            if n % 250 == 0: print(f"{n}/{len(tasks)}", flush=True)
    print(f"A5 DONE calls={n} out={out}", flush=True)

if __name__ == "__main__":
    main()
