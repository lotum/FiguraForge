import {STRATEGY_COLORS,isMixedRegion} from './plan-guidance.js';
// Dependency-free WebGL renderer. Geometry remains server-validated; this is a viewer only.
const I=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const add=(a,b)=>a.map((v,i)=>v+b[i]), sub=(a,b)=>a.map((v,i)=>v-b[i]);
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0), cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const norm=a=>{const l=Math.hypot(...a)||1;return a.map(v=>v/l)};
const mul=(a,b)=>{const c=Array(16).fill(0);for(let i=0;i<4;i++)for(let j=0;j<4;j++)for(let k=0;k<4;k++)c[i*4+j]+=a[i*4+k]*b[k*4+j];return c};
const trans=a=>new Float32Array(a.map((_,i)=>a[(i%4)*4+Math.floor(i/4)]));
const point=(m,p)=>[0,1,2].map(i=>m[i*4]*p[0]+m[i*4+1]*p[1]+m[i*4+2]*p[2]+m[i*4+3]);
const flatten=a=>a.flat();
const decode=s=>{const b=atob(s),a=new Uint8Array(b.length);for(let i=0;i<b.length;i++)a[i]=b.charCodeAt(i);return new Float32Array(a.buffer)};
const rgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)/255);
function lookAt(eye,target){const z=norm(sub(eye,target)),x=norm(cross([0,0,1],z)),y=cross(z,x);return [...x,-dot(x,eye),...y,-dot(y,eye),...z,-dot(z,eye),0,0,0,1]}
function perspective(fov,aspect,near,far){const f=1/Math.tan(fov/2);return [f/aspect,0,0,0,0,f,0,0,0,0,(far+near)/(near-far),2*far*near/(near-far),0,0,-1,0]}

export class Viewer{
 constructor(canvas,onSelect=()=>{}){
  this.canvas=canvas;this.gl=canvas.getContext('webgl',{antialias:true,alpha:true,preserveDrawingBuffer:true});this.onSelect=onSelect;
  if(!this.gl){this.software=true;this.ctx=canvas.getContext('2d');if(!this.ctx)throw new Error('Kein Canvas-Renderer verfuegbar.');}
  this.lighting=true;this.faceSelection=false;this.brushEnabled=false;this.brushRadius=20;this.onFaces=null;
  this.meshes=[];this.mode='assembly';this.explode=.35;this.plates=[];this.plate=0;this.selected=null;this.colorMap={};this.target=[0,0,80];this.radius=180;this.yaw=-1.12;this.pitch=.22;this.distance=350;
  const gl=this.gl;
  if(gl){
  const vertex=`attribute vec3 aPosition;attribute vec3 aNormal;attribute vec3 aColor;attribute vec2 aUV;varying vec2 vUV;uniform mat4 uMVP;uniform mat4 uModel;varying vec3 vNormal;varying vec3 vColor;varying vec3 vWorld;void main(){vUV=aUV;gl_Position=uMVP*vec4(aPosition,1.);vNormal=mat3(uModel)*aNormal;vColor=aColor;vWorld=(uModel*vec4(aPosition,1.)).xyz;}`;
  const fragment=`precision mediump float;varying vec2 vUV;uniform sampler2D uTexture;uniform float uUseTexture;uniform vec3 uTextureFactor;varying vec3 vNormal;varying vec3 vColor;varying vec3 vWorld;uniform vec3 uColor;uniform float uUseColor;uniform float uPick;uniform float uSelect;uniform float uLighting;void main(){if(uPick>0.5){gl_FragColor=vec4(mix(vColor,uColor,uUseColor),1.);return;}vec3 n=normalize(vNormal);float key=max(dot(n,normalize(vec3(-.5,-.8,1.4))),0.);float fill=max(dot(n,normalize(vec3(.8,.4,.65))),0.);float hemi=.5+.5*n.z;float light=.47+.33*key+.15*fill+.12*hemi;vec3 c=mix(vColor,uColor,uUseColor);if(uUseTexture>0.5){vec3 tex=texture2D(uTexture,vUV).rgb;vec3 lin=mix(tex/12.92,pow((tex+0.055)/1.055,vec3(2.4)),step(vec3(.04045),tex))*uTextureFactor;c=mix(12.92*lin,1.055*pow(max(lin,vec3(0.)),vec3(1./2.4))-.055,step(vec3(.0031308),lin));}c=c*mix(1.,light,uLighting);c=mix(c,vec3(.74,.84,.48),uSelect*.18);gl_FragColor=vec4(c,1.);}`;
  const compile=(type,source)=>{let s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(s));return s};
  this.program=gl.createProgram();gl.attachShader(this.program,compile(gl.VERTEX_SHADER,vertex));gl.attachShader(this.program,compile(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(this.program);
  if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(this.program));
  this.a={};['Position','Normal','Color','UV'].forEach(k=>this.a[k]=gl.getAttribLocation(this.program,'a'+k));
  this.u={};['MVP','Model','Color','UseColor','Pick','Select','Texture','UseTexture','TextureFactor','Lighting'].forEach(k=>this.u[k]=gl.getUniformLocation(this.program,'u'+k));
  }
  canvas.addEventListener('pointerdown',e=>{if(this.brushEnabled&&!e.shiftKey){this.drag={paint:true};canvas.setPointerCapture(e.pointerId);this.pickFaces(e);return;}this.drag={x:e.clientX,y:e.clientY,ox:e.clientX,oy:e.clientY,shift:e.shiftKey};canvas.setPointerCapture(e.pointerId)});
  canvas.addEventListener('pointermove',e=>{if(!this.drag)return;if(this.drag.paint){if(!this.paintFrame)this.paintFrame=requestAnimationFrame(()=>{this.paintFrame=null;this.pickFaces(e)});return;}const d=this.drag,dx=e.clientX-d.x,dy=e.clientY-d.y;
   if(d.shift){const k=this.distance*.0015;this.target[0]-=Math.sin(this.yaw)*dx*k;this.target[1]+=Math.cos(this.yaw)*dx*k;this.target[2]+=dy*k}
   else{this.yaw-=dx*.008;this.pitch=Math.max(-1.2,Math.min(1.35,this.pitch+dy*.006))}d.x=e.clientX;d.y=e.clientY;this.draw()});
  canvas.addEventListener('pointerup',e=>{if(this.drag&&!this.drag.paint&&Math.hypot(e.clientX-this.drag.ox,e.clientY-this.drag.oy)<4)this.pick(e);this.drag=null});
  canvas.addEventListener('pointercancel',()=>this.drag=null);
  canvas.addEventListener('wheel',e=>{e.preventDefault();this.distance=Math.max(this.radius*.4,Math.min(this.radius*15,this.distance*Math.exp(e.deltaY*.001)));this.draw()},{passive:false});
  this.observer=new ResizeObserver(()=>this.draw());this.observer.observe(canvas);
 }
 buffer(array){if(!this.gl)return array;const gl=this.gl,b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,array,gl.STATIC_DRAW);return b}
 setData(data){const gl=this.gl;if(gl)this.meshes.forEach(m=>['pos','normal','colors','uv','pickColors'].forEach(k=>m[k]&&gl.deleteBuffer(m[k])));if(gl)this.meshes.forEach(m=>m.textureBuffer&&gl.deleteTexture(m.textureBuffer));
  this.meshes=(data.meshes||[]).map(m=>{const count=m.vertex_count/3,picks=new Float32Array(m.vertex_count*3);for(let f=0;f<count;f++){const id=(m.face_ids?.[f]??f)+1;for(let v=0;v<3;v++)picks.set([(id&255)/255,((id>>8)&255)/255,((id>>16)&255)/255],f*9+v*3)}const item={...m,pos:this.buffer(decode(m.positions)),normal:this.buffer(decode(m.normals)),uv:m.uvs?this.buffer(decode(m.uvs)):null,colors:(this.software&&m.fallback_colors)?this.buffer(decode(m.fallback_colors)):(m.colors?this.buffer(decode(m.colors)):null),pickColors:this.buffer(picks),baseColors:m.colors?decode(m.colors):null};if(gl&&m.texture){const texture=gl.createTexture();item.textureBuffer=texture;const image=new Image();image.onload=()=>{if(!this.meshes.includes(item))return;gl.bindTexture(gl.TEXTURE_2D,texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);item.textureReady=true;this.draw()};image.src=m.texture;}return item;});
  this.selected=null;this.reset();
 }
 setColors(map){this.colorMap=map||{};this.draw()}
 setMode(mode){this.mode=mode;this.reset()}
 setPlates(plates){this.plates=plates||[];this.plate=Math.min(this.plate,Math.max(0,this.plates.length-1));this.draw()}
 transform(m){if(this.mode==='plates'){const p=this.plates[this.plate]?.placements.find(p=>p.part_id===m.id);return p?flatten(p.transform):null}
  const t=I();const tiledBody=m.role==='body'&&this.meshes.filter(x=>x.role==='body').length>1;if(this.mode==='explode'&&(m.role!=='body'||tiledBody)){const dir=tiledBody?norm(sub(m.center,this.center||[0,0,80])):(m.direction||norm(sub(m.center,this.center||[0,0,80])));for(let i=0;i<3;i++)t[i*4+3]=dir[i]*this.radius*this.explode*.9}return t;
 }
 reset(){let lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
  // Fit the assembled geometry first, then include explosion so the viewer never clips inserts.
  for(const m of this.meshes){let t=this.mode==='plates'?this.transform(m):I();if(!t)continue;for(let a=0;a<2;a++)for(let b=0;b<2;b++)for(let c=0;c<2;c++){let p=point(t,[m.bounds[a][0],m.bounds[b][1],m.bounds[c][2]]);for(let k=0;k<3;k++){lo[k]=Math.min(lo[k],p[k]);hi[k]=Math.max(hi[k],p[k])}}}
  if(!isFinite(lo[0])){lo=[-50,-50,0];hi=[50,50,180]}
  this.center=lo.map((v,i)=>(v+hi[i])/2);this.target=[...this.center];this.radius=Math.max(...hi.map((v,i)=>v-lo[i]))*.65;
  this.yaw=this.mode==='plates'?-1.4:-1.12;this.pitch=this.mode==='plates'?1.0:.22;this.distance=this.radius*(this.mode==='explode'?3.8:3.0);this.draw();
 }
 attribute(buffer,index,fallback){const gl=this.gl;if(buffer){gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.enableVertexAttribArray(index);gl.vertexAttribPointer(index,3,gl.FLOAT,false,0,0)}else{gl.disableVertexAttribArray(index);gl.vertexAttrib3fv(index,fallback)}}
 draw(picking=false){if(!this.gl){this.drawSoftware();return;}const gl=this.gl,c=this.canvas,dpr=Math.min(window.devicePixelRatio||1,2),w=Math.max(1,Math.round(c.clientWidth*dpr)),h=Math.max(1,Math.round(c.clientHeight*dpr));if(c.width!==w||c.height!==h){c.width=w;c.height=h}
  if(picking)gl.disable(gl.DITHER);else gl.enable(gl.DITHER);gl.viewport(0,0,w,h);gl.clearColor(0,0,0,picking?1:0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.disable(gl.BLEND);gl.disable(gl.CULL_FACE);gl.useProgram(this.program);gl.uniform1f(this.u.Lighting,this.lighting===false?0:1);
  const eye=add(this.target,[Math.cos(this.pitch)*Math.cos(this.yaw)*this.distance,Math.cos(this.pitch)*Math.sin(this.yaw)*this.distance,Math.sin(this.pitch)*this.distance]);
  const vp=mul(perspective(.68,w/h,Math.max(.05,this.radius/100),Math.max(1000,this.distance+this.radius*10)),lookAt(eye,this.target));
  for(let i=0;i<this.meshes.length;i++){
   const m=this.meshes[i],t=this.transform(m);if(!t)continue;this.attribute(m.pos,this.a.Position,[0,0,0]);this.attribute(m.normal,this.a.Normal,[0,0,1]);this.attribute(picking&&this.faceSelection?m.pickColors:m.colors,this.a.Color,[1,1,1]);if(m.uv){gl.bindBuffer(gl.ARRAY_BUFFER,m.uv);gl.enableVertexAttribArray(this.a.UV);gl.vertexAttribPointer(this.a.UV,2,gl.FLOAT,false,0,0)}else{gl.disableVertexAttribArray(this.a.UV);gl.vertexAttrib2f(this.a.UV,0,0)}gl.uniform1f(this.u.UseTexture,!picking&&m.textureReady?1:0);gl.uniform3fv(this.u.TextureFactor,m.texture_factor||[1,1,1]);if(m.textureReady){gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,m.textureBuffer);gl.uniform1i(this.u.Texture,0);}
   gl.uniformMatrix4fv(this.u.MVP,false,trans(mul(vp,t)));gl.uniformMatrix4fv(this.u.Model,false,trans(t));
   const color=picking?[(i+1)/255,0,0]:rgb(this.colorMap[m.id]||m.color||'#A0AB91');
   gl.uniform3fv(this.u.Color,color);gl.uniform1f(this.u.UseColor,picking?(this.faceSelection?0:1):(m.colors&&!this.colorMap[m.id]?0:1));gl.uniform1f(this.u.Pick,picking?1:0);gl.uniform1f(this.u.Select,m.id===this.selected?1:0);gl.drawArrays(gl.TRIANGLES,0,m.vertex_count);
  }
  if(!picking){this.drawGrid(vp);}
 }
 drawGrid(vp){const gl=this.gl;let extent=this.mode==='plates'?Math.max(...(this.plates[this.plate]?.volume_mm||[300,320]).slice(0,2)):this.radius*1.25;
  const step=Math.max(5,Math.pow(10,Math.floor(Math.log10(extent/8)))),vertices=[];
  let ox=0,oy=0,z=-.2;if(this.mode==='plates'){ox=extent/2;oy=extent/2;extent/=2}
  const n=Math.ceil(extent/step);for(let i=-n;i<=n;i++){let v=i*step;vertices.push(ox-extent,oy+v,z,ox+extent,oy+v,z,ox+v,oy-extent,z,ox+v,oy+extent,z)}
  if(!this.gridBuffer)this.gridBuffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,this.gridBuffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(vertices),gl.DYNAMIC_DRAW);
  this.attribute(this.gridBuffer,this.a.Position,[0,0,0]);this.attribute(null,this.a.Normal,[0,0,1]);this.attribute(null,this.a.Color,[1,1,1]);
  gl.uniformMatrix4fv(this.u.MVP,false,trans(vp));gl.uniformMatrix4fv(this.u.Model,false,trans(I()));gl.uniform3fv(this.u.Color,[.78,.815,.735]);gl.uniform1f(this.u.UseColor,1);gl.uniform1f(this.u.UseTexture,0);gl.uniform1f(this.u.Pick,1);gl.uniform1f(this.u.Select,0);gl.drawArrays(gl.LINES,0,vertices.length/3);
 }
 pick(e){if(this.faceSelection){this.pickFaces(e);return;}if(!this.gl){this.pickSoftware(e);return;}this.draw(true);const rect=this.canvas.getBoundingClientRect(),gl=this.gl,pixel=new Uint8Array(4);gl.readPixels(Math.round((e.clientX-rect.left)*this.canvas.width/rect.width),Math.round((rect.bottom-e.clientY)*this.canvas.height/rect.height),1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);let m=this.meshes[pixel[0]-1];this.selected=m?.id||null;this.draw();this.onSelect(this.selected)}

 updatePlan(plan,view='strategy',selected=null){const regions=new Map(plan.regions.map(r=>[r.id,r]));for(const m of this.meshes){const colors=new Float32Array(m.vertex_count*3);for(let f=0;f<m.vertex_count/3;f++){const r=regions.get(plan.face_regions[m.face_ids?.[f]??f]);let c=rgb(view==='color'?r.color:STRATEGY_COLORS[isMixedRegion(r)?'mixed':r.strategy]);if(r.id===selected)c=c.map(x=>x*.7+.3);for(let v=0;v<3;v++)colors.set(c,f*9+v*3)}if(this.gl){if(m.colors)this.gl.deleteBuffer(m.colors);m.colors=this.buffer(colors)}else m.colors=colors;}this.draw();}
 pickFaces(e){if(!this.gl){this.pickSoftware(e);return;}this.draw(true);const r=this.canvas.getBoundingClientRect(),scale=this.canvas.width/r.width,cx=(e.clientX-r.left)*scale,cy=(r.bottom-e.clientY)*scale,radius=this.brushEnabled?this.brushRadius*scale:0;const x=Math.max(0,Math.floor(cx-radius)),y=Math.max(0,Math.floor(cy-radius)),w=Math.min(this.canvas.width-x,Math.max(1,Math.ceil(radius*2))),h=Math.min(this.canvas.height-y,Math.max(1,Math.ceil(radius*2)));if(w<=0||h<=0)return;const pixels=new Uint8Array(w*h*4);this.gl.readPixels(x,y,w,h,this.gl.RGBA,this.gl.UNSIGNED_BYTE,pixels);const faces=new Set();for(let iy=0;iy<h;iy++)for(let ix=0;ix<w;ix++){if(radius&&Math.hypot(x+ix-cx,y+iy-cy)>radius)continue;const i=(iy*w+ix)*4,id=pixels[i]+(pixels[i+1]<<8)+(pixels[i+2]<<16);if(id)faces.add(id-1);}this.draw();if(faces.size)this.onFaces?.([...faces],this.brushEnabled);}

 drawSoftware(){
  const c=this.canvas,ctx=this.ctx;if(!ctx)return;const dpr=Math.min(window.devicePixelRatio||1,1.5),w=Math.max(1,Math.round(c.clientWidth*dpr)),h=Math.max(1,Math.round(c.clientHeight*dpr));if(c.width!==w||c.height!==h){c.width=w;c.height=h}
  ctx.fillStyle='#e9ece3';ctx.fillRect(0,0,w,h);
  const eye=add(this.target,[Math.cos(this.pitch)*Math.cos(this.yaw)*this.distance,Math.cos(this.pitch)*Math.sin(this.yaw)*this.distance,Math.sin(this.pitch)*this.distance]);
  const vp=mul(perspective(.68,w/h,Math.max(.05,this.radius/100),Math.max(1000,this.distance+this.radius*10)),lookAt(eye,this.target));
  const project=p=>{const z=vp[12]*p[0]+vp[13]*p[1]+vp[14]*p[2]+vp[15];if(z<=0)return null;return [(vp[0]*p[0]+vp[1]*p[1]+vp[2]*p[2]+vp[3])/z*w/2+w/2,h/2-(vp[4]*p[0]+vp[5]*p[1]+vp[6]*p[2]+vp[7])/z*h/2,(vp[8]*p[0]+vp[9]*p[1]+vp[10]*p[2]+vp[11])/z]};
  const extent=this.mode==='plates'?330:this.radius*1.35,offset=this.mode==='plates'?150:0,step=Math.max(10,Math.pow(10,Math.floor(Math.log10(extent/8))));
  ctx.strokeStyle='#cdd6c2';ctx.lineWidth=.7*dpr;ctx.beginPath();
  for(let i=-extent;i<=extent;i+=step){for(const segment of [[[offset-extent,offset+i,0],[offset+extent,offset+i,0]],[[offset+i,offset-extent,0],[offset+i,offset+extent,0]]]){const a=project(segment[0]),b=project(segment[1]);if(a&&b){ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1])}}}ctx.stroke();
  const faces=[],lightA=norm([-.5,-.8,1.4]),lightB=norm([.8,.4,.65]);
  for(const m of this.meshes){const t=this.transform(m);if(!t)continue;const v=m.pos,n=m.normal,override=this.colorMap[m.id],base=rgb(override||m.color||'#A0AB91');
   for(let i=0;i<v.length;i+=9){const a=point(t,[v[i],v[i+1],v[i+2]]),b=point(t,[v[i+3],v[i+4],v[i+5]]),d=point(t,[v[i+6],v[i+7],v[i+8]]);
    const normal=norm([t[0]*n[i]+t[1]*n[i+1]+t[2]*n[i+2],t[4]*n[i]+t[5]*n[i+1]+t[6]*n[i+2],t[8]*n[i]+t[9]*n[i+1]+t[10]*n[i+2]]);
    if(dot(normal,sub(eye,a))<=0)continue;
    const p=project(a),q=project(b),r=project(d);if(!p||!q||!r)continue;
    const color=m.colors&&!override?[m.colors[i],m.colors[i+1],m.colors[i+2]]:base;
    const l=this.lighting===false?1:.47+.33*Math.max(dot(normal,lightA),0)+.15*Math.max(dot(normal,lightB),0)+.12*(.5+.5*normal[2]);
    const highlight=m.id === this.selected ? .18 : 0;
    const col=color.map((v,k)=>Math.round(Math.min(1,Math.max(0,v*l*(1-highlight)+[.74,.84,.48][k]*highlight))*255));
    faces.push({p,q,r,z:(p[2]+q[2]+r[2])/3,id:m.id,color:`rgb(${col.join(',')})`});
   }
  }
  faces.sort((a,b)=>b.z-a.z);this.softwareFaces=faces;
  for(const f of faces){ctx.fillStyle=f.color;ctx.strokeStyle=f.color;ctx.lineWidth=.45;ctx.beginPath();ctx.moveTo(f.p[0],f.p[1]);ctx.lineTo(f.q[0],f.q[1]);ctx.lineTo(f.r[0],f.r[1]);ctx.closePath();ctx.fill();ctx.stroke()}
  ctx.fillStyle='#859778';ctx.font=`${9*dpr}px sans-serif`;ctx.fillText('SOFTWARE 3D PREVIEW',18*dpr,h-40*dpr);
 }
 pickSoftware(e){const rect=this.canvas.getBoundingClientRect(),x=(e.clientX-rect.left)*this.canvas.width/rect.width,y=(e.clientY-rect.top)*this.canvas.height/rect.height;let selected=null;
  for(let i=(this.softwareFaces?.length||0)-1;i>=0;i--){const {p:a,q:b,r:c,id}=this.softwareFaces[i],den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);if(Math.abs(den)<1e-9)continue;const u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den,v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;if(u>=0&&v>=0&&u+v<=1){selected=id;break}}
  this.selected=selected;this.draw();this.onSelect(selected);
 }
 focusColorComparison(){
  // Fit the upper 65% of the figure, excluding feet and most of a low tail.
  // This is a geometric framing heuristic, not anatomical recognition.
  const original={target:[...this.target],distance:this.distance,yaw:this.yaw,pitch:this.pitch};
  const bounds=this.meshes.map(m=>m.bounds).filter(Boolean);if(!bounds.length)return ()=>{};
  const lo=[0,1,2].map(k=>Math.min(...bounds.map(b=>b[0][k]))),hi=[0,1,2].map(k=>Math.max(...bounds.map(b=>b[1][k]))),height=hi[2]-lo[2];
  if(!(height>0))return ()=>{};
  const focusLo=[Infinity,Infinity,lo[2]+height*.4],focusHi=[-Infinity,-Infinity,hi[2]];
  for(const mesh of this.meshes){const points=mesh.positions?decode(mesh.positions):this.software?mesh.pos:null;if(!points)continue;for(let i=0;i<points.length;i+=3){if(points[i+2]<lo[2]+height*.55)continue;for(let k=0;k<2;k++){focusLo[k]=Math.min(focusLo[k],points[i+k]);focusHi[k]=Math.max(focusHi[k],points[i+k]);}}}
  for(let k=0;k<2;k++)if(!isFinite(focusLo[k])){focusLo[k]=lo[k];focusHi[k]=hi[k];}
  this.target=focusLo.map((v,k)=>(v+focusHi[k])/2);
  const aspect=Math.max(.5,this.canvas.clientWidth/this.canvas.clientHeight),vertical=height*.65,horizontal=Math.max(focusHi[0]-focusLo[0],focusHi[1]-focusLo[1]);
  this.distance=Math.max(vertical,horizontal/aspect)/(2*Math.tan(.34))*1.1;this.draw();
  return ()=>{Object.assign(this,original);this.draw();};
 }
 screenshot(){this.draw();const a=document.createElement('a');a.href=this.canvas.toDataURL('image/png');a.download='figuraforge-preview.png';a.click()}
}
