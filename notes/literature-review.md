# Literature review: memory structure for long-running AI agents in R&D workflows

*Compiled 2026-09-30. Scope: alternatives to context compaction, structured agent memory,
and how AI research agents track hypotheses/experiments/results across sessions.*

> **Verification status — read before citing.** The environment that produced this review
> could not open arxiv.org, Semantic Scholar, OpenReview or ACL Anthology. Titles, IDs and
> numbers were confirmed from search-engine listings of those pages, or by opening the
> project's GitHub repo / vendor page directly. Items marked ⚠ are only partly verified.
> Many 2026 entries are recent preprints, not peer-reviewed. **Open every arXiv link and
> check the numbers before putting a citation in the paper.**

---

## TL;DR

1. **Naive compaction (rewrite-the-history summarization) is well documented as lossy and
   often not cost-effective.** It is blind to future needs, compounds loss when summaries
   are re-summarized ("context collapse"), drops standing constraints, hides failure
   signals, and invalidates the KV/prompt cache. Simple *reversible* pruning (masking old
   tool outputs) matches it at lower cost.
2. **But trained / model-native compaction works.** OpenAI (Codex-Max), Anthropic (server
   compaction), and RL papers (MEM1, FoldGRPO, CompactionRL, ACON) report real gains. The
   argument "compaction is bad" only holds for untrained, full-rewrite summarization.
3. **Best-supported pattern:** keep raw episodes losslessly, build a structured, typed,
   time-aware index over them, update memory with **incremental itemized deltas** (not
   rewrites), and keep durable state (plan, constraints, progress) in files that survive
   any compaction.
4. **No memory substrate dominates** (flat vs. hierarchical vs. graph). Graphs help on
   multi-hop, temporal and "what superseded what" questions; plain dense retrieval or
   even grep-over-files is a very strong baseline.
5. **Record *form* matters more than retrieval.** Raw transcripts pollute context;
   atomic LLM-extracted facts over-generalize. Bounded, typed records win (VibeMemBench,
   Negative Knowledge, MOOSEDev).
6. **R&D agents today mostly remember artifacts and scores, not knowledge.** Memory usually
   dies with the run. Decisions/rationale, claim status (supported/refuted/superseded),
   negative results and *invalidation when code/data change* are rarely tracked.
7. **Open space:** a typed, live, cross-session R&D memory schema
   (Question → Hypothesis → Experiment → Run → Result → Claim(status, scope) →
   Decision(rationale, supersedes) → Open question) with first-class negative results,
   provenance, dependency-based invalidation and re-validation before reuse — evaluated
   against flat CLAUDE.md / progress-file baselines. Pieces exist (ARA, Negative Knowledge,
   Agora, HEP, MOOSEDev, StatefulDiscovery); no one appears to combine and benchmark them.
8. **Evaluation is fragile.** LoCoMo is near-saturated and judge-sensitive; vendor numbers
   conflict; rankings flip by backbone model. There is no benchmark for multi-session R&D
   memory specifically.

---

## 1. Why compaction falls short

### 1a. Long contexts degrade (the reason to manage context at all)

| Work | Venue | Key finding |
|---|---|---|
| Lost in the Middle — Liu et al. | TACL 2024 · [link](https://aclanthology.org/2024.tacl-1.9/) | U-shaped accuracy: info in the middle of the context is used worst. |
| RULER — Hsieh et al. (NVIDIA) | COLM 2024 · [2404.06654](https://arxiv.org/abs/2404.06654) | Only ~half of models claiming ≥32K hold up at 32K on harder tasks. |
| NoLiMa — Modarressi et al. | ICML 2025 · [repo](https://github.com/adobe-research/NoLiMa) | 10/12 models fall below 50% of short-context score at 32K when needle and question share few words. |
| LongBench v2 — Bai et al. | ACL 2025 | Best direct model 50.1%, o1-preview 57.7%, human experts 53.7%. |
| Context Rot — Hong, Troynikov, Huber (Chroma) | 2025 · [page](https://www.trychroma.com/research/context-rot) | 18 models get less reliable as input grows, even on trivial tasks. |
| Diagnosing and Mitigating Context Rot in Long-horizon Search — Xia et al. | 2026 · [2606.29718](https://arxiv.org/abs/2606.29718) | "Premature termination" rises with context length, well before the window is full. |

### 1b. Evidence against summarization-style compaction

| Work | Venue | Key finding |
|---|---|---|
| **ACE: Agentic Context Engineering** — Zhang et al. (Stanford/SambaNova) | ICLR 2026 · [2510.04618](https://arxiv.org/abs/2510.04618) | Names **brevity bias** and **context collapse**: an 18,282-token context collapsed to 122 tokens in one rewrite; accuracy fell *below the no-memory baseline* (66.7→57.1 vs 63.7). Fix: itemized playbook with incremental delta updates. +10.6% agents, +8.6% finance. |
| **The Complexity Trap** — Lindenbauer et al. (JetBrains) | NeurIPS 2025 wksp · [2508.21433](https://arxiv.org/abs/2508.21433) | On SWE-bench Verified, masking old observations ≈ LLM summarization at ~half cost. Summaries hide failure signals → trajectories 13–15% longer. Hybrid (mask first, summarize last) is cheapest. |
| LongMemEval — Wu et al. | ICLR 2025 · [2410.10813](https://arxiv.org/abs/2410.10813) | Storing summaries/facts as *values* instead of raw sessions hurts QA. Use facts to augment *keys*, keep raw rounds as values. |
| Recursive Language Models — Zhang, Kraska, Khattab (MIT) | 2025 · [2512.24601](https://arxiv.org/abs/2512.24601) | Treat the prompt as a REPL variable the model inspects/recurses on; beats compaction by median 26% with GPT-5. |
| Governance Decay ⚠ | 2026 · [2606.22528](https://arxiv.org/abs/2606.22528) | Policy violations 0% → 30% (up to 59%) after compaction; "constraint pinning" restores 0%. |
| CliffCompaction — Nguyen, …, Dettmers | 2026 · [2609.26779](https://arxiv.org/abs/2609.26779) | Only truncate/drop, never rephrase; "never compact a compaction". Up to 50% cheaper on Terminal-Bench. |
| Beyond Compaction: Structured Context Eviction — Semenov, Dorofeev | 2026 · [2606.11213](https://arxiv.org/abs/2606.11213) | Agent tags typed, dependency-linked episodes; deterministic eviction. Evidence thin (one long session). |
| Slipstream | 2026 · [2605.08580](https://arxiv.org/abs/2605.08580) | "Validation gap": compactor can't know future needs; validate summary against the next k steps. +8.8 pp. |
| Context Compaction Theory — Tirmazi, …, Mitzenmacher | 2026 · [2608.01326](https://arxiv.org/abs/2608.01326) | Formal model; summary compaction ≡ one-way communication complexity → hard limits when future queries are unknown. |
| Parallel Context Compaction — Cim et al. (Penn State) | 2026 · [2605.23296](https://arxiv.org/abs/2605.23296) | Summarizer blocks inference for tens of seconds; length instructions largely ignored. |
| BooookScore — Chang et al. | ICLR 2024 · [2310.00785](https://arxiv.org/abs/2310.00785) | Hierarchical merging loses detail; incremental updating keeps detail but adds coherence errors. |
| Anthropic, *Effective harnesses for long-running agents* | Blog, Nov 2025 | "Compaction isn't sufficient"; use progress file + JSON feature list + git commits per session. |

### 1c. Where compaction still works (the counter-evidence)

| Work | Key finding |
|---|---|
| Anthropic, *Effective context engineering for AI agents* (Sep 2025) | Compaction for long back-and-forth; notes for milestone work; sub-agents for parallel research. Tune compaction prompt for recall first. Tool-result clearing is the safest form. |
| Anthropic, *Managing context on the Claude Developer Platform* (Sep 2025) | 100-turn web search: context editing +29%, + file-based memory tool +39%, −84% tokens. |
| OpenAI, GPT-5.1-Codex-Max (Nov 2025) ⚠ | Model natively trained to work across windows via compaction; 24h+ tasks. |
| Context-Folding / FoldGRPO — Sun et al., ICML 2026 · [2510.11967](https://arxiv.org/abs/2510.11967) | Branch-and-fold sub-trajectories; 10× smaller active context; beats summarization-based management. |
| AgentFold — Tongyi, ICLR 2026 · [2510.24699](https://arxiv.org/abs/2510.24699) | Multi-scale folding; 30B-A3B beats 671B model on BrowseComp. |
| ACON — Kang et al. (Microsoft), ICML 2026 | Optimizes compression guidelines from failure cases; −26–54% peak tokens. |
| ReSum · [2509.13313](https://arxiv.org/abs/2509.13313); CompactionRL · [2607.05378](https://arxiv.org/abs/2607.05378); SelfCompact · [2606.23525](https://arxiv.org/abs/2606.23525) | Trained / self-timed summarization gives gains on web and coding agents. |
| MEM1 · [2506.15841](https://arxiv.org/abs/2506.15841); MemAgent · [2507.02259](https://arxiv.org/abs/2507.02259) | RL-trained constant-size state works when the true task state is small. |

**Engineering write-ups worth reading:** Manus, *Context Engineering for AI Agents* (Jul 2025) —
KV-cache hit rate is the #1 metric; append-only context; file system as memory; only
*restorable* compression. Cognition, *Don't Build Multi-Agents* (Jun 2025). LangChain,
*Context Engineering for Agents* (write / select / compress / isolate). Anthropic,
*How we built our multi-agent research system* (+90% but ~15× tokens; poor fit for coupled tasks like coding).

---

## 2. Structured memory architectures for agents

### 2a. Foundational (2023–2024)

| Work | Venue | Memory structure | Key result |
|---|---|---|---|
| **MemGPT** — Packer et al. | 2023 · [2310.08560](https://arxiv.org/abs/2310.08560) | OS-style virtual context: core memory + FIFO queue in-context; recall (raw history) + archival (vector) storage out of context; the LLM pages via function calls. | 32.1% → 92.5% on deep memory retrieval. |
| **Generative Agents** — Park et al. | UIST 2023 · [2304.03442](https://arxiv.org/abs/2304.03442) | Memory stream; retrieval by recency × importance × relevance; reflection writes higher-level abstractions back. | Removing memory/reflection/planning each hurts. |
| **CoALA** — Sumers et al. | TMLR 2024 · [2309.02427](https://arxiv.org/abs/2309.02427) | Taxonomy: working vs. long-term episodic / semantic / procedural memory. | Conceptual; the standard reference. |
| MemoryBank — Zhong et al. | AAAI 2024 · [2305.10250](https://arxiv.org/abs/2305.10250) | Ebbinghaus-curve decay, reinforced on recall. | Small-scale. |
| Voyager — Wang et al. | TMLR 2024 · [2305.16291](https://arxiv.org/abs/2305.16291) | Procedural memory as a library of code skills. | 15.3× faster tech-tree progress in Minecraft. |
| ExpeL — Zhao et al. | AAAI 2024 · [2308.10144](https://arxiv.org/abs/2308.10144) | Extracts natural-language "insights" (add/edit/vote) from trajectories. | Beats ReAct/Reflexion ⚠. |
| RAPTOR — Sarthi et al. | ICLR 2024 · [2401.18059](https://arxiv.org/abs/2401.18059) | Recursive cluster-and-summarize tree. | +20 pts on QuALITY. |
| GraphRAG — Edge et al. (Microsoft) | 2024 · [2404.16130](https://arxiv.org/abs/2404.16130) | Entity graph + community summaries. | Better on global "sensemaking" questions. |
| HippoRAG / HippoRAG 2 — Gutiérrez et al. | NeurIPS 2024 / ICML 2025 · [2405.14831](https://arxiv.org/abs/2405.14831), [2502.14802](https://arxiv.org/abs/2502.14802) | KG as "hippocampal index", Personalized PageRank. | HippoRAG 2 finds GraphRAG/RAPTOR/LightRAG *below* plain dense RAG on simple factual recall. |

### 2b. Conversational / personal memory systems (2025–2026)

| Work | Venue | Memory structure | Key result / caveat |
|---|---|---|---|
| **A-MEM** — Xu et al. | NeurIPS 2025 · [2502.12110](https://arxiv.org/abs/2502.12110) | Zettelkasten notes; LLM links new notes and *evolves* old ones. | Beats MemGPT/MemoryBank on LoCoMo with fewer tokens ⚠. Did *not* help on coding (VibeMemBench). |
| **Mem0** — Chhikara et al. | 2025 · [2504.19413](https://arxiv.org/abs/2504.19413) | Extract facts → ADD/UPDATE/DELETE/NOOP; optional graph (Mem0g). | 66.9% vs OpenAI 52.9% on LoCoMo; **but full context scored 72.9%** (at 17 s p95). Graph adds ~2 pts. |
| **Zep / Graphiti** — Rasmussen et al. | 2025 · [2501.13956](https://arxiv.org/abs/2501.13956) | Bi-temporal KG: episodes → facts → communities; facts *invalidated*, not deleted. | +18.5% on LongMemEval, −90% latency. |
| MemoryOS — Kang et al. | EMNLP 2025 · [2506.06326](https://arxiv.org/abs/2506.06326) | Short/mid/long-term tiers, heat-based promotion. | +49% F1 on LoCoMo. |
| MemOS — Li et al. | 2025 · [2507.03724](https://arxiv.org/abs/2507.03724) | "MemCubes" unify text, KV and LoRA memory with provenance and versioning. | +39% overall vs OpenAI memory. |
| MIRIX — Wang & Chen | 2025 · [2507.07957](https://arxiv.org/abs/2507.07957) | Six typed stores, each with its own agent. | 85.4% LoCoMo. |
| LightMem — Fang et al. | ICLR 2026 · [2510.18866](https://arxiv.org/abs/2510.18866) | Sensory filter → topic STM → offline "sleep-time" LTM. | Up to 117× fewer tokens. |
| Hindsight — Latimer et al. | 2025 · [2512.12818](https://arxiv.org/abs/2512.12818) | Separate networks for world facts, experiences, entities, **beliefs**; evidence kept apart from belief. | 91.4% LongMemEval. |
| **GAM (General Agentic Memory)** — Yan et al. | 2025 · [2511.18423](https://arxiv.org/abs/2511.18423) | Just-in-time: lossless page-store + light index; a researcher agent searches at query time. Argues pre-organized memory is inherently lossy. | Beats memory baselines. |
| Sleep-time Compute — Lin, …, Packer (Letta) | 2025 · [2504.13171](https://arxiv.org/abs/2504.13171) | Offline consolidation between queries. | ~5× less test-time compute. |
| SimpleMem · [2601.02553](https://arxiv.org/abs/2601.02553); FluxMem · [2602.14038](https://arxiv.org/abs/2602.14038) ⚠ | 2026 | FluxMem *learns to choose* among memory structures per interaction. | "No single structure fits all." |

### 2c. Learned memory management (RL)

- **Memory-R1** ([2508.19828](https://arxiv.org/abs/2508.19828), ACL 2026): RL-trained ADD/UPDATE/DELETE/NOOP from 152 examples; +48% F1 over Mem0.
- **Mem-α** ([2509.25911](https://arxiv.org/abs/2509.25911)): RL writes to core/semantic/episodic stores; trained at 30K, generalizes to 400K+.
- **MEM1** ([2506.15841](https://arxiv.org/abs/2506.15841), ICLR 2026): learned compaction to a constant-size state.

### 2d. Experiential / procedural memory

- **Agent Workflow Memory** ([2409.07429](https://arxiv.org/abs/2409.07429), ICML 2025): reusable workflows induced from trajectories; +51% WebArena.
- **ReasoningBank** ([2509.25140](https://arxiv.org/abs/2509.25140), ICLR 2026): distills strategies from **successes *and* failures**; beats raw-trajectory memory.
- **Memp** ([2508.06433](https://arxiv.org/abs/2508.06433), ACL 2026): step-level + script-level procedural memory.
- **Dynamic Cheatsheet** ([2504.07952](https://arxiv.org/abs/2504.07952), EACL 2026): evolving cheatsheet — but its full-rewrite curator is what ACE shows can collapse.

### 2e. Surveys

- Zhang et al., *A Survey on the Memory Mechanism of LLM-based Agents*, ACM TOIS 2025 · [2404.13501](https://arxiv.org/abs/2404.13501)
- Du et al., *Rethinking Memory in AI* · [2505.00675](https://arxiv.org/abs/2505.00675) — six operations: consolidation, updating, indexing, forgetting, retrieval, compression.
- Hu et al., *Memory in the Age of AI Agents: A Survey* (Dec 2025) · [2512.13564](https://arxiv.org/abs/2512.13564) — broadest current survey.
- *A Survey of Agent Memory in the Second Half* (2026) · [2602.06052](https://arxiv.org/abs/2602.06052)

---

## 3. Memory in AI research (R&D) agents

### 3a. How existing systems structure research memory

| System | Memory structure | Persists across runs? |
|---|---|---|
| AI Scientist v1 — Lu et al. (Sakana) · [2408.06292](https://arxiv.org/abs/2408.06292) | Flat `ideas.json` archive + `run_i/` folders + free-text `notes.txt`. | No |
| AI Scientist v2 — Yamada et al. · [2504.08066](https://arxiv.org/abs/2504.08066) | Experiment *tree*: nodes hold plan, code, analysis, metric, `is_buggy`. | No |
| AI co-scientist — Gottweis et al. (Google) · [2502.18864](https://arxiv.org/abs/2502.18864) | "Context memory" of hypothesis pool, reviews, Elo tournament; meta-review feedback appended to prompts. | Per research goal |
| Kosmos — Mitchener et al. (Edison) · [2511.02824](https://arxiv.org/abs/2511.02824) | Shared "structured world model" updated after every task; every claim traced to code or paper. Schema not public ⚠. | Within run (≤12h) |
| Agent Laboratory · [2501.04227](https://arxiv.org/abs/2501.04227) + AgentRxiv · [2503.18102](https://arxiv.org/abs/2503.18102) | Phase checkpoints; AgentRxiv = shared preprint server as cross-lab memory. | AgentRxiv: yes |
| DeepScientist · [2509.26603](https://arxiv.org/abs/2509.26603) | Cumulative "Findings Memory" driving a Bayesian-optimization loop (~1 month). | Yes |
| EvoScientist · [2603.08127](https://arxiv.org/abs/2603.08127) | Ideation memory (incl. **failed directions**) + experimentation memory. | Yes |
| AutoSci · [2605.31468](https://arxiv.org/abs/2605.31468) | "SciMem": schema-governed markdown wiki with typed pages (papers, ideas, experiments, claims, failure logs) + graph edges. | Yes |
| Arbor (Microsoft) · [2606.11926](https://arxiv.org/abs/2606.11926) | Persistent hypothesis tree linking hypotheses, artifacts, evidence, insights. | Yes |
| StatefulDiscovery · [2606.11851](https://arxiv.org/abs/2606.11851) | Observations, investigations, evidence, and **evidential status** of each claim. | — |
| HEP · [2607.09195](https://arxiv.org/abs/2607.09195) | Explicit, auditable hypothesis → test → evidence → belief-update cycle. | — |
| AlphaEvolve · [2506.13131](https://arxiv.org/abs/2506.13131); AIDE · [2502.13138](https://arxiv.org/abs/2502.13138) | Program database / solution tree with scores. | No |
| **Agora** (NVIDIA) · [2609.18094](https://arxiv.org/abs/2609.18094) | Append-only **git DAG**: every result, failure, hypothesis, reproduction is a commit; SQLite index shows frontier and contested verifications. | Yes |
| **Negative Knowledge** · [2606.21024](https://arxiv.org/abs/2606.21024) | Failures as typed JSON (route, observation, failure layer/scope, recommended alternative); agents must adopt/reject them before proposing. | Yes |
| VERDI · [2608.09537](https://arxiv.org/abs/2608.09537) | "Retrieval is not transfer": re-validate retrieved experience before reuse; negative transfer 0.34 → 0.06. | — |
| Karpathy *autoresearch* (Mar 2026) | git branch + `results.tsv` (commit, metric, keep/discard/crash). | Yes |

### 3b. Claim / evidence / provenance records

- **ARA — Agent-Native Research Artifact** ([2604.24658](https://arxiv.org/abs/2604.24658)): `logic/` claim graph, `trace/` exploration DAG with **dead ends as nodes**, `evidence/`, provenance tags (user / ai-suggested / ai-executed / user-revised). QA 72.4% → 93.7%.
- **Symposium** ([2608.19511](https://arxiv.org/abs/2608.19511)): immutable community record of claims, evidence, hypotheses, assumptions.
- **From Fluent to Verifiable (AAR)** ([2602.13855](https://arxiv.org/abs/2602.13855)): metrics for provenance coverage and contradiction transparency.
- **PROV-AGENT** ([2508.02866](https://arxiv.org/abs/2508.02866), IEEE eScience 2025): W3C PROV extended to agent actions.
- **MOOSEDev** ([2608.13662](https://arxiv.org/abs/2608.13662), coding): decisions, lessons, constraints with **lifecycle status and supersession links**; 0.98–1.00 on supersession queries vs 6–27% for top-k retrieval.

### 3c. Project memory files (CLAUDE.md / AGENTS.md)

- *Evaluating AGENTS.md* — Gloaguen et al. ([2602.11988](https://arxiv.org/abs/2602.11988)): context files don't generally improve success and raise cost >20%.
- **VibeMemBench** ([2609.23570](https://arxiv.org/abs/2609.23570)): verified past experience helps (+1.1–4.5 pts), but MemoryOS, A-MEM, Mem0, SimpleMem failed to beat memory-off in 11/12 pairings — **record form, not retrieval, is the problem.**
- Karpathy *LLM Wiki* gist (Apr 2026): immutable `raw/` + LLM-maintained `wiki/` + schema file; ingest / query / lint (lint = contradictions, stale claims, orphans).

### 3d. Benchmarks bearing on R&D memory

- MLAgentBench (ICML 2024): reference agent keeps a "Research Plan and Status" with *only confirmed results* + a "Fact Check" — the cleanest early lab-notebook discipline.
- RE-Bench (METR, [2411.15114](https://arxiv.org/abs/2411.15114)): agents 4× humans at 2h, humans 2× agents at 32h — signature of weak long-horizon accumulation.
- *Beyond Final Scores* ([2608.13417](https://arxiv.org/abs/2608.13417)): experience reuse "can help or mislead".
- *Why LLMs Aren't Scientists Yet* ([2601.03315](https://arxiv.org/abs/2601.03315)): memory/context degradation is one of six recurring failure modes.
- PaperBench, MLE-bench (OpenAI).

---

## 4. Memory benchmarks and evaluation caveats

| Benchmark | Notes |
|---|---|
| LoCoMo · [2402.17753](https://arxiv.org/abs/2402.17753) | ~300 turns, up to 35 sessions. **Near-saturated and judge-sensitive.** |
| LongMemEval · [2410.10813](https://arxiv.org/abs/2410.10813) | 500 Qs: extraction, multi-session, temporal, knowledge updates, abstention. |
| MemoryAgentBench · [2507.05257](https://arxiv.org/abs/2507.05257) | Selective forgetting fails for every method (multi-hop ~7%). |
| BEAM · [2510.27246](https://arxiv.org/abs/2510.27246) | Up to 10M-token conversations. |
| MemoryArena · [2602.16313](https://arxiv.org/abs/2602.16313) ⚠ | Agents that saturate LoCoMo do poorly on interdependent multi-session tasks. |
| Evo-Memory · [2511.20857](https://arxiv.org/abs/2511.20857) | Streaming experience reuse. |

Warnings: *Anatomy of Agentic Memory* ([2602.19320](https://arxiv.org/abs/2602.19320)) — saturation,
judge sensitivity, ignored maintenance cost. *Harness the Memory* ([2608.15008](https://arxiv.org/abs/2608.15008)) —
no substrate dominates; broad retrieval helps QA but hurts sequential decisions. *MemDelta*
([2606.29914](https://arxiv.org/abs/2606.29914)) — rankings flip by backbone; embedding choice alone moves ±6 pts;
agent-managed memory (42%) < basic retrieval (47%). Letta's *Is a Filesystem All You Need?* —
grep over files scores 74% on LoCoMo, above Mem0g. Zep vs Mem0 dispute over LoCoMo numbers (vendor blogs).

---

## 5. Gaps — where a new contribution could sit

1. **No shared R&D memory schema.** Every system invents its own record types; none agree on
   hypothesis / experiment / run / result / claim / decision.
2. **Decisions and rationale are rarely stored** (why a direction was chosen or dropped; what
   superseded what). Only MOOSEDev models supersession, and only for coding.
3. **Claim status and scope** (supported / refuted / superseded / regime-bound) appear only in
   HEP, StatefulDiscovery, Negative Knowledge.
4. **Negative results became first-class only in 2026** and are still rare.
5. **Most AI-scientist memory dies with the run.**
6. **Nobody tracks invalidation**: when code, data or an assumption changes, no system flags
   which stored results are now stale (build-system-style dependency tracking).
7. **Reuse without re-validation misleads** (VERDI, Beyond Final Scores).
8. **No benchmark for multi-session R&D memory** — e.g. can a fresh session reconstruct *why*
   direction X was dropped, or avoid re-running a known failure?
9. **No head-to-head** of compaction vs. masking vs. retrieval vs. structured memory on the same
   long-horizon agentic benchmark.

---

## 6. Suggested reading order (top 12)

1. Anthropic — *Effective context engineering for AI agents* (2025)
2. ACE — [2510.04618](https://arxiv.org/abs/2510.04618)
3. The Complexity Trap — [2508.21433](https://arxiv.org/abs/2508.21433)
4. LongMemEval — [2410.10813](https://arxiv.org/abs/2410.10813)
5. MemGPT — [2310.08560](https://arxiv.org/abs/2310.08560)
6. CoALA — [2309.02427](https://arxiv.org/abs/2309.02427)
7. Zep — [2501.13956](https://arxiv.org/abs/2501.13956)
8. Hu et al. survey — [2512.13564](https://arxiv.org/abs/2512.13564)
9. VibeMemBench — [2609.23570](https://arxiv.org/abs/2609.23570)
10. ARA — [2604.24658](https://arxiv.org/abs/2604.24658)
11. Negative Knowledge — [2606.21024](https://arxiv.org/abs/2606.21024)
12. Kosmos — [2511.02824](https://arxiv.org/abs/2511.02824)

---

## Not verified / follow-ups

- Exact numbers for A-MEM tokens, ExpeL, FluxMem, SelfCompact; venues of LoCoMo, MemoryArena, Evo-Memory.
- Kosmos world-model schema; OpenAI / Gemini Deep Research memory internals; SciAgents (not searched).
- Titles seen but not checked: 2511.21726 (*Goal-Directed Search Outperforms Goal-Agnostic Memory
  Compression*), 2606.05250, 2606.12329 (PROJECTMEM), 2606.30911, 2609.17631, 2606.31478, 2609.01526.
- arXiv 2606.18874 appears under two different titles — check before citing.
- Governance Decay (2606.22528) authors not verified.
- Nanopublications / micropublications / FAIR as agent *working* memory: nothing found, but the
  search budget ran out — absence not confirmed.
