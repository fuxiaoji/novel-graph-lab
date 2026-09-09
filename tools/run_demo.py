"""Rebuild the published example using real APIs. Never fabricate a fallback."""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from core import API,build,answer
from kernel_build import VERSION

QUESTIONS=[
    'Who actually stole the blue carbuncle, and what evidence shows that John Horner was framed?',
    'Trace how the blue carbuncle travelled inside a goose from James Ryder to Peterson. Why did Ryder lose track of it?',
    'What did Henry Baker know about the jewel, and how did Holmes test whether he was involved?',
]


def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',default='glm-4.7')
    parser.add_argument('--base-url',default='https://open.bigmodel.cn/api/coding/paas/v4')
    parser.add_argument('--reuse-new-graph',action='store_true',help='Only reuse a graph whose version and source hash match this exact story')
    parser.add_argument('--out',type=Path,default=ROOT/'outputs/v3')
    parser.add_argument('--source',type=Path,default=ROOT/'examples/blue-carbuncle.txt')
    parser.add_argument('--title',default='蓝宝石案 · The Blue Carbuncle')
    parser.add_argument('--source-url',default='https://www.gutenberg.org/ebooks/1661')
    parser.add_argument('--story',default='The Adventure of the Blue Carbuncle')
    parser.add_argument('--author',default='Arthur Conan Doyle')
    parser.add_argument('--scope',default='complete short story, not a long-context benchmark')
    parser.add_argument('--questions',type=Path,default=None,help='JSON file with a list of questions; default is the built-in Blue Carbuncle set')
    parser.add_argument('--pass1-group',type=int,default=1,help='passages per pass1 selection call (large-context batching)')
    parser.add_argument('--pass2-chars',type=int,default=0,help='verified span characters per pass2 extraction call (0 = per passage)')
    parser.add_argument('--build-max-tokens',type=int,default=6000)
    parser.add_argument('--workers',type=int,default=1)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    text=args.source.read_text('utf-8')
    questions=json.loads(args.questions.read_text('utf-8')) if args.questions else QUESTIONS
    source_hash=hashlib.sha256(text.encode()).hexdigest()
    api=API(dict(base_url=args.base_url,model=args.model,api_key=os.environ.get('NOVEL_API_KEY','')))
    if not api.key: raise SystemExit('Set NOVEL_API_KEY in the process environment.')
    def emit(kind,**data): print(data.get('label',kind),flush=True)
    wide=dict(pass1_group=args.pass1_group,pass2_chars=args.pass2_chars,max_tokens=args.build_max_tokens,workers=args.workers)
    graph_path=args.out/'graph.json'
    if args.reuse_new_graph and graph_path.exists():
        graph=json.loads(graph_path.read_text('utf-8'))
        if graph.get('version')!=VERSION or graph['meta'].get('source_sha256')!=source_hash:
            raise SystemExit('Refusing legacy or different-source graph. Rebuild without --reuse-new-graph.')
    else:
        graph=build(text,args.title,api,args.out/'build-cache',emit,wide=wide)
        write(graph_path,graph)
    code_hash=hashlib.sha256(b''.join((ROOT/p).read_bytes() for p in ['core.py','kernel_build.py','kernel_retrieve.py','research_prompts.py'])).hexdigest()
    results=[]
    # No scoring or filtering: every prespecified question runs with all four methods.
    for qi,question in enumerate(questions):
        for method in ('agm_s','agm_r','agm_d','walk'):
            print(f'QUESTION {qi+1}/{len(questions)} METHOD {method}',flush=True)
            signature=hashlib.sha256(json.dumps([source_hash,code_hash,args.model,question,method],ensure_ascii=False).encode()).hexdigest()
            path=args.out/'answers'/(signature+'.json')
            if path.exists(): result=json.loads(path.read_text('utf-8'))
            else:
                result=answer(graph,question,api,emit,method=method,dense_mode='required')
                result['run_signature']=signature;result['generated_at']=time.strftime('%Y-%m-%dT%H:%M:%S%z')
                write(path,result)
            results.append(result)
            write(args.out/'session.json',dict(graph=graph,results=results))
    manifest=dict(kernel_version=VERSION,kernel_sha256=code_hash,source_sha256=source_hash,source_url=args.source_url,
        story=args.story,author=args.author,source_characters=len(text),scope=args.scope,
        model=args.model,methods=['agm_s','agm_r','agm_d','walk'],questions=questions,result_count=len(results),
        build_usage=graph['meta'].get('build_usage'),answer_usage=dict(calls=sum(r['usage']['calls'] for r in results),total_tokens=sum(r['usage']['total_tokens'] for r in results)),
        graph_quality=graph['meta']['quality'],build_batching=graph['meta'].get('wide'),generated_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
    write(args.out/'manifest.json',manifest)
    print('COMPLETE: graph.json, session.json, manifest.json',flush=True)
