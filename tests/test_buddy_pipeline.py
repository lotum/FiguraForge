import numpy as np
import pytest
import trimesh
from figuraforge.geometry.types import Part,Surface,GeometryError
from figuraforge.services.buddy_pipeline import pack_buddy_parts,suggest_buddy_plan,MESH_HASH


def test_buddy_packing_counts_spools_instead_of_average_part_color():
    mapping={'fur':['gold','brown'],'collar':['gold','navy'],'eye':['black','cream'],
             'nose':['black'],'paper':['cream'],'ear':['gold']}
    parts=[Part(key,key,trimesh.creation.box([20,20,20]),'#FFFFFF') for key in mapping]
    plates=pack_buddy_parts(parts,construction_report={'part_filament_ids':mapping})
    assert len(plates)==3
    seen=[]
    for plate in plates:
        ids=[row['part_id'] for row in plate['placements']];seen.extend(ids)
        union={ident for key in ids for ident in mapping[key]}
        assert len(union)<=2
        assert sorted(union)==plate['physical_filament_ids']
    assert sorted(seen)==sorted(mapping)


def test_buddy_packing_rejects_missing_or_three_spool_mapping():
    parts=[Part('part','part',trimesh.creation.box(), '#FFFFFF')]
    with pytest.raises(GeometryError):pack_buddy_parts(parts,construction_report={'part_filament_ids':{}})
    with pytest.raises(GeometryError):pack_buddy_parts(parts,construction_report={'part_filament_ids':{'part':['a','b','c']}})


def test_buddy_suggestion_rejects_other_geometry_before_using_inventory():
    mesh=trimesh.creation.box();surface=Surface(mesh,np.zeros((12,3,2)),np.ones((12,3,3)),np.zeros(12,dtype=int))
    with pytest.raises(GeometryError,match='unveränderte verifizierte'):
        suggest_buddy_plan(surface,{'mesh_hash':MESH_HASH},{'height_mm':1000,'up_axis':'Y'},MESH_HASH,[])


def test_old_palette_indexes_are_not_reused_as_new_anatomical_material_ids(monkeypatch):
    import copy
    from figuraforge.services import buddy_pipeline as b
    from figuraforge.geometry.buddy_materials import PALETTE
    document={'mesh_hash':MESH_HASH,'face_regions':[0],'regions':[{'id':i,'color':color} for i,(color,_,_) in enumerate(PALETTE)]}
    monkeypatch.setattr(b,'_source',lambda *args:({'owned_filaments_only':True},np.array([0]),{}))
    monkeypatch.setattr(b,'anatomical_masks',lambda *args:({},{}))
    monkeypatch.setattr(b,'propose_materials',lambda *args:(copy.deepcopy(document),{'decisions':[]},None))
    colors={'gold':'#ECA24D','brown':'#61360C','navy':'#0C2842','black':'#292119','cream':'#DCD4B7'}
    stock=[{'id':key,'hex':color,'material':'PLA','owned':True,'allowed':True} for key,color in colors.items()]
    # Original six-cluster index 3 is navy; new semantic index 3 is the nose.
    old={'mesh_hash':MESH_HASH,'face_regions':[0],'regions':[{'id':3,'filament_id':'navy'},{'id':5,'filament_id':'gold'}]}
    suggested,_=b.suggest_buddy_plan(None,{'mesh_hash':MESH_HASH},{},MESH_HASH,stock,current_plan=old)
    byid={r['id']:r for r in suggested['regions']}
    assert byid[2]['filament_id']=='navy'
    assert byid[3]['filament_id']=='black'
    assert byid[4]['filament_id']=='black'
    assert byid[5]['filament_id']=='cream'
    assert byid[7]['filament_id']=='gold'


def test_reassign_loaded_parts_updates_real_spool_union_and_preview_color(monkeypatch):
    from figuraforge.services import buddy_pipeline as b
    mesh=trimesh.creation.box();surface=Surface(mesh,np.zeros((12,3,2)),np.ones((12,3,3)),np.zeros(12,dtype=int))
    tags=[0]+[1]*11
    plan={'mesh_hash':MESH_HASH,'face_regions':tags,'nozzle_count':2,'regions':[
        {'id':0,'color':'#111111','filament_id':'new-black','color_mode':'solid'},
        {'id':1,'color':'#EEEEDD','filament_id':'new-cream','color_mode':'solid'}]}
    monkeypatch.setattr(b,'_source',lambda *args:({},np.array(tags),{}))
    monkeypatch.setattr(b,'anatomical_masks',lambda *args:({},{}))
    mapping={'two_materials_per_part_passed':True,'part_region_ids':{'part':[0,1]},
             'part_physical_classes':{'part':['black','cream']},'decisions':[]}
    monkeypatch.setattr(b,'propose_materials',lambda *args:(plan,mapping,None))
    part=Part('part','part',mesh.copy(),'#FF0000',filament_id='old-filament')
    result=b.assign_buddy_materials([part],surface,plan,{},reference_plan={})
    assert result['part_filament_ids']['part']==['new-black','new-cream']
    assert part.color=='#EEEEDD'
    assert part.color_index==1
    assert part.filament_id is None


def test_large_single_color_parts_keep_only_their_actual_plate_spool():
    parts=[Part(key,key,trimesh.creation.box([280,300,200]),'#FFFFFF') for key in ['a','b']]
    plates=pack_buddy_parts(parts,construction_report={'part_filament_ids':{'a':['gold'],'b':['brown']}})
    assert len(plates)==2
    for plate in plates:
        key=plate['placements'][0]['part_id']
        assert plate['physical_filament_ids']==[{'a':'gold','b':'brown'}[key]]


def test_buddy_support_routing_uses_only_actual_plate_spools(monkeypatch):
    from figuraforge.services.buddy_pipeline import configure_buddy_plate
    from figuraforge.services import mixed_filament
    monkeypatch.setattr(mixed_filament,'validate_native_settings',lambda config:{'physical_slots':[1,2,3,4,5],'slot_count':5})
    monkeypatch.setattr(mixed_filament,'mark_explicit_process_overrides',lambda result,source:result)
    original={'filament_map':['1']*5,'nozzle_temperature':['220']*5}
    single=configure_buddy_plate(original,{'native_physical_slots':[4],'placements':[{'part_id':'nose'}]})
    assert single['support_filament']==single['support_interface_filament']=='4'
    assert single['raft_layers']=='3'
    pair=configure_buddy_plate(original,{'native_physical_slots':[3,5],'placements':[{'part_id':'body','rect':[8,8,100,100]}]})
    assert pair['support_filament']==pair['support_interface_filament']=='0'
    assert [pair['filament_map'][i] for i in [2,4]]==['1','2']
    assert pair['nozzle_temperature']==original['nozzle_temperature']
    assert original['filament_map']==['1']*5
    with pytest.raises(GeometryError):configure_buddy_plate(original,{'native_physical_slots':[1,2,3]})


def test_buddy_two_spool_plate_reserves_tower_and_splits_full_pair():
    parts=[Part(key,key,trimesh.creation.box([278,135,100]),'#B19870') for key in ['left','right']]
    mapping={key:['gold','navy'] for key in ['left','right']}
    plates=pack_buddy_parts(parts,construction_report={'part_filament_ids':mapping})
    assert len(plates)==2
    for plate in plates:
        x,y,w,h=plate['prime_tower_reserve']['rect']
        assert 0<=x<x+w<=300 and 0<=y<y+h<=320
        for item in plate['placements']:
            xx,yy,ww,hh=item['rect']
            assert x+w+5<=xx or xx+ww+5<=x or y+h+5<=yy or yy+hh+5<=y
    with pytest.raises(GeometryError,match='mindestens10'):pack_buddy_parts(parts,construction_report={'part_filament_ids':mapping},margin=8)


def test_buddy_instructions_reconstruct_tree_before_closing_neck():
    from figuraforge.services.buddy_pipeline import assembly_instructions,PRESET
    report={'construction_preset':PRESET,'structural_splits':[
        {'id':'joint-001','parent':'collar-body','children':['collar-body-a','collar-body-b'],'axis':1,'pins':[{}],'path_check':{'passed':True}},
        {'id':'joint-002','parent':'collar-body-a','children':['leaf1','leaf2'],'axis':0,'pins':[{}],'path_check':{'passed':True}}],
        'collar_assembly':{'ordered_part_ids':['collar-body','collar-left','collar-right','collar-neck-0','collar-neck-1','collar-head']}}
    instructions=assembly_instructions(report);text='\n'.join(instructions)
    assert text.index('Struktur joint-002')<text.index('Struktur joint-001')<text.index('Halsmontage 1')
    assert text.index('Halsmontage 3')<text.index('Halsmontage 4')<text.index('Halsmontage 6')
    assert 'drei ausdrücklich stiftlose' in text
    report['structural_splits'][0]['path_check']['passed']=False
    with pytest.raises(GeometryError,match='ungeprüfte'):assembly_instructions(report)


def test_buddy_preview_keeps_original_outer_normals_and_flat_inner_cap():
    from figuraforge.services.buddy_pipeline import _buddy_corner_normals
    source=trimesh.creation.box([2,2,2]);surface=Surface(source,np.zeros((12,3,2)),np.ones((12,3,3)),np.zeros(12,dtype=int))
    # An added inner construction triangle changes shared-vertex averages,
    # although none of the original outside triangles/positions changed.
    cap=trimesh.Trimesh(vertices=[source.vertices[0],source.vertices[1],[0,0,0]],faces=[[0,1,2]],process=False)
    part=trimesh.util.concatenate([source,cap]);part.merge_vertices()
    outside=np.array([True]*12+[False]);ids=np.r_[np.arange(12),0]
    positions=part.vertices.copy();faces=part.faces.copy()
    normals=_buddy_corner_normals(part,surface,outside,ids)
    assert np.allclose(normals[:12],source.vertex_normals[source.faces])
    assert np.allclose(normals[-1],part.face_normals[-1])
    assert np.array_equal(part.vertices,positions) and np.array_equal(part.faces,faces)


def test_buddy_nose_keys_print_vertical_on_their_own_supported_plate():
    nose=Part('nose','nose',trimesh.creation.box([20,30,10]),'#272729',assembly_direction=[0,-1,0])
    vertices=nose.mesh.vertices.copy()
    plates=pack_buddy_parts([nose],construction_report={'part_filament_ids':{'nose':['black']}})
    assert len(plates)==1 and len(plates[0]['placements'])==1
    item=plates[0]['placements'][0];rotation=np.array(item['transform'])[:3,:3]
    assert np.allclose(rotation@-np.array(nose.assembly_direction),[0,0,1])
    assert 'raft' in item['support_status']
    assert np.array_equal(nose.mesh.vertices,vertices)


def test_buddy_tower_reserve_includes_measured_native_ribs():
    from figuraforge.services.buddy_pipeline import _buddy_tower
    reserve=_buddy_tower({'placements':[{'rect':[10,10,100,100]}]})
    x,y,w,h=reserve['rect'];anchor=np.asarray(reserve['physical_xy'])
    # Endpoint bounds measured on native H2D tower with official 8-mm ribs;
    # include another .25 mm for the bead footprint, not only centerlines.
    lo=anchor+[-7.396,-8.192]-.25;hi=anchor+[42.812,42.144]+.25
    assert np.all(lo>=[x+25,y]) and np.all(hi<=[x+25+w,y+h])


def test_connection_summary_counts_original_interfaces_and_only_real_final_leaves():
    from figuraforge.services.buddy_pipeline import connection_summary,PRESET
    pins=lambda n:[{'shape':'keyed'} for _ in range(n)]
    report={'construction_preset':PRESET,'anatomical_attempts':[
        {'part_id':'nose','parts':[{'id':'nose','connectors':pins(2)}]},
        {'part_id':'tail','pins':pins(2)},
        {'part_id':'left-eye','parts':[{'id':'left-eye','connectors':[]}]}],
        'collar_assembly':{'parts':[{'id':'collar-body','connectors':pins(3)},
            {'id':'collar-neck-0','connectors':pins(3)}, {'id':'collar-left','connectors':pins(2)},
            {'id':'collar-right','connectors':[]}]},
        'structural_splits':[{'id':'j1','parent':'collar-body','children':['body-a','body-b'],
             'pins':pins(2),'path_check':{'passed':True}},
            {'id':'j2','parent':'body-a','children':['body-a-a','body-a-b'],
             'pins':pins(2),'path_check':{'passed':True}}],
        'part_region_ids':{key:[] for key in ['body-a-a','body-a-b','body-b','nose','tail','left-eye','right-eye','collar-neck-1','collar-right']}}
    result=connection_summary({'construction':report})
    assert result['total_keys']==16
    assert result['total_keyed_interfaces']==7
    assert result['structural_keys']==4
    assert result['structural_leaf_part_ids']==['body-a-a','body-a-b','body-b']
    assert result['glue_part_ids']==['left-eye','right-eye','collar-neck-1']
    assert 'collar-right' not in result['glue_part_ids']
    assert all('connectors' not in row for row in result['interfaces'])
    report['part_region_ids'].pop('body-b')
    with pytest.raises(GeometryError,match='Endteilen'):connection_summary(report)
    report['structural_splits'][0]['path_check']['passed']=False
    with pytest.raises(GeometryError,match='ungeprüfte'):connection_summary(report)


def test_ring_support_rotation_happens_after_tower_separates_shared_plate(monkeypatch):
    from figuraforge.services import buddy_pipeline as b
    import copy
    original={'id':1,'placements':[
        {'part_id':'collar-left','transform':np.eye(4).tolist(),'rect':[10.,10.,276.7,137.8]},
        {'part_id':'collar-right','transform':np.eye(4).tolist(),'rect':[10.,164.7546,276.7014,137.844]}]}
    monkeypatch.setattr(b,'pack_parts',lambda *args,**kwargs:[copy.deepcopy(original)])
    monkeypatch.setattr(b,'_buddy_tower',lambda plate:None if len(plate['placements'])>1 else {'rect':[0,0,55,85]})
    monkeypatch.setattr(b,'validate_packing',lambda *args:{'passed':True})
    parts=[Part(key,key,trimesh.creation.box(), '#FFFFFF') for key in ['collar-left','collar-right']]
    result=b.pack_buddy_parts(parts,construction_report={'part_filament_ids':{p.id:['a','b'] for p in parts}})
    assert len(result)==2
    left,right=[plate['placements'][0] for plate in result]
    assert np.array_equal(left['transform'],np.eye(4))
    assert np.allclose(np.asarray(right['transform'])[:2,:2],[[0,-1],[1,0]])
    assert np.allclose(right['rect'],[74.0184,20.238,137.844,276.7014])
    assert 'support_placement_policy' in right


def test_mono_torso_support_has_additional_real_linewidth_reserve(monkeypatch):
    from figuraforge.services import buddy_pipeline as b
    import copy
    ident='collar-body-a-b-a-a'
    plate={'placements':[{'part_id':ident,'transform':np.eye(4).tolist(),'rect':[10.,10.,228.7,210.1]}]}
    monkeypatch.setattr(b,'pack_parts',lambda *args,**kwargs:[copy.deepcopy(plate)])
    monkeypatch.setattr(b,'validate_packing',lambda *args:{'passed':True})
    part=Part(ident,ident,trimesh.creation.box(),'#B19870')
    mono=b.pack_buddy_parts([part],construction_report={'part_filament_ids':{ident:['wood']}})[0]
    dual=b.pack_buddy_parts([part],construction_report={'part_filament_ids':{ident:['wood','brown']}})[0]
    a=mono['placements'][0];c=dual['placements'][0]
    assert a['rect'][0]==pytest.approx(c['rect'][0]+1.)
    assert np.allclose(np.asarray(a['transform'])[:3,:3],np.asarray(c['transform'])[:3,:3])
    assert a['transform'][1:]==c['transform'][1:]
