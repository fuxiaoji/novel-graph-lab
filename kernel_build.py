"""Relation-centered v4 two-pass builder with a lossless source sidecar."""
import hashlib
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from core import chunks, normalize, TYPES
from research_prompts import PASS1_SYSTEM, PASS1_WIDE, PASS2_SYSTEM_V4

VERSION = 'agm-port-3.1'
RELATIONS = {'located_at','appears_at','belongs_to','mentions','temporal_sequence','supports','contradicts','related_to','motive','means','opportunity','witnessed_by'}


def cached(api, folder, phase, system, data, max_tokens=6000):
    signature = json.dumps([VERSION, api.fingerprint, phase, system, data], ensure_ascii=False, sort_keys=True)
    path = Path(folder)/(hashlib.sha256(signature.encode()).hexdigest()+'.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return json.loads(path.read_text('utf-8'))
    result = api.complete(system, data, max_tokens)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(result, ensure_ascii=False), 'utf-8')
    temp.replace(path)
    return result


def _norm_with_positions(text):
    out = []
    pos = []
    prev_space = False
    for index, char in enumerate(text):
        if char.isspace():
            if prev_space:
                continue
            out.append(' ')
            pos.append(index)
            prev_space = True
        else:
            out.append(char)
            pos.append(index)
            prev_space = False
    return ''.join(out), pos


def locate(container, quote):
    """Find quote inside container; exact first, then whitespace-run-insensitive.

    Returns the exact container slice plus its start offset, or (None, None).
    Models sometimes collapse newlines into spaces when copying verbatim spans;
    the stored quote is always the exact source slice, never the model's spelling.
    """
    if not quote.strip():
        return None, None
    if quote in container:
        start = container.index(quote)
        return container[start:start+len(quote)], start
    norm_text, pos = _norm_with_positions(container)
    norm_quote, _ = _norm_with_positions(quote)
    if not norm_quote.strip():
        return None, None
    at = norm_text.find(norm_quote)
    if at < 0:
        return None, None
    start = pos[at]
    end = pos[at+len(norm_quote)-1]+1
    return container[start:end], start


def quality(graph):
    degree = Counter(e[k] for e in graph['edges'] for k in ('source','target') if e['source'] != e['target'])
    isolates = sum(not degree[n['id']] for n in graph['nodes'])
    count = len(graph['nodes'])
    rate = isolates/max(1,count)
    ratio = len(graph['edges'])/max(1,count)
    rejected = graph['meta']['rejected_relations']
    dropped = rejected/max(1,rejected+len(graph['edges']))
    return dict(nodes=count, edges=len(graph['edges']), isolates=isolates, isolate_rate=rate,
                edge_node_ratio=ratio, dropped_relation_rate=dropped,
                passed=bool(count) and rate<=.60 and ratio>=.50 and dropped<=.55,
                thresholds=dict(max_isolate_rate=.60,min_edge_node_ratio=.50,max_dropped_relation_rate=.55))


def consolidate(graph, api, cache_dir, emit):
    # Conservative, evidence-bearing proposals. Ambiguous aliases remain distinct.
    persons = [n for n in graph['nodes'] if n['type']=='person']
    mapping = {}
    for offset in range(0,len(persons),48):
        batch = persons[:12]+persons[offset:offset+48]
        batch = list({n['id']:n for n in batch}.values())
        if len(batch)<2: continue
        data = [dict(id=n['id'], name=n['name'], aliases=n['aliases'], evidence=n['evidence_ids'][:2]) for n in batch]
        raw = cached(api,cache_dir,'consolidate',
            'Merge ONLY names definitely referring to the SAME person, never relatives or people sharing a surname. '
            'Use the supplied literal evidence. Return {"groups":[{"ids":["n1","n2"],"quote":"one supplied exact quote proving the alias"}]}. '
            'If unsure return an empty groups array.',data)
        by_id = {n['id']:n for n in batch}
        for group in raw.get('groups',[]):
            ids = list(dict.fromkeys(group.get('ids',[])))
            quote = str(group.get('quote',''))
            if len(ids)<2 or any(i not in by_id or i in mapping for i in ids): continue
            # Explicit supplied alias or lexical compatibility + grounded proposal.
            anchor = by_id[ids[0]]
            def compatible(n):
                left=set(normalize(anchor['name']).replace('.','').split())
                right=set(normalize(n['name']).replace('.','').split())
                if (left & {'mr','sir','lord'} and right & {'mrs','miss','lady'}) or (right & {'mr','sir','lord'} and left & {'mrs','miss','lady'}): return False
                a=set(normalize(anchor['name']).replace('.','').split())-{'mr','mrs','miss','dr','sir'}
                b=set(normalize(n['name']).replace('.','').split())-{'mr','mrs','miss','dr','sir'}
                aliases={normalize(v) for v in anchor['aliases']+[anchor['name']]}
                return bool(a and b and (a<=b or b<=a)) or normalize(n['name']) in aliases
            evidence=[e['quote'] for i in ids for e in by_id[i]['evidence_ids']]
            if not quote or not any(quote in q for q in evidence) or not all(compatible(by_id[i]) for i in ids[1:]): continue
            for i in ids[1:]:
                mapping[i]=anchor['id']
                anchor['aliases']=sorted(set(anchor['aliases']+by_id[i]['aliases']+[by_id[i]['name']]))
                anchor['evidence_ids']+= [e for e in by_id[i]['evidence_ids'] if e not in anchor['evidence_ids']]
    graph['nodes']=[n for n in graph['nodes'] if n['id'] not in mapping]
    edges=[]; seen=set()
    for e in graph['edges']:
        e['source']=mapping.get(e['source'],e['source']); e['target']=mapping.get(e['target'],e['target'])
        marker=(e['source'],e['target'],e['type'],e['start'],e['end'])
        if e['source']==e['target'] or marker in seen: continue
        seen.add(marker); edges.append(e)
    graph['edges']=edges
    graph['meta']['merged_person_nodes']=len(mapping)
    emit('build',label='人物别名归并',detail=f'{len(mapping)} 个有证据的名称变体已合并')


def build(text,title,api,cache_dir,emit=lambda *a,**k:None,cancelled=lambda:False,size=1500,wide=None):
    if not text.strip(): raise ValueError('小说内容为空。')
    # wide: large-context batching for ~1M-token models. pass1_group passages share one
    # selection call; pass2_chars characters of verified spans share one extraction call;
    # workers fetches independent calls concurrently (results processed in fixed order).
    wide=dict(wide or {})
    group=max(1,int(wide.get('pass1_group',1)))
    batch_chars=max(0,int(wide.get('pass2_chars',0)))
    out_tokens=max(6000,int(wide.get('max_tokens',6000)))
    workers=max(1,int(wide.get('workers',1)))
    source=chunks(text,size,min(100,size//8))
    nodes=[]; edges=[]; names={}; markers=set(); kept_all=[]
    rejected=0; bad_rel=0
    windows=[source[i:i+group] for i in range(0,len(source),group)]
    def fetch_pass1(window):
        if group==1:
            return cached(api,cache_dir,'pass1',PASS1_SYSTEM,{'text':window[0]['text']})
        return cached(api,cache_dir,'pass1-wide',PASS1_WIDE,
            {'segments':[{'id':p['id'],'text':p['text']} for p in window]},out_tokens)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[]
        for window in windows:
            if cancelled(): raise ValueError('任务已停止；已完成的双遍建图缓存可复用。')
            futures.append(pool.submit(fetch_pass1,window))
        selections=[]
        for wi,future in enumerate(futures):
            window=windows[wi]
            detail='第一遍逐字筛选情节证据；完整原文仍保留' if group==1 else f'大上下文批量：一次筛选 {len(window)} 个分块；完整原文仍保留'
            if workers>1: detail+=f'（{workers} 路并发）'
            emit('build',label=f'证据筛选 {wi+1}/{len(windows)}',done=wi,total=len(windows),detail=detail)
            selections.append(future.result())
    for wi,window in enumerate(windows):
        selected=selections[wi]
        if group==1:
            proposals=[(None,item) for item in selected.get('kept',[])]
        else:
            by_seg={p['id']:p for p in window}
            proposals=[(by_seg.get(str(item.get('segment_id',''))),item) for item in selected.get('kept',[])]
        kept_by_id={}
        for seg,item in proposals:
            quote=str(item.get('text',''))
            search=([seg] if seg else [])+[p for p in window if p is not seg]
            located=None
            for p in search:
                exact,offset=locate(p['text'],quote)
                if exact is not None:
                    located=(p,exact,offset); break
            if located is None: rejected+=1; continue
            hit,exact,offset=located
            kept_by_id.setdefault(hit['id'],[]).append(dict(text=exact,time_label=item.get('time_label','unknown'),start=hit['start']+offset,passage_id=hit['id']))
        # Unparseable/empty selection is explicit: no silent filtering of the book.
        for p in window:
            if not kept_by_id.get(p['id']):
                kept_by_id[p['id']]=[dict(text=p['text'],time_label='unknown',start=p['start'],passage_id=p['id'])]
                p['selection_fallback']='full_chunk'
            kept_all+=kept_by_id[p['id']]
    if batch_chars:
        batches=[]; current=[]; used=0
        for k in kept_all:
            if current and used+len(k['text'])>batch_chars:
                batches.append(current); current=[]; used=0
            current.append(k); used+=len(k['text'])
        if current: batches.append(current)
    else:
        by_passage={}
        for k in kept_all: by_passage.setdefault(k['passage_id'],[]).append(k)
        batches=[by_passage[p['id']] for p in source if by_passage.get(p['id'])]
    def fetch_pass2(kept):
        return cached(api,cache_dir,'pass2-v4',PASS2_SYSTEM_V4,{'lines':'\n'.join(f'[{i}] {k["text"]}' for i,k in enumerate(kept))},out_tokens)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures=[]
        for kept in batches:
            if cancelled(): raise ValueError('任务已停止。')
            futures.append(pool.submit(fetch_pass2,kept))
        extractions=[]
        for bi,future in enumerate(futures):
            emit('build',label=f'关系优先建图 {bi+1}/{len(batches)}',done=bi,total=len(batches),detail=f'{len(batches[bi])} 段已校验证据 → v4 实体与关系')
            extractions.append(future.result())
    for bi,kept in enumerate(batches):
        raw=extractions[bi]
        if not isinstance(raw.get('entities'),list) or not isinstance(raw.get('relations'),list):
            raise ValueError('关系抽取缺少 entities / relations，请重试。')
        def ground(item,field):
            try:
                line_index=int(item['sentence_index'])
                if line_index<0: return None
                k=kept[line_index]
            except (KeyError,ValueError,TypeError,IndexError): return None
            quote=str(item.get(field,''))
            if not quote.strip() or len(quote)>400: return None
            exact,offset=locate(k['text'],quote)
            if exact is None: return None
            start=k['start']+offset
            return dict(passage_id=k['passage_id'],quote=exact,start=start,end=start+len(exact))
        local={}
        for item in raw['entities']:
            if not isinstance(item,dict): continue
            name=str(item.get('name','')).strip(); typ=item.get('type')
            quotes=[g for m in item.get('mentions',[]) if isinstance(m,dict) and (g:=ground(m,'text'))]
            if not name or typ not in TYPES or not quotes: rejected+=1; continue
            key=(typ,normalize(name))
            if key not in names:
                n=dict(id=f'n{len(nodes)+1}',name=name,type=typ,aliases=[],evidence_ids=[],description=str(item.get('description',''))[:160],salience=item.get('salience',3))
                names[key]=n; nodes.append(n)
            n=names[key]
            n['evidence_ids'] += [q for q in quotes if q not in n['evidence_ids']]
            n['aliases']=sorted(set(n['aliases']+[str(a) for a in item.get('aliases',[]) if isinstance(a,str)]))
            for alias in [name]+n['aliases']: local.setdefault(normalize(alias),[]).append(n)
        for item in raw['relations']:
            if not isinstance(item,dict): bad_rel+=1; continue
            g=ground(item,'evidence')
            ss={n['id']:n for n in local.get(normalize(item.get('source','')),[])}
            tt={n['id']:n for n in local.get(normalize(item.get('target','')),[])}
            typ=item.get('type')
            if not g or len(ss)!=1 or len(tt)!=1 or typ not in RELATIONS: bad_rel+=1; continue
            s=next(iter(ss)); t=next(iter(tt)); marker=(s,t,typ,g['start'],g['end'])
            if s==t: bad_rel+=1; continue
            if marker in markers: continue
            markers.add(marker)
            try: confidence=max(0,min(1,float(item.get('confidence',.8))))
            except (ValueError,TypeError): confidence=.8
            edges.append(dict(id=f'e{len(edges)+1}',source=s,target=t,type=typ,confidence=confidence,decoy=item.get('decoy') is True,importance=item.get('importance',3),**g))
    graph=dict(version=VERSION,title=title,nodes=nodes,edges=edges,passages=source,evidence_spans=kept_all,
        meta=dict(mode='live',characters=len(text),source_sha256=hashlib.sha256(text.encode()).hexdigest(),model=api.model,
                  builder='pass1-verbatim + pass2-v4-relation-centered + guarded-person-consolidation',
                  wide=None if group==1 and not batch_chars else dict(pass1_group=group,pass2_chars=batch_chars,max_tokens=out_tokens,workers=workers),
                  rejected_quotes=rejected,rejected_relations=bad_rel,kept_spans=len(kept_all),chunks=len(source),chunk_size=size,overlap=min(100,size//8)))
    if cancelled(): raise ValueError('任务已停止。')
    consolidate(graph,api,cache_dir,emit)
    graph['meta']['quality']=quality(graph)
    graph['meta']['build_usage']=api.usage.copy()
    emit('build',label='建图质量检查',done=len(source),total=len(source),detail=json.dumps(graph['meta']['quality'],ensure_ascii=False))
    if not graph['nodes']: raise ValueError('建图未产生可校验节点，请检查抽取模型。')
    return graph
