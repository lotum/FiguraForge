"""Buddy dispatch/binding regressions; no actual 1m rebuild or Blender launch."""
from copy import deepcopy
import hashlib
from types import SimpleNamespace
import numpy as np
import pytest
import trimesh
from figuraforge.models import Settings
from figuraforge.geometry.types import Part,Surface,GeometryError
from figuraforge.services import buddy_pipeline as b
from figuraforge.services.plan_presets import available_presets


def project():
    return {'settings':Settings(height_mm=1000,up_axis='Y',printer_id='h2d-dual',pin_clearance_mm=.05,plate_margin_mm=10,part_gap_mm=20).model_dump(),
            'artifacts':{'mesh':{'hash':b.MESH_HASH,'source':{'sha256':b.SOURCE_SHA256}}}}


def test_buddy_offer_is_bound_to_its_exact_source_hash_scale_axis_and_hardware():
    valid=project();assert [x['id'] for x in available_presets(valid)]==[b.PRESET]
    for key,value in [('height_mm',180),('height_mm',999),('up_axis','Z'),('printer_id','h2d-single')]:
        changed=deepcopy(valid);changed['settings'][key]=value;assert available_presets(changed)==[]
    for field in ('hash','sha256'):
        changed=deepcopy(valid)
        if field=='hash':changed['artifacts']['mesh']['hash']='0'*64
        else:changed['artifacts']['mesh']['source']['sha256']='0'*64
        assert available_presets(changed)==[]


@pytest.mark.parametrize('settings',[{'height_mm':180,'up_axis':'Y'},{'height_mm':1000,'up_axis':'Z'}])
def test_buddy_kernel_rechecks_scale_axis_even_when_known_geometry_matches(monkeypatch,settings):
    mesh=SimpleNamespace(vertices=np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]),faces=np.tile([[0,1,2]],(150000,1)))
    signature=hashlib.sha256(np.asarray(mesh.vertices,dtype='<f8').round(6).tobytes()+np.asarray(mesh.faces,dtype='<i8').tobytes()).hexdigest()
    monkeypatch.setattr(b,'SOURCE_SIGNATURE',signature)
    with pytest.raises(GeometryError,match='1000 mm und Y-up'):
        b._source(SimpleNamespace(mesh=mesh),settings,b.MESH_HASH,{'mesh_hash':b.MESH_HASH})


@pytest.mark.parametrize('connections',[None,{'total_keys':8,'total_keyed_interfaces':3}])
def test_buddy_worker_passes_workdir_and_original_reference_without_refine_or_second_tile(tmp_path,monkeypatch,connections):
    from figuraforge.services.geometry_task import execute
    from figuraforge.geometry import io,refine,split
    mesh=trimesh.creation.box();surface=Surface(mesh,np.zeros((12,3,2)),np.ones((12,3,3)),np.zeros(12,int));reference={'immutable':'original six-color source'};seen={}
    monkeypatch.setattr(io,'load_surface',lambda *_:surface)
    monkeypatch.setattr(io,'save_colored_glb',lambda *args:None)
    def forbidden(*args,**kwargs):pytest.fail('Buddy kernel already partitions/tiles; do not refine or tile a second time')
    monkeypatch.setattr(refine,'refine_with_plan',forbidden);monkeypatch.setattr(split,'tile_parts',forbidden)
    part=Part('body','Body',mesh.copy(),'#805947')
    construction={'part_filament_ids':{'body':['brown','cream']},'part_region_ids':{'body':[0]}}
    if connections:construction['assembly_connections']=connections
    def construct(actual,plan,settings,*,reference_plan,workdir):
        assert actual is surface and reference_plan is reference and workdir==tmp_path
        seen['constructed']=True;return [part],construction
    def pack(parts,*,construction_report,volume,margin,gap):
        assert parts==[part] and construction_report is construction
        seen['packed']=True;tf=np.eye(4);tf[:3,3]=[10,10,.5]
        return [{'id':1,'volume_mm':[300,320,320],'placements':[{'part_id':'body','transform':tf.tolist(),'rect':[9.5,9.5,1,1],'height_mm':1}]}]
    monkeypatch.setattr(b,'construct_buddy',construct);monkeypatch.setattr(b,'pack_buddy_parts',pack)
    request={'operation':'segment','source':'unused.glb','out':str(tmp_path),'settings':project()['settings'],
        'color_plan':{'construction_preset':b.PRESET,'face_regions':[0]*12,'regions':[{'id':0,'color':'#805947'}]},'construction_reference_plan':reference}
    request['settings']['auto_tile']=True
    result=execute(request,lambda _:None)
    assert seen=={'constructed':True,'packed':True}
    assert result['summary']==({'parts':1,'plates':1,'pins':8,'keyed_interfaces':3} if connections else {'parts':1,'plates':1,'pins':0})
    assert result['geometry_report']['tiling']==[] and result['geometry_report']['packing']['passed']
    assert result['geometry_report']['refinement']['construction_preset']==b.PRESET
    assert reference=={'immutable':'original six-color source'}


def test_user_three_spool_region_edits_cannot_bypass_buddy_two_nozzle_guard(monkeypatch):
    mesh=trimesh.creation.box();surface=Surface(mesh,np.zeros((12,3,2)),np.ones((12,3,3)),np.zeros(12,int));plan={'mesh_hash':b.MESH_HASH,'nozzle_count':2,'face_regions':[0]*12,'regions':[{'id':i,'color':'#FFFFFF','filament_id':f'spool-{i}','color_mode':'solid'} for i in range(3)]}
    monkeypatch.setattr(b,'_source',lambda *args:({},np.array(plan['face_regions']),{}));monkeypatch.setattr(b,'anatomical_masks',lambda *args:({},{}))
    material={'two_materials_per_part_passed':True,'part_region_ids':{'body':[0,1,2]},'part_physical_classes':{'body':['brown','cream']},'decisions':[]}
    monkeypatch.setattr(b,'propose_materials',lambda *args:(plan,material,None))
    with pytest.raises(GeometryError,match='mehr physische Spulen als Düsen'):
        b.assign_buddy_materials([Part('body','Body',mesh,'#FFFFFF')],surface,plan,{},reference_plan={})

def test_separate_single_spool_plates_do_not_inherit_other_parts_batch_union():
    mapping={'brown-only':['brown'],'cream-only':['cream']}
    parts=[Part(key,key,trimesh.creation.box([280,300,20]),'#FFFFFF') for key in mapping]
    plates=b.pack_buddy_parts(parts,construction_report={'part_filament_ids':mapping})
    assert len(plates)==2
    for plate in plates:
        actual=sorted({spool for row in plate['placements'] for spool in mapping[row['part_id']]})
        assert plate['physical_filament_ids']==actual
        assert plate['physical_spool_count']==len(actual)

def native_config():
    return {'enable_mixed_color_sublayer':'1','filament_colour':['#805947','#F7E6DE','#AAAAAA'],
        'filament_is_mixed':['0','0','1'],'filament_mixed_components':['','','1,2'],
        'filament_mixed_sublayer_ratios':['','','0.50,0.50'],'filament_mixed_gradient':['0']*3,
        'filament_mixed_gradient_range':['']*3,'filament_mixed_gradient_curve':['']*3,
        'filament_mixed_gradient_per_part':['0']*3,'filament_map':['2','1','1'],
        'nozzle_temperature':['220','220'],'flow_ratio':['.98','.98'],
        'different_settings_to_system':['','','','',''],'layer_height':'.12'}


def test_buddy_native_plate_configuration_is_explicit_and_preserves_thermal_profiles():
    original=native_config();before=deepcopy(original)
    result=b.configure_buddy_plate(original,{'native_physical_slots':[1,2],'placements':[{'part_id':'left-eye','rect':[10,10,20,20]}]})
    assert original==before
    assert result['nozzle_temperature']==before['nozzle_temperature'] and result['flow_ratio']==before['flow_ratio']
    assert result['layer_height']=='0.2' and result['enable_support']=='1' and result['raft_layers']=='3'
    assert result['filament_map'][:2]==['1','2']
    for key in ['layer_height','enable_support','raft_layers','brim_type']:
        assert key in result['different_settings_to_system'][0].split(';')
    with pytest.raises(GeometryError):b.configure_buddy_plate(original,{'native_physical_slots':[3],'placements':[]})


def test_normal_buddy_export_dispatches_actual_plate_spools_and_support_policy(tmp_path,monkeypatch):
    from figuraforge.services.geometry_task import execute
    from figuraforge.geometry import io,types
    from figuraforge.services import mixed_filament as native,plan_materials,export
    mesh=trimesh.creation.box();part=Part('left-eye','Eye',mesh,'#805947');surface=Surface(mesh,np.zeros((12,3,2)),np.ones((12,3,3)),np.zeros(12,int));seen={}
    monkeypatch.setattr(types,'load_part',lambda *args:part)
    monkeypatch.setattr(io,'load_surface',lambda *args:surface)
    monkeypatch.setattr(native,'inspect_template',lambda *args:{'nozzle_count':2})
    monkeypatch.setattr(native,'read_native_template',lambda *args:(native_config(),{}))
    monkeypatch.setattr(native,'native_bed_bounds',lambda *args:{'min':[25,0,0]})
    monkeypatch.setattr(plan_materials,'prepare_native_materials',lambda *args,**kwargs:({'left-eye':[1,2]*6},{'filament_slots':{'brown':1,'cream':2}},kwargs['native_settings']))
    def build(template,output,parts,placements,settings,slots):
        assert parts==[part] and slots=={'left-eye':[1,2]*6}
        assert settings['raft_layers']=='3' and settings['enable_support']=='1'
        assert settings['filament_map'][:2]==['1','2']
        assert placements[0]['transform'][0][3]==35
        seen['build']=True;return {'slicing_verified':False}
    monkeypatch.setattr(native,'build_native_from_parts',build)
    monkeypatch.setattr(export,'export_bundle',lambda parts,plates,out,manifest,additional_files:manifest)
    transform=np.eye(4);transform[:3,3]=[10,10,1]
    result=execute({'operation':'export','out':str(tmp_path),'settings':project()['settings'],'parts_dir':'unused','parts':[part.summary()],
        'filaments':{'left-eye':{'hex':'#805947','id':'brown'}},'manifest':{},'color_plan':{'construction_preset':b.PRESET},
        'native_template':'source-profile.3mf','source':'unused.glb','inventory':[],
        'plates':[{'id':1,'physical_filament_ids':['brown','cream'],'placements':[{'part_id':'left-eye','transform':transform.tolist(),'rect':[9.5,9.5,1,1]}]}]},lambda _:None)
    assert seen=={'build':True} and not result['native_color_export']['slicing_verified']


@pytest.mark.parametrize('change',[{'build_volume_mm':[300,320,325]},{'plate_margin_mm':8},{'part_gap_mm':5}])
def test_unsupported_buddy_packing_is_rejected_before_expensive_construction(tmp_path,monkeypatch,change):
    from figuraforge.services.geometry_task import execute
    from figuraforge.geometry import io
    mesh=trimesh.creation.box();surface=Surface(mesh,np.zeros((12,3,2)),np.ones((12,3,3)),np.zeros(12,int))
    monkeypatch.setattr(io,'load_surface',lambda *_:surface)
    def forbidden(*args,**kwargs):pytest.fail('Unsupported bed/spacing reached expensive Buddy construction')
    monkeypatch.setattr(b,'construct_buddy',forbidden)
    settings=project()['settings'];settings.update(change)
    with pytest.raises(GeometryError,match='Buddy braucht'):
        execute({'operation':'segment','source':'unused.glb','out':str(tmp_path),'settings':settings,
                 'color_plan':{'construction_preset':b.PRESET}},lambda _:None)
