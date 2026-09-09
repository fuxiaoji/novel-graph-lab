import tempfile
import unittest
from unittest.mock import patch
from core import build, answer
from kernel_retrieve import pagerank, navigate, Dense
from test_core import FakeAPI, TEXT


class KernelTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.graph=build(TEXT,'fixture',FakeAPI(),self.folder.name)

    def test_rank_conservation_and_real_flows(self):
        ranks,seeds,frames=pagerank(self.graph,'苏禾')
        self.assertAlmostEqual(sum(ranks.values()),1)
        by_id={e['id']:e for e in self.graph['edges']}
        for frame in frames:
            for flow in frame['traversals']:
                e=by_id[flow['edge_id']]
                self.assertEqual({flow['source'],flow['target']},{e['source'],e['target']})
                self.assertGreater(flow['mass'],0)

    def test_walk_uses_only_current_neighbors(self):
        events=[]
        class Walker(FakeAPI):
            def complete(self,system,data,max_tokens=6000):
                if 'starting node' in system: return {'node_id':'n1'}
                if 'navigation tool controller' in system: return {'action':'traverse','edge_id':'e2'}
                return super().complete(system,data)
        indices,reason=navigate(self.graph,'苏禾',Walker(),lambda k,**d:events.append(dict(kind=k,**d)),lambda:False)
        self.assertEqual(reason,'invalid_action') # e2 exists but is not adjacent to n1.
        self.assertFalse(any(e['kind']=='hop' for e in events))

    def test_walk_read_choose_read_and_stop(self):
        events=[]
        class Walker(FakeAPI):
            reads=0
            def complete(self,system,data,max_tokens=6000):
                if 'starting node' in system: return {'node_id':'n1'}
                if 'navigation tool controller' in system:
                    self.reads+=1
                    return {'action':'traverse','edge_id':'e1'} if self.reads==1 else {'action':'stop'}
                return super().complete(system,data)
        _,reason=navigate(self.graph,'苏禾',Walker(),lambda k,**d:events.append(dict(kind=k,**d)),lambda:False)
        self.assertEqual([e['kind'] for e in events],['read','hop','read','stop'])
        self.assertEqual(events[2]['node_ids'],['n2'])
        self.assertEqual(reason,'model_stop')

    def test_reranker_invalid_ids_never_reach_answer(self):
        class Ranker(FakeAPI):
            def complete(self,system,data,max_tokens=6000):
                if 'Select up to 8' in system:
                    self.usage['calls']+=1
                    return {'selected_passage_ids':['p999','p1','p1']}
                return super().complete(system,data)
        result=answer(self.graph,'苏禾怎么离开？',Ranker(),method='agm_r',dense_mode='off')
        rerank=next(e for e in result['trace'] if e['kind']=='rerank')
        self.assertEqual(rerank['rejected_ids'],['p999'])
        self.assertEqual(rerank['selected_passage_ids'],['p1'])
        self.assertEqual([e['id'] for e in result['evidence']],['c1'])

    def test_disagreement_triggers_evidence_referee(self):
        class Judge(FakeAPI):
            readers=0
            referee=False
            def complete(self,system,data,max_tokens=6000):
                if 'evidence referee' in system:
                    self.referee=True
                    assert set(data['candidates'])=={'agm_s','agm_r'}
                    assert data['evidence']
                raw=super().complete(system,data)
                if 'Read only supplied evidence' in system:
                    self.readers+=1;raw['answer_key']=str(self.readers)
                return raw
        api=Judge();result=answer(self.graph,'苏禾怎么离开？',api,method='agm_d',dense_mode='off')
        self.assertTrue(api.referee)
        self.assertEqual(len(result['route_records']),2)
        self.assertFalse(next(e for e in result['trace'] if e['kind']=='arbitrate')['agreement'])

    def test_dense_failure_is_explicit(self):
        with patch('kernel_retrieve.urllib.request.urlopen',side_effect=OSError('offline')):
            d=Dense('required')
            with tempfile.TemporaryDirectory() as folder:
                from pathlib import Path
                d.cache=Path(folder)
                with self.assertRaisesRegex(ValueError,'BGE-M3'): d.embed(['uncached test'])

    def test_negative_line_reference_rejected(self):
        class BadLine(FakeAPI):
            def complete(self,system,data,max_tokens=6000):
                raw=super().complete(system,data)
                for r in raw.get('relations',[]): r['sentence_index']=-1
                return raw
        with tempfile.TemporaryDirectory() as folder:
            graph=build(TEXT,'bad',BadLine(),folder)
        self.assertEqual(graph['edges'],[])
        self.assertFalse(graph['meta']['quality']['passed'])

    def test_wide_batching_groups_pass1_and_keeps_grounding(self):
        from core import chunks as split
        long_text=TEXT+'。'+'纯粹的景物描写，与情节无关。'*60
        passages=split(long_text,500,50)
        self.assertGreater(len(passages),1)
        calls=[]
        class WideFake(FakeAPI):
            def complete(self,system,data,max_tokens=6000):
                calls.append(('wide' if 'large context' in system else 'other',system[:24]))
                if 'large context' in system:
                    kept=[]
                    for seg in data['segments']:
                        kept.append(dict(segment_id=seg['id'],text=seg['text'],time_label='unknown'))
                    return {'kept':kept}
                if 'condensation editor' in system:
                    raise AssertionError('wide mode must not call per-chunk pass1')
                return super().complete(system,data)
        with tempfile.TemporaryDirectory() as folder:
            graph=build(long_text,'wide',WideFake(),folder,wide=dict(pass1_group=len(passages),pass2_chars=10000,max_tokens=12000,workers=2))
        self.assertEqual(graph['meta']['wide'],dict(pass1_group=len(passages),pass2_chars=10000,max_tokens=12000,workers=2))
        self.assertTrue(any(c[0]=='wide' for c in calls))
        source={p['id']:p for p in graph['passages']}
        for e in graph['edges']:
            p=source[e['passage_id']]
            self.assertEqual(p['text'][e['start']-p['start']:e['end']-p['start']],e['quote'])
        self.assertEqual(len(graph['nodes']),3)
        self.assertEqual(sorted(e['type'] for e in graph['edges']),['located_at','means'])


if __name__=='__main__': unittest.main()
