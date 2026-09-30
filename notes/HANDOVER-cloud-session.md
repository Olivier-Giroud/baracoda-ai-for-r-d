# Handover from the cloud session (2026-09-30)

Start here in the local session.

## State
- Repo scaffold: Python package + LaTeX paper + CI (CI builds the PDF; LaTeX not installed locally, by choice).
- Local setup verified on the Mac: `.venv` from `/usr/local/bin/python3.11`, `make test lint figures` green.
- Writing format for now: Markdown (.md); LaTeX conversion at the end, server side (CI).

## Documents
- `docs/BRIEF.md` — EIM toy-model build brief (owner's spec, milestones M0–M8).
- `docs/PAPER.md` — paper outline (EIM: "compress the map, never the territory").
- `notes/literature-review.md` — ~100 papers on compaction vs structured memory; verify citations (arXiv was blocked in the cloud).
- `notes/eim-novelty-check.md` — claim-by-claim novelty check + 5 fixes to the toy evaluation
  (most important: add a `raw-rag` baseline).
- `notes/pcb-track-b-findings.md` — PCB repo analysis: confidentiality rules, evidence for paper claims, extraction sources.

## Next step (brief's kickoff)
Read the four documents above, write CLAUDE.md with the brief's conventions, propose a plan for
M0 and M1 only; no code until the owner approves.

## Notes for the plan (from the Claude API reference, checked 2026-09-30)
- Structured outputs: `client.messages.parse(..., output_format=<PydanticModel>)` → `response.parsed_output`
  (supported on Haiku 4.5, Sonnet 5.5, Opus 5.5).
- Log per call: `usage.input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, and `response.model`.
- Sonnet 5.5 / Opus 5.5 reject non-default temperature → no temperature=0 determinism; keep seeds + a
  response cache/replay so reports are reproducible without re-spending.
- Prompt caching minimum prefix on Haiku 4.5 is 4096 tokens (shorter prefixes silently don't cache).
- Probe answering at checkpoints is batchable (Message Batches API, ~50% cost).
- Python: the brief says 3.12 via uv; `uv python install 3.12` works without Homebrew.
