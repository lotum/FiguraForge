"""Regression: two native plates remain separate with intact meshes/processes."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile
from xml.etree import ElementTree as E
import numpy as np
import pytest
import trimesh
from figuraforge.geometry.types import Surface,Part
from figuraforge.services.native_plates import merge_two_native_plates,CORE,PROD,REL,ROOT,MODEL,CONFIG
from figuraforge.services.mixed_filament import ARRAYS


def fixture(path,*,fine=False,color='#805947'):
    settings={k:['']*3 for k in ARRAYS}
    settings.update(filament_is_mixed=['0']*3,enable_mixed_color_sublayer='0',filament_colour=[color,'#F7E6DE','#272729'],filament_settings_id=['Brown','Beige','Black'],filament_map=['1','2','2'],printer_settings_id='H2D',printable_area=['0x0','350x0','350x320','0x320'],wipe_tower_x=['235'],wipe_tower_y=['250'],layer_height='0.12' if fine else '0.16',raft_layers='3' if fine else '0',support_top_z_distance='0.12' if fine else '0.16',brim_type='outer_only' if fine else 'auto_brim',brim_width='5')
    root=f'<model xmlns="{CORE}" xmlns:p="{PROD}" requiredextensions="p"><resources><object id="2" type="model"><components><component p:path="/3D/Objects/object_1.model" objectid="1"/></components></object></resources><build><item objectid="2" transform="1 0 0 0 1 0 0 0 1 100 50 0"/></build></model>'
    model='<config><object id="2"><metadata key="name" value="'+('nose' if fine else 'body')+'"/><part id="1"/></object><plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value=""/><metadata key="gcode_file" value="old.gcode"/><model_instance><metadata key="object_id" value="2"/><metadata key="instance_id" value="0"/><metadata key="identify_id" value="1"/></model_instance></plate><assemble/></config>'
    rel=f'<Relationships xmlns="{REL}"><Relationship Id="r1" Target="/3D/Objects/object_1.model" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    mesh=(f'<model xmlns="{CORE}"><resources><object id="1"><mesh><vertices><vertex x="0" y="0" z="0"/><vertex x="1" y="0" z="0"/><vertex x="0" y="1" z="0"/></vertices><triangles><triangle v1="0" v2="1" v3="2" paint_color="4"/></triangles></mesh></object></resources><build/></model>').encode()
    with zipfile.ZipFile(path,'x') as z:
        for n,d in {ROOT:root,MODEL:model,CONFIG:json.dumps(settings),'3D/_rels/3dmodel.model.rels':rel,'_rels/.rels':f'<Relationships xmlns="{REL}"><Relationship Id="r" Target="/3D/3dmodel.model"/><Relationship Id="thumb" Target="/Metadata/plate_1.png"/></Relationships>','3D/Objects/object_1.model':mesh,'Metadata/plate_1.png':b'stale','Metadata/slice_info.config':b'stale'}.items():z.writestr(n,d)
    return mesh


def test_merge_preserves_geometry_profiles_and_plate2_process(tmp_path):
    first=tmp_path/'a.3mf';second=tmp_path/'b.3mf';output=tmp_path/'combined.3mf';payload=fixture(first);fixture(second,fine=True)
    hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in (first,second)]
    proof=merge_two_native_plates(first,second,output)
    assert proof['parts_per_plate']==[1,1] and proof['plate2_world_offset_mm']==[420,0,0]
    assert hashes==[hashlib.sha256(p.read_bytes()).hexdigest() for p in (first,second)]
    with zipfile.ZipFile(output) as z:
        assert z.read('3D/Objects/object_1.model')==payload
        left=E.fromstring(z.read('3D/Objects/object_1.model'));right=E.fromstring(z.read('3D/Objects/plate2_object_1.model'))
        assert E.tostring(left.find('.//{'+CORE+'}mesh'))==E.tostring(right.find('.//{'+CORE+'}mesh'))
        all_ids=[o.get('id') for name in z.namelist() if name.startswith('3D/') and name.endswith('.model') for o in E.fromstring(z.read(name)).findall('{'+CORE+'}resources/{'+CORE+'}object')]
        assert len(all_ids)==len(set(all_ids)), 'GUI mesh cache requires global IDs across external model files'
        child=right.find('{'+CORE+'}resources/{'+CORE+'}object');assert child.get('id')=='4'
        root=E.fromstring(z.read(ROOT));items=root.findall('{'+CORE+'}build/{'+CORE+'}item');assert [i.get('objectid') for i in items]==['2','3'];assert list(map(float,items[1].get('transform').split()))[9]==520
        meta=E.fromstring(z.read(MODEL));plates=meta.findall('plate');assert [p.find("metadata[@key='plater_id']").get('value') for p in plates]==['1','2']
        assert plates[1].find("model_instance/metadata[@key='object_id']").get('value')=='3'
        obj=meta.find("object[@id='3']");assert obj.find('part').get('id')=='4';assert obj.find("metadata[@key='raft_layers']").get('value')=='3';assert obj.find("metadata[@key='layer_height']").get('value')=='0.12'
        config=json.loads(z.read(CONFIG));assert config['filament_colour']==['#805947','#F7E6DE','#272729'];assert config['wipe_tower_x']==['235','235'];assert config['filament_is_mixed']==['0']*3
        assert b'<Relationships xmlns=' in z.read('3D/_rels/3dmodel.model.rels')  # native parser rejects prefixed tags
        assert 'Metadata/plate_1.png' not in z.namelist();assert b'Target="/Metadata/plate_1.png"' not in z.read('_rels/.rels')
    with pytest.raises(ValueError,match='New output'):merge_two_native_plates(first,second,output)


def test_incompatible_materials_fail_before_writing(tmp_path):
    a=tmp_path/'a';b=tmp_path/'b';out=tmp_path/'out';fixture(a);fixture(b,color='#FFFFFF')
    with pytest.raises(ValueError,match='Incompatible'):merge_two_native_plates(a,b,out)
    assert not out.exists()


def test_solid_mapping_merges_shading_but_retains_cream_and_black():
    spec=importlib.util.spec_from_file_location('mochi_solid',Path(__file__).resolve().parents[1]/'scripts/build_mochi_solid.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    from figuraforge.geometry.colors import hex_rgb
    mesh=trimesh.creation.box();palette=np.array([hex_rgb(c) for c in ['#AF440A','#852F06','#EFB27C']]);classes=np.arange(len(mesh.faces))%3
    surface=Surface(mesh,np.zeros((len(mesh.faces),3,2)),np.repeat(palette[classes,None,:],3,axis=1),np.zeros(len(mesh.faces),int))
    body=Part('body','Body',mesh.copy(),'#805947');nose=Part('nose','Nose',mesh.copy(),'#272729')
    before=body.mesh.vertices.copy();slots,proof=module.solid_face_slots([body,nose],surface)
    assert np.array_equal(slots['body'],np.where(classes==2,2,1));assert set(slots['nose'])=={3};assert np.array_equal(before,body.mesh.vertices)
    assert proof['body']['exterior_faces']==len(mesh.faces)


def test_new_scale_preserves_user_paint_and_does_not_change_source(tmp_path):
    import sys
    spec=importlib.util.spec_from_file_location('prepare_user',Path(__file__).resolve().parents[1]/'scripts/prepare_mochi_user_edition.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    src=tmp_path/'user.3mf';out=tmp_path/'large.3mf';fixture(src)
    before=hashlib.sha256(src.read_bytes()).hexdigest()
    config=module.selected_scaled_plate(src,out,['body'],320)
    from verify_native_parity import records
    a,_=records(src);b,_=records(out);v,f,p=a['body'][0];w,g,q=b['body'][0]
    assert np.array_equal(f,g) and p==q
    assert np.allclose(np.ptp(w,axis=0),np.ptp(v,axis=0)*320/180)
    assert config['wipe_tower_no_sparse_layers']=='0' and config['prime_tower_width']=='40'
    assert config['wipe_tower_x']==['250'] and config['wipe_tower_y']==['245']
    assert hashlib.sha256(src.read_bytes()).hexdigest()==before
    with pytest.raises(FileExistsError):module.selected_scaled_plate(src,out,['body'],320)


def test_append_third_plate_preserves_overrides_and_uses_second_row(tmp_path):
    first=tmp_path/'a.3mf';second=tmp_path/'b.3mf';third=tmp_path/'c.3mf';two=tmp_path/'ab.3mf';three=tmp_path/'abc.3mf'
    fixture(first);fixture(second);fixture(third,fine=True)
    # An explicit key raft override must beat its source plate's default raft.
    with zipfile.ZipFile(third) as z:contents={n:z.read(n) for n in z.namelist()}
    meta=E.fromstring(contents[MODEL]);E.SubElement(meta.find('object'),'metadata',key='raft_layers',value='0');contents[MODEL]=E.tostring(meta)
    explicit=tmp_path/'explicit.3mf'
    with zipfile.ZipFile(explicit,'x') as z:
        for n,d in contents.items():z.writestr(n,d)
    merge_two_native_plates(first,second,two)
    proof=merge_two_native_plates(two,explicit,three,names=('Torso','Head','Black + key'))
    assert proof['plates']==3 and proof['appended_plate_world_offset_mm']==[0,-384,0]
    with zipfile.ZipFile(three) as z:
        root=E.fromstring(z.read(ROOT));items=root.findall('{'+CORE+'}build/{'+CORE+'}item');assert list(map(float,items[-1].get('transform').split()))[9:11]==[100,-334]
        meta=E.fromstring(z.read(MODEL));assert len(meta.findall('plate'))==3
        obj=meta.find("object[@id='5']");assert len(obj.findall("metadata[@key='raft_layers']"))==1;assert obj.find("metadata[@key='raft_layers']").get('value')=='0'
        ids=[o.get('id') for name in z.namelist() if name.startswith('3D/') and name.endswith('.model') for o in E.fromstring(z.read(name)).findall('{'+CORE+'}resources/{'+CORE+'}object')];assert len(ids)==len(set(ids))
        assert len(json.loads(z.read(CONFIG))['wipe_tower_x'])==3
