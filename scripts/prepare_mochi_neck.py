"""Reproduce the source-bound geometric neck analysis and scale-correct joint."""
from pathlib import Path
import argparse,json,hashlib,sys
import numpy as np
import trimesh
from shapely.geometry import Polygon,LineString
from scipy.ndimage import gaussian_filter1d
from figuraforge.geometry.mochi_neck import split_neck
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_native_parity import records

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--height',type=float,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
expected='4197d3b9bbd3dff88fe65bacc47bc0448c0d76530c56b66d221760318df73508';digest=hashlib.sha256(args.source.read_bytes()).hexdigest()
if digest!=expected:raise ValueError('This reviewed neck preset is bound to Richards immutable Mochi source')
if not 180<=args.height<=500:raise ValueError('Reviewed reference scale range is 180..500 mm')
source,_=records(args.source);v,f,paint=source['body'][0];v=v.copy();v[:,:2]-=(v[:,:2].min(0)+v[:,:2].max(0))/2;mesh=trimesh.Trimesh(v,f,process=False)
zs=np.arange(104.,116.01,.5);angles=np.linspace(0,2*np.pi,64,endpoint=False);center=np.array([0.,-27.]);radii=np.zeros((len(zs),len(angles)))
for i,z in enumerate(zs):
 section=mesh.section(plane_origin=[0,0,z],plane_normal=[0,0,1]);poly=max((Polygon(p[:,:2]) for p in section.discrete),key=lambda p:p.area)
 for j,t in enumerate(angles):
  direction=np.array([np.cos(t),np.sin(t)]);hit=poly.boundary.intersection(LineString([center,center+direction*150]));points=[hit] if hit.geom_type=='Point' else list(hit.geoms);radii[i,j]=max(np.linalg.norm(np.array(p.coords)[0]-center) for p in points)
radii=gaussian_filter1d(radii,1.2,axis=0);index=np.argmin(radii,axis=0);z=zs[index];radius=radii[index,np.arange(len(angles))];points=np.column_stack([center+radius[:,None]*np.column_stack([np.cos(angles),np.sin(angles)]),z])
coef=np.linalg.lstsq(np.column_stack([np.ones(len(points)),points[:,0],points[:,1],points[:,0]**2,points[:,0]*points[:,1],points[:,1]**2]),z,rcond=None)[0]
low,high,key,report=split_neck(mesh,paint,coef.tolist(),args.height/180);out=args.output;out.mkdir(parents=True,exist_ok=False)
np.savez_compressed(out/'source-body.npz',vertices=mesh.vertices,faces=mesh.faces);(out/'source-paint.json').write_text(json.dumps(paint))
for name,(part,colors,*_) in [('torso',low),('head',high),('neck-key',key)]:
 np.savez_compressed(out/f'{name}-source.npz',vertices=part.vertices,faces=part.faces);(out/f'{name}-paint.json').write_text(json.dumps(colors))
(out/'neck-valley.json').write_text(json.dumps({'valley_points':points.tolist(),'quadratic_coefficients':coef.tolist(),'z_samples':zs.tolist(),'angle_count':len(angles)},indent=2))
(out/'construction.json').write_text(json.dumps({'source_file':str(args.source),'source_sha256':digest,'interface':report,'body_socket':low[2],'head_socket':high[2]},indent=2));print(out)
