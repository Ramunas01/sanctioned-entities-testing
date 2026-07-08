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
| `data/`     | Refreshable working snapshots (UK Sanctions List). **Not** ground truth — see below. |

## Other lists

The US CSL above is the pinned, frozen oracle. The **UK Sanctions List** lives in
`data/` as a *refreshable* snapshot and backs no census or ground-truth claim.
To refresh it and extract what changed:

```bash
python3 harness/fetch_uk_list.py                                        # refresh
python3 harness/uk_latest.py --against data/UK-Sanctions-List.prev.xml  # what was added
```

Use `--against`, not `--n 50`: "the newest N by designation date" is a different
set from "what was added" (and can never show delistings). Full procedure, the
alias/name derivation rules, and the three traps this XML sets:
**`docs/uk-sanctions-refresh.md`**.

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
