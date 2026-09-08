"""Extract embedded JSON from the supplied dashboard without executing its scripts."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def extract(path):
    raw = path.read_bytes()
    html = raw.decode('utf-8-sig')
    decoder = json.JSONDecoder()
    g = decoder.raw_decode(html.split('var G = ', 1)[1].lstrip())[0]
    rows = decoder.raw_decode(html.split('var ROWS = ', 1)[1].lstrip())[0]
    nodes = [dict(id=n['id'], name=n['name'], type=n['type'], aliases=n.get('aliases', []),
                  evidence_ids=[dict(passage_id='historical', quote=q) for q in n.get('ev', [])],
                  fx=n['fx'], fy=n['fy'], fz=n['fz'], x=n['x'], y=n['y']) for n in g['nodes']]
    edges = [dict(id=f'e{i+1}', source=e['s'], target=e['t'], type=e['type'], quote=e['ev'],
                  passage_id='historical', confidence=e.get('conf', .9)) for i, e in enumerate(g['edges'])]
    # Historical dashboard has excerpts but no complete source text/character offsets.
    unique_quotes = list(dict.fromkeys(e['quote'] for e in edges if e['quote']))
    passages = [dict(id=f'h{i+1}', start=None, end=None, text=q) for i, q in enumerate(unique_quotes)]
    graph = dict(version='1.0', title='原始小说 · 侦探证据图谱', nodes=nodes, edges=edges, passages=passages,
                 meta=dict(mode='historical', source_file=path.name, source_sha256=hashlib.sha256(raw).hexdigest(),
                           note='Extracted historical graph; full novel and original API credentials are not included.'))
    by_name = {n['name'].casefold(): n['id'] for n in nodes}
    results = []
    for row in rows:
        def ids(key):
            return list(dict.fromkeys(by_name[name.casefold()] for name in row.get(key, []) if name.casefold() in by_name))
        first, second, third = ids('first_order'), ids('second_order'), ids('third_order')
        def traversal(srcs, targets):
            out = []
            for t in targets:
                edge = next((e for e in edges if e['source'] in srcs and e['target'] == t or e['target'] in srcs and e['source'] == t), None)
                if edge:
                    src = edge['target'] if edge['source'] == t else edge['source']
                    out.append(dict(source=src, target=t, edge_id=edge['id']))
            return out
        evidence = []
        for i, quote in enumerate(row.get('evidence_sentences', [])):
            matched = [e for e in edges if e['quote'] and len(e['quote']) > 15 and (e['quote'] in quote or quote in e['quote'])]
            evidence.append(dict(id=f'c{i+1}', quote=quote, passage_id='historical', start=None, end=None,
                                 node_ids=list(dict.fromkeys(n for e in matched for n in (e['source'], e['target']))),
                                 edge_id=matched[0]['id'] if matched else None))
        trace = [dict(kind='question', label='输入问题', detail=row['question'], node_ids=[], edge_ids=[]),
                 dict(kind='plan', label='查询目标', detail='历史记录未保存 LLM 查询规划文本；此处仅展示原问题，不补造规划。', node_ids=[], edge_ids=[]),
                 dict(kind='seed', label='一阶 · 词法定位', detail='原 Demo 保存的一阶检索节点。', node_ids=first, edge_ids=[])]
        for label, srcs, dest in [('二阶 · 关系扩散', first, second), ('三阶 · 补充探索', first+second, third)]:
            travels = traversal(srcs, dest)
            trace.append(dict(kind='hop', label=label, detail=f'历史命中 {len(dest)} 个节点；动画从现有图谱重建 {len(travels)} 条连接，不声称是原始执行顺序。',
                              node_ids=dest, edge_ids=[t['edge_id'] for t in travels], traversals=travels))
        trace.extend([dict(kind='evidence', label='读取原文证据', detail=f'原 Demo 保存的 {len(evidence)} 段证据。', node_ids=first+second+third,
                           edge_ids=[e['edge_id'] for e in evidence if e['edge_id']]),
                      dict(kind='answer', label='LLM · 证据回答', detail='回放原 Demo 的回答；不重新调用模型。',
                           node_ids=list(dict.fromkeys(n for e in evidence for n in e['node_ids'])), edge_ids=[e['edge_id'] for e in evidence if e['edge_id']])])
        results.append(dict(question=row['question'], answer=row.get('answer', ''), evidence=evidence, trace=trace, citations=[],
                            mode='historical', uncertainty='原始记录未保存逐断言引用和完整原文坐标；下方证据不等同于已验证每个回答断言。', warnings=[]))
    return dict(graph=graph, results=results)


def standalone(data, destination):
    html = (ROOT/'web/index.html').read_text('utf-8')
    css = (ROOT/'web/style.css').read_text('utf-8')
    js = (ROOT/'web/app.js').read_text('utf-8').replace('</script', '<\\/script')
    payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    html = html.replace('<link rel="stylesheet" href="/style.css">', '<style>'+css+'</style>')
    html = html.replace('<script src="/graph-utils.js"></script>', '<script>'+(ROOT/'web/graph-utils.js').read_text('utf-8')+'</script>')
    html = html.replace('<script src="/app.js"></script>', '<script>window.__BOOT__='+payload+';</script><script>'+js+'</script>')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html, 'utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    data = extract(args.source)
    (ROOT/'examples').mkdir(exist_ok=True)
    (ROOT/'examples/demo.json').write_text(json.dumps(data, ensure_ascii=False), 'utf-8')
    standalone(data, ROOT/'outputs/NovelGraph-Demo.html')
    print(f"Extracted {len(data['graph']['nodes'])} nodes, {len(data['graph']['edges'])} edges, {len(data['results'])} questions.")
