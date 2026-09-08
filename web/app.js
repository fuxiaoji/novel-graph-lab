'use strict';
const $ = id => document.getElementById(id);
const colors = {person:'#6082a2', location:'#709386', time_anchor:'#b4975b', clue_object:'#be8b62', event:'#b47b83', evidence_sentence:'#8e82a9'};
const typeNames = {person:'人物', location:'地点', time_anchor:'时间', clue_object:'物件', event:'事件', evidence_sentence:'证词'};
const S = {graph:null, result:null, demo:null, config:null, text:'', title:'', time:0, playing:false, speed:1, yaw:.25, pitch:.18, zoom:1, layout:'force', positions:new Map(), points:[], selected:null, job:null, liveTrace:[], frame:0, viewIds:new Set()};
const canvas = $('graph'), ctx = canvas.getContext('2d');
let cssSource='', jsSource='', htmlSource='';
const esc = s => String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(text){$('toast').textContent=text;$('toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').hidden=true,6500);}
function tabs(node){$('answerPane').hidden=node;$('nodePane').hidden=!node;$('answerTab').classList.toggle('selected',!node);$('nodeTab').classList.toggle('selected',node);}
$('answerTab').onclick=()=>tabs(false);$('nodeTab').onclick=()=>tabs(true);
$('legend').innerHTML=Object.keys(colors).map(k=>`<span><i style="background:${colors[k]}"></i>${typeNames[k]}</span>`).join('');
function trace(){return S.result?.trace || S.liveTrace;}
const duration=()=>Math.max(1,trace().length)*3.8;
function stageIndex(){return Math.floor((S.time+0.000001)/3.8);}
function stage(){return S.overview?undefined:trace()[Math.min(trace().length-1,stageIndex())];}
function hydrateGraph(g){
  if(!g || !Array.isArray(g.nodes)||!Array.isArray(g.edges)||!Array.isArray(g.passages))throw Error('不是有效的 Novel Graph Lab 图谱。');
  const ids=new Set(g.nodes.map(n=>n.id));
  if(ids.size!==g.nodes.length||g.edges.some(e=>!ids.has(e.source)||!ids.has(e.target)))throw Error('图谱存在重复节点或无效连线。');
  S.graph=g;S.nodes=new Map(g.nodes.map(n=>[n.id,n]));S.edges=new Map(g.edges.map(e=>[e.id,e]));
  S.adj=new Map(g.nodes.map(n=>[n.id,[]]));for(const e of g.edges){S.adj.get(e.source).push(e);S.adj.get(e.target).push(e);}
  S.labelIds=new Set([...g.nodes].sort((a,b)=>S.adj.get(b.id).length-S.adj.get(a.id).length).slice(0,6).map(n=>n.id));
  S.positions=GraphAnalysis.forceLayout(g);S.focusKey=null;const count=g.nodes.length;
  S.metrics=GraphAnalysis.metrics(g);
  const m=S.metrics;
  $('isolatedRate').textContent=(m.isolatedRate*100).toFixed(1)+'%';
  $('isolatedDetail').textContent=`${m.isolated} / ${m.nodes} 个节点无其他节点连接`;
  $('coverageRate').textContent=m.coverage===null?'无法计算':(m.coverage*100).toFixed(1)+'%';
  $('coverageDetail').textContent=m.coverage===null?'缺少完整原文或可校验位置，不能推算覆盖率。':`${m.covered.toLocaleString()} / ${m.total.toLocaleString()} 原文字符；${m.anchored} / ${m.nodes} 节点已定位原文。`;
  showOverview();
  $('bookTitle').textContent=g.title||'未命名小说';$('nodeCount').textContent=count.toLocaleString();$('edgeCount').textContent=g.edges.length.toLocaleString();
  $('bookInfo').textContent=g.meta?.mode==='historical'?'研究示例 / 已保存的图谱与问答':`${(g.meta?.characters||0).toLocaleString()} 字符 · ${g.passages.length} 个文本块`;
  S.selected=null;S.viewIds=new Set();$('nodeTitle').textContent='选择一个节点';$('nodeEvidence').replaceChildren();$('nodeRelations').replaceChildren();
}
function setResult(result){
  S.result=result;S.liveTrace=[];S.time=0;S.playing=false;S.viewIds=new Set((result.trace||[]).flatMap(s=>s.node_ids||[]));
  $('modeBadge').textContent=result.mode==='historical'?'历史记录回放':(result.method_label||'真实 API 记录');
  $('modeNote').textContent=result.mode==='historical'?'历史 Demo：回放原始检索与回答记录':'已完成 API 问答 · 可重播或继续提问';
  $('answerState').textContent=result.mode==='historical'?'历史回答 · 引用来自原 Demo':'回答完成 · 点击引用核对原文';
  $('answerText').innerHTML=esc(result.answer).replace(/\[(c\d+)\]/g,(_,id)=>`<button class="citation" data-cite="${id}">[${id}]</button>`);
  $('uncertainty').textContent=[result.uncertainty,...(result.warnings||[])].filter(Boolean).join(' ');
  $('evidenceCount').textContent=`/ ${result.evidence.length}`;
  $('evidenceList').innerHTML=result.evidence.map(e=>`<article class="evidence" id="cite-${esc(e.id)}" data-cite="${esc(e.id)}"><strong>${esc(e.id.toUpperCase())} · ${e.start!=null?`原文字符 ${e.start}–${e.end}`:'历史证据（无完整原文坐标）'}</strong><p>${esc(e.quote)}</p></article>`).join('');
  S.overview=true;renderSteps();updateStage();tabs(false);
  if(result.usage)$('footerStatus').textContent=`本次 API ${result.usage.calls} 次 · ${result.usage.total_tokens.toLocaleString()} tokens · 证据已保留`;
}
function renderSteps(){ $('steps').innerHTML=trace().map((s,i)=>`<button data-step="${i}" title="${esc(s.label)}">${String(i+1).padStart(2,'0')}<br>${esc(s.label.replace(/LLM · |一阶 · |二阶 · |三阶 · /g,''))}</button>`).join('');if(!trace().length){S.time=0;S.playing=false;$('evidenceCount').textContent='';$('modeBadge').textContent='等待新检索';$('answerState').textContent='等待检索';updateStage();}}
function updateStage(){const s=stage();if(s){$('stageTitle').textContent=s.label;$('stageDetail').textContent=s.detail||'';}else{$('stageTitle').textContent=S.graph?'完整小说图谱':'从问题出发，连接线索';$('stageDetail').textContent=S.graph?`全图 ${S.graph.nodes.length} 节点 · ${S.graph.edges.length} 条边 · 包含 ${S.metrics?.isolated||0} 个孤立节点。播放后查看检索路径。`:'拖拽旋转 · 滚轮缩放 · 点击节点查看证据';}
  const current=S.overview?-1:stageIndex();document.querySelectorAll('[data-step]').forEach((b,i)=>{b.classList.toggle('active',i===current);b.classList.toggle('past',i<current);});
  $('scrub').value=Math.round(S.time/duration()*1000);$('play').textContent=S.playing?'Ⅱ':'▶';
}
$('steps').onclick=e=>{const b=e.target.closest('[data-step]');if(b){S.overview=false;S.time=+b.dataset.step*3.8;S.playing=false;updateStage();}};
$('play').onclick=()=>{if(!trace().length)return;S.overview=false;if(S.time>=duration()-.02)S.time=0;S.playing=!S.playing;updateStage();};
$('prev').onclick=()=>{S.overview=false;S.time=Math.max(0,(stageIndex()-1)*3.8);S.playing=false;updateStage();};
$('next').onclick=()=>{S.overview=false;S.time=Math.min(duration()-.01,(stageIndex()+1)*3.8);S.playing=false;updateStage();};
$('speed').onchange=e=>S.speed=+e.target.value;
$('scrub').oninput=e=>{S.overview=false;S.time=+e.target.value/1000*(duration()-.001);S.playing=false;updateStage();};
function showOverview(){S.overview=true;S.playing=false;S.time=0;S.layout='force';S.zoom=1;$('focus').checked=false;$('force').classList.add('selected');$('layers').classList.remove('selected');updateStage();}
$('overview').onclick=showOverview;
$('force').onclick=()=>{S.layout='force';$('force').classList.add('selected');$('layers').classList.remove('selected');};
$('layers').onclick=()=>{S.layout='layers';$('layers').classList.add('selected');$('force').classList.remove('selected');};
$('resetView').onclick=()=>{S.yaw=.25;S.pitch=.18;S.zoom=1;};
function project(p,w,h){const ca=Math.cos(S.yaw),sa=Math.sin(S.yaw),cb=Math.cos(S.pitch),sb=Math.sin(S.pitch);const x=p.x*ca-p.z*sa,z=p.x*sa+p.z*ca,y=p.y*cb-z*sb,z2=p.y*sb+z*cb;const scale=650/(750+z2)*Math.min(w/590,h/510)*S.zoom;return{x:w/2+x*scale,y:h/2+15+y*scale,z:z2,scale};}
function focusedPositions(ids){
  const key=ids.join('|');if(S.focusKey===key)return S.focusPositions;S.focusKey=key;
  const ps=ids.map(id=>({...S.positions.get(id)})),center={x:0,y:0,z:0};
  for(const p of ps)for(const axis of ['x','y','z'])center[axis]+=p[axis]/ps.length;
  let radius=Math.max(1,...ps.map(p=>Math.hypot(p.x-center.x,p.y-center.y,p.z-center.z)));
  for(const p of ps)for(const axis of ['x','y','z'])p[axis]=(p[axis]-center[axis])*210/radius;
  if(ps.length<180)for(let k=0;k<35;k++)for(let i=0;i<ps.length;i++)for(let j=i+1;j<ps.length;j++){
    const a=ps[i],b=ps[j],dx=b.x-a.x||.01,dy=b.y-a.y||.01,dz=b.z-a.z||.01,d=Math.hypot(dx,dy,dz);
    if(d<55){const f=(55-d)*.13;for(const[axis,v]of[['x',dx],['y',dy],['z',dz]]){a[axis]-=v/d*f;b[axis]+=v/d*f;}}
  }
  S.focusPositions=new Map(ids.map((id,i)=>[id,ps[i]]));return S.focusPositions;
}
function line(a,b,color,width=1){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();}
function glow(p,color,r=4,bright=false){if(bright){const g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r*5);g.addColorStop(0,color+'30');g.addColorStop(1,color+'00');ctx.fillStyle=g;ctx.beginPath();ctx.arc(p.x,p.y,r*5,0,Math.PI*2);ctx.fill();}ctx.fillStyle=color;ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fill();}
function frame(ts){
  const dt=Math.min(.05,(ts-(S.frame||ts))/1000);S.frame=ts;
  if(!document.hidden){
  if(S.playing){S.overview=false;S.time=Math.min(duration()-.001,S.time+dt*S.speed);if(S.time>=duration()-.002)S.playing=false;updateStage();}
  if($('rotate').checked&&!drag&&!matchMedia('(prefers-reduced-motion: reduce)').matches)S.yaw+=dt*.055;
  const rect=canvas.getBoundingClientRect(),w=rect.width,h=rect.height,dpr=Math.min(devicePixelRatio||1,2);
  if(canvas.width!==Math.round(w*dpr)||canvas.height!==Math.round(h*dpr)){canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);}
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);
  if(S.graph){
    const st=stage(),active=new Set(st?.node_ids||[]),activeEdges=new Set(st?.edge_ids||[]),focus=$('focus').checked;
    const visible=new Set((focus&&S.viewIds.size)?S.viewIds:S.graph.nodes.map(n=>n.id));
    canvas.dataset.visibleNodes=visible.size;canvas.dataset.totalNodes=S.graph.nodes.length;
    const focused=focus&&S.viewIds.size?focusedPositions([...visible]):null;
    const projected=new Map();S.graph.nodes.forEach((n,i)=>{if(!visible.has(n.id))return;let p=focused?.get(n.id)||S.positions.get(n.id);if(S.layout==='layers'){const pos=n.text_pos??n.x??i/Math.max(1,S.graph.nodes.length);p={x:(pos-.5)*480,y:(Object.keys(colors).indexOf(n.type)-2.5)*65,z:((n.y??Math.sin(i*2.3)*.5+.5)-.5)*240};}projected.set(n.id,project(p,w,h));});
    for(const e of S.graph.edges){const a=projected.get(e.source),b=projected.get(e.target);if(!a||!b)continue;const on=activeEdges.has(e.id);line(a,b,on?'#507998aa':S.selected&&(e.source===S.selected||e.target===S.selected)?'#6b8aa8aa':'#70879e38',on?1.6:.65);}
    const sorted=[...projected].sort((a,b)=>b[1].z-a[1].z);S.points=[];const labelBoxes=[];
    for(const[id,p]of sorted){const n=S.nodes.get(id),on=active.has(id)||id===S.selected;const c=on?'#385e7f':colors[n.type]||'#899eb2';const r=Math.max(1.3,(on?4:2.2)*p.scale);ctx.globalAlpha=on?1:((st?.kind==='question'||!st)? .9:.5);glow(p,c,r,on);ctx.globalAlpha=1;S.points.push({id,...p,r});if((on&&(active.size<26||id===S.selected))||(S.overview&&S.labelIds.has(id))){
      ctx.font='11px "Segoe UI","Microsoft YaHei",sans-serif';const label=n.name.length>22?n.name.slice(0,22)+'…':n.name,lw=ctx.measureText(label).width;let lx=Math.min(w-lw-12,p.x+r+5),ly=p.y+3;
      for(let k=0;k<15;k++){if(!labelBoxes.some(b=>lx<b.x+b.w&&lx+lw>b.x&&Math.abs(ly-b.y)<14))break;ly+=14;}
      labelBoxes.push({x:lx,y:ly,w:lw});if(Math.abs(ly-p.y)>18)line(p,{x:lx,y:ly-4},'#7892aa77',.5);ctx.fillStyle='#40566a';ctx.fillText(label,lx,ly);
    }}
    const progress=(S.time%3.8)/3.8;
    const travel=st?.traversals?.length?st.traversals:(st?.edge_ids||[]).map(id=>S.edges.get(id)).filter(Boolean);
    travel.forEach((e,i)=>{const a=projected.get(e.source),b=projected.get(e.target);if(!a||!b)return;for(let j=0;j<2;j++){const t=(progress*2+i*.13+j*.5)%1;const p={x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t};glow(p,'#386c94',3,true);}});
    if(st?.kind==='seed'||st?.kind==='question'||st?.kind==='plan'){
      const origin={x:w/2,y:Math.max(105,h*.26)};glow(origin,'#547c9d',7,true);ctx.textAlign='center';ctx.fillStyle='#526e86';ctx.font='11px "Microsoft YaHei"';ctx.fillText('问题',origin.x,origin.y-18);ctx.textAlign='left';
      if(st.kind==='seed')for(const id of active){const p=projected.get(id);if(!p)continue;line(origin,p,'#7094b45c',1);const t=progress;glow({x:origin.x+(p.x-origin.x)*t,y:origin.y+(p.y-origin.y)*t},'#547c9d',3,true);}
    }
    if(st?.kind==='answer'||st?.kind==='evidence'){
      const target={x:w-75,y:h-110};glow(target,'#9a7850',8,true);ctx.fillStyle='#796746';ctx.font='11px "Microsoft YaHei"';ctx.fillText(st.kind==='answer'?'回答':'证据',target.x-27,target.y+27);
      [...active].slice(0,16).forEach((id,i)=>{const a=projected.get(id);if(!a)return;line(a,target,'#ab94714a');const t=(progress+i*.073)%1;glow({x:a.x+(target.x-a.x)*t,y:a.y+(target.y-a.y)*t},'#a68454',2.5,true);});
    }
  }}requestAnimationFrame(frame);
}
let drag=null;
canvas.onpointerdown=e=>{drag={x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY};canvas.setPointerCapture(e.pointerId);};
canvas.onpointermove=e=>{const r=canvas.getBoundingClientRect();if(drag){S.yaw+=(e.clientX-drag.x)*.006;S.pitch=Math.max(-1.4,Math.min(1.4,S.pitch+(e.clientY-drag.y)*.006));drag.x=e.clientX;drag.y=e.clientY;return;}const p=hit(e.clientX-r.left,e.clientY-r.top);$('hover').hidden=!p;if(p){$('hover').textContent=S.nodes.get(p.id).name;$('hover').style.left=Math.min(r.width-180,e.clientX-r.left+14)+'px';$('hover').style.top=e.clientY-r.top+15+'px';}canvas.style.cursor=p?'pointer':'grab';};
canvas.onpointerup=e=>{if(drag&&Math.hypot(e.clientX-drag.startX,e.clientY-drag.startY)<6){const r=canvas.getBoundingClientRect(),p=hit(e.clientX-r.left,e.clientY-r.top);if(p)selectNode(p.id);}drag=null;};
canvas.onpointercancel=()=>drag=null;canvas.onpointerleave=()=>{$('hover').hidden=true;};
canvas.addEventListener('wheel',e=>{e.preventDefault();S.zoom=Math.max(.3,Math.min(4,S.zoom*Math.exp(-e.deltaY*.001)));},{passive:false});
function hit(x,y){return [...S.points].reverse().find(p=>Math.hypot(x-p.x,y-p.y)<Math.max(9,p.r+4));}
function selectNode(id){const n=S.nodes.get(id);if(!n)return;S.selected=id;tabs(true);$('nodeTitle').textContent=n.name;$('nodeType').textContent=`${typeNames[n.type]||n.type} · ${id} · ${(S.adj.get(id)||[]).length} 条关系`;
  $('nodeEvidence').innerHTML=(n.evidence_ids||[]).slice(0,12).map(e=>`<div class="evidence"><strong>${esc(e.passage_id||'历史片段')}</strong><p>${esc(e.quote)}</p></div>`).join('');
  $('nodeRelations').innerHTML=(S.adj.get(id)||[]).slice(0,30).map(e=>`<div class="relation">${esc(S.nodes.get(e.source)?.name)} <span class="accent">${esc(e.type)}</span> ${esc(S.nodes.get(e.target)?.name)}<p class="micro">${esc(e.quote)}</p></div>`).join('');
}
document.addEventListener('click',e=>{const el=e.target.closest('[data-cite]');if(!el||!S.result)return;const item=S.result.evidence.find(x=>x.id===el.dataset.cite);if(!item)return;document.querySelectorAll('.evidence.active').forEach(el=>el.classList.remove('active'));const card=$('cite-'+item.id);card?.classList.add('active');card?.scrollIntoView({behavior:'smooth',block:'nearest'});if(item.node_ids?.length)S.selected=item.node_ids[0];});
async function loadDemo(){if(S.job)return toast('请先等待当前任务完成。');try{S.demo=window.__BOOT__||S.originalDemo||await fetch('/demo.json').then(r=>r.json());S.originalDemo=S.demo;S.text='';hydrateGraph(S.demo.graph);$('presets').hidden=false;$('presets').innerHTML=S.demo.results.map((r,i)=>`<option value="${i}">${i+1}. [${esc(r.method_label||r.method||"历史")}] ${esc(r.question)}</option>`).join('');selectPreset(0);}catch(e){toast(e.message);}}
function selectPreset(i){const r=S.demo.results[i];if(r.method)$('method').value=r.method;$('question').value=r.question;setResult(r);}
$('presets').onchange=e=>selectPreset(+e.target.value);$('loadDemo').onclick=loadDemo;
$('importBtn').onclick=()=>{if(window.__PUBLIC_DEMO__)return toast('在线示例只回放已有记录。请从 GitHub 下载项目，在本机运行后导入小说和 API。');$('importDialog').showModal();};$('closeDialog').onclick=()=>$('importDialog').close();
async function readNovel(){const file=$('novelFile').files[0];if(!file)return;if(file.size>20_000_000)throw Error('文本文件上限为 20MB。');const buf=await file.arrayBuffer();$('novelText').value=new TextDecoder($('encoding').value,{fatal:true}).decode(buf);$('fileInfo').textContent=file.name;estimate();}
$('novelFile').onchange=() =>readNovel().catch(e=>toast('文件解码失败：可切换 GB18030 后重试。'+e.message));$('encoding').onchange=()=>readNovel().catch(e=>toast(e.message));
function estimate(){const chars=$('novelText').value.length,size=+$('chunkSize').value||1500;const n=Math.ceil(chars/Math.max(1,size-100));$('estimate').textContent=`${chars.toLocaleString()} 字符 · 预计约 ${n}–${Math.ceil(n*1.5)} 个块，实际按句末切分。每块约 2 次建图请求，另有人物归并；问答按方法约 2–10 次。`;}
$('novelText').oninput=estimate;$('chunkSize').oninput=estimate;
$('importForm').onsubmit=e=>{e.preventDefault();if(S.job)return toast('请先等待任务完成。');const base=$('baseUrl').value.trim(),model=$('model').value.trim();if(!base||!model)return toast('请填写 Base URL 和模型名称。');S.config={base_url:base,model,api_key:$('apiKey').value};const text=$('novelText').value;if(text.trim()){S.text=text;S.title=$('novelFile').files[0]?.name.replace(/\.(txt|md)$/i,'')||'我的小说';S.result=null;S.liveTrace=[];S.graph=null;S.points=[];$('bookTitle').textContent=S.title;$('bookInfo').textContent=`${text.length.toLocaleString()} 字符 · 等待建图`;$('nodeCount').textContent='—';$('edgeCount').textContent='—';$('presets').hidden=true;$('question').value='';$('answerText').textContent='小说已导入，输入问题后开始建图。';$('evidenceList').replaceChildren();$('uncertainty').textContent='';renderSteps();}$('modeNote').textContent='API 已配置 · 输入问题开始真实检索';$('importDialog').close();toast('配置已应用。输入问题后点击开始。');};
async function jsonPost(path,data){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const j=await r.json();if(!r.ok)throw Error(j.error||'请求失败');return j;}
$('ask').onclick=async()=>{
  const q=$('question').value.trim();if(!q)return toast('请先输入一个问题。');if(S.job)return;
  if(!S.config){const old=S.demo?.results.find(r=>r.question===q&&r.method===$('method').value);if(old){setResult(old);S.playing=true;return;}return toast('新问题需要 API，请点击右上角配置。');}
  if(location.protocol==='file:'||window.__PUBLIC_DEMO__)return toast('离线 HTML 支持回放；新问答请双击项目中的启动脚本，进入本地服务。');
  if(!S.graph&&!S.text)return toast('请先导入小说。');
  S.playing=false;S.result=null;S.liveTrace=[];S.time=0;S.viewIds.clear();$('steps').replaceChildren();$('answerText').textContent='正在检索与组织证据…';$('evidenceList').replaceChildren();$('uncertainty').textContent='';$('answerState').textContent='API 任务进行中';$('ask').disabled=true;$('buildOverlay').hidden=false;$('buildLabel').textContent=S.graph?'LLM 正在规划检索':'准备全文分块';$('buildProgress').value=0;$('buildDetail').textContent='真实调用 API；首次建图需要逐块读取。';
  try{const payload={question:q,config:S.config,chunk_size:+$('chunkSize').value,method:$('method').value,dense_mode:$('denseMode').value};if(S.graph)payload.graph=S.graph;else Object.assign(payload,{text:S.text,title:S.title});const j=await jsonPost('/api/run',payload);S.job=j.id;poll();}catch(e){finishJob();toast(e.message);$('answerState').textContent='请求未完成';}
};
async function poll(){if(!S.job)return;try{const r=await fetch('/api/jobs/'+S.job);const j=await r.json();if(!r.ok)throw Error(j.error);const last=j.events.at(-1);if(last){$('buildLabel').textContent=last.label;$('buildDetail').textContent=last.detail||'';if(last.total){$('buildProgress').max=last.total;$('buildProgress').value=last.done;}else{$('buildProgress').removeAttribute('value');}}
  if(j.graph&&!S.graph){hydrateGraph(j.graph);S.text='';}
  S.liveTrace=j.events.filter(e=>e.kind!=='build');S.viewIds=new Set(S.liveTrace.flatMap(e=>e.node_ids||[]));renderSteps();if(S.liveTrace.length){S.time=(S.liveTrace.length-1)*3.8;updateStage();}
  if(j.status==='complete'){if(j.graph)hydrateGraph(j.graph);setResult(j.result);S.playing=true;finishJob();toast('回答完成，正在播放本次真实检索记录。');}
  else if(j.status==='error'||j.status==='cancelled'){finishJob();$('answerState').textContent='任务未完成';$('answerText').textContent=j.error;toast(j.error);}
  else setTimeout(poll,1000);
}catch(e){finishJob();toast('无法读取任务状态：'+e.message);}}
function finishJob(){S.job=null;$('ask').disabled=false;$('buildOverlay').hidden=true;}
$('cancel').onclick=async()=>{if(S.job){await jsonPost('/api/cancel',{id:S.job});$('buildDetail').textContent='将在当前 API 请求返回后停止；已完成块可复用。';}};
function download(name,content,type){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
async function serverExport(format){const r=await jsonPost('/api/export',{session:session(),format});const a=document.createElement('a');a.href=r.url;a.download='NovelGraph-回放.'+format;a.click();toast('导出已保存：'+r.path);}
function session(){if(!S.graph)throw Error('请先加载或构建图谱。');return {graph:S.graph,results:S.result?[S.result]:[]};}
$('exportJson').onclick=async()=>{try{if(location.protocol!=='file:'&&!window.__BOOT__)return await serverExport('json');download('novel-graph-session.json',JSON.stringify(session(),null,2),'application/json');}catch(e){toast(e.message);}};
$('jsonFile').onchange=async e=>{if(S.job)return toast('请先等待任务完成。');try{const file=e.target.files[0];if(!file)return;const data=JSON.parse(await file.text());hydrateGraph(data.graph||data);S.text='';S.result=null;S.liveTrace=[];renderSteps();$('presets').hidden=true;if(data.results?.length){S.demo=data;$('presets').innerHTML=data.results.map((r,i)=>`<option value="${i}">${i+1}. [${esc(r.method_label||r.method||"历史")}] ${esc(r.question)}</option>`).join('');$('presets').hidden=false;selectPreset(0);}else{$('answerText').textContent='图谱已载入。配置 API 后可以提问。';$('evidenceList').replaceChildren();}toast('已载入图谱。');}catch(err){toast(err.message);}};
function safeJSON(data){return JSON.stringify(data).replace(/</g,'\\u003c').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');}
$('exportHtml').onclick=async()=>{try{if(location.protocol!=='file:'&&!window.__BOOT__)return await serverExport('html');const data=session();if(!htmlSource){[htmlSource,cssSource,jsSource]=await Promise.all(['/', '/style.css','/app.js'].map(p=>fetch(p).then(r=>{if(!r.ok)throw Error('无法读取导出资源');return r.text();})));}
  const html=htmlSource.replace('<link rel="stylesheet" href="/style.css">',`<style>${cssSource}</style>`).replace('<script src="/app.js"></script>',`<script>window.__BOOT__=${safeJSON(data)};</script><script>${jsSource.replace(/<\/script/gi,'<\\/script')}</script>`);
  download('NovelGraph-动画回放.html',html,'text/html');toast('已导出可离线播放的 HTML，未包含 API 密钥。');}catch(e){toast('导出失败：'+e.message);}};
async function start(){if(window.__PUBLIC_DEMO__){$('importBtn').textContent='在本机使用';$('footerStatus').textContent='静态交互示例。新小说与 API 问答请在本机运行。';}if(window.__BOOT__){S.demo=window.__BOOT__;hydrateGraph(S.demo.graph);if(S.demo.results.length){$('presets').innerHTML=S.demo.results.map((r,i)=>`<option value="${i}">${i+1}. [${esc(r.method_label||r.method||"历史")}] ${esc(r.question)}</option>`).join('');selectPreset(0);}htmlSource=document.documentElement.outerHTML; // Offline re-export uses the current self-contained file, handled below.
  $('exportHtml').onclick=()=>download('NovelGraph-动画回放.html','<!doctype html>\n'+htmlSource,'text/html');
}else await loadDemo();requestAnimationFrame(frame);}
start().catch(e=>toast(e.message));

$('method').onchange=()=>{const match=S.demo?.results.findIndex(r=>r.question===$('question').value&&r.method===$('method').value);if(match>=0){$('presets').value=match;selectPreset(match);}};
