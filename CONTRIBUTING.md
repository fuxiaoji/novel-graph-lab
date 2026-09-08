# Contributing

Start with an issue describing the observable problem, a minimal example, and expected behavior. Use a short synthetic novel rather than uploading private text, credentials or full provider logs.

Run locally with `python server.py --open`. Runtime code uses only the Python standard library and browser APIs. Keep that setup simple; discuss new runtime dependencies before adding them.

Before a pull request:

```bash
python -m unittest discover -s tests -v
node tests/test_graph_utils.cjs
node --check web/app.js
python tools/build_demo.py --public --out docs/index.html
```

For a visual change, include desktop and narrow-screen screenshots. Verify full-graph defaults, playback, citation clicks, exports, keyboard focus and reduced-motion behavior. For retrieval changes, test a meaningful invariant rather than implementation wording.

Do not invent edges to improve a screenshot, hide isolated nodes by default, infer coverage from partial excerpts, or describe reconstructed paths as original model execution traces.

Keep English and Chinese setup instructions aligned. Do not commit `data/`, `outputs/`, credentials, local absolute paths or generated skill asset copies. Release archives may include the project template; the repository keeps one source of truth.
