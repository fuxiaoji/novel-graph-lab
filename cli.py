"""Batch entry point for the reusable skill. Secrets come from environment only."""
import argparse
import json
import os
from pathlib import Path
from core import API, build, answer
from tools.extract_demo import standalone


def main():
    p = argparse.ArgumentParser(description='Novel → graph → evidence QA → animated HTML')
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--novel', type=Path)
    source.add_argument('--graph', type=Path)
    p.add_argument('--question', required=True)
    p.add_argument('--base-url', default=os.environ.get('NOVEL_API_BASE', 'https://api.deepseek.com'))
    p.add_argument('--model', default=os.environ.get('NOVEL_API_MODEL', ''))
    p.add_argument('--encoding', default='utf-8-sig')
    p.add_argument('--chunk-size', type=int, default=5000)
    p.add_argument('--out', type=Path, default=Path('outputs/session'))
    a = p.parse_args()
    api = API(dict(base_url=a.base_url, model=a.model, api_key=os.environ.get('NOVEL_API_KEY', '')))
    a.out.mkdir(parents=True, exist_ok=True)
    def emit(kind, **data):
        print(data.get('label', kind), flush=True)
    if a.novel:
        graph = build(a.novel.read_text(a.encoding), a.novel.stem, api, a.out/'cache', emit, size=a.chunk_size)
    else:
        data = json.loads(a.graph.read_text('utf-8-sig'))
        graph = data.get('graph', data)
    # Save graph before answering so a failed answer never loses a completed build.
    (a.out/'graph.json').write_text(json.dumps(graph, ensure_ascii=False), 'utf-8')
    result = answer(graph, a.question, api, emit)
    session = dict(graph=graph, results=[result])
    (a.out/'session.json').write_text(json.dumps(session, ensure_ascii=False, indent=2), 'utf-8')
    standalone(session, a.out/'replay.html')
    print(str((a.out/'replay.html').resolve()))


if __name__ == '__main__':
    main()
