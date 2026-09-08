"""Local deterministic API fixture for browser smoke tests. Never a real model."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from test_core import FakeAPI


class Mock(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass
    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        result = FakeAPI().complete(req['messages'][0]['content'], json.loads(req['messages'][1]['content']))
        body = json.dumps({'choices': [{'message': {'content': json.dumps(result, ensure_ascii=False)}, 'finish_reason': 'stop'}],
                           'usage': {'total_tokens': 100}}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8766), Mock).serve_forever()
