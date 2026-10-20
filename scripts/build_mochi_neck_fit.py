"""Optional exact-key/socket print coupons; no claim about the full organic seam."""
from pathlib import Path
import sys,json,copy
import numpy as np
import trimesh
from shapely.geometry import Polygon
from figuraforge.geometry.mochi_neck import cap_and_socket,labelled_mesh
from figuraforge.geometry.topology import triangulate_polygon,orient_local
from figuraforge.geometry.types import Part
from figuraforge.services.mixed_filament import read_native_template,mark_explicit_process_overrides,build_native_from_parts
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_mochi_neck import placement,native_paint,write
root=Path(sys.argv[1]);out=root/(sys.argv[2] if len(sys.argv)>2 else 'fit-probe');out.mkdir(exist_ok=False);factor=470/180;center=np.array([0.,-27.]);w,d=70/factor/2,50/factor/2
outline=Polygon(center+np.array([[-w,-d],[w,-d],[w,d],[-w,d]]));boundary=np.column_stack([np.asarray(outline.exterior.coords)[:-1],np.zeros(4)]);parts=[];paints={}
for head,name in [(False,'torso-probe'),(True,'kopf-probe')]:
    cap,proof=cap_and_socket(outline,boundary,center=tuple(center),coefficients=[0]*6,scale_factor=factor,head=head,landing_z=0)
    lower,upper=(0,38/factor) if head else (-21.6/factor,0);xy=np.asarray(outline.exterior.coords)[:-1];lo=np.column_stack([xy,np.repeat(lower,4)]);hi=np.column_stack([xy,np.repeat(upper,4)]);t=[cap]
    walls=[]
    for i in range(4):j=(i+1)%4;walls.extend([[lo[i],lo[j],hi[j]],[lo[i],hi[j],hi[i]]])
    t.append(np.asarray(walls));tri=triangulate_polygon(outline);z=upper if head else lower;t.append(orient_local(np.concatenate([tri,np.full((*tri.shape[:2],1),z)],axis=2),head));alltri=np.concatenate(t);mesh,p=labelled_mesh(alltri,['4']*len(alltri));mesh.vertices*=factor;assert mesh.is_volume;parts.append(Part(name,name,mesh,'#805947'));paints[name]=p
with np.load(root/'parts/neck-key.npz') as a:key=trimesh.Trimesh(a['vertices'],a['faces'],process=False)
parts.append(Part('neck-key','neck-key',key,'#272729'));paints['neck-key']=['0C']*len(key.faces)
rows=[placement(parts[0],np.eye(3),[85,95]),placement(parts[1],np.eye(3),[190,95]),placement(parts[2],np.array([[0,0,1],[0,1,0],[-1,0,0]]),[140,175])]
config,_=read_native_template(root/'plate-3-painted.3mf');updated={**config,'enable_support':'0','layer_height':'0.16','support_top_z_distance':'0.16','raft_layers':'0','brim_type':'outer_only','brim_width':'5'};config=mark_explicit_process_overrides(updated,config)
baked=[];locations=[]
for part,row in zip(parts,rows):
    tf=np.array(row['transform']);rotation=np.eye(4);rotation[:3,:3]=tf[:3,:3];p=copy.copy(part);p.mesh=part.mesh.copy();p.mesh.apply_transform(rotation);baked.append(p);loc=np.eye(4);loc[:3,3]=tf[:3,3];locations.append({'part_id':p.id,'transform':loc.tolist()})
# The real cups use .16 mm, the real key .12 mm. Separate plates avoid
# Bambu's variable-layer-height / prime-tower incompatibility and match materials.
from figuraforge.services.native_plates import merge_two_native_plates
native=[]
for i,indices in [(1,[0,1]),(2,[2])]:
    selected=[baked[j] for j in indices];selected_rows=[locations[j] for j in indices]
    settings=config if i==1 else mark_explicit_process_overrides({**config,'layer_height':'0.12'},config)
    bare=out/f'plate-{i}-bare.3mf';proof=build_native_from_parts(root/'plate-3-painted.3mf',bare,selected,selected_rows,settings,{p.id:[3 if p.id=='neck-key' else 1]*len(p.mesh.faces) for p in selected})
    file=out/f'plate-{i}.3mf';native_paint(bare,file,{p.id:paints[p.id] for p in selected},key_overrides=i==2);native.append(file)
file=out/'Mochi-Hals-Passungsprobe.3mf';merged=merge_two_native_plates(*native,file,names=('Halsaufnahmen · Braun · 0,16 mm','Massiver Schlüssel · Schwarz · 0,12 mm'))
write(out/'geometry-verification.json',{'parts':[p.summary() for p in parts],'merge':merged,'scope':'Exact 20x28x36 key and 0.10 mm radial clearance sockets/roof; same materials and layer heights as production; does not test the organic outside seam.'});print(file)
