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
    p.add_argument('--method', choices=['agm_s','agm_r','agm_d','walk'], default='agm_s')
    p.add_argument('--dense-mode', choices=['auto','required','off'], default='auto')
    p.add_argument('--base-url', default=os.environ.get('NOVEL_API_BASE', 'https://api.deepseek.com'))
    p.add_argument('--model', default=os.environ.get('NOVEL_API_MODEL', ''))
    p.add_argument('--encoding', default='utf-8-sig')
    p.add_argument('--chunk-size', type=int, default=1500)
    p.add_argument('--pass1-group', type=int, default=1, help='passages per pass1 selection call; raise for ~1M-token models')
    p.add_argument('--pass2-chars', type=int, default=0, help='verified span characters per pass2 extraction call; 0 = per passage')
    p.add_argument('--build-max-tokens', type=int, default=6000)
    p.add_argument('--workers', type=int, default=1, help='concurrent build calls; results stay deterministic')
    p.add_argument('--out', type=Path, default=Path('outputs/session'))
    a = p.parse_args()
    api = API(dict(base_url=a.base_url, model=a.model, api_key=os.environ.get('NOVEL_API_KEY', '')))
    a.out.mkdir(parents=True, exist_ok=True)
    def emit(kind, **data):
        print(data.get('label', kind), flush=True)
    wide = dict(pass1_group=a.pass1_group, pass2_chars=a.pass2_chars, max_tokens=a.build_max_tokens, workers=a.workers)
    if a.novel:
        graph = build(a.novel.read_text(a.encoding), a.novel.stem, api, a.out/'cache', emit, size=a.chunk_size, wide=wide)
    else:
        data = json.loads(a.graph.read_text('utf-8-sig'))
        graph = data.get('graph', data)
    # Save graph before answering so a failed answer never loses a completed build.
    (a.out/'graph.json').write_text(json.dumps(graph, ensure_ascii=False), 'utf-8')
    result = answer(graph, a.question, api, emit, method=a.method, dense_mode=a.dense_mode)
    session = dict(graph=graph, results=[result])
    (a.out/'session.json').write_text(json.dumps(session, ensure_ascii=False, indent=2), 'utf-8')
    standalone(session, a.out/'replay.html')
    print(str((a.out/'replay.html').resolve()))


if __name__ == '__main__':
    main()
