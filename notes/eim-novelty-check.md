# EIM: is it already published, and does it hold up?

*2026-09-30. Checks `docs/PAPER.md` and `docs/BRIEF.md` against `notes/literature-review.md`.
Same verification caveat applies: arXiv pages could not be opened from the cloud session;
re-check every citation locally.*

## Verdict in one paragraph

The **combination** is not published as far as the review found, and the gap it targets is
real (see gaps 2, 3, 6, 8 in the literature review: no decision/supersession tracking, rare claim
status, **no invalidation when a dependency changes**, no benchmark for multi-session R&D memory).
But **claim 1 on its own (index lossily, store losslessly) is already well established** and
must be positioned as prior art you build on, not a contribution. The strongest, most defensible
contributions are **claim 2 (dependency-directed reactivation)** and **claim 5 (the
campaign-replay benchmark)**. Claim 3 is plausible but needs its ablations to carry it; claim 4
is the weakest and could be folded into the design section.

## Claim by claim

### Claim 1 — Index/store separation: **already published (as a principle)**

Close prior work the paper's related-work table does not yet cite:

| Work | What it already does |
|---|---|
| **GAM, General Agentic Memory via Deep Research** (Yan et al., 2025, arXiv 2511.18423) | Lossless page-store of raw history + lightweight index; argues *pre-organised memory is inherently lossy*. Almost the same thesis sentence. |
| **HippoRAG** (Gutiérrez et al., NeurIPS 2024, 2405.14831) | Explicitly built on **hippocampal memory indexing theory** (Teyler & DiScenna) — the same analogy PAPER.md §1.5 uses. |
| **MemGPT** (Packer et al., 2023, 2310.08560) | Raw "recall storage" outside context, paged in on demand. |
| **Zep / Graphiti** (2501.13956) | Lossless episode subgraph under an extracted fact graph (already in your table). |
| **LongMemEval** (ICLR 2025, 2410.10813) | Empirical result: store raw rounds as *values*, use extracted facts only to augment *keys*; summarised values hurt QA. This is evidence *for* your claim 1 — cite it as support. |
| **Hindsight** (2512.12818) | Keeps evidence separate from beliefs. |
| Manus (2025), Karpathy LLM Wiki (2026) | "Restorable compression" / immutable `raw/` + LLM-maintained wiki. |

**Recommendation:** reframe claim 1 as "we adopt index/store separation (GAM, HippoRAG, Zep) and
add the constraint that *consolidation may edit only the index*" — the I1 content-invariance rule
is the distinctive part, not the separation itself.

### Claim 2 — Epistemic typing + dependency propagation / reactivation: **partly published, the core is open**

Pieces exist, the combination with reactivation does not appear to:

| Work | Overlap | What it lacks vs EIM |
|---|---|---|
| **StatefulDiscovery** (2606.11851) | Evidential status per claim, calibrated against executed evidence | No reactivation of pruned hypotheses |
| **HEP** (2607.09195) | Explicit hypothesis → test → evidence → belief update | No propagation through calibrations |
| **ARA** (2604.24658) | Typed claim dependency graph; dead ends as first-class nodes | A publication/hand-off artifact, not live memory |
| **MOOSEDev** (2608.13662) | Lifecycle status + supersession links; 0.98–1.00 on supersession queries vs 6–27% top-k | Coding decisions, not scientific evidence; no reactivation |
| **Negative Knowledge** (2606.21024) | Typed failure records with scope | No dependency propagation |
| **VERDI** (2608.09537) | Re-validate retrieved experience before reuse | Retrieval-time, not structural |
| **Beyond Compaction: Structured Context Eviction** (2606.11213) | Typed, *dependency-linked* episodes | For context eviction, not epistemic status |
| **PROV-AGENT** (2508.02866) | W3C PROV for agent actions | Provenance only, no status |
| Zep | Invalidates contradicted facts | Not their dependants (your table already says this) |

**Recommendation:** this is the paper's strongest novelty. Add the five rows above to related
work. Make the TMS lineage (Doyle, de Kleer, Johnson & Shapiro) + "first application to LLM
research-agent memory with measured reactivation accuracy" the headline.

### Claim 3 — Multi-timescale, structure-only consolidation: **partly published**

Sleep-time compute (Letta, 2504.13171), LightMem's offline "sleep-time" LTM (ICLR 2026,
2510.18866) and the scientific-agent episodic–semantic paper you cite already do scheduled offline
consolidation. ACE's incremental delta updates are the nearest thing to "patches, not rebuilds".
What is new is **structure-only + tiered write authority + stability-weighted cost + decision log**.
**Risk:** this is a lot of mechanism for one claim; reviewers will ask which part matters. H3/H6
ablations must isolate them, or trim the claim to "structure-only patches with a decision log".

### Claim 4 — Layered ontology: **weakest**

SciAgents, AutoSci's schema-governed wiki (2605.31468), MOOSEDev's ontology grounding already
exist, and the toy explicitly has "no full domain ontology" as a non-goal. **Recommendation:**
demote to a design section, not a contribution — unless H4 gets a real experiment.

### Claim 5 — Campaign-replay benchmark: **open and valuable**

No benchmark tests multi-session R&D memory (review gap 8). Nearest: MemoryArena (2602.16313),
Evo-Memory (2511.20857), VibeMemBench (2609.23570, coding), *Beyond Final Scores* (2608.13417).
LoCoMo is saturated, so a research-specific benchmark with perturbations is a genuine
contribution — possibly the one that carries a NeurIPS D&B submission.

## Does the toy model's evaluation make sense? Five issues to fix before building

1. **The key baseline is missing: raw store + retrieval, no graph.** H1 (detail fidelity) is
   guaranteed by construction for *any* system that keeps raw events (G1). Beating a 1,500-token
   rolling summary will look like a strawman. Add a `raw-rag` system (BM25 over raw event text →
   answer) — Letta's "filesystem is all you need" result (74% on LoCoMo) shows this is a strong
   baseline. Then claim 1's test becomes EIM vs `raw-rag`, and the graph must earn its keep on
   **dependency, reactivation and status** probes, where `raw-rag` should fail.
2. **Synthetic calibration ids are structured fields**, so `calibrated-by` edges are trivial to
   extract. Dependency correctness then measures bookkeeping, not memory. Report **edge-extraction
   accuracy** separately, and include a variant where the calibration is only mentioned in prose.
   Track B is the real test (whether PCB RESULTS files record their legality-model epoch is being
   checked now).
3. **Mock mode reads an `_oracle` field.** Good for plumbing — make sure no reported number ever
   comes from a mock run (the brief says so; enforce it in the report header).
4. **Promotion safety is enforced by a rule** (simulated human gate), so it is by construction too.
   Present it as a guarantee (G-list), not as a measured win, or measure how often the *LLM*
   proposes an unsafe promotion that the gate blocks.
5. **Add at least one published-system baseline** early (the paper lists ACE, A-MEM, Graphiti).
   ACE is the most relevant (it's the source of the context-collapse evidence) and has code.

## Citations in PAPER.md to verify

Not found in this review's searches — could be fine, but check they exist before submission:
Infini Memory (2606.10677), Episodic-Semantic Memory for Scientific Agents (2605.17625),
Kumiho (2603.17244), BeliefMem, IBM EoG (2601.17915), "Anthropic Dreams" (a news article, not a
paper — find a primary source), G-Memory (2506.07398).
