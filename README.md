# sanctioned-entities-testing

Black-box test harness for the Sanctions person-matcher Add-on, focused on validating
the new US data integration (Consolidated Screening List).

## Method (two tracks)

- **Presence = census.** Push every primary name + strong alias from the pinned source
  through the Add-on; check HIT / NO-HIT / ERROR. Catches catastrophic ingestion failures
  (missing program, dropped batch) with certainty.
- **Behavior = sample.** Stratified + random vectors exercise transliteration, fuzzy
  thresholds, aliases, disambiguation, structural edge cases. Recall and precision measured
  separately.

## Layout

| Dir         | Contents |
|-------------|----------|
| `oracle/`   | Deterministic parser + pinned source snapshot + `snapshot.json` (hashes). Ground truth. |
| `vectors/`  | Test vectors as CSV, by equivalence class. |
| `harness/`  | Add-on driver (pushes vectors, captures raw responses). |
| `results/`  | Timestamped raw run captures. |
| `reports/`  | Census, behavioral diff, coverage, stats. |
| `docs/`     | Test plan, interface contract, equivalence-class matrix, acceptance criteria. |

## Roles

- **Advisor (Claude Opus):** methodology, equivalence classes, acceptance criteria, oracle review, adjudication of ambiguous expected-outputs.
- **PM (Claude):** GitHub board, issue decomposition, snapshot discipline, blocker escalation.
- **Programmer (Claude Code):** interface discovery -> oracle -> census harness -> behavioral harness.
- **Chrome (Claude):** secondary spot-check oracle only, against official portals.

## Disciplines (non-negotiable)

1. **GitHub is the single source of truth** -- issues, PRs, CSVs, reports. No chat relays.
2. **Oracle/checker separation** -- the agent that authors the oracle parser is not the sole validator of it. Oracle reviewed against raw source by human or Advisor before trust.
3. **Snapshot pinning** -- `oracle/snapshot.json` records source date + SHA-256 of each source file. Every harness run records the Add-on's echoed `version_used`.

See `docs/test-plan.md`.
