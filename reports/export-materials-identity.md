# EXPORT MATERIALS, INC. — Identity Resolution (Finding #6 fork)

_Generated: 2026-06-11_
_Raw capture: `results/export-materials-identity-20260611T180353Z.jsonl` (gitignored)_
_Runner: `harness/export_materials_identity.py` (stdlib urllib, POST, query in query string, serial, ~2s apart, 10 calls)_
_Cross-check source: `results/determinism-probe-20260611T172417Z.jsonl`_

## Verdict

**The codes `1145893` / `1145895` are a DIFFERENT, UNRELATED party — NOT `EXPORT MATERIALS, INC.`**
The bug is **spurious fuzzy hits**, not a whole-result dropout. The run-3 empty observed in the
original probe was **the correct result**; the *non-empty* runs are the defect.

This flips the Sev-1 "listed party intermittently returns nothing" hypothesis. The listed BIS Denied
Persons List party `EXPORT MATERIALS, INC.` is **never matched at all** (0 correct hits in 15 total
runs: 5 in the original probe + 10 here). What varies is whether two unrelated entities leak into
`possible_codes` on weak single-word overlap.

## Identity of the two codes

| Code | Title | type | issuer | source | Relation to query |
|------|-------|------|--------|--------|-------------------|
| `1145893` | Shanxi Shutong Import and Export Trade Co. Ltd. | person | US | 95286 | Unrelated. Overlap = generic word **"Export"** only. |
| `1145895` | Shandong Mingming New Material Technology Co., Ltd. | person | US | 95286 | Unrelated. Overlap = generic word **"Material"** only. |

Both are Chinese trading/technology companies. Neither is `EXPORT MATERIALS, INC.` nor a plausible
alias. The endpoint's own `output.reasoning` agrees and self-describes the matches as spurious — e.g.:

> "No definite matches found... The only overlapping word is generic 'Export', which is insufficient
> for a possible match." (run 3)

> "...Shandong Mingming New Material Technology Co., Ltd. (contains 'Material') and Shanxi Shutong
> Import and Export Trade Co. Ltd. (contains 'Export')... These similarities are weak, so they are
> listed as possible matches." (run 5)

The LLM is non-deterministically deciding whether weak single-token overlap clears the
`possible_codes` bar — hence the union-churn. It is consistent on one point across all 15 runs:
**zero `codes` (definite) hits, ever**, and the correct entity never appears in either bucket.

## 10-run results (this capture)

- **Empty runs (both buckets empty): 2 / 10** = 20%.
- Non-empty runs: 8 / 10, **all** with the identical possible set `{1145893, 1145895}` (no `codes`).
- `stage_used` = `llm` on all 10 runs. `version_used` = 2026-06-11. No errors.

| run | codes | possible_codes |
|----:|-------|----------------|
| 1 | ∅ | 1145893, 1145895 |
| 2 | ∅ | ∅ |
| 3 | ∅ | ∅ |
| 4 | ∅ | 1145893, 1145895 |
| 5 | ∅ | 1145893, 1145895 |
| 6 | ∅ | 1145893, 1145895 |
| 7 | ∅ | 1145893, 1145895 |
| 8 | ∅ | 1145893, 1145895 |
| 9 | ∅ | 1145893, 1145895 |
| 10 | ∅ | 1145893, 1145895 |

Note: this 10-run sample never reproduced the original probe's intermediate `{1145893}`-only state
(runs 2,5 there). Here it was binary: either both spurious codes or neither. The dropout-of-the-
correct-entity rate is **100%** (it is structurally absent), independent of the empty-bucket rate.

## Cross-check of the 1/240 figure (original probe)

Confirmed against `results/determinism-probe-20260611T172417Z.jsonl`:

- `kind=="listed"` (name,run) records: **240** (48 listed names × 5 runs, 0 errors).
- Pairs with **both** `codes` and `possible_codes` empty: **1**.
- The single both-empty pair is **`('EXPORT MATERIALS, INC.', 3)`** — exactly the run cited.
- Fraction = **1/240 = 0.4167%** ✓ (matches the Advisor's 0.42%).

This 0.42% is an artifact of how rare empty-bucket states are *given* the spurious-hit behavior — it
should not be read as a dropout rate for a correctly-matched party. For this one name the
empty-bucket rate is far higher when sampled in isolation (2/10 = 20% here; 1/5 = 20% in the probe).

## Failure mode & remediation direction

- **Failure mode: spurious / false `possible_codes` hits** driven by generic single-word token overlap
  ("Export", "Material"), with LLM non-determinism flipping the weak-match threshold call.
- **NOT a true whole-result dropout.** Run 3 (and run 2 here) returning empty is correct.
- Remediation points the **opposite** way from the Sev-1 hypothesis: tighten the `possible_codes`
  gate against generic-token matches; do not "fix" the empty runs. Separately, `EXPORT MATERIALS,
  INC.` is genuinely never recalled — worth a recall check against the BIS DPL source name, but that
  is a coverage/recall gap, not an intermittent dropout.
