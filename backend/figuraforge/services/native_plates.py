"""Combine two already-native H2D plates without touching their mesh payloads.

Bambu PartPlate uses a 1.2 * printable-area-width grid stride. Object process
options carry the second plate's finer layer height/raft into the shared project.
Only two or three plates on the two-column Bambu grid are supported; no printer communication occurs.
"""
from copy import deepcopy
from pathlib import Path
import json
import uuid
import zipfile
from xml.etree import ElementTree as E
from .mixed_filament import read_native_template, validate_native_settings

CORE='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
PROD='http://schemas.microsoft.com/3dmanufacturing/production/2015/06'
REL='http://schemas.openxmlformats.org/package/2006/relationships'
N='{'+CORE+'}';P='{'+PROD+'}'
E.register_namespace('',CORE);E.register_namespace('p',PROD)
CONFIG='Metadata/project_settings.config';MODEL='Metadata/model_settings.config';ROOT='3D/3dmodel.model'
# These are genuine object-level print options, not thermal/hardware settings.
OBJECT_PROCESS_KEYS=('layer_height','raft_layers','support_top_z_distance','brim_type','brim_width')


def merge_two_native_plates(first, second, output, *, names=('Körper · Braun + Beige','Schwarze Gesichtsdetails')):
    first,second,output=map(Path,(first,second,output))
    if output.exists():raise ValueError('New output required')
    configs=[read_native_template(p)[0] for p in (first,second)]
    for config in configs:validate_native_settings(config)
    a,b=configs
    for key in ('printer_settings_id','printable_area','filament_colour','filament_settings_id','filament_is_mixed','filament_map'):
        if a.get(key)!=b.get(key):raise ValueError('Incompatible plate profiles: '+key)
    unexpected=[k for k in set(a)|set(b) if a.get(k)!=b.get(k) and k not in OBJECT_PROCESS_KEYS+('different_settings_to_system','wipe_tower_x','wipe_tower_y')]
    if unexpected:raise ValueError('Unrepresentable process difference: '+','.join(unexpected))
    points=[list(map(float,p.split('x'))) for p in a['printable_area']]
    stride=1.2*(max(p[0] for p in points)-min(p[0] for p in points))
    with zipfile.ZipFile(first) as z:contents={n:z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(second) as z:other={n:z.read(n) for n in z.namelist()}
    root=E.fromstring(contents[ROOT]);root.set('xmlns:BambuStudio','http://schemas.bambulab.com/package/2021');root2=E.fromstring(other[ROOT]);meta=E.fromstring(contents[MODEL]);meta2=E.fromstring(other[MODEL])
    existing=meta.findall('plate');count=len(existing)+1
    if len(existing) not in (1,2) or len(meta2.findall('plate'))!=1:raise ValueError('Append one native plate to one or two existing plates')
    if len(names)!=count:raise ValueError('Supply one name for each final plate')
    depth=1.2*(max(p[1] for p in points)-min(p[1] for p in points));offset=[stride*((count-1)%2),-depth*((count-1)//2),0.]
    # Bambu's GUI resolves resource IDs across external model documents too.
    # Unique root IDs alone pass CLI slices but can replace a small mesh with
    # the body on GUI save. Allocate a globally disjoint resource ID space.
    used=set()
    for name,data in contents.items():
        if name.startswith('3D/') and name.endswith('.model'):
            used.update(int(o.get('id')) for o in E.fromstring(data).findall(N+'resources/'+N+'object'))
    next_id=max(used,default=0)+1
    remap={}
    for o in root2.findall(N+'resources/'+N+'object'):
        remap[o.get('id')]=str(next_id);next_id+=1
    pathmap={n:f'3D/Objects/plate{count}_'+Path(n).name for n in other if n.startswith('3D/Objects/') and n.endswith('.model')}
    child_ids={}
    for old,new in pathmap.items():
        document=E.fromstring(other[old])
        for obj in document.findall(N+'resources/'+N+'object'):
            before=obj.get('id');child_ids[(old,before)]=str(next_id);obj.set('id',str(next_id));next_id+=1
            obj.set(P+'UUID',str(uuid.uuid4()))
        contents[new]=E.tostring(document,encoding='utf-8',xml_declaration=True)
    part_ids={}
    for obj in root2.findall(N+'resources/'+N+'object'):
        old_root=obj.get('id');obj.set('id',remap[old_root]);obj.set(P+'UUID',str(uuid.uuid4()))
        for c in obj.findall(N+'components/'+N+'component'):
            old=c.get(P+'path','').lstrip('/')
            if old not in pathmap:raise ValueError('External/native component path required')
            before=c.get('objectid');after=child_ids[(old,before)];part_ids[(old_root,before)]=after
            c.set('objectid',after);c.set(P+'path','/'+pathmap[old]);c.set(P+'UUID',str(uuid.uuid4()))
        root.find(N+'resources').append(obj)
    for item in root2.findall(N+'build/'+N+'item'):
        item.set('objectid',remap[item.get('objectid')]);item.set(P+'UUID',str(uuid.uuid4()))
        tf=list(map(float,item.get('transform').split()));tf[9]+=offset[0];tf[10]+=offset[1]
        item.set('transform',' '.join(f'{x:.12g}' for x in tf));root.find(N+'build').append(item)
    for obj in meta2.findall('object'):
        old_root=obj.get('id');obj.set('id',remap[old_root])
        for part in obj.findall('part'):part.set('id',part_ids[(old_root,part.get('id'))])
        for key in OBJECT_PROCESS_KEYS:
            if a.get(key)!=b.get(key) and obj.find(f"metadata[@key='{key}']") is None:E.SubElement(obj,'metadata',key=key,value=str(b[key]))
        meta.insert(0,obj)
    for i,(plate,title) in enumerate(zip([*existing,meta2.find('plate')],names),1):
        for m in list(plate.findall('metadata')):
            key=m.get('key')
            if key in ('gcode_file','thumbnail_file','thumbnail_no_light_file','top_file','pick_file'):plate.remove(m)
            elif key=='plater_id':m.set('value',str(i))
            elif key=='plater_name':m.set('value',title)
        # Deterministic physical-nozzle assignment on each build plate.
        for key,value in [('filament_map_mode','Manual'),('filament_maps',' '.join(a['filament_map'])),('filament_volume_maps',' '.join(['0']*len(a['filament_map'])))]:
            old=next((m for m in plate.findall('metadata') if m.get('key')==key),None)
            if old is not None:plate.remove(old)
            E.SubElement(plate,'metadata',key=key,value=value)
        if i==count:
            for j,instance in enumerate(plate.findall('model_instance'),100*(count-1)):
                for m in instance.findall('metadata'):
                    if m.get('key')=='object_id':m.set('value',remap[m.get('value')])
                    if m.get('key')=='identify_id':m.set('value',str(j))
            meta.insert(list(meta).index(meta.find('assemble')),plate)
    relpath='3D/_rels/3dmodel.model.rels';rels=E.fromstring(contents[relpath])
    for i,new in enumerate(pathmap.values(),100):E.SubElement(rels,'{'+REL+'}Relationship',Id=f'rel-plate{count}-'+str(i),Type='http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel',Target='/'+new)
    config=deepcopy(a)
    for key in ('wipe_tower_x','wipe_tower_y'):config[key]=a[key][:len(existing)]+[b[key][0]]
    # Thumbnails and cached slicing data would refer to the old single plate.
    contents={n:d for n,d in contents.items() if not (n.startswith(('Metadata/plate_','Metadata/top_','Metadata/pick_','Auxiliaries/')) or n in ('Metadata/slice_info.config','Metadata/cut_information.xml'))}
    for path,tree in ((ROOT,root),(MODEL,meta)):contents[path]=E.tostring(tree,encoding='utf-8',xml_declaration=True)
    # Bambu's relationship reader matches unprefixed tags; default REL is required.
    E.register_namespace('',REL)
    contents[relpath]=E.tostring(rels,encoding='utf-8',xml_declaration=True)
    package_rels=E.fromstring(contents['_rels/.rels'])
    for r in list(package_rels):
        if r.get('Target','').lstrip('/') not in contents:package_rels.remove(r)
    contents['_rels/.rels']=E.tostring(package_rels,encoding='utf-8',xml_declaration=True)
    E.register_namespace('',CORE)
    contents[CONFIG]=(json.dumps(config,indent=2)+'\n').encode()
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as z:
        for n,d in contents.items():z.writestr(n,d)
    return {'plates':count,'plate2_world_offset_mm':offset if count==2 else [stride,0,0],'appended_plate_world_offset_mm':offset,'parts_per_plate':[len(p.findall('model_instance')) for p in meta.findall('plate')],
        'second_plate_object_overrides':{k:b[k] for k in OBJECT_PROCESS_KEYS if a.get(k)!=b.get(k)},'source_geometry_and_paint_unchanged':True,'global_resource_ids_unique':True,'slicing_verified':False}
