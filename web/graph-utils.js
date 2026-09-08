/* Graph-wide statistics and deterministic 3D force layout, independent of query. */
(function(root){
  function unionLength(ranges){let end=-1,total=0;for(const[a,b]of ranges.sort((x,y)=>x[0]-y[0])){if(b>end){total+=b-Math.max(a,end);end=b;}}return total;}
  function metrics(g){
    const connected=new Set();for(const e of g.edges){if(e.source!==e.target){connected.add(e.source);connected.add(e.target);}}
    const isolated=g.nodes.filter(n=>!connected.has(n.id)).length;
    const total=g.meta?.characters;
    const validPassages=g.passages.filter(p=>Number.isInteger(p.start)&&p.start>=0&&Number.isInteger(p.end)&&p.end>=p.start&&Array.from(p.text||'').length===p.end-p.start);
    const ps=new Map(validPassages.filter(p=>!Number.isInteger(total)||p.end<=total).map(p=>[p.id,p]));
    const full=Number.isInteger(total)&&total>0&&validPassages.every(p=>p.end<=total)&&unionLength(validPassages.map(p=>[p.start,p.end]))===total;
    const ranges=[];let anchored=0;
    for(const n of g.nodes){let found=false;for(const ev of n.evidence_ids||[]){const p=ps.get(ev.passage_id),quote=ev.quote;if(!p||!Number.isInteger(p.start)||!quote?.trim())continue;const at=p.text.indexOf(quote);if(at<0)continue;
      const a=p.start+Array.from(p.text.slice(0,at)).length,b=a+Array.from(quote).length;
      if(a>=0&&b<=p.end){ranges.push([a,b]);found=true;}
    }if(found)anchored++;}
    const covered=full?unionLength(ranges):null;
    return {nodes:g.nodes.length,edges:g.edges.length,isolated,isolatedRate:g.nodes.length?isolated/g.nodes.length:0,covered,total:full?total:null,coverage:full?covered/total:null,anchored:full?anchored:null};
  }
  function forceLayout(g,iterations=90){
    const n=g.nodes.length,indices=new Map(g.nodes.map((v,i)=>[v.id,i]));
    const p=g.nodes.map((v,i)=>{const y=1-2*(i+.5)/Math.max(1,n),r=Math.sqrt(1-y*y),a=i*2.3999632297;return{x:210*r*Math.cos(a),y:210*y,z:210*r*Math.sin(a)};});
    const edges=g.edges.map(e=>[indices.get(e.source),indices.get(e.target)]).filter(([a,b])=>a!=null&&b!=null&&a!==b);
    for(let k=0;k<iterations;k++){
      const f=p.map(()=>({x:0,y:0,z:0})),stride=Math.max(1,Math.ceil(n/1200));
      for(let i=0;i<n;i++)for(let j=i+1+(k%stride);j<n;j+=stride){const a=p[i],b=p[j];const dx=a.x-b.x,dy=a.y-b.y,dz=a.z-b.z,d2=dx*dx+dy*dy+dz*dz+25,d=Math.sqrt(d2),repel=1800*stride/d2;
        for(const[axis,v]of[['x',dx],['y',dy],['z',dz]]){const value=v/d*repel;f[i][axis]+=value;f[j][axis]-=value;}
      }
      for(const[i,j]of edges){const a=p[i],b=p[j],dx=b.x-a.x,dy=b.y-a.y,dz=b.z-a.z,d=Math.hypot(dx,dy,dz)||1,attract=(d-48)*.014;for(const[axis,v]of[['x',dx],['y',dy],['z',dz]]){f[i][axis]+=v/d*attract;f[j][axis]-=v/d*attract;}}
      for(let i=0;i<n;i++){for(const axis of ['x','y','z'])f[i][axis]-=p[i][axis]*.003;const d=Math.hypot(f[i].x,f[i].y,f[i].z)||1,step=Math.min(d,9*(1-k/iterations)+.5)/d;for(const axis of ['x','y','z'])p[i][axis]+=f[i][axis]*step;}
    }
    let max=1;for(const v of p)max=Math.max(max,Math.hypot(v.x,v.y,v.z));for(const v of p)for(const axis of ['x','y','z'])v[axis]*=245/max;
    return new Map(g.nodes.map((v,i)=>[v.id,p[i]]));
  }
  const api={metrics,forceLayout,unionLength};if(typeof module!=='undefined')module.exports=api;else root.GraphAnalysis=api;
})(typeof window!=='undefined'?window:globalThis);
