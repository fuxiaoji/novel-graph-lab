import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from core import BM25, chunks, build, answer, retrieve
from tools.extract_demo import standalone

TEXT = '第一章\n林舟站在书房里。林舟把铜钥匙交给苏禾。苏禾用铜钥匙打开了侧门。苏禾从侧门离开，没有经过花园。花园里的泥土没有脚印。'


class FakeAPI:
    fingerprint = 'local-test|fixture'
    model = 'fixture'
    def __init__(self):
        self.usage = {'calls': 0, 'total_tokens': 0}
    def complete(self, system, data):
        self.usage['calls'] += 1
        if 'entities' in system:
            return {'summary': '苏禾持钥匙从侧门离开。', 'entities': [
                {'name': '苏禾', 'type': 'person', 'quote': '苏禾从侧门离开', 'aliases': []},
                {'name': '侧门', 'type': 'location', 'quote': '苏禾从侧门离开', 'aliases': []},
                {'name': '铜钥匙', 'type': 'clue_object', 'quote': '苏禾用铜钥匙打开了侧门', 'aliases': []},
                {'name': '伪造', 'type': 'event', 'quote': '原文不存在的句子'}], 'relations': [
                {'source': '苏禾', 'target': '侧门', 'quote': '苏禾从侧门离开，没有经过花园', 'type': 'located_at'},
                {'source': '铜钥匙', 'target': '侧门', 'quote': '苏禾用铜钥匙打开了侧门', 'type': 'means'},
                {'source': '苏禾', 'target': '侧门', 'quote': '苏禾飞上月球', 'type': 'related_to'}]}
        if 'glossary' in data:
            return {'query': '苏禾 侧门 铜钥匙 离开', 'targets': ['苏禾'], 'summary': '检索离开路径和开门工具。'}
        return {'answer': '苏禾用铜钥匙打开侧门并离开。[c1]', 'citations': ['c1', 'c999'],
                'evidence_summary': '原文描述了钥匙与离开路径。', 'uncertainty': ''}


class PipelineTests(unittest.TestCase):
    def test_chunk_coverage(self):
        text = ('一段文字。\n'*2000)+'末尾独一无二'
        ps = chunks(text, 800, 100)
        cover = set()
        for p in ps:
            self.assertEqual(p['text'], text[p['start']:p['end']])
            cover.update(range(p['start'], p['end']))
        self.assertEqual(len(cover), len(text))
        self.assertTrue(ps[-1]['text'].endswith('末尾独一无二'))
        with self.assertRaises(ValueError):
            chunks(text, 500, 500)

    def test_chinese_retrieval(self):
        hits = BM25(['苏禾从侧门离开了房屋。', '楼上有一个摆钟。']).search('侧门离开')
        self.assertEqual(hits[0][0], 0)
        self.assertEqual(BM25(['hello']).search('不存在'), [])

    def test_grounding_cache_and_answer(self):
        with tempfile.TemporaryDirectory() as d:
            api = FakeAPI()
            g = build(TEXT, '试验小说', api, d)
            self.assertEqual(len(g['nodes']), 3)
            self.assertEqual(len(g['edges']), 2)
            self.assertEqual(g['meta']['rejected_quotes'], 2)
            for edge in g['edges']:
                self.assertEqual(TEXT[edge['start']:edge['end']], edge['quote'])
            build(TEXT, '试验小说', api, d)
            self.assertEqual(api.usage['calls'], 1)
            events = []
            result = answer(g, '苏禾怎么离开？', api, lambda k, **v: events.append(k))
            self.assertEqual(events, ['question', 'plan', 'seed', 'hop', 'hop', 'evidence', 'answer'])
            self.assertNotIn('c999', result['citations'])
            self.assertTrue(result['warnings'])
            for ev in result['evidence']:
                self.assertEqual(TEXT[ev['start']:ev['end']], ev['quote'])
            path = Path(d)/'replay.html'
            g['title'] = '</script><script>alert(1)</script>'
            standalone({'graph': g, 'results': [result]}, path)
            html = path.read_text('utf-8')
            self.assertNotIn(g['title'], html)
            class Assets(HTMLParser):
                external = []
                def handle_starttag(self, tag, attrs):
                    if tag == 'script' and dict(attrs).get('src'):
                        self.external.append(dict(attrs)['src'])
            parser = Assets()
            parser.feed(html)
            self.assertEqual(parser.external, [])

    def test_hops_are_real_edges(self):
        g = {'nodes': [dict(id=str(i), name='seed' if i==0 else f'node{i}') for i in range(4)],
             'edges': [dict(id=f'e{i}', source=str(i), target=str(i+1), confidence=.8) for i in range(3)]}
        stages, seen = retrieve(g, 'seed')
        self.assertEqual(seen, {'0', '1', '2'})
        self.assertEqual(stages[1]['traversals'][0]['source'], '0')
        self.assertEqual(stages[2]['traversals'][0]['target'], '2')

    def test_cancel_before_api(self):
        with tempfile.TemporaryDirectory() as d:
            api = FakeAPI()
            with self.assertRaisesRegex(ValueError, '停止'):
                build(TEXT, 'cancel', api, d, cancelled=lambda: True)
            self.assertEqual(api.usage['calls'], 0)


if __name__ == '__main__':
    unittest.main()
