const assert=require('node:assert/strict');
const {metrics,forceLayout}=require('../web/graph-utils.js');
const g={meta:{characters:6},passages:[{id:'p1',start:0,end:6,text:'甲😀乙丙丁戊'}],nodes:[
 {id:'a',evidence_ids:[{passage_id:'p1',quote:'甲😀乙'}]},
 {id:'b',evidence_ids:[{passage_id:'p1',quote:'乙丙'}]},
 {id:'c',evidence_ids:[]}],edges:[{source:'a',target:'b'}]};
const m=metrics(g);assert.equal(m.isolated,1);assert.equal(m.isolatedRate,1/3);assert.equal(m.covered,4);assert.equal(m.coverage,4/6);assert.equal(m.anchored,2);
g.nodes[1].evidence_ids.push({passage_id:'p1',quote:'甲😀乙'});assert.equal(metrics(g).covered,4);
assert.equal(metrics({...g,meta:{}}).coverage,null);
assert.equal(metrics({...g,passages:[]}).coverage,null);
const p=forceLayout(g);assert.equal(p.size,3);for(const v of p.values())for(const x of Object.values(v))assert.ok(Number.isFinite(x));
assert.deepEqual([...p],[...forceLayout(g)]);
assert.equal(metrics({nodes:[],edges:[],passages:[]}).isolatedRate,0);
console.log('Graph metrics: overlap, Unicode offsets, missing source, isolated nodes and force layout passed.');
const demo=require('../examples/demo.json').graph;console.time('739-node force layout');const layout=forceLayout(demo);console.timeEnd('739-node force layout');assert.equal(layout.size,demo.nodes.length);console.log(JSON.stringify(metrics(demo)));
