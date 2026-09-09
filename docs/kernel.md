# Kernel lineage: v0.4 / agm-port-3.1

The v0.2 release mistakenly presented an early saved Dashboard graph as the main example and implemented a simpler two-hop retrieval pipeline. v0.3 replaced that kernel and rebuilt the published example from complete source text. v0.4 adds large-context batching so ~1M-token models build full-length novels with an order of magnitude fewer calls, tightens verbatim validation (whitespace-run-insensitive matching, exact-slice storage), and republishes the demo on a complete public-domain novel. Old answers are not used as model inputs or as demo outputs.

## Sources inspected

- Novel KG Studio commit `828f23ee01783db13dc7bbb3c823488f65f8a119`.
- Q1 development checkout commit `a1f306cfd5f88a84122312f03e1302faebd6c271`.
- [Research report](https://github.com/fuxiaoji/novel-kg-studio/blob/main/docs/PROJECT_REPORT.md).
- Build: `pipeline/pass1_filter.py`, `pipeline/pass2_graph.py` (`PASS2_SYSTEM_V4`), `pipeline/consolidate.py`, `scripts/build_c_next10_graphs.py`.
- Retrieval: `c8_graph_passage.py`, `c13_option_rebuttal.py`, `run_dqa30_g6_graph_expansion.py`, `run_dqa_g7_tight.py`, `run_dqa_g9_graph_rerank.py`, `run_dqa_g10_graph_referee.py`, Q1 `q1_methods.py`.
- Tool navigation: `detectiveqa_three_groups.py::answer_graph_agentic_v2` (v5b), which exposes lookup, search and relation traversal.

The two extraction prompts are carried into `research_prompts.py` directly; their source-file hashes are in [upstream-kernel.json](upstream-kernel.json). Retrieval is ported to standard-library Python, not a copy of the experiment runners and their dataset-specific imports. No confirmatory dataset or frozen research output was modified or used for the public example.

## Why these methods

Historical exploratory results reported on 234 questions with Qwen3.5-9B:

| Research method | Portable entry | Reported historical accuracy | Reason for inclusion |
|---|---|---:|---|
| G7 tight graph-guided evidence expansion | `agm_s` | 126/234, 53.8% | Strongest aggregate of these three graph methods |
| G9 graph-native metadata reranking | `agm_r` | 119/234, 50.9% | Strongest of these three on the reported question-only-hard subset (45.0%) |
| G10 graph disagreement referee | `agm_d` | 125/234, 53.4% | Complementary evidence routes; 58.6% on the later 70-question cohort |
| v5b relation-aware agentic traversal | `walk` | No accuracy claim here | Observable read/choose-edge/read operations requested for the animation |

These figures come from two different graph-construction cohorts and are descriptive. They are **not scores for this software, GLM-4.7, or the new demo**. The Q1 branch calls the later graph interfaces AGM-S/R/D; its confirmatory evaluation is unfinished. “Later” does not mean “proven superior.”

## Build pipeline

1. Split the complete source into 1,500-character blocks with 100-character overlap.
2. Pass 1 selects exact plot-bearing spans and records time labels. Every selected span is checked against its original block. If no valid selection remains, retain that complete block and mark the fallback.
3. Pass 2 uses the original relation-centered v4 prompt. It asks for typed entities participating in grounded relationships, explicit supporting/contradicting evidence, confidence and decoy information. Each quote must exist in the referenced input span. Endpoints must resolve unambiguously within that extraction response.

### Large-context batching (v0.4)

The per-block loop above was sized for ~16k-token models. The `wide` parameters batch the same two passes for ~1M-token models without changing the grounding rules:

- `pass1_group` blocks share one selection call (`PASS1_WIDE`); each returned span names its `segment_id` and is validated inside that segment.
- `pass2_chars` characters of verified spans share one extraction call.
- `max_tokens` raises the completion cap for batched outputs; truncation is a hard error, never silent loss.
- `workers` fetches independent batch calls concurrently (results are always processed in fixed reading order, so the graph is deterministic); default 1 keeps the sequential behavior.

Verbatim matching is whitespace-run-insensitive: some models (observed with GLM-5.3) collapse newlines into spaces when copying spans. A quote still has to match the source word-for-word and in order; only whitespace-run differences are bridged, and the stored quote is always replaced by the exact source slice with true character offsets. The published long-novel run uses `pass1_group=24` (about 36k characters per selection call) and `pass2_chars=6000`.
4. Consolidate person-name variants using bounded model proposals, supplied evidence and conservative name compatibility. Ambiguities remain distinct. Collapse resulting self-loops and exact duplicate edges; keep isolated nodes visible.
5. Report quality thresholds inherited from the later builder: isolate rate ≤60%, edge/node ratio ≥0.5, rejected-relation rate ≤55%. A failed threshold is visible; it never causes fabricated edges or hidden nodes.

Full source passages remain a lossless sidecar. Narration order and source offsets are authoritative. Time labels are not used to invent a total ordering for unknown/ambiguous event times. Coverage is a union of grounded node-evidence intervals divided by full-source character count, **not** the graph's question-answering accuracy.

## Retrieval pipeline

**AGM-S.** Each supplied option (or neutral evidence facet for an open question) gets a query. Combine BM25 top 36, BGE-M3 top 80 and graph-ranked top 40 passages using reciprocal-rank fusion with denominator 40 and weights 1.0/1.2/1.5. Graph ranking uses 16 personalized PageRank iterations, restart 0.22 and relation/confidence weights. Select diverse passages and cap the combined dossier at six. The reading prompt treats graph links as hypotheses and checks the original evidence.

**AGM-R.** Build a graph-native pool from node/edge evidence documents, add the tight route's candidates, cap at 28 cards. A model schedules at most eight source passages using graph metadata and text position. Reject unknown IDs. Fill missing slots deterministically from the candidate pool. Read the selected original passages.

**AGM-D.** Independently answer the S and R dossiers. If their nonempty canonical answer keys match, retain S; otherwise a referee receives the source union and the two proposals. The referee never sees gold answers, question-only answers or baseline predictions. Both route records are exported.

**Node tools.** Prefer a connected query seed (without removing isolates from the graph), read the current node's exact source evidence, list its real adjacent edges, and ask the model to choose one edge or stop. Validate the selected edge before movement. Read the destination before choosing again. At most eight nodes, forty candidate edges per node and eight source passages are admitted. Reject invalid actions and stop cycles. The exported record contains visible observations, offered edges, accepted traversal and a short evidence summary, never private chain-of-thought.

## Deliberate portable adaptations

- The research evaluation is four-option English MCQ. This app also accepts Chinese/open questions, using neutral retrieval facets and canonical answer keys for arbitration. These interfaces are not benchmark-equivalent.
- Extraction is chunk-local with original positions; uncertain timestamps do not reorder the source globally.
- Person consolidation demands a supplied source quote; the research runner used name-only proposals plus name guards.
- BGE-M3 runs through local Ollama. `required` fails if unavailable; `auto` visibly falls back to BM25+graph, and `off` explicitly omits dense retrieval. The published demo uses `required`.
- Navigation is a stricter one-node/one-edge interface adapted from v5b's multi-action controller. Its public demo is an execution trace, not evidence that it outperforms S/R/D.
- Animation time is playback time. Graph rank animation displays the highest-mass real transitions in selected propagation iterations, not all internal updates and not model inference speed.

## Fresh demo and reproduction

The public demo (v0.4) uses the complete public-domain novel *The Moonstone* by Wilkie Collins (1868, 1,073,378 characters, about 25x the previous short story) from [Project Gutenberg](https://www.gutenberg.org/ebooks/155), with a retained license. The graph is newly extracted with GLM-5.3 under large-context batching: 427 nodes, 1,460 edges, 3 isolates (0.7%), 109 build calls / ~810k tokens, then 47 answer calls for 12 method runs. The adapter requests JSON mode and retries malformed JSON at most twice. Three prespecified questions run through all four methods; no answer is selected according to correctness. The previous v0.3 run on the complete *Blue Carbuncle* short story (42,115 characters, GLM-4.7) remains reproducible.

`python tools/run_demo.py` builds and runs the example. It reads `NOVEL_API_KEY` from the environment, uses BGE-M3 in required mode, writes a source/kernel fingerprint and refuses legacy graph reuse. Partial results stay in `outputs/v3`; a provider failure does not turn into a simulated result. Publish only after auditing the complete run.

[Published run manifest](../examples/demo-manifest.json) records the exact source, model, methods, request usage and graph quality.
