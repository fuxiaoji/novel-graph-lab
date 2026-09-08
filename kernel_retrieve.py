"""Portable AGM-S/R/D retrieval and bounded edge-by-edge tool navigation.

Ports the post-DQA30 graph/dense/BM25 fusion, graph metadata scheduler and
disagreement referee. Open questions use neutral retrieval facets, not invented
multiple-choice answers. Historical accuracy does not transfer to this adapter.
"""
import hashlib
import json
import math
import re
import urllib.request
from collections import defaultdict
from pathlib import Path
from core import BM25, normalize
from kernel_build import VERSION

METHODS = {'agm_s':'AGM-S · 证据扩展','agm_r':'AGM-R · 图谱重排','agm_d':'AGM-D · 分歧仲裁','walk':'逐节点工具导航'}
HIGH = {'supports','contradicts','motive','means','opportunity','witnessed_by','temporal_sequence','belongs_to'}
LOW = {'related_to','mentions','located_at','appears_at'}


def weight(e, propagation=False):
    factor=(1.45 if e['type'] in HIGH else .35 if e['type'] in LOW else 1) if propagation else (1.8 if e['type'] in HIGH else .2 if e['type'] in LOW else .8)
    return max(.05,float(e.get('confidence',.6)))*factor*(1.15 if propagation and e.get('quote') else 1)


class Dense:
    def __init__(self, mode='auto'):
        self.mode=mode
        self.active=mode!='off'
        self.cache=Path(__file__).resolve().parent/'data/embeddings'
        self.cache.mkdir(parents=True,exist_ok=True)
        self.warning=''

    def embed(self,texts):
        if not self.active: return None
        output=[]
        try:
            for offset in range(0,len(texts),16):
                batch=texts[offset:offset+16]
                digest=hashlib.sha256(json.dumps(['bge-m3',batch],ensure_ascii=False).encode()).hexdigest()
                path=self.cache/(digest+'.json')
                if path.exists(): vectors=json.loads(path.read_text('utf-8'))
                else:
                    req=urllib.request.Request('http://127.0.0.1:11434/api/embed',json.dumps({'model':'bge-m3','input':batch,'keep_alive':'10m'}).encode(),{'Content-Type':'application/json'})
                    with urllib.request.urlopen(req,timeout=180) as response: vectors=json.load(response)['embeddings']
                    if len(vectors)!=len(batch): raise ValueError('Wrong embedding count')
                    path.write_text(json.dumps(vectors),'utf-8')
                for v in vectors:
                    norm=math.sqrt(sum(x*x for x in v)) or 1
                    output.append([x/norm for x in v])
            return output
        except Exception:
            if self.mode=='required': raise ValueError('BGE-M3 不可用，请启动 Ollama 并安装 bge-m3，或显式选择无向量模式。') from None
            self.active=False; self.warning='BGE-M3 不可用：本次采用 BM25 + 图谱模式，不能视为原三路检索配置。'
            return None


def similarities(matrix,query):
    return [sum(a*b for a,b in zip(row,query)) for row in matrix]


def pagerank(graph, query, iterations=16):
    nodes=graph['nodes']; ids=[n['id'] for n in nodes]
    hits=BM25([' '.join([n['name']]+n.get('aliases',[])+[n.get('description','')]) for n in nodes]).search(query,len(nodes))
    seed={i:0.0 for i in ids}
    for index,score in hits: seed[ids[index]]=score
    total=sum(seed.values())
    seed={i:v/total if total else 1/max(1,len(ids)) for i,v in seed.items()}
    adj=defaultdict(list)
    for e in graph['edges']:
        adj[e['source']].append((e['target'],e)); adj[e['target']].append((e['source'],e))
    rank=seed.copy(); frames=[]
    for iteration in range(iterations):
        updated={i:.22*v for i,v in seed.items()}; flows=[]; dangling=0
        for s in ids:
            neighbors=adj[s]
            if not neighbors: dangling+=rank[s]; continue
            denom=sum(weight(e,True) for _,e in neighbors)
            for t,e in neighbors:
                mass=.78*rank[s]*weight(e,True)/denom
                updated[t]+=mass
                flows.append(dict(source=s,target=t,edge_id=e['id'],mass=mass))
        for i in ids: updated[i]+=.78*dangling*seed[i]
        rank=updated
        if iteration in (0,3,7,15):
            flows=sorted((f for f in flows if f['mass']>0),key=lambda f:-f['mass'])[:12]
            frames.append(dict(kind='hop',label=f'关联传播 · {iteration+1}/16',detail='按关系类型和置信度传播查询相关度；光点对应本轮实际传播量最大的边。',
                node_ids=list(dict.fromkeys([x[k] for x in flows for k in ('source','target')])),edge_ids=[x['edge_id'] for x in flows],traversals=flows))
    return rank, [ids[i] for i,_ in hits[:8]], frames


def diverse(order,limit):
    selected=[]
    for i in order:
        if not any(abs(i-j)<=1 for j in selected): selected.append(i)
        if len(selected)>=limit: break
    return selected


def retrieve(graph,query,facets,dense,step):
    passages=graph['passages']; by_pid={p['id']:i for i,p in enumerate(passages)}
    matrix=dense.embed([p['text'] for p in passages])
    queries=[query+' '+f for f in facets] or [query]
    vectors=dense.embed(queries)
    bm=BM25([p['text'] for p in passages])
    packets=[]; edge_scores=defaultdict(float)
    for qi,q in enumerate(queries):
        ranks,seeds,frames=pagerank(graph,q)
        if qi==0:
            step('seed',label='查询实体定位',detail='BM25 节点种子 → 16 轮个性化 PageRank。',node_ids=seeds,edge_ids=[])
            for frame in frames:
                frame=frame.copy();step(frame.pop('kind'),**frame)
        mass=defaultdict(float)
        for e in graph['edges']:
            score=weight(e)*(ranks[e['source']]+ranks[e['target']])
            edge_scores[e['id']]=max(edge_scores[e['id']],score)
            if e.get('passage_id') in by_pid: mass[by_pid[e['passage_id']]]+=score
        lexical=[i for i,_ in bm.search(q,36)]
        graph_order=sorted(mass,key=lambda i:-mass[i])[:40]
        channels=[(lexical,1.0),(graph_order,1.5)]
        if matrix is not None and vectors is not None:
            scores=similarities(matrix,vectors[qi]); channels.append((sorted(range(len(scores)),key=lambda i:-scores[i])[:80],1.2))
        fused=defaultdict(float)
        for order,factor in channels:
            for r,i in enumerate(order): fused[i]+=factor/(40+r)
        ordered=sorted(fused,key=lambda i:(-fused[i],i))
        packets.append([(i,fused[i]) for i in diverse(ordered,5)])
    selected=[]
    for packet in packets:
        for i,_ in packet:
            if i not in selected: selected.append(i);break
    for i,_ in sorted([row for packet in packets for row in packet],key=lambda row:-row[1]):
        if i not in selected: selected.append(i)
    return selected[:6],edge_scores,packets


def evidence(graph,indices):
    selected={graph['passages'][i]['id'] for i in indices}
    edges=[e for e in graph['edges'] if e.get('passage_id') in selected]
    rows=[]
    # Stable citation IDs across independent routes and referee union.
    for i in sorted(set(indices)):
        p=graph['passages'][i]
        linked=[e for e in edges if e.get('passage_id')==p['id']]
        nodes={n['id'] for n in graph['nodes'] if any(q.get('passage_id')==p['id'] for q in n.get('evidence_ids',[]))}
        rows.append(dict(id=f'c{i+1}',quote=p['text'],passage_id=p['id'],start=p.get('start'),end=p.get('end'),node_ids=sorted(nodes),edge_id=None))
    return rows,edges


def rerank(graph,query,facets,tight,edge_scores,dense,api,step):
    nodes={n['id']:n for n in graph['nodes']}; passages=graph['passages']; pid_index={p['id']:i for i,p in enumerate(passages)}
    docs=[]; maps=[]
    for n in graph['nodes']:
        docs.append(' '.join([n['name'],n.get('description','')]+[q['quote'] for q in n.get('evidence_ids',[])[:3]]))
        maps.append({pid_index[q['passage_id']] for q in n.get('evidence_ids',[]) if q.get('passage_id') in pid_index})
    for e in graph['edges']:
        docs.append(f"{nodes[e['source']]['name']} {e['type']} {nodes[e['target']]['name']} {e['quote']}")
        maps.append({pid_index[e['passage_id']]} if e.get('passage_id') in pid_index else set())
    matrix=dense.embed(docs)
    vectors=dense.embed([query+' '+f for f in facets]+[query+' final revelation true solution causal conclusion decisive evidence'])
    if matrix is not None and vectors is not None:
        scores=[max(sum(a*b for a,b in zip(row,q)) for q in vectors) for row in matrix]
    else:
        scoremap=dict(BM25(docs).search(query+' '+' '.join(facets),len(docs)))
        scores=[scoremap.get(i,0) for i in range(len(docs))]
    by_chunk=defaultdict(list)
    for di in sorted(range(len(docs)),key=lambda i:-scores[i]):
        for ci in maps[di]: by_chunk[ci].append((scores[di],di))
    ranked=sorted(by_chunk,key=lambda i:-(by_chunk[i][0][0]+(.15*by_chunk[i][1][0] if len(by_chunk[i])>1 else 0)))
    pool=list(dict.fromkeys(tight+ranked))[:28]
    cards=[dict(id=passages[i]['id'],position=passages[i]['start']/max(1,graph['meta']['characters']),tight_route=i in tight,
                facts=[docs[di][:360] for _,di in by_chunk[i][:2]]) for i in pool]
    raw=api.complete('Select up to 8 source passage IDs using ONLY graph metadata. Prefer decisive facts and explicit revelations; demote decoys and repetition. Do not answer. Return {"selected_passage_ids":["p1"],"evidence_summary":"brief selection criterion"}.',dict(question=query,cards=cards))
    allowed={passages[i]['id']:i for i in pool}
    proposed=raw.get('selected_passage_ids',[])
    if not isinstance(proposed,list): proposed=[]
    valid=list(dict.fromkeys(allowed[p] for p in proposed if isinstance(p,str) and p in allowed))[:8]
    invalid=[str(p) for p in proposed if not isinstance(p,str) or p not in allowed]
    chosen=list(dict.fromkeys(valid+pool))[:8]
    ev,links=evidence(graph,chosen)
    step('rerank',label='图谱候选重排',detail=str(raw.get('evidence_summary','图谱证据卡 → 最多 8 块原文')),
         node_ids=sorted({n for r in ev for n in r['node_ids']}),edge_ids=[e['id'] for e in links],candidate_passage_ids=list(allowed),selected_passage_ids=[passages[i]['id'] for i in chosen],rejected_ids=invalid)
    return chosen


ANSWER_SYSTEM = '''Read only supplied evidence. Graph relations are retrieval hypotheses, NOT proof.
Compare candidate claims; prefer explicit final revelations to early suspicions; missing evidence is unknown,
not refutation. Distinguish testimony, inferred claims and contradictions. Follow NOT/EXCEPT literally.
Return {"answer":"Chinese answer with [c1] citations for each key claim", "answer_key":"short canonical conclusion (or supplied option letter)",
"citations":["c1"], "evidence_summary":"short evidence conclusion, no private reasoning", "uncertainty":"remaining limitations"}.'''


def read_answer(graph,question,indices,api,step,route):
    ev,links=evidence(graph,indices)
    step('evidence',label=route+' · 读取原文',detail=f'{len(ev)} 块完整原文；先证据、后作答。',node_ids=sorted({n for r in ev for n in r['node_ids']}),edge_ids=[e['id'] for e in links],evidence_ids=[r['id'] for r in ev])
    high=[e for e in links if e['type'] in HIGH and not e.get('decoy')][:10]
    response=api.complete(ANSWER_SYSTEM+' Preserve supplied citation IDs exactly; never renumber passages. Only these IDs exist: '+', '.join(r['id'] for r in ev),dict(evidence=ev,graph_links=high,question=question))
    return response,ev


def navigate(graph,question,api,step,cancelled,max_steps=8):
    nodes={n['id']:n for n in graph['nodes']}; edges={e['id']:e for e in graph['edges']}
    hits=BM25([' '.join([n['name'],n.get('description','')]+[q['quote'] for q in n.get('evidence_ids',[])]) for n in nodes.values()]).search(question,8)
    seeds=[list(nodes)[i] for i,_ in hits]
    if not seeds: seeds=list(nodes)[:8]
    connected={e[k] for e in graph['edges'] for k in ('source','target')}
    # A navigation entry needs an exit. Isolates remain visible and inspectable.
    seeds=[i for i in seeds if i in connected] or seeds
    if not seeds: return [],'empty_graph'
    pick=api.complete('Choose one starting node for evidence navigation; do not answer. Return {"node_id":"provided id"}.',dict(question=question,nodes=[dict(id=i,name=nodes[i]['name']) for i in seeds]))
    current=pick.get('node_id');current=current if current in seeds else seeds[0]
    visited=[]; used_edges=set(); stop_reason='step_budget'
    adj=defaultdict(list)
    for e in graph['edges']: adj[e['source']].append(e);adj[e['target']].append(e)
    for index in range(max_steps):
        if cancelled(): raise ValueError('任务已停止。')
        visited.append(current); node=nodes[current]
        step('read',label=f'读取节点 {index+1} · {node["name"]}',detail='读取这个节点的原文证据，再由 LLM 选择下一条边。',node_ids=[current],edge_ids=[],observations=node.get('evidence_ids',[])[:4])
        adjacent=sorted(adj[current],key=lambda e:(e['id'] in used_edges,-weight(e)))[:40]
        candidates=[dict(edge_id=e['id'],relation=e['type'],target=e['target'] if e['source']==current else e['source'],
                         name=nodes[e['target'] if e['source']==current else e['source']]['name'],quote=e['quote']) for e in adjacent]
        raw=api.complete('You are a bounded graph navigation tool controller. After reading this node choose ONE listed adjacent edge, or stop if evidence is sufficient. Never invent an edge. '
                         'Cross-check at least one adjacent relation before concluding whenever the node has neighbors. For a route question follow the next unresolved transfer or ownership relation. '
                         'Return {"action":"traverse|stop", "edge_id":"listed id or empty", "evidence_summary":"one short source-grounded reason for choosing that relation"}. No private chain of thought.',
                         dict(question=question,current_node=dict(id=current,name=node['name'],evidence=node.get('evidence_ids',[])[:4]),adjacent_edges=candidates,visited=[nodes[n]['name'] for n in visited],remaining_steps=max_steps-index-1))
        eid=raw.get('edge_id'); candidate_ids={e['id'] for e in adjacent}
        if raw.get('action')=='stop':
            stop_reason='model_stop';step('stop',label='导航停止',detail=str(raw.get('evidence_summary','证据已足够')),node_ids=[current],edge_ids=[]);break
        if raw.get('action')!='traverse' or eid not in candidate_ids:
            stop_reason='invalid_action';step('stop',label='拒绝无效导航',detail='模型选择的边不在当前节点邻接表内，本次导航已停止。',node_ids=[current],edge_ids=[],rejected_edge_id=str(eid));break
        e=edges[eid];target=e['target'] if e['source']==current else e['source']
        if eid in used_edges:
            stop_reason='repeated_edge';step('stop',label='循环保护',detail='该边已读取，停止重复访问。',node_ids=[current],edge_ids=[]);break
        if index==max_steps-1: break
        step('hop',label=f'选择边 · {e["type"]}',detail=str(raw.get('evidence_summary','沿已存在的关系读取下一节点')),
             node_ids=[current,target],edge_ids=[eid],traversals=[dict(source=current,target=target,edge_id=eid)],candidate_edge_ids=sorted(candidate_ids),action='traverse')
        used_edges.add(eid);current=target
    passage_ids=list(dict.fromkeys(q['passage_id'] for n in visited for q in nodes[n].get('evidence_ids',[])))
    indices=[i for pid in passage_ids for i,p in enumerate(graph['passages']) if p['id']==pid][:8]
    return indices,stop_reason


def answer(graph,question,api,emit=lambda *a,**k:None,cancelled=lambda:False,method='agm_s',dense_mode='auto'):
    if method not in METHODS: raise ValueError('未知检索方法。')
    if not question.strip(): raise ValueError('请输入问题。')
    if not graph.get('nodes'): raise ValueError('图谱没有节点。')
    trace=[];before=api.usage.copy();dense=Dense(dense_mode);route_records={};stop_reason=None
    def step(kind,**data):
        if cancelled(): raise ValueError('任务已停止。')
        trace.append(dict(kind=kind,**data));emit(kind,**data)
    step('question',label=METHODS[method],detail=question,node_ids=[],edge_ids=[])
    if method=='walk':
        indices,stop_reason=navigate(graph,question,api,step,cancelled)
        response,ev=read_answer(graph,question,indices,api,step,'节点导航')
    else:
        plan=api.complete('Plan evidence retrieval in the language of the novel. Return {"query":"expanded search query", "facets":["up to 4 neutral evidence subqueries"], "summary":"one sentence"}. '
                          'If options appear in the question use each supplied option as a separate facet. Do not invent candidate answers or guess the solution.',
                          dict(question=question,glossary=[n['name'] for n in graph['nodes'] if n['type']=='person'][:80]))
        query=question+' '+str(plan.get('query','')); facets=plan.get('facets',[])
        facets=[f for f in facets if isinstance(f,str)][:4] if isinstance(facets,list) else []
        step('plan',label='查询与证据分面',detail=str(plan.get('summary','按证据需求检索')),node_ids=[],edge_ids=[],facets=facets)
        tight,scores,packets=retrieve(graph,query,facets,dense,step)
        if method=='agm_s': response,ev=read_answer(graph,question,tight,api,step,'AGM-S')
        else:
            chosen=rerank(graph,query,facets,tight,scores,dense,api,step)
            if method=='agm_r': response,ev=read_answer(graph,question,chosen,api,step,'AGM-R')
            else:
                left,lev=read_answer(graph,question,tight,api,step,'AGM-S 独立阅读')
                right,rev=read_answer(graph,question,chosen,api,step,'AGM-R 独立阅读')
                route_records={'agm_s':left,'agm_r':right}
                ev=sorted({r['id']:r for r in lev+rev}.values(),key=lambda r:int(r['id'][1:]))
                same=bool(left.get('answer_key')) and normalize(left['answer_key'])==normalize(right.get('answer_key'))
                step('arbitrate',label='双路径一致性检查',detail='结论一致，采用证据扩展回答。' if same else '两条路径结论不同或无法确认一致，交给证据裁判。',node_ids=[],edge_ids=[],agreement=same)
                if same: response=left
                else:
                    response=api.complete(ANSWER_SYSTEM+' You are the evidence referee. Compare the two candidates against their source union. Never use baseline answers or gold answers.',dict(evidence=ev,question=question,candidates=route_records))
    valid={e['id'] for e in ev}
    text=str(response.get('answer',''))
    proposed=response.get('citations',[])
    proposed=proposed if isinstance(proposed,list) else []
    inline=set(re.findall(r'\[(c\d+)\]',text))
    attempted={str(c) for c in proposed}|inline
    repair=False
    if valid and (attempted-valid or not inline or not (inline&valid)):
        repair=True
        step('citation_check',label='原文引用复核',detail='回答引用不符合本次证据编号，要求模型依据原文修正一次；保留本次修复记录。',node_ids=[],edge_ids=[],invalid_ids=sorted(attempted-valid))
        response=api.complete(ANSWER_SYSTEM+' Repair this draft using ONLY the supplied evidence. Citation IDs are fixed, not sequential from c1. Do not cite graph node IDs or passage IDs. Allowed citation IDs: '+', '.join(sorted(valid)),
            dict(evidence=ev,question=question,draft=text,invalid_ids=sorted(attempted-valid)))
        text=str(response.get('answer',''))
    listed=response.get('citations',[]);listed=listed if isinstance(listed,list) else []
    used={str(c) for c in listed}|set(re.findall(r'\[(c\d+)\]',text));unknown=used-valid
    for c in unknown: text=text.replace('['+c+']','[无效引用]')
    citations=sorted(used&valid);warnings=[]
    if unknown: warnings.append('模型引用了未提供的证据，已标记。')
    if not citations: warnings.append('回答没有有效引用。')
    if dense.warning and method!='walk': warnings.append(dense.warning)
    if graph.get('meta',{}).get('quality',{}).get('passed') is False: warnings.append('此图谱未通过建图质量阈值，回答需谨慎核对。')
    cited_nodes={n for e in ev if e['id'] in citations for n in e['node_ids']}
    step('answer',label='有据回答',detail=str(response.get('evidence_summary','回答完成')),node_ids=sorted(cited_nodes),edge_ids=[])
    return dict(question=question,answer=text,citations=citations,evidence=ev,trace=trace,uncertainty=str(response.get('uncertainty','')),
                warnings=warnings,usage={k:api.usage[k]-before.get(k,0) for k in api.usage},mode='live',method=method,method_label=METHODS[method],
                kernel_version=VERSION,retrieval_backend='node-tools' if method=='walk' else 'bge-m3+bm25+graph' if dense.active else 'bm25+graph',
                route_records=route_records,stop_reason=stop_reason,citation_repaired=repair,model=api.model,source_sha256=graph['meta'].get('source_sha256'))
