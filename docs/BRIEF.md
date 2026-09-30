# EIM toy model: build brief for Claude Code

*30 September 2026 · Olivier · companion document: PAPER.md (design rationale)*

## Goal

Build a small, runnable Python system that replays a synthetic 12-week research campaign, then the recorded history of a real PCB placement-and-routing campaign, through three memory designs and shows, with probe accuracy and token logs, that Epistemic Index Memory (EIM) keeps details and dependencies that a rolling summary loses.

**The toy must demonstrate three things:**

1. **Detail fidelity.** After several consolidation cycles, EIM still answers qualifier questions (stack pressure, calibration, scope) that the summary baseline has dropped.
2. **Dependency correctness.** When a calibration is invalidated, EIM returns exactly the observations and claims that depended on it, and reopens the dormant hypothesis that was pruned because of it.
3. **Promotion safety.** An automated interpretation (a "new phase" from an XRD fit) is never promoted to a validated claim without independent evidence.

**Success criterion:** one command runs all systems on the same seed and produces a report where points 1 to 3 are visible in the numbers, with token cost per system.

**Non-goals:** real scientific data, a UI, a vector database, a full domain ontology, concurrency between real agents, production hardening. Keep the codebase small enough to read in an afternoon.

## Scenario: a synthetic 12-week campaign

A seeded generator creates a hidden ground truth and about 120 events (roughly 10 per simulated week) that mimic a solid-electrolyte campaign; everything the probes ask is computable from the ground truth, so scoring needs no human.

**Ground truth (hidden from the memory systems):**

- A base garnet electrolyte and three dopants. Dopant D truly raises conductivity; dopant E truly raises it too; dopant F has no effect.
- About 30 samples (S-01 to S-30), each with dopant, dopant level, synthesis batch, stack pressure (MPa), electrode type, temperature and calibration id (CAL-1 to CAL-4).
- Measured conductivity = true value × pressure effect × noise, except that CAL-3 (used in weeks 2 to 7) under-reads by a fixed factor. Most dopant-E samples are measured on CAL-3, so E looks useless until week 8.
- Three dendrite-mechanism hypotheses: H2a mechanical cracks, H2b electronic conductivity, H2c interface leakage. The true answer is "electronic leakage at defects and interfaces, not in the bulk".

**Event types:** each event has structured fields plus 150 to 400 words of prose that repeats the qualifiers, so a summariser is under real pressure.

| Type | Carries | Example |
| --- | --- | --- |
| measurement | Sample, protocol, conditions, calibration id, value with uncertainty | "S-17, 60 MPa, blocking Au electrodes, CAL-2: 1.4 mS/cm ± 0.2" |
| simulation | Method, assumptions, scope, result | "DFT, bulk only: electronic conductivity negligible" |
| literature | Source id, claim, scope, method | "Operando profiling: lithium deposits inside the bulk" |
| synthesis | Batch, recipe, automated phase identification with fit quality | "Batch B-9: new phase P, fit residual high" |
| calibration notice | Calibration id, what was wrong, affected period | "CAL-3 geometry factor wrong, weeks 2 to 7" |
| composition analysis | Batch, method, result | "B-9 composition matches known phase Q" |

**Scripted perturbations:** these must happen at the stated weeks in every seed.

| Week | Event | Correct memory behaviour |
| --- | --- | --- |
| 3 | S-17 measured high on CAL-2, with unusual stack pressure | Keep pressure and electrodes attached to the observation |
| 4 | Dopant E looks ineffective (CAL-3 data) | Weekly pass may prune E to dormant, storing CAL-3 observations as the justification |
| 5 | Literature: lithium inside the bulk | Supports H2b |
| 6 | Simulation: bulk electronic conductivity negligible; defects or surfaces suspected | Split H2b into H2b-bulk (refuted, scope bulk) and H2b-defect (under test) |
| 8 | Calibration notice: CAL-3 wrong | Flag every CAL-3 observation, revert dependent claims to contested, reactivate E |
| 10 | Automated XRD reports new phase P | Store as interpretation with low confidence, never as validated |
| 11 | Composition analysis: P is known phase Q | Refute the new-phase interpretation |

**Probes:** about 50 questions with gold answers, asked at the end of weeks 4, 8 and 12.

| Category | Example | Gold answer type |
| --- | --- | --- |
| Detail recall | What stack pressure was S-17 measured at? | Exact value |
| Provenance | Which observations support the claim that D raises conductivity? | Set of ids |
| Dependency impact | Which observations and claims depend on CAL-3? | Set of ids |
| Status with scope | What is the status of the electronic-conductivity hypothesis, and in what scope? | Status plus scope |
| Reactivation | Which pruned hypotheses should be reconsidered after week 8? | Set of ids |
| Promotion safety | Is phase P a new material? | No, with the reason |

## Memory systems

All systems implement one interface and see the same events in the same order; only the memory differs.

```python
class MemorySystem(Protocol):
    name: str
    def ingest(self, event: Event) -> None: ...
    def end_of_day(self, day: int) -> None: ...
    def end_of_week(self, week: int) -> None: ...
    def answer(self, probe: Probe) -> Answer: ...  # Answer(text, cited_ids, tokens)
    def stats(self) -> dict: ...
```

| System | Behaviour | Role |
| --- | --- | --- |
| `summary` | One rolling summary, capped at a token budget (default 1,500), rewritten by the LLM at end of day; probes answered from the summary only | Main baseline: shows compaction loss |
| `fullcontext` | Raw events concatenated; oldest dropped beyond a window budget (default 50,000 tokens) | Upper bound early, degrades late |
| `eim` | Full design: typed graph, lossless document store, nightly and weekly passes, dependency propagation | The system under test |
| `eim-summarydocs` | EIM, but the nightly pass replaces each document with its summary | Ablation for claim 1 |
| `eim-notms` | EIM without dependency propagation or reactivation | Ablation for claim 2 |
| `eim-onetier` | One model does nightly and weekly work every night | Ablation for claim 3 |
| `eim-fifo` | EIM with FIFO eviction of open documents | Ablation for the eviction choice |
| `current-practice` | Answers only from the latest handover file and the hand-maintained map (Track B only) | Real-world baseline: how the PCB campaign works today |

Ablations are config flags on `eim`, not separate code paths.

## EIM toy specification

The LLM proposes; deterministic code stores, validates and propagates. No LLM output ever writes to the document store or the graph without passing validation.

### Data model

| Object | Fields |
| --- | --- |
| Node | `id`, `type`, `label` (12 words max, regenerable), `status`, `uncertainty` (`level` low/medium/high, `basis` text), `doc_ref` (doc id + revision), `aliases`, `created_week` |
| Edge | `src`, `dst`, `type`, `state` (proposed or accepted), `created_by` (agent or pass name) |
| Status change | `node`, `from`, `to`, `justified_by` (node ids), `by` (tier), `at` (day) |
| Graph version | Snapshot of nodes, edges and status log, plus a diff against the previous version |

**Node types:** question, hypothesis, prediction, experiment, simulation, sample, protocol, calibration, dataset, observation, interpretation, evidence, claim, knowledge, decision.

**Edge types:** addresses, predicts, tests, produced-by, calibrated-by, derived-from, supports, contradicts, depends-on, supersedes, alias-of.

**Statuses:** proposed, active, supported, contested, refuted, dormant, validated, superseded.

### Stores

- **Document store:** `data/docs/<node_id>/rev-0001.md`, append-only. Observation documents are write-once and hold the raw event text verbatim.
- **Graph store:** `data/graph/v0001.json` plus `v0001.diff.json`. Every pass reads version N and writes version N+1; it never edits N.

### Invariants (each is a test, checked after every pass)

1. **I1 content invariance:** a nightly, weekly or event pass never changes the document store.
2. **I2 provenance:** every observation has a produced-by edge and, if measured, a calibrated-by edge; every supported claim reaches at least one observation through supports edges.
3. **I3 justified status:** every status other than proposed has a non-empty `justified_by`.
4. **I4 no deletion:** nodes are never removed; dormant, refuted and superseded nodes stay in the graph.
5. **I5 regenerable view:** the context view is a pure function of the graph version, the focus and the budget.

### Dependency propagation (deterministic)

```python
def on_withdraw(x):  # x refuted, retracted, or calibration invalidated
    for v in dependants(x):  # reverse closure over depends-on, derived-from, calibrated-by, supports
        if v.status in {"active", "supported", "validated"}:
            set_status(v, "contested", justified_by=[x])
    for d in dormant_nodes():
        if x in d.justification:
            d.justification.remove(x)
            if not d.justification:
                mark_reactivation_candidate(d)
```

### Context view and eviction

- `build_view(focus_ids, budget_tokens)`: focus nodes and their 2-hop justification neighbourhood in full (id, type, status, uncertainty, label); everything else collapsed to one line per question and hypothesis family with status counts. Token estimate: characters divided by 4.
- Open documents: the focus node's document, the hypothesis under test and its protocol are pinned; others are evicted by graph distance from the focus, then least recent use. The `eim-fifo` ablation swaps in FIFO.
- Retrieval for probes: BM25 over node labels and document text, then the view around the top hits, then up to 5 documents opened.

### Passes

| Pass | Model tier | Input | Output (JSON ops, validated) |
| --- | --- | --- | --- |
| Ingest (per event) | Agent | Event + view around related nodes | New nodes (observation doc = raw event text), proposed edges |
| Nightly | Small | The day's diff + neighbourhood | Accept or reject proposed edges; alias merges; contradiction flags; label refresh. Code then runs propagation |
| Weekly | Large | Collapsed whole-graph view, nightly flags, flagged documents | `split`, `merge`, `prune`, `reactivate`, `open_question`, `promote_request` |
| Event | Code, then small | Calibration notice or retraction | Immediate propagation; may request an early weekly pass |
| Human gate | Simulated rule | Promotion requests | Approve only with 2 or more supporting observations from different calibrations and no open contradiction |

## LLM usage

Every LLM call goes through one client wrapper with a mock mode, so the whole pipeline runs offline in tests and only the evaluation runs cost tokens.

| Tier | Default model (config) | Used for |
| --- | --- | --- |
| Agent | `claude-haiku-4-5-20251001` | Ingest, probe answering |
| Nightly | `claude-haiku-4-5-20251001` | Edge review, alias merges, contradiction flags |
| Weekly | `claude-sonnet-5-5` (try `claude-opus-5-5` as a variant) | Portfolio restructuring |
| Judge | `claude-sonnet-5-5` | Optional scoring of free-text reasons only |
| Summary baseline | Same as agent | Rolling summary rewrite |

Model ids live in `config.yaml`; check them against Anthropic's current documentation before the first paid run.

- **Client:** official `anthropic` Python SDK, key from `ANTHROPIC_API_KEY`.
- **Mock mode:** a rule-based responder that reads a hidden `_oracle` field on each event (present only in mock runs) and returns the correct ops. It exists to test plumbing and invariants, not to produce results.
- **Structured outputs:** each prompt asks for JSON matching a pydantic model; on a validation error, retry once with the error message, then skip and log.
- **Prompts:** plain files in `prompts/`, one per pass, versioned with the code.
- **Token logging:** every call appends tier, model, input and output tokens and latency to `runs/<run_id>/calls.jsonl`.
- **Budget guard:** a per-run token cap in config; the run stops cleanly when it is reached.

## Evaluation harness and report

One command runs every configured system on the same seed, scores all probes deterministically where possible, and writes a single markdown report.

- **Scoring:** exact match for values, set F1 for id sets, status and scope matched as fields. The LLM judge scores only the free-text "why" part, and its score is reported separately.
- **Repeats:** 3 seeds by default; report mean and range.
- **Invariant log:** invariant violations per system per pass (should be zero for `eim`).

**Report contents (`runs/<run_id>/report.md`):**

1. Accuracy by probe category × system × checkpoint week (4, 8, 12), as a table.
2. A line chart of detail-recall accuracy over the checkpoints, one line per system.
3. Tokens per system and per tier, with calls and latency.
4. Three failure traces from the summary baseline: the probe, the gold answer, what the summary said, and the event it came from.
5. The week-8 CAL-3 case in full for `eim`: flagged nodes, reverted claims, reactivated hypotheses, and the graph diff.

**Expected pattern (to confirm, not to force):** `summary` drops on detail recall and dependency probes after week 4; `eim-notms` fails reactivation; `eim-summarydocs` behaves like `summary` on qualifiers; `eim` stays flat.

## Real campaign: the PCB repository (Track B)

Track B replays a real campaign, the BConnect PCB placement engine, whose goal is a placement method that generalises across a corpus of boards. The EIM repository reads it as data and never writes to it.

### Reference

| Item | Value |
| --- | --- |
| Repository | BConnect PCB placement engine (remote URL: add before starting) |
| Branch to use | `origin/codex/stickhub-stiffness-pilot` at `e558eaa` (pseudonymised, pushed) |
| Newer local work | Head `14388e7` at the 29 to 30 September snapshot, not pushed: use only once scrubbed and pushed |
| Live view | [StickHub Convergence Map](https://claude.ai/artifact/5PfjXNa2NooWaFqF6sF4VD) |
| Plan and reviews | `docs/PLAN-2026-09-29-best-of-pipeline.md`, `docs/REVIEW-2026-09-29-best-of-pipeline.md`, the 30 September review (commit `4846bba`) |
| Handover | `docs/HANDOVER-2026-09-29-CLAUDE-EXPERIMENTS.md`, `benchmarks/handover/2026-09-29-claude-takeover.json` |
| Results | `docs/RESULTS-2026-09-*.md`, one file per task |
| Latest safe checkpoint | `archive/experiments/stickhub-thermal-padface/run1/05-D1-1/c0/q/refilled.kicad_pcb` |
| Boards | StickHub (under study); PIC, Multichannel, Sonde (regression boards) |

### Rules

- **Read-only.** Clone the branch into `data/pcb-repo/` (git-ignored). Never commit, push or run the PCB pipeline from the EIM repository.
- **Confidentiality.** Work only from the pseudonymised branch; reports quote ids and commit hashes, never client names.
- **Owner gate.** The PCB campaign's standing rule applies: any drift from its plan goes to the owner. The pilot proposes a map; it never executes PCB tasks.

### From repository to events

| Source | Becomes |
| --- | --- |
| Commit | Provenance: hash, time, author role (owner, reviewer, executor) |
| RESULTS file | An experiment with its observations (error counts, router calls, replay status) and the status changes it reports |
| PLAN file | Questions, hypotheses, planned experiments, priorities |
| REVIEW file | Decisions and status changes with justification; splits and relabels |
| HANDOVER file, takeover JSON | An agent-handover event; its inventory becomes a checkpoint |
| Legality-model, gate or rule change | A calibration node (epoch); each result is tagged with the epochs it ran under |

`eim-toy pcb-extract --repo data/pcb-repo --ref e558eaa` writes an ordered event stream that the harness replays like the synthetic scenario.

### Probes and baseline

- **Probes:** about 40, drawn from past review questions, with gold answers signed off by the owner: hypothesis status and scope, results affected by an epoch change, the latest safe checkpoint, boards backing a corpus-level claim, decisions awaiting the owner.
- **`current-practice` baseline:** answers only from the latest handover file and the convergence-map text, as the campaign does today.

## Tech stack and repository layout

Python 3.12 managed with `uv`; `pydantic` for every data object, `networkx` for graph algorithms, `rank-bm25` for retrieval, `typer` for the CLI, `pytest` for tests, `matplotlib` for the report chart. Storage is plain files (JSON and markdown), so every run can be inspected and diffed with git.

```text
eim-toy/
  CLAUDE.md              conventions for Claude Code
  docs/BRIEF.md          this brief
  docs/PAPER.md          the paper draft (design rationale)
  config.yaml            models, budgets, seeds, ablation flags
  prompts/               one prompt file per pass
  eim_toy/
    models.py            Node, Edge, StatusChange, Event, Probe, Answer
    store/docs.py        append-only document store, write-once observations
    store/graph.py       versioned graph, copy-on-write, diffs
    tms.py               dependants(), on_withdraw(), reactivation
    view.py              build_view(), eviction policies
    invariants.py        I1 to I5 as functions
    passes/              ingest.py, nightly.py, weekly.py, event.py, gate.py
    memory/              eim.py, summary.py, fullcontext.py
    scenario/            world.py, generate.py, probes.py
    pcb/                 extract.py (repo history to events), gold.py, mapview.py
    llm/                 client.py (real + mock), budget.py
    eval/                harness.py, metrics.py, report.py
    cli.py
  tests/                 one test file per module, plus test_invariants.py
  data/                  generated scenarios and the PCB repo clone (git-ignored)
  runs/                  run outputs and reports (git-ignored)
```

**CLI:**

```bash
eim-toy scenario --seed 7                 # write events, ground truth, probes
eim-toy run --system eim --seed 7         # one system, one seed
eim-toy run --all --seeds 7,8,9           # everything in config
eim-toy report --run <run_id>             # build report.md
eim-toy pcb-extract --repo data/pcb-repo --ref e558eaa   # PCB history to events
```

## Milestones

Nine milestones, each closed by its acceptance test; M1 and M2 need no API key, which keeps the expensive part until the plumbing is proven.

- [ ] **M0 Scaffold.** uv project, CLI skeleton, config loading, mock LLM client, CI running pytest. *Accept:* `pytest` green; `eim-toy --help` lists the commands.
- [ ] **M1 Core EIM, no LLM.** Models, document store, versioned graph with diffs, `tms.py`, `view.py`, `invariants.py`. *Accept:* unit tests for I1 to I5; a hand-built graph where invalidating CAL-3 returns exactly the expected dependent set and reactivates dormant dopant E; a view never exceeds its budget.
- [ ] **M2 Scenario and probes.** Generator, ground truth, about 120 events, about 50 probes with gold answers. *Accept:* the same seed produces byte-identical files; every perturbation from the scenario table appears in its week; every gold answer is computed from the ground truth.
- [ ] **M3 Baselines.** `summary` and `fullcontext` with the real LLM. *Accept:* weeks 1 to 4 complete on one seed; token log written; probes answered.
- [ ] **M4 EIM with LLM.** Ingest, nightly, weekly, event pass, simulated human gate. *Accept:* a full 12-week run on one seed with zero invariant violations; the week-8 CAL-3 trace is written.
- [ ] **M5 Evaluation and report.** Harness, metrics, report. *Accept:* `eim-toy run --all` then `eim-toy report` produces the report described above.
- [ ] **M6 Ablations.** The four ablation flags. *Accept:* each runs from config alone and appears in the report.
- [ ] **M7 Track B replay.** `eim_toy/pcb/` extractor, a gold graph for one review cycle built with the owner, the probes, the `current-practice` baseline. *Accept:* the event stream is byte-identical for the same commit; extractor recall against the gold graph is reported; every system runs on the replay.
- [ ] **M8 Live pilot.** At each PCB task boundary, regenerate the convergence map from the EIM graph beside the hand-maintained page and write a divergence report. *Accept:* two consecutive task boundaries with divergence reports reviewed by the owner.

## Working with Claude Code

Put this file in `docs/BRIEF.md` and the paper draft in `docs/PAPER.md`, then drive Claude Code one milestone at a time with a plan first and tests first.

1. **Kick-off prompt:** "Read docs/BRIEF.md (and docs/PAPER.md for the design rationale). Write CLAUDE.md with the conventions below, then propose a plan for M0 and M1 only. Do not write code until I approve the plan."
2. **Conventions for CLAUDE.md:** pydantic models for every structure crossing a module boundary; no LLM output written to a store without validation; invariants checked after every pass; each milestone ends with its acceptance test passing; small commits, one per milestone step.
3. **Tests before logic for M1:** ask for the invariant tests and the CAL-3 propagation test first, then the implementation.
4. **Mock first:** run M3 and M4 in mock mode end to end before the first paid run.
5. **Review points:** read the week-8 trace and three summary failure traces yourself before trusting the numbers.

**Open decisions for you:**

- [ ] Retrieval: BM25 only (default), or add embeddings as a variant?
- [ ] Weekly model: Sonnet by default, Opus as a variant, or the reverse?
- [ ] Event prose: template-only (default, reproducible) or LLM paraphrased (more realistic, less reproducible)?
- [ ] Scale: 120 events (default) or a longer 24-week variant to stress the summary further?
