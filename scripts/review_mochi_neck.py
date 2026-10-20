"""Local geometric review: part colors are explicit identification colors only."""
from pathlib import Path
import argparse,json
import numpy as np
import trimesh
from figuraforge.geometry.preview import mesh_preview

p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);args=p.parse_args();root=args.directory
report=json.loads((root/'construction-verification.json').read_text());meshes=[];alltri=[];allcolors=[];groups=[]
for part in report['parts']:
    ident=part['id'];a=np.load(root/'parts'/f'{ident}.npz');m=trimesh.Trimesh(a['vertices'],a['faces'],process=False)
    color='#805947' if ident=='torso' else '#8CC6DD' if ident=='head' else '#D5EF31' if ident=='neck-key' else '#272729'
    direction=[1,0,0] if ident=='neck-key' else [0,0,1]
    meshes.append(mesh_preview(m,color=color,ident=ident,name=part['name'],role=part['role'],direction=direction,smooth_normals=True))
    alltri.append(m.triangles);allcolors.append(np.tile(np.array([int(color[i:i+2],16)/255 for i in [1,3,5]]),(len(m.faces),1)));groups.extend([ident]*len(m.faces))
(root/'geometric-preview.json').write_text(json.dumps({'meshes':meshes,'warnings':['Bauteilfarben sind Kennfarben, keine Filamentvorschau.']}))
viewer=Path('frontend/viewer.js').read_text().split('\n',1)[1].replace('export class Viewer','class Viewer')
html='''<!doctype html><meta charset="utf-8"><title>Mochi · organische Halsfuge</title><style>body{margin:0;font:18px system-ui;color:#18212c;background:#eef1f4}header{padding:14px 22px}p{margin:8px 0}button{font:inherit;background:white;padding:10px 16px;margin:4px;border:1px solid #92a0ad;border-radius:8px}canvas{width:100vw;height:74vh;display:block}small{font-size:15px}</style><header><b>Mochi · 470 mm · Kopf am geometrischen Hals getrennt</b><p>Hellblau: Kopf · Braun: Rumpf · Lime: separater Halsverbinder · Schwarz: Nase/Augen.</p><small>Bauteil-Kennfarben, keine Druckfarbvorschau. Die 3MF-Datei erhält Richards Braun-/Beige-Bemalung.</small><p><button id="assembly">Zusammengebaut</button><button id="explode">Kopf abheben</button><button id="neck">Hals vergrößern</button><button id="under">Aufnahme von unten</button><button id="rotate">45° drehen</button><button id="reset">Ganze Figur</button></p><a href="Mochi-470mm-Hals-geteilt-3-Platten.3mf">3MF · drei Platten herunterladen</a></header><canvas id="view"></canvas><script>const STRATEGY_COLORS={body:'#728197',part:'#00B2FF',mixed:'#CFFF00'};const isMixedRegion=r=>r?.strategy==='mixed'||r?.color_mode==='mixed';'''+viewer+'''
fetch('geometric-preview.json').then(r=>r.json()).then(data=>{const v=new Viewer(document.querySelector('#view'));v.setData(data);window.mochiViewer=v;
document.querySelector('#assembly').onclick=()=>v.setMode('assembly');document.querySelector('#explode').onclick=()=>{v.explode=.42;v.setMode('explode')};document.querySelector('#neck').onclick=()=>{v.mode='explode';v.explode=.12;v.target=[0,-70,290];v.radius=110;v.distance=270;v.draw()};document.querySelector('#under').onclick=()=>{v.mode='explode';v.explode=.3;v.target=[0,-70,340];v.pitch=-.85;v.distance=270;v.draw()};document.querySelector('#rotate').onclick=()=>{v.yaw+=Math.PI/4;v.draw()};document.querySelector('#reset').onclick=()=>v.setMode('assembly');}).catch(e=>document.querySelector('header').append(document.createTextNode(e.message)));</script>'''
html=html.replace('470 mm',f"{report['height_mm']:g} mm").replace('Mochi-470mm',f"Mochi-{report['height_mm']:g}mm")
(root/'Mochi-Hals-Vorschau.html').write_text(html)
# Offline geometric QA sheet; no generative image or substituted geometry.
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
tri=np.concatenate(alltri);col=np.concatenate(allcolors);groups=np.asarray(groups)
fig,axs=plt.subplots(1,3,figsize=(17,9),facecolor='#eef1f4')
for ax,(azim,elev,exploded,title) in zip(axs,[(-90,10,False,'Vorn · montiert'),(-30,12,False,'Seite · montiert'),(-60,15,True,'Halsfuge · Kopf abgehoben')]):
 t=tri.copy()
 if exploded:
  t[(groups!='torso')&(groups!='neck-key')]+=[0,0,80];t[groups=='neck-key']+=[100,0,0]
 az=np.deg2rad(azim);el=np.deg2rad(elev);view=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]);right=np.array([-np.sin(az),np.cos(az),0]);up=np.cross(view,right)
 normal=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12);visible=normal@view>0;selected=t[visible];shade=.65+.35*np.maximum(normal[visible]@view,0);xy=np.stack([selected@right,selected@up],axis=-1);order=np.argsort(selected.mean(axis=1)@view)
 ax.add_collection(PolyCollection(xy[order],facecolors=np.clip(col[visible][order]*shade[order,None],0,1),edgecolors='none',antialiased=False,rasterized=True));pts=xy.reshape(-1,2);lo=pts.min(0);hi=pts.max(0);pad=(hi-lo)*.04;ax.set_xlim(lo[0]-pad[0],hi[0]+pad[0]);ax.set_ylim(lo[1]-pad[1],hi[1]+pad[1]);ax.set_aspect('equal');ax.axis('off');ax.set_title(title,fontsize=15)
fig.suptitle(f"Mochi · {report['height_mm']:g} mm · organische Halsfuge + separater, asymmetrischer Verbinder\nBauteil-Kennfarben zur Geometrieprüfung; Druckfarben bleiben Braun / Beige / Schwarz",fontsize=16);fig.tight_layout();fig.savefig(root/'Mochi-Hals-Geometriepruefung.png',dpi=120)
print(root/'Mochi-Hals-Geometriepruefung.png')
