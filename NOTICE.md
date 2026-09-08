# Source and attribution

Novel Graph Lab adapts the author's [Novel KG Studio](https://github.com/fuxiaoji/novel-kg-studio) research. Version 0.3 replaces the early Dashboard graph and simplified retrieval from version 0.2 with a later relation-centered build and AGM-style evidence readers. Exact lineage and adaptations are documented in [docs/kernel.md](docs/kernel.md).

The public example contains the complete *The Adventure of the Blue Carbuncle*, Arthur Conan Doyle (1892), taken from [Project Gutenberg ebook 1661](https://www.gutenberg.org/ebooks/1661). Original transcription credits: an anonymous Project Gutenberg volunteer and Jose Menendez. The download's license is preserved in [examples/GUTENBERG-LICENSE.txt](examples/GUTENBERG-LICENSE.txt). The story is public domain in the USA according to its source listing. Check applicable local terms before redistribution in another jurisdiction.

The new graph and all twelve answers were generated from this source with GLM-4.7 and the v0.3 kernel. The [run manifest](examples/demo-manifest.json) identifies the source hash, model, kernel hash and methods. They are model-generated artifacts, subject to extraction and answer errors. All prespecified runs are retained; the record is not a benchmark accuracy claim.

The MIT license applies to application code and original project documentation. It does not extend to novels users later import. Source licenses and attribution remain separate from the code license.

The design used the [Anthropic frontend-design skill](https://github.com/anthropics/skills/tree/main/skills/frontend-design) as guidance. The skill is not bundled. Excalidraw and LightRAG README structures were studied as references. There is no affiliation or endorsement.
