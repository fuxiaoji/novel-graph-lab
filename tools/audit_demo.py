"""Audit a complete real demo without using gold answers or changing outputs."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def audit(session,source):
    graph=session['graph'];results=session['results'];ids={n['id'] for n in graph['nodes']};edges={e['id']:e for e in graph['edges']}
    assert graph['meta']['source_sha256']==hashlib.sha256(source.encode()).hexdigest()
    assert graph['version']=='agm-port-3.0'
    for p in graph['passages']: assert source[p['start']:p['end']]==p['text']
    for n in graph['nodes']:
        for q in n['evidence_ids']: assert source[q['start']:q['end']]==q['quote']
    for e in edges.values():
        assert e['source'] in ids and e['target'] in ids
        assert source[e['start']:e['end']]==e['quote']
    counts={};rows=[]
    for result in results:
        assert result['mode']=='live' and result['kernel_version']=='agm-port-3.0'
        counts.setdefault(result['question'],set()).add(result['method'])
        ev={e['id']:e for e in result['evidence']}
        for e in ev.values(): assert source[e['start']:e['end']]==e['quote']
        assert set(result['citations'])<=set(ev)
        assert set(re.findall(r'\[(c\d+)\]',result['answer']))<=set(ev)
        traversals=[]
        for step in result['trace']:
            assert set(step.get('node_ids',[]))<=ids
            assert set(step.get('edge_ids',[]))<=set(edges)
            for t in step.get('traversals',[]):
                e=edges[t['edge_id']]
                assert {e['source'],e['target']}=={t['source'],t['target']}
                if result['method']=='walk': assert t['edge_id'] in step['candidate_edge_ids']
                traversals.append(t)
        rows.append(dict(question=result['question'],method=result['method'],backend=result['retrieval_backend'],
            citations=len(result['citations']),invalid_citation_marker='无效引用' in result['answer'],warnings=result['warnings'],
            node_reads=sum(s['kind']=='read' for s in result['trace']),traversals=len(traversals),
            stop_reason=result.get('stop_reason'),citation_repaired=result.get('citation_repaired',False)))
    assert len(results)==12 and len(counts)==3 and all(m=={'agm_s','agm_r','agm_d','walk'} for m in counts.values())
    return dict(passed=True,source_characters=len(source),nodes=len(ids),edges=len(edges),results=rows,
                note='Structural, provenance and citation-ID audit only; not an answer-accuracy evaluation.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--session',type=Path,default=Path('outputs/v3/session.json'))
    parser.add_argument('--source',type=Path,default=Path('examples/blue-carbuncle.txt'));parser.add_argument('--out',type=Path,default=Path('outputs/v3/audit.json'))
    args=parser.parse_args();report=audit(json.loads(args.session.read_text('utf-8')),args.source.read_text('utf-8'))
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
