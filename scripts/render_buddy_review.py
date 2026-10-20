"""Offline static comparison from source and actual stock-colored geometry."""
from pathlib import Path
import argparse,json,base64
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from figuraforge.geometry.io import load_surface
from figuraforge.geometry.preview import surface_preview

def render(preview_path,source_path):
    path=Path(preview_path);preview=json.loads(path.read_text());surface=load_surface(Path(source_path),1000,'Y')
    original=surface.mesh.triangles;origcolor=surface.sample();triangles=[];colors=[]
    for item in preview['meshes']:
        triangles.append(np.frombuffer(base64.b64decode(item['positions']),dtype='<f4').reshape(-1,3,3))
        colors.append(np.frombuffer(base64.b64decode(item['colors']),dtype='<f4').reshape(-1,3,3).mean(axis=1))
    proposed=np.concatenate(triangles);proposedcolor=np.concatenate(colors)
    fig=plt.figure(figsize=(18,12),facecolor='#EEF0EA')
    for row,(tri,col,name) in enumerate([(original,origcolor,'Originaltextur (Flächenabtastung)'),(proposed,proposedcolor,'Bestandsspulen (HEX unkalibriert)')]):
        for column,(elev,azim,title) in enumerate([(10,-90,'Vorn'),(10,90,'Hinten'),(10,0,'Rechts'),(25,-45,'Dreiviertel')]):
            ax=fig.add_subplot(2,4,row*4+column+1);ax.set_facecolor('#EEF0EA')
            az=np.deg2rad(azim);el=np.deg2rad(elev);view=np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)])
            right=np.array([-np.sin(az),np.cos(az),0]);up=np.cross(view,right)
            normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
            visible=normal@view>0
            selected=tri[visible];shade=.6+.4*np.maximum(normal[visible]@view,0)
            projected=np.stack([selected@right,selected@up],axis=-1)
            order=np.argsort(selected.mean(axis=1)@view)
            ax.add_collection(PolyCollection(projected[order],facecolors=np.clip(col[visible][order]*shade[order,None],0,1),edgecolors='none',antialiased=False,rasterized=True))
            points=surface.mesh.vertices;xy=np.column_stack([points@right,points@up]);lo=xy.min(axis=0);hi=xy.max(axis=0);pad=(hi-lo)*.05
            ax.set_xlim(lo[0]-pad[0],hi[0]+pad[0]);ax.set_ylim(lo[1]-pad[1],hi[1]+pad[1]);ax.set_aspect('equal');ax.set_axis_off();ax.set_title(name+'\n'+title,fontsize=12)
    fig.suptitle('Buddy · sichtbare Originalgeometrie / Materialvorschlag · keine geslicte Vorschau',fontsize=17)
    fig.subplots_adjust(left=0,right=1,bottom=.02,top=.9,wspace=.08,hspace=.25)
    output=path.parent/'material-four-views.png';fig.savefig(output,dpi=140);plt.close(fig);print(output,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('preview');p.add_argument('source');a=p.parse_args();render(a.preview,a.source)
