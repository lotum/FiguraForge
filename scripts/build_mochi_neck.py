"""Build a new three-plate neck-split Mochi without changing existing editions."""
from pathlib import Path
import argparse,copy,json,hashlib,zipfile,sys
from xml.etree import ElementTree as E
import numpy as np
import trimesh
from figuraforge.geometry.types import Part,load_part
from figuraforge.geometry.validation import validate_mesh,check_insert_path,basic_stability,DistanceQuery
from figuraforge.services.native_plates import N,P,CORE,ROOT,MODEL,CONFIG,merge_two_native_plates
from figuraforge.services.mixed_filament import read_native_template,build_native_from_parts,mark_explicit_process_overrides
sys.path.insert(0,str(Path(__file__).resolve().parent))


def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):
    with np.load(path) as a:return trimesh.Trimesh(a['vertices'],a['faces'],process=False)


def native_paint(source,output,paints,*,key_overrides=False):
    with zipfile.ZipFile(source) as z:contents={n:z.read(n) for n in z.namelist()}
    root=E.fromstring(contents[ROOT]);meta=E.fromstring(contents[MODEL]);objects={o.get('id'):o for o in root.findall(N+'resources/'+N+'object')}
    for obj in meta.findall('object'):
        name=obj.find("metadata[@key='name']").get('value');component=objects[obj.get('id')].find(N+'components/'+N+'component');path=component.get(P+'path').lstrip('/');child=E.fromstring(contents[path]);mesh=next(o for o in child.findall(N+'resources/'+N+'object') if o.get('id')==component.get('objectid'))
        triangles=mesh.findall(N+'mesh/'+N+'triangles/'+N+'triangle');assert len(triangles)==len(paints[name])
        for tri,paint in zip(triangles,paints[name]):tri.set('paint_color',paint)
        contents[path]=E.tostring(child,encoding='utf-8',xml_declaration=True)
        if key_overrides and name=='neck-key':
            for key,value in [('layer_height','0.12'),('enable_support','0'),('raft_layers','0'),('brim_type','outer_only'),('brim_width','5'),('sparse_infill_density','100%'),('sparse_infill_pattern','rectilinear'),('wall_loops','4')]:
                existing=obj.find(f"metadata[@key='{key}']")
                if existing is not None:existing.set('value',value)
                else:E.SubElement(obj,'metadata',key=key,value=value)
    contents[MODEL]=E.tostring(meta,encoding='utf-8',xml_declaration=True)
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as z:
        for n,d in contents.items():z.writestr(n,d)


def placement(part,rotation,xy):
    points=part.mesh.vertices@rotation.T;lo,hi=points.min(0),points.max(0);tf=np.eye(4);tf[:3,:3]=rotation;tf[:3,3]=[xy[0]-(lo[0]+hi[0])/2,xy[1]-(lo[1]+hi[1])/2,-lo[2]]
    return {'part_id':part.id,'transform':tf.tolist()}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--height',type=float,default=470);args=p.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False);factor=args.height/180
    work=args.work
    cached=json.loads((work/'construction.json').read_text())
    if not np.isclose(cached['interface']['source_scale_factor'],factor):raise ValueError('Prepare the joint at the requested physical scale before export')
    parts=[];paints={}
    for ident,name,color in [('torso','Mochi · Rumpf mit Halsaufnahme','#805947'),('head','Mochi · Kopf mit Halsaufnahme','#805947'),('neck-key','Asymmetrischer Halsverbinder','#272729')]:
        mesh=load(work/f'{ident}-source.npz');mesh.vertices*=factor;part=Part(ident,name,mesh,color,role='body' if ident=='torso' else 'neck-head' if ident=='head' else 'loose-key');parts.append(part);paints[ident]=json.loads((work/f'{ident}-paint.json').read_text())
    original=Path('benchmarks/mochi-unified-production/build-83f51796f58841c7be1371687fbe528c');data=json.loads((original/'construction.json').read_text())
    delta=np.array([0.,-.498082899,0.])
    for row in data['parts']:
        if row['id']=='body':continue
        part=load_part(original/'parts',row);part.mesh.vertices=(part.mesh.vertices+delta)*factor;parts.append(part);paints[part.id]=['0C']*len(part.mesh.faces)
    for part in parts:part.save(out/'parts');write(out/f'{part.id}-paint.json',paints[part.id])
    user=Path('benchmarks/mochi-user-edition-20261018/Mochi-Richards-Anpassungen-180mm-ORIGINAL.3mf');config,_=read_native_template(user);modified=copy.deepcopy(config)
    modified.update(wipe_tower_x=['250'],wipe_tower_y=['245'],prime_tower_width='40',wipe_tower_no_sparse_layers='0',raft_layers='0',brim_type='auto_brim',brim_width='5',layer_height='0.16',support_top_z_distance='0.16')
    config=mark_explicit_process_overrides(modified,config)
    angle=np.deg2rad(17);R=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
    torso=next(p for p in parts if p.id=='torso');head=next(p for p in parts if p.id=='head');key=next(p for p in parts if p.id=='neck-key')
    plate1=[placement(torso,R,[175,160])];plate2=[placement(head,np.eye(3),[175,125])];plate3=[]
    rotations={row['part_id']:np.asarray(row['transform'])[:3,:3] for row in json.loads((original/'plates.json').read_text())[1]['placements']}
    for x,ident in zip([50,90,130,170,210],['nose','eye-1','eye-2','eye-3','eye-4']):plate3.append(placement(next(p for p in parts if p.id==ident),rotations[ident],[x,50]))
    Ry=np.array([[0,0,1],[0,1,0],[-1,0,0]]);plate3.append(placement(key,Ry,[115,120]))
    native=[]
    for i,rows in enumerate([plate1,plate2,plate3],1):
        selected=[p for p in parts if p.id in {r['part_id'] for r in rows}];settings=copy.deepcopy(config)
        if i==3:settings=mark_explicit_process_overrides({**settings,'layer_height':'0.12','support_top_z_distance':'0.12','raft_layers':'3','brim_type':'outer_only'},settings)
        bare=out/f'plate-{i}-bare.3mf';face_slots={p.id:[3 if p.id not in ('head','torso') else 2 if c=='8' else 1 for c in paints[p.id]] for p in selected}
        # Bake rotations into each NEW printable mesh so Bambu's conservative
        # transformed bounding box cannot falsely put the diagonal torso outside.
        baked=[];baked_rows=[]
        for part in selected:
            row=next(r for r in rows if r['part_id']==part.id);tf=np.asarray(row['transform']);rotation=np.eye(4);rotation[:3,:3]=tf[:3,:3]
            item=copy.copy(part);item.mesh=part.mesh.copy();item.mesh.apply_transform(rotation);baked.append(item)
            location=np.eye(4);location[:3,3]=tf[:3,3];baked_rows.append({'part_id':part.id,'transform':location.tolist()})
        proof=build_native_from_parts(user,bare,baked,baked_rows,settings,face_slots);write(out/f'native-{i}-geometry.json',proof)
        file=out/f'plate-{i}-painted.3mf';native_paint(bare,file,{p.id:paints[p.id] for p in selected},key_overrides=i==3);native.append(file);print(json.dumps({'plate':i,'file':str(file)}),flush=True)
    merge_two_native_plates(native[0],native[1],out/'body-head.3mf',names=(f'Rumpf · {args.height:g} mm Gesamtfigur','Kopf · organische Halsfuge'))
    merged=out/f'Mochi-{args.height:g}mm-Hals-geteilt-3-Platten.3mf';merge=merge_two_native_plates(out/'body-head.3mf',native[2],merged,names=(f'Rumpf · {args.height:g} mm Gesamtfigur','Kopf · organische Halsfuge','Schwarze Details + Halsverbinder'))
    print(json.dumps({'phase':'assembly_checks'}),flush=True)
    path=check_insert_path(head.mesh,torso.mesh,[0,0,1],travel_mm=45,samples=16,tolerance=.025)
    key_paths={p.id:check_insert_path(key.mesh,p.mesh,[0,0,1] if p.id=='torso' else [0,0,-1],travel_mm=45,samples=16,tolerance=.025) for p in [torso,head]}
    quality={p.id:validate_mesh(p.mesh) for p in parts}
    # Verify socket/roof points remain inside the original source solid.
    source=load(work/'source-body.npz');source.vertices*=factor;q=DistanceQuery(source);socket=json.loads((work/'construction.json').read_text());socket_samples=[]
    for name in ['body_socket','head_socket']:
        r=socket[name];xy=np.array(r['socket_outline_source_xy'])*factor;z=r['socket_end_source_z']*factor
        socket_samples.extend(np.column_stack([xy,np.repeat(z,len(xy))]))
    distances=q.values(np.array(socket_samples));wall=float(-distances.max())
    report={'height_mm':args.height,'source_user_file':str(user),'source_user_sha256':sha(user),'original_modified':False,'parts':[p.summary() for p in parts],'quality':quality,'plate_placements':[plate1,plate2,plate3],'project':str(merged),'project_sha256':sha(merged),'merge':merge,'head_extraction':path,'key_extraction':key_paths,'socket_minimum_sampled_source_wall_mm':wall,'physical_print_verified':False,'paid_api_calls':0,'printer_communication':False}
    write(out/'construction-verification.json',report)
    if not path['passed'] or any(not r['passed'] for r in key_paths.values()) or wall<3:raise ValueError('Assembly or wall check failed')
    print(json.dumps({'phase':'done','project':str(merged),'head_extraction':path,'keys':key_paths,'socket_wall':wall}),flush=True)

if __name__=='__main__':main()
