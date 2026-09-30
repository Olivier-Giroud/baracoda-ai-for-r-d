# PCB repo (Track B): findings for the EIM extractor

*2026-09-30. Read-only look at `bconnect-pcb-engine`, branch `codex/stickhub-stiffness-pilot`
(shallow clone, commits from 27 Sep only). No client names are quoted here.*

## Confidentiality — read first
- **History is not scrubbed.** Commits `321c089` and `f8e660a` removed confidential net names from
  the tracked files but say explicitly that git history was not rewritten. Reading any file
  revision before `321c089` exposes the names.
- **The current tree is not fully clean either:** some client names remain in doc filenames/text,
  the 29 Sep handover contains a personal filesystem path, and one FINDING file contains a
  placeholder-style net token.
- **Rule for the extractor:** read file contents only at `321c089` or later, or run the repo's
  leak gate on every string before emitting events.

## Brief is out of date
- Branch tip is now `f3aa5b3` (11 commits past `e558eaa`); `14388e7` is pushed.
- Suggested gold cycle: the 30 Sep review, `4846bba` → `f3aa5b3` (review adopted → gate hardening
  `2ff6cb2` → step 2 variants → steps 3a/3b nulls → step 4 stage 1). Entirely post-scrub, bounded,
  and includes a gate change that re-audits earlier results (a natural "withdrawal" event).

## Paper claims (PAPER.md §7) — confirmed with evidence
- **Identifier reuse — H4a names two hypotheses:** `docs/REVIEW-2026-09-29-best-of-pipeline.md:240`
  (adaptive shape/area search) vs `docs/PLAN-2026-09-29-stickhub-h4a-partial-bands.md:1`
  (half/quarter-depth exit reservations). Also "C4" (Task C4 vs a component variant) and
  "Step N" (different plans before/after `4846bba`); older RESULTS reuse H1–H5 locally.
- **Status divergence — H4:** "stays unresolved" (`RESULTS-2026-09-29-stickhub-h4-layer-aware-score.md:89`,
  `docs/HANDOVER.md:165,345,351`) vs "closed" (`RESULTS-2026-09-29-stickhub-h4a-partial-bands.md:97`,
  `docs/HANDOVER.md:211`). HANDOVER.md holds both at once.
- **Manual epoch propagation:** `RESULTS-2026-09-29-legality-model-corners.md:54-63` (commit `b7182d8`):
  "model epoch change … records stay as they were … must not compare null counts across the two epochs."
- **New for the paper:** hypothesis status lives in an external claude.ai page (the convergence
  map), not in git (`docs/HANDOVER.md:11-13`) — status is unversioned. "Epoch" has four meanings
  (metric, score 1/1s/2, legality model, repair code) — the PCB domain layer needs an epoch type
  with subtypes, mapped to EIM calibration nodes.
- RESULTS files are edited in place (correction blockquotes), so a RESULTS diff is itself a
  status-change event.

## Sources, best first
| Source | Extraction |
|---|---|
| `benchmarks/experiments/<id>/*.json` (gate verdict, router calls, `provenance{commit, source_sha256}`) | Deterministic — best source of observations |
| `experiments/*.json` (registered specs linking to PLAN files) | Deterministic |
| `benchmarks/history/*.jsonl` (per-commit DRC counts; `legality.jsonl` has an `epoch{…}` field) | Deterministic |
| Commits (hash, date, subject conventions: "Register …", "… null", "(refuted)") | Deterministic |
| RESULTS markdown (title verdict suffix, plan link, some tables) | Mixed; metrics in prose need an LLM |
| REVIEW (P1/P2 findings, H-table, mermaid tree) | Semi-structured; decisions need an LLM |
| PLAN | Mostly LLM |
| `docs/HANDOVER.md` | Use per-commit diffs + LLM; the takeover JSON is a file manifest only |
| Epochs | Code-path diffs + `source_sha256` + "epoch change" regex; one manual map of which files count as legality/gate/rule code |

No file registers hypotheses. Hardest part: hypothesis identity resolution (namespace = document
scope + date + active plan, plus human adjudication). Estimate: ~1.5–2 weeks for the 27–30 Sep
window; ~40% of events deterministic.
