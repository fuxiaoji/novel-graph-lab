import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer
import server
from mock_api import Mock
from test_core import TEXT


class HTTPTests(unittest.TestCase):
    def test_full_protocol_and_export(self):
        previous = server.ROOT
        with tempfile.TemporaryDirectory() as folder:
            server.ROOT = Path(folder)
            app = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
            mock = ThreadingHTTPServer(('127.0.0.1', 0), Mock)
            for instance in (app, mock):
                threading.Thread(target=instance.serve_forever, daemon=True).start()
            base = f'http://127.0.0.1:{app.server_port}'
            def post(path, data, origin=None):
                headers = {'Content-Type': 'application/json'}
                if origin:
                    headers['Origin'] = origin
                with urllib.request.urlopen(urllib.request.Request(base+path, json.dumps(data).encode(), headers)) as r:
                    return json.load(r)
            try:
                config = dict(base_url=f'http://127.0.0.1:{mock.server_port}', model='fixture', api_key='TEST_SECRET_DO_NOT_EXPORT')
                def run(payload):
                    j = post('/api/run', payload)
                    for _ in range(100):
                        with urllib.request.urlopen(base+'/api/jobs/'+j['id']) as r:
                            result = json.load(r)
                        if result['status'] != 'running':
                            break
                        time.sleep(.02)
                    self.assertEqual(result['status'], 'complete', result.get('error'))
                    return result
                result = run(dict(config=config, text=TEXT, title='HTTP小说', question='苏禾怎么离开？'))
                self.assertEqual(result['result']['usage']['calls'], 3)
                second = run(dict(config=config, graph=result['graph'], question='苏禾用了什么工具？'))
                self.assertEqual(second['result']['usage']['calls'], 2)
                export = post('/api/export', dict(session={'graph': result['graph'], 'results': [result['result']]}, format='html'))
                with urllib.request.urlopen(base+export['url']) as r:
                    html = r.read().decode()
                self.assertIn('window.__BOOT__=', html)
                self.assertNotIn(config['api_key'], html)
                self.assertNotIn(config['api_key'], json.dumps(result))
                for file in Path(folder).rglob('*.json'):
                    self.assertNotIn(config['api_key'], file.read_text('utf-8'))
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    post('/api/run', {}, 'https://foreign.example')
                self.assertEqual(caught.exception.code, 403)
            finally:
                for instance in (app, mock):
                    instance.shutdown()
                    instance.server_close()
                server.ROOT = previous
                server.JOBS.clear()


if __name__ == '__main__':
    unittest.main()
