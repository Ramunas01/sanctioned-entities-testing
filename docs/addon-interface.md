# Sanctions Add-on — Programmatic Interface

**Task:** Determine how the Sanctions person extractor
(`sanctions_person_versions_regulations`) can be invoked programmatically from
this Windows/WSL machine, and document the request/response contract.

**Verdict:** **(a) A documented HTTP/REST API exists and is the preferred
interface.** No CLI, library, or GUI gymnastics are needed — the extractor is a
plain HTTP endpoint reachable directly from WSL. Findings below; the harness is
**not** built (per instructions — report and stop).

Probed live on **2026-06-11** from this machine against the production host.

---

## 1. Endpoint

```
POST https://fast.customsclear.net/api/sanctions_person_versions_regulations/match
```

| Property        | Value                                                         |
|-----------------|---------------------------------------------------------------|
| Method          | **POST only** (`GET` → `405 Method Not Allowed`)              |
| Auth            | **None required.** No `X-API-Key` / token / cookie. Returns `200` with no credentials. |
| Content-Type    | Not needed (params go in the query string; no request body). |
| Server          | `nginx/1.18.0 (Ubuntu)`, HSTS enabled.                        |
| Rate limit      | **None observed.** 6 rapid sequential calls all `200`; no `RateLimit-*` / `Retry-After` headers. |
| Session/state   | Stateless. Each call is independent.                          |

### Parameters (query string)

| Param          | Required | Notes |
|----------------|----------|-------|
| `query`        | **Yes**  | The name to match, e.g. `Putin`. Must be in the **query string** — sending it only in a JSON body returns `422`. |
| `version_date` | No       | `YYYY-MM-DD`. **Accepted but currently inert** — see caveat §6. Omitting it is fine (`200`). |

> The `param=value` design means a request body is neither required nor read.
> The `{query, version_date}` are echoed back under `input` in the response.

---

## 2. Minimal working example

### curl

```bash
curl -s -X POST \
  "https://fast.customsclear.net/api/sanctions_person_versions_regulations/match?query=Putin&version_date=2026-06-10"
```

### Python (stdlib only — no deps, runs as-is in WSL)

```python
import json, urllib.parse, urllib.request

BASE = "https://fast.customsclear.net/api/sanctions_person_versions_regulations/match"

def match(query: str, version_date: str | None = None) -> dict:
    params = {"query": query}
    if version_date:
        params["version_date"] = version_date
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, method="POST")
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)

res = match("Putin")
definite = res["output"]["codes"]          # {} when no definite hit
possible = res["output"]["possible_codes"] # fuzzy / same-person variants
print("definite hits:", list(definite))     # -> ['1137110']
print("reasoning:", res["output"]["reasoning"])
```

---

## 3. Response shape (all fields)

`200 OK`, `application/json`. Top-level keys: **`output`, `input`, `processing`, `query`**.

```jsonc
{
  "output": {
    "codes": {                         // DEFINITE matches. {} if none.
      "1137110": {
        "title": "Putin Vladimir Vladimirovich",
        "type": "person",              // person | associate | (entity...)
        "information": "Aliases: ...; Birthdate: 1952-10-07; Title: President ...; Listed: 2022-02-25 (EO 14024); Related: ...",
        "source": "95284",
        "valid_from": "2022-02-25",     // sanction listing validity
        "valid_to": "2099-12-31",
        "envelope_valid_from": "2026-06-05", // data-snapshot validity
        "envelope_valid_to": "2099-12-31",
        "envelope_filename": "reg-us-russia-eo14024.json",
        "meta": { "issuer": "US" }      // issuing regime: US | EU | UK | ...
      }
    },
    "possible_codes": {                 // SAME structure as codes[]; fuzzy/variant matches
      "1123014": { "...": "..." }       // e.g. EU/UK/US variants of the same person
    },
    "reasoning": "Found 1 definite match and multiple possible matches because ..."
  },
  "input": {                            // request as the server interpreted it
    "query": "Putin",
    "version_date": "2026-06-11",       // NOTE: normalized to latest (see §6)
    "stages_enabled": ["keyword", "meilisearch"],
    "similarity_threshold": 0.7,
    "max_candidates": 5
  },
  "processing": {
    "stage_used": "llm",                // which pipeline stage decided: keyword | meilisearch | llm
    "version_used": "2026-06-11",
    "processing_time": 1.45,            // seconds, server-side
    "keyword_match": null,
    "approved_match": null,
    "top_candidates": [],
    "llm_best_match": {                 // structured echo of the LLM decision
      "reasoning": "...",
      "matches":          [{ "code": "1137110", "title": "Putin Vladimir Vladimirovich" }],
      "possible_matches": [{ "code": "1123014", "title": "Vladimir Vladimirovich PUTIN" }],
      "match_type": "llm",
      "similarity": null,
      "matched_text": null
    }
  },
  "query": "Putin"
}
```

**Hit / no-hit logic:** a definite match ⇔ `output.codes` is non-empty.
`output.possible_codes` is often populated even on a "miss" (it returns fuzzy
neighbours), so **do not** treat a non-empty `possible_codes` as a hit. Example:
`query="Jonas Petraitis Nobody Random"` → `codes: {}` but `possible_codes`
listed unrelated people whose aliases contained "Jonas".

---

## 4. Latency

| Measurement                    | Value                          |
|--------------------------------|--------------------------------|
| Server `processing_time`       | ~**1.3–1.5 s** (LLM stage)     |
| Wall-clock (WSL → prod, total) | ~**1.8–2.6 s** per query       |

The LLM stage (`stage_used: "llm"`) dominates. A `keyword`/`meilisearch` short-circuit
would be faster but was not triggered for the names tested. Budget **~2 s/query**
and expect it to be the bottleneck for any batch loop.

---

## 5. Rate limits / auth / session

- **Auth:** none. (The picoco codebase carries `X-API-Key: picoco-demo-001` for
  the *other*, generic `/api` gateway — see §7 — but this dedicated endpoint
  ignores it and serves unauthenticated.)
- **Rate limit:** none observed in this probe. Be a good citizen anyway: serial
  or low-concurrency, since each call runs an LLM server-side.
- **Session:** stateless; no cookies/CSRF.

---

## 6. Caveats & gotchas

1. **`version_date` is currently inert.** Despite the endpoint name
   (`..._versions_...`) and the `version_date` param, every value tested
   (`2026-06-10`, `2022-01-01`, `2030-01-01`, omitted) resolved to
   `version_used: "2026-06-11"` (today) and `input.version_date` was always
   normalized to today. The versioning contract is wired (param accepted, echoed,
   `version_used` reported) but **historical snapshots are not currently
   selectable** — only the latest envelope is served. Treat point-in-time queries
   as **not yet functional**; confirm with the add-on owner before relying on them.
2. **`query` must be in the query string**, not a JSON body (`422` otherwise).
3. **LLM non-determinism.** Repeated identical calls returned a *varying* split
   between `codes` and `possible_codes` (e.g. 1 vs 3 vs 4 definite codes for
   `Putin` across runs). Any harness should tolerate this — match on the stable
   numeric `code` IDs, and consider `codes ∪ possible_codes` when recall matters.
4. **No OpenAPI/Swagger** exposed: `/openapi.json` and `/docs` both `404`. This
   doc is the contract of record.

---

## 7. Secondary interface (context, not the target)

The picoco repo also speaks to a **generic gateway** at
`POST https://fast.customsclear.net/api` (header `X-API-Key: picoco-demo-001`)
with body `{"route": "eu_sanctions", "params": {"action": "process_addon_data",
"param": {...}}}`. That is the *shipment-level* sanctions classifier
(HS code / route / dual-use / person combined) used by
`backend/tools/eu_sanctions/api.py` — **not** the standalone person extractor
this task targets. Documented here only so the two are not confused.

---

## 8. Recommendation for the (future) harness

- Use the **dedicated REST endpoint** in §1 — simplest and dependency-free
  (stdlib `urllib` works; the repo's `requests`/`aiohttp` also fine).
- Drive it with a list of person JSONs → `query` = each name; collect
  `output.codes` (and optionally `possible_codes`) keyed by the numeric code ID.
- Budget ~2 s/query; serialize or cap concurrency.
- Do **not** depend on `version_date` until point-in-time selection is confirmed working.

*(Harness intentionally not built — per task instructions.)*
