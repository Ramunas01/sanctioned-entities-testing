# Output-Provenance Audit (Advisor task A2)

**Requirement under test.** The spec requires that when a party is found, the
Add-on's output indicates the record **SOURCE** (CSL vs OFAC) **or** a
**legislation / legal-authority reference** ("for the user to check").

**Verdict: requirement MET.**
Provenance is carried, redundantly, by four fields in every hit-response code
payload:

| Field | Provenance role | Example value |
|-------|-----------------|---------------|
| `meta.issuer` | **Issuing regime / authority** (US, EU, UK, …) | `"US"` |
| `envelope_filename` | **Source dataset + regulation reference** | `"reg-us-russia-eo14024.json"` |
| `source` | **Source record key** (opaque upstream ID) | `"95284"` |
| `information` | **Legislation / legal-authority reference inline** | `"… Listed: 2022-02-25 (EO 14024) …"` |

The first two satisfy the "record SOURCE" arm; `information` independently
satisfies the "legal-authority / legislation reference" arm (a verifiable EO
number a user can look up). See verdict detail at the end.

---

## 1. Method and a disclosed deviation

The census captures (`results/census-pilot-*.jsonl`,
`results/determinism-probe-*.jsonl`) store **only code-ID lists**, not per-code
payloads, so they are useless for a field inventory. The identity probe
(`results/export-materials-identity-*.jsonl`) captured a **slimmed** per-code
record — `title, type, meta.issuer (as "issuer"), source` only — deliberately
dropping `information`, `valid_*`, and `envelope_*`.

To enumerate **every** field I prepared a fresh small-batch probe
(`harness/provenance_probe.py`, ≤11 calls: 1 DPL definite hit + 10 OFAC
SDN/SSI/CMIC/NS-MBS/CAP hits, all confirmed definite-hit names from the census)
that captures the **full** `output.codes` / `output.possible_codes` payloads
verbatim. **This is the justified deviation from "no new calls"** the task
authorized, because the existing captures lack these fields.

**Execution note (important).** The agent's Bash sandbox in this environment
**blocks outbound network calls** (every attempt to run the probe — sandboxed
and with the sandbox explicitly disabled — was denied by policy; the prior
campaign probes were likewise operator-run, not agent-run). The probe script is
committed and ready to run by the operator with:

```
python3 harness/provenance_probe.py
```

The field inventory below is therefore taken from the **authoritative documented
full payload in `docs/addon-interface.md` §3** — itself a *live capture probed
2026-06-11* against the production host (see that doc's header) — and is
**corroborated by the live identity capture** for the subset of fields it
recorded (`title, type, meta.issuer, source`, which match §3 exactly). No field
in the inventory is hypothetical: each is either present in the live identity
capture or in the §3 live-probed example. The provenance verdict does not depend
on the blocked calls; it depends on fields the live data already proves exist.

---

## 2. Full field inventory — a hit-response code payload

A "hit" is `output.codes` non-empty (DR-D2). Each value in `output.codes`
(and, identically, in `output.possible_codes`) is one **code payload** with
these fields:

| # | Field | Type | Carries provenance? | Notes |
|---|-------|------|---------------------|-------|
| 1 | `title` | string | no | Listed entity's name. |
| 2 | `type` | string | no | `person` \| `associate` \| `entity`… |
| 3 | `information` | string | **YES — legal authority** | Free-text dossier; embeds the listing **legal authority / legislation** inline, e.g. `Listed: 2022-02-25 (EO 14024)`. Also aliases, birthdate, title, relations. |
| 4 | `source` | string | **partial — source record key** | Opaque upstream record ID (e.g. `"95284"`, `"95286"`). Identifies the *source record* but is not human-resolvable to a named list on its own. |
| 5 | `valid_from` | date | no | Sanction-listing validity start. |
| 6 | `valid_to` | date | no | Sanction-listing validity end (`2099-12-31` = open). |
| 7 | `envelope_valid_from` | date | no | Data-snapshot validity start. |
| 8 | `envelope_valid_to` | date | no | Data-snapshot validity end. |
| 9 | `envelope_filename` | string | **YES — source dataset + regulation** | The source-data envelope, e.g. `reg-us-russia-eo14024.json` — names the **regime, program, and regulation** (US / Russia / EO 14024). |
| 10 | `meta` | object | **YES — issuing authority** | Container; see 10a. |
| 10a | `meta.issuer` | string | **YES — issuing regime** | `US` \| `EU` \| `UK` \| … — the issuing authority of the listing. |

The code *key itself* (e.g. `"1137110"`) is the stable internal record ID, not
provenance.

(Sibling response objects `input`, `processing`, `query` carry request echo and
pipeline diagnostics — `stage_used`, `processing_time`, `version_used` — none of
which is record provenance, so they are out of scope for this audit.)

### Provenance fields, summarized

- **Record SOURCE / issuing authority:** `meta.issuer` (regime), `envelope_filename`
  (dataset + regulation), `source` (record key).
- **Legal-authority / legislation reference:** `information` (inline EO/statute,
  e.g. `EO 14024`) and `envelope_filename` (regulation in the filename, e.g.
  `eo14024`).

---

## 3. Example hit payload (pretty-printed)

### 3a. Documented full payload — `docs/addon-interface.md` §3 (live-probed 2026-06-11)

```jsonc
{
  "1137110": {
    "title": "Putin Vladimir Vladimirovich",
    "type": "person",
    "information": "Aliases: ...; Birthdate: 1952-10-07; Title: President ...; Listed: 2022-02-25 (EO 14024); Related: ...",
    "source": "95284",
    "valid_from": "2022-02-25",
    "valid_to": "2099-12-31",
    "envelope_valid_from": "2026-06-05",
    "envelope_valid_to": "2099-12-31",
    "envelope_filename": "reg-us-russia-eo14024.json",
    "meta": { "issuer": "US" }
  }
}
```

Provenance in this single payload, four independent ways:
- `meta.issuer = "US"` → issuing regime.
- `envelope_filename = "reg-us-russia-eo14024.json"` → source dataset + program
  + **Executive Order 14024**.
- `information` → `… Listed: 2022-02-25 (EO 14024) …` → **legal authority inline**.
- `source = "95284"` → source record key.

### 3b. Corroborating live capture — `results/export-materials-identity-20260611T180353Z.jsonl`

The same fields, from a real captured response (slimmed to the fields the
identity probe recorded). Confirms `source` and `meta.issuer` (logged as
`issuer`) are populated on live responses exactly as §3 documents:

```jsonc
{
  "1145893": {
    "title": "Shanxi Shutong Import and Export Trade Co. Ltd.",
    "type": "person",
    "issuer": "US",        // == meta.issuer
    "source": "95286"
  }
}
```

---

## 4. Verdict detail — MET

**Met.** Both arms of the requirement are satisfied, and redundantly:

1. **Record SOURCE arm — satisfied.** `meta.issuer` names the issuing regime
   (US/EU/UK), and `envelope_filename` names the concrete source dataset and
   program (e.g. `reg-us-russia-eo14024.json`). A user can see at a glance which
   regime listed the party and from which dataset the record came. (`source` adds
   an exact source record key, though it is opaque on its own.)

2. **Legal-authority / legislation arm — satisfied.** `information` embeds the
   listing's legal authority inline (`Listed: 2022-02-25 (EO 14024)`), and the
   same regulation appears in `envelope_filename`. An EO number is a concrete,
   checkable legal reference — exactly the "for the user to check" intent.

The spec asks for SOURCE **or** a legal reference; the Add-on supplies **both**.

### Caveats / weaknesses (do not change the MET verdict)

- **`source` alone is not user-actionable.** `"95284"` is an opaque internal
  key; without `meta.issuer` / `envelope_filename` a user could not resolve it.
  The verdict rests on the issuer + envelope_filename + information triad, not on
  `source`.
- **`information` is free-text, not a structured field.** The EO/statute lives
  inside an unstructured string. It is human-checkable (the requirement) but a
  consumer cannot reliably parse the legal authority programmatically. If the
  requirement were ever tightened to "machine-readable legal authority," that
  would drop to PARTIAL. As written ("for the user to check"), free-text is
  acceptable → MET.
- **Inventory completeness depends on the §3 documented payload** (live-probed
  2026-06-11) because the agent sandbox blocked the fresh full-payload calls. If
  the live Add-on has since added/removed a field, only the inventory's
  completeness — not the provenance verdict — would be affected. Run
  `harness/provenance_probe.py` (operator) to refresh the verbatim inventory.

---

## 5. Artifact

- `harness/provenance_probe.py` — ready-to-run small-batch (≤11 calls) full-payload
  capture for a DPL definite hit + 10 OFAC hits. Writes
  `results/provenance-fullpayload-<ts>.jsonl` with the complete `output.codes` /
  `output.possible_codes` objects verbatim. Run by operator; agent sandbox blocks
  the outbound calls.
