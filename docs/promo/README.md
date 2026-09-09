# Media kit / 媒体素材

Screenshots and posters for talks, blog posts and social sharing. All images show the real public demo (complete *The Moonstone* graph with the gold-node overlay). Regenerate the posters after a demo change with `python docs/promo/make_poster.py` (Pillow required).

| File | What it shows | Suggested use |
| --- | --- | --- |
| `01-hero-full-1440x900.png` | Full three-pane workspace: graph, replay timeline, answer with citations and the per-method gold hit panel | README/banner, blog header |
| `02-gold-closeup-780x700.png` | Zoomed graph: bright-gold retrieved gold nodes (with labels) vs gold-ringed unretrieved ones | Social post hero image |
| `03-retrieval-animation-780x700.png` | Replay frame: evidence converging along recorded edges | Social post, docs |
| `04-poster-1200x675.png` | 16:9 stat poster (1.07M-char novel → 427 nodes / 1,460 edges, 109 API calls, 4 methods) | Link-card sized share image |
| `05-poster-1200x1200.png` | Square stat poster with full-workspace screenshot | Timeline-sized share image |

## Project one-liner

- **EN:** Novel Graph Lab turns a complete novel into an evidence-grounded knowledge graph and lets four auditable retrieval strategies answer questions on it — with every quote verbatim-checked against the source.
- **中文：** Novel Graph Lab 把完整小说变成有原文证据的知识图谱，提供四种可审计的检索策略回答问题，每条引文都与原文逐字核对。

## Key facts (v0.4 demo)

- Source: complete public-domain novel *The Moonstone* (Wilkie Collins, 1868), 1,073,378 characters
- Graph: 427 nodes / 1,460 edges / 0.7% isolated nodes, built with GLM-5.3 in 109 calls (large-context batching)
- 12 recorded answers: 3 preset questions × 4 methods (AGM-S / AGM-R / AGM-D / node-walk)
- Gold overlay: per-question key entities; retrieved ones pulse gold, unretrieved ones wear a ring
- Live demo (no account/key): <https://fuxiaoji.github.io/novel-graph-lab/> · Code: <https://github.com/fuxiaoji/novel-graph-lab>
- License: MIT (code); the bundled novel is public domain (Project Gutenberg #155)

素材截图与海报均来自公开 demo 实况（完整《月亮宝石》图谱 + 金标叠加）。图片采用项目截图，无额外版权限制；转载请注明项目链接。
