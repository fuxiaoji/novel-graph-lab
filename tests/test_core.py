import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from core import BM25, chunks, build, answer
from tools.extract_demo import standalone

TEXT = '第一章\n林舟站在书房里。林舟把铜钥匙交给苏禾。苏禾用铜钥匙打开了侧门。苏禾从侧门离开，没有经过花园。花园里的泥土没有脚印。'


class FakeAPI:
    fingerprint = 'local-test|fixture'
    model = 'fixture'
    def __init__(self):
        self.usage = {'calls': 0, 'total_tokens': 0}
    def complete(self, system, data, max_tokens=6000):
        self.usage['calls'] += 1
        if 'condensation editor' in system:
            return {'kept':[{'text':TEXT,'time_label':'unknown'}]}
        if 'Merge ONLY' in system: return {'groups':[]}
        if 'entities' in system:
            def entity(name,typ,quote):
                return dict(name=name,type=typ,mentions=[dict(text=quote,sentence_index=0)])
            def edge(source,target,quote,typ):
                return dict(source=source,target=target,evidence=quote,type=typ,sentence_index=0)
            return {'entities': [entity('苏禾','person','苏禾从侧门离开'),entity('侧门','location','苏禾从侧门离开'),entity('铜钥匙','clue_object','苏禾用铜钥匙打开了侧门'),entity('伪造','event','原文不存在的句子')],
                    'relations':[edge('苏禾','侧门','苏禾从侧门离开，没有经过花园','located_at'),edge('铜钥匙','侧门','苏禾用铜钥匙打开了侧门','means'),edge('苏禾','侧门','苏禾飞上月球','related_to')]}
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
            self.assertEqual(g['meta']['rejected_quotes'], 1)
            for edge in g['edges']:
                self.assertEqual(TEXT[edge['start']:edge['end']], edge['quote'])
            build(TEXT, '试验小说', api, d)
            self.assertEqual(api.usage['calls'], 2)
            events = []
            result = answer(g, '苏禾怎么离开？', api, lambda k, **v: events.append(k), dense_mode='off')
            self.assertEqual(events, ['question', 'plan', 'seed', 'hop', 'hop', 'hop', 'hop', 'evidence', 'citation_check', 'answer'])
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

    def test_cancel_before_api(self):
        with tempfile.TemporaryDirectory() as d:
            api = FakeAPI()
            with self.assertRaisesRegex(ValueError, '停止'):
                build(TEXT, 'cancel', api, d, cancelled=lambda: True)
            self.assertEqual(api.usage['calls'], 0)


if __name__ == '__main__':
    unittest.main()
