"""Local-only application server; run python server.py --open."""
from __future__ import annotations
import argparse
import json
import mimetypes
import re
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from core import API, build, answer
from tools.extract_demo import standalone

ROOT = Path(__file__).resolve().parent
JOBS = {}
LOCK = threading.Lock()


def run_job(job, payload):
    def emit(kind, **data):
        with LOCK:
            job['events'].append(dict(kind=kind, **data))
    try:
        api = API(payload.get('config', {}))
        graph = payload.get('graph')
        if graph is None:
            graph = build(str(payload.get('text', '')), str(payload.get('title', '未命名小说')), api, ROOT/'data/cache', emit,
                          lambda: job['cancel'], int(payload.get('chunk_size', 5000)))
        else:
            validate_graph(graph)
        if job['cancel']:
            raise ValueError('任务已停止。')
        with LOCK:
            job['graph'] = graph
        result = answer(graph, str(payload.get('question', '')), api, emit, lambda: job['cancel'])
        if job['cancel']:
            raise ValueError('任务已停止。')
        with LOCK:
            job.update(status='complete', result=result)
    except Exception as exc:
        # Unexpected exceptions never echo provider bodies, credentials or novel content.
        message = str(exc) if isinstance(exc, ValueError) else '处理失败，请检查模型返回格式并重试。'
        with LOCK:
            job.update(status='cancelled' if job['cancel'] else 'error', error=message)
    finally:
        payload.clear()


def validate_graph(g):
    if not isinstance(g, dict) or not all(isinstance(g.get(k), list) for k in ('nodes', 'edges', 'passages')):
        raise ValueError('图谱文件缺少 nodes、edges 或 passages 数组。')
    ids = {n['id'] for n in g['nodes']}
    if len(ids) != len(g['nodes']) or any(e['source'] not in ids or e['target'] not in ids for e in g['edges']):
        raise ValueError('图谱包含重复节点或不存在的关系端点。')


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, status, data, content_type='application/json; charset=utf-8'):
        body = json.dumps(data, ensure_ascii=False).encode() if not isinstance(data, bytes) else data
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def local_request(self):
        expected = {'127.0.0.1', 'localhost', '::1'}
        host = urlparse('//'+self.headers.get('Host', '')).hostname
        origin = self.headers.get('Origin')
        return host in expected and (not origin or origin in (f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'))

    def do_GET(self):
        if not self.local_request():
            return self.reply(403, {'error': '仅接受本地页面访问。'})
        path = urlparse(self.path).path
        if path.startswith('/api/jobs/'):
            with LOCK:
                job = JOBS.get(path.rsplit('/', 1)[-1])
                if not job:
                    return self.reply(404, {'error': '任务不存在或服务已重启。'})
                return self.reply(200, {k: v for k, v in job.items() if k != 'cancel'})
        mapping = {'/': ROOT/'web/index.html', '/app.js': ROOT/'web/app.js', '/style.css': ROOT/'web/style.css', '/demo.json': ROOT/'examples/demo.json'}
        mapping['/graph-utils.js'] = ROOT/'web/graph-utils.js'
        if re.fullmatch(r'/exports/[a-f0-9]{32}\.(html|json)', path):
            mapping[path] = ROOT/'outputs/exports'/path.rsplit('/', 1)[-1]
            if not mapping[path].is_file():
                return self.reply(404, {'error': '导出文件不存在。'})
        if path not in mapping:
            return self.reply(404, {'error': 'Not found'})
        file = mapping[path]
        self.reply(200, file.read_bytes(), (mimetypes.guess_type(file.name)[0] or 'text/plain')+'; charset=utf-8')

    def do_POST(self):
        if not self.local_request() or 'application/json' not in self.headers.get('Content-Type', ''):
            return self.reply(403, {'error': '仅接受本地 JSON 请求。'})
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 40_000_000:
                return self.reply(413, {'error': '输入太大，单次请求上限 40MB。'})
            payload = json.loads(self.rfile.read(length))
            if self.path == '/api/export':
                data = payload.get('session', {})
                validate_graph(data.get('graph'))
                # Export a narrowly selected session, never request config/credentials.
                data = {'graph': data['graph'], 'results': data.get('results', [])}
                suffix = 'json' if payload.get('format') == 'json' else 'html'
                name = uuid.uuid4().hex+'.'+suffix
                dest = ROOT/'outputs/exports'/name
                dest.parent.mkdir(parents=True, exist_ok=True)
                if suffix == 'html':
                    standalone(data, dest)
                else:
                    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2), 'utf-8')
                return self.reply(200, {'url': '/exports/'+name, 'path': str(dest)})
            if self.path == '/api/run':
                # Single active build avoids duplicate API cost/cache races.
                with LOCK:
                    if any(j['status'] == 'running' for j in JOBS.values()):
                        return self.reply(409, {'error': '已有任务运行中，请等待或停止后再试。'})
                    for key in list(JOBS):
                        if time.time()-JOBS[key]['created'] > 3600:
                            del JOBS[key]
                    job = dict(id=uuid.uuid4().hex, status='running', events=[], cancel=False, created=time.time())
                    JOBS[job['id']] = job
                threading.Thread(target=run_job, args=(job, payload), daemon=True).start()
                return self.reply(202, {'id': job['id']})
            if self.path == '/api/cancel':
                with LOCK:
                    job = JOBS.get(payload.get('id'))
                    if job:
                        job['cancel'] = True
                return self.reply(200, {'ok': bool(job)})
            self.reply(404, {'error': 'Not found'})
        except (ValueError, TypeError):
            self.reply(400, {'error': '请求格式无效。'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Novel Graph Lab: http://127.0.0.1:{server.server_port}', flush=True)
    if args.open:
        webbrowser.open(f'http://127.0.0.1:{server.server_port}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
