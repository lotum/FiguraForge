"""Preserve a user-painted body, correct details and scale NEW native editions."""
from pathlib import Path
import argparse,copy,json,hashlib,zipfile,uuid,sys
from xml.etree import ElementTree as E
import numpy as np
from figuraforge.services.native_plates import N,P,CORE,REL,ROOT,MODEL,CONFIG,merge_two_native_plates
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_native_parity import records,matrix


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_archive(contents,path):
    with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED) as z:
        for n,d in contents.items():z.writestr(n,d)


def selected_scaled_plate(source,output,keys,height,*,shared_config=None,right_only=False):
    with zipfile.ZipFile(source) as z:contents={n:z.read(n) for n in z.namelist()}
    record,config=records(source);root=E.fromstring(contents[ROOT]);root.set('xmlns:BambuStudio','http://schemas.bambulab.com/package/2021');meta=E.fromstring(contents[MODEL])
    names={o.get('id'):o.find("metadata[@key='name']").get('value') for o in meta.findall('object')};ids={i for i,n in names.items() if n in keys}
    if {names[i] for i in ids}!=set(keys):raise ValueError('Missing requested objects')
    scale=height/180.;objects=root.find(N+'resources');build=root.find(N+'build')
    retained=set()
    for obj in list(objects):
        if obj.get('id') not in ids:objects.remove(obj)
        else:
            for c in obj.findall(N+'components/'+N+'component'):retained.add(c.get(P+'path').lstrip('/'))
    for item in list(build):
        if item.get('objectid') not in ids:build.remove(item);continue
        key=names[item.get('objectid')];tf=matrix(item.get('transform'));vertices=record[key][0][0];lo=vertices.min(0);hi=vertices.max(0)
        if key=='body':
            anchor=np.array([(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]]);target=anchor.copy() if height==180 else np.array([175.,145.,0.])
        else:target=np.array([(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,0]);anchor=np.array([target[0],target[1],lo[2]])
        tf[:3,:3]*=scale;tf[:3,3]=scale*(tf[:3,3]-anchor)+target
        item.set('transform',' '.join(f'{v:.12g}' for v in tf[:3,:].T.reshape(-1)))
    for obj in list(meta.findall('object')):
        if obj.get('id') not in ids:meta.remove(obj)
    for plate in list(meta.findall('plate')):meta.remove(plate)
    assemble=meta.find('assemble')
    if assemble is not None:meta.remove(assemble)
    plate=E.SubElement(meta,'plate')
    for k,v in [('plater_id','1'),('plater_name','Körper' if keys==['body'] else 'Korrekte schwarze Details'),('locked','false'),('filament_map_mode','Manual')]:E.SubElement(plate,'metadata',key=k,value=v)
    for j,ident in enumerate(sorted(ids,key=int),1):
        instance=E.SubElement(plate,'model_instance')
        for k,v in [('object_id',ident),('instance_id','0'),('identify_id',str(j))]:E.SubElement(instance,'metadata',key=k,value=v)
    E.SubElement(meta,'assemble')
    if shared_config is not None:
        own=config;config=copy.deepcopy(shared_config)
        for k in ('layer_height','raft_layers','support_top_z_distance','brim_type','brim_width'):config[k]=own[k]
    if right_only:config['filament_map']=['2']*len(config['filament_map'])
    if height>180:
        previous=copy.deepcopy(config)
        config.update(wipe_tower_x=['250'],wipe_tower_y=['245'],prime_tower_width='40',wipe_tower_no_sparse_layers='0')
        from figuraforge.services.mixed_filament import mark_explicit_process_overrides
        config=mark_explicit_process_overrides(config,previous)
    else:
        config['wipe_tower_x']=[config['wipe_tower_x'][0]];config['wipe_tower_y']=[config['wipe_tower_y'][0]]
    E.SubElement(plate,'metadata',key='filament_maps',value=' '.join(config['filament_map']))
    # Caches, stale assembly transforms and other plates must never survive scaling.
    contents={n:d for n,d in contents.items() if not n.startswith(('Metadata/plate_','Metadata/top_','Metadata/pick_','Auxiliaries/')) and not n.endswith('.gcode') and n not in ('Metadata/slice_info.config','Metadata/cut_information.xml','Metadata/model_settings.config.rels') and (not n.startswith('3D/Objects/') or n in retained)}
    contents[ROOT]=E.tostring(root,encoding='utf-8',xml_declaration=True);contents[MODEL]=E.tostring(meta,encoding='utf-8',xml_declaration=True);contents[CONFIG]=json.dumps(config,indent=2).encode()
    E.register_namespace('',REL)
    for path in ('_rels/.rels','3D/_rels/3dmodel.model.rels'):
        rels=E.fromstring(contents[path])
        for r in list(rels):
            if r.get('Target','').lstrip('/') not in contents:rels.remove(r)
        contents[path]=E.tostring(rels,encoding='utf-8',xml_declaration=True)
    E.register_namespace('',CORE);write_archive(contents,output)
    return config


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--black',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    source_sha=sha(args.source);reports=[]
    for height,right in [(180,False),(320,False),(325,True)]:
        name=f'Mochi-{height}mm-'+('rechte-Duese' if right else 'zwei-Duesen');body=args.output/(name+'-Koerper.3mf');black=args.output/(name+'-Details.3mf')
        config=selected_scaled_plate(args.source,body,['body'],height,right_only=right)
        selected_scaled_plate(args.black,black,['nose','eye-1','eye-2','eye-3','eye-4'],height,shared_config=config,right_only=right)
        merged=args.output/(name+'-2-Platten.3mf');proof=merge_two_native_plates(body,black,merged)
        reports.append({'height_mm':height,'right_only':right,'body':str(body),'black':str(black),'project':str(merged),'sha256':sha(merged),'merge':proof})
        print(json.dumps(reports[-1]),flush=True)
    assert sha(args.source)==source_sha
    (args.output/'build-verification.json').write_text(json.dumps({'user_source':str(args.source),'user_source_sha256':source_sha,'user_source_unchanged':True,'editions':reports},indent=2))

if __name__=='__main__':main()
