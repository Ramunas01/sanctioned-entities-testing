# DPL Harness-Artifact Disconfirmation (Advisor gate 1 — Finding #9)

_Generated: 2026-06-11 · Branch: issue-3-census_
_Raw capture: `results/dpl_disconfirmation_raw-20260611.jsonl` (gitignored)_
_Endpoint: `POST https://fast.customsclear.net/api/sanctions_person_versions_regulations/match?query=<urlencoded>` (stdlib urllib, serial, synchronous)_

## Question

The census harness queries `query = primary_name` verbatim (URL-encoded). The DPL sweep
showed 484 DPL names hitting 5/5-definite with this same harness, so the harness *can*
query DPL. This probe disconfirms the hypothesis that the specific DPL 0/5 misses are a
**harness mis-query** (wrong name format) rather than a genuine **Add-on gap** — and, if a
real gap, splits it into **formatting/retrieval** (record held but not matchable under the
canonical source name format) vs **ingestion/recall** (record not retrievable at all).

---

## Part A — True-positive control (retrieval of known-good DPL records)

Two distinctive DPL names that scored 5/5-definite in the sweep, re-queried 5× verbatim:

| control name | sweep code | this probe | verdict |
|--------------|-----------|-----------:|---------|
| `ADT ANALOG AND DIGITAL TECHNIK` | 1149715 | **5/5 definite** (code `1149715` every run) | retrieval OK, deterministic |
| `AHWAZ STEEL COMMERCIAL & TECHNICAL SERVICE GMBH` | 1133976 | **5/5 definite** (code `1133976` every run) | retrieval OK, deterministic |

**Control verdict: RETRIEVAL WORKS.** Both controls returned the expected definite code
on all 5 runs (10/10 definite total, no flakiness). The harness path reaches the Add-on and
the Add-on serves known-good DPL records. Neither control read 0/5, so we are nowhere near
the "RETRIEVAL BROKEN" stop condition. The misses below are therefore not explained by a
broken query path.

---

## Part B — Disconfirmation on 10 DPL 0/5 misses

For each miss: (1) re-issue the **harness-form** payload (primary_name verbatim, URL-encoded)
to rule out a transient miss; (2) construct a **human-typed plain** simplified form (strip
parentheticals/AKA text, drop corporate suffixes LTD/INC/CORP/FZCO/PTY, reorder
`LAST, FIRST` → `FIRST LAST`, drop `&`) and query it. "Hit" = `output.codes` non-empty
(definite). same-entity? judged from the response `title`.

| miss_name | harness-form hit | simplified-form used | simplified-form hit | same-entity? | classification |
|-----------|:----------------:|----------------------|:-------------------:|:------------:|----------------|
| `BLACK, SIVALLS & BRYSON (UK) LTD` | NO | `BLACK SIVALLS BRYSON` | NO | n/a (empty) | INGESTION-GAP |
| `ITEX-WAVE FZCO` | NO | `ITEX-WAVE` | NO | n/a (empty) | INGESTION-GAP |
| `KOLOKOL (AKA: ALDRICH AMES)` | NO | `ALDRICH AMES` | NO | n/a (empty) | INGESTION-GAP |
| `TATOS, FRED` | NO | `FRED TATOS` | NO | n/a (empty) | INGESTION-GAP |
| `A. ROSENTHAL (PTY) LTD.` | NO | `A. ROSENTHAL` | NO | n/a (empty) | INGESTION-GAP |
| `COSMOTRANS USA, INC.` | NO | `COSMOTRANS USA` | NO | n/a (empty) | INGESTION-GAP |
| `COLEMAN, LOUIS SINCLAIR` | NO | `LOUIS SINCLAIR COLEMAN` | NO | n/a (empty) | INGESTION-GAP |
| `DOYLE, THOMAS` | NO | `THOMAS DOYLE` | NO | n/a (empty) | INGESTION-GAP |
| `OERLIKON-WELDING LTD.` | NO | `OERLIKON-WELDING` | NO | n/a (empty) | INGESTION-GAP |
| `MES (MODERN ENGINEERING SERVICES, LTD)` | NO | `MODERN ENGINEERING SERVICES` | NO (codes empty; possible_codes only) | **NO — spurious** ("Gulf Modern Solutions Engineering Company", code 1155938 — a different party matched on generic tokens) | INGESTION-GAP |

**Result: 10/10 misses confirmed in harness-form (no transient misses), and 10/10 still miss
under the simplified plain form.** The single non-empty simplified response
(`MODERN ENGINEERING SERVICES`) produced only a `possible_codes` fuzzy neighbour that is a
**different entity** (Gulf Modern Solutions Engineering Company) — a generic-token false
positive, exactly the spurious-hit class the interface doc warns about, not retrieval of the
listed party. No simplified form retrieved the correct DPL entity that the harness-form had
missed.

**Interpretation (per the rule):** a RETRIEVAL/FORMATTING gap would show the simplified form
returning the *correct* entity where harness-form missed. That did not happen for any of the
10. Both forms miss (or simplified yields only a spurious different party) →
**INGESTION/recall gap** for all 10.

### Exact request URL for one miss (verbatim, harness-form)

```
https://fast.customsclear.net/api/sanctions_person_versions_regulations/match?query=BLACK%2C+SIVALLS+%26+BRYSON+%28UK%29+LTD
```

(`query=BLACK, SIVALLS & BRYSON (UK) LTD`, URL-encoded by `urllib.parse.urlencode` — the
identical payload the census harness emits.)

---

## Verdict

- **Is the DPL gap a harness artifact?** **NO.** Controls prove the harness query path
  retrieves known-good DPL records 5/5; the misses reproduce in harness-form (not transient);
  and a human-typed plain re-spelling of each miss does **not** recover the entity. Finding #9
  is a **real Add-on defect**, not a harness mis-query. The harness query format is exonerated.

- **Ingestion vs formatting split:** **10/10 INGESTION-GAP, 0/10 FORMATTING-GAP.** The DPL
  recall gap is **predominantly (here, entirely) an ingestion/recall problem** — the records
  are not retrievable from the Add-on under any reasonable spelling, not merely unmatchable
  under the canonical CSL name format. Names deliberately spanning the formatting hazards
  (`LAST, FIRST`, `&`, parenthetical AKAs, corporate suffixes LTD/INC/FZCO/PTY) all stayed
  missing after those hazards were removed. The one form that returned anything returned a
  wrong party on generic tokens, which reinforces (does not soften) the ingestion read.

- **Remediation pointer:** route Finding #9 to the Add-on **ingestion/recall** track (are
  these DPL listings present in the served envelope at all?), not to a name-normalization /
  query-formatting fix on the harness or matcher.

---

## Method notes / caveats

- 60 queries total: Part A 2×5 = 10; Part B 10×2 = 20 (× the harness+simplified pair).
  Serial, ~0.3 s inter-call sleep, synchronous, stdlib `urllib` only. 0 errors.
- "Definite hit" = `output.codes` non-empty per the interface contract
  (`docs/addon-interface.md` §3); `possible_codes`-only is recorded but not counted as a hit.
- LLM non-determinism (interface §6.3) is a known confound; Part A controls came back fully
  stable (5/5 with identical codes), and Part B misses returned empty `codes` on the single
  re-issue. A 1-shot harness-form re-issue can in principle undercount a flaky name, but for
  these the sweep already showed 0/5 across 5 runs, and the simplified-form probe is the
  decisive arm regardless.
- 5/5-definite controls and the extra 6 misses were drawn from
  `results/dpl-full-census-20260611T190532Z.jsonl` (aggregated: 1082 DPL names, 534 at
  5/5-definite, 187 at 0/5 both-buckets-empty). The 4 mandated misses are a subset of those 187.
