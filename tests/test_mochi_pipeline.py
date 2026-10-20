from copy import deepcopy
import numpy as np
import pytest
import trimesh
from figuraforge.geometry.types import GeometryError,Surface
from figuraforge.services.mochi_pipeline import suggest_mochi_plan,construct_mochi,MESH_HASH


def unrelated_surface():
    mesh=trimesh.creation.box();n=len(mesh.faces)
    return Surface(mesh,np.zeros((n,3,2)),np.ones((n,3,3)),np.zeros(n,int))


def test_unrelated_geometry_is_never_guessed_from_character_title_or_reference_hash():
    surface=unrelated_surface();reference={'mesh_hash':MESH_HASH,'face_regions':[0]*len(surface.mesh.faces),'regions':[]}
    original=deepcopy(reference)
    with pytest.raises(GeometryError,match='150k-Arbeitskopie'):
        suggest_mochi_plan(surface,reference,{'height_mm':180,'up_axis':'Y'},MESH_HASH,[])
    assert reference==original


@pytest.mark.parametrize('settings',[{'height_mm':1000,'up_axis':'Y'},{'height_mm':180,'up_axis':'Z'}])
def test_changed_scale_and_axis_require_separate_analysis(settings):
    with pytest.raises(GeometryError,match='180 mm'):
        suggest_mochi_plan(unrelated_surface(),{'mesh_hash':MESH_HASH},settings,MESH_HASH,[])


def test_changed_mesh_hash_is_explicitly_rejected():
    with pytest.raises(GeometryError,match='Meshversion'):
        suggest_mochi_plan(unrelated_surface(),{'mesh_hash':'b'*64},{'height_mm':180,'up_axis':'Y'},'b'*64,[])


def test_physical_batches_do_not_split_virtual_recipe_colors_into_extra_spools():
    from figuraforge.geometry.types import Part
    from figuraforge.services.mochi_pipeline import pack_mochi_parts,PART_KEYS
    parts=[]
    for index,key in enumerate(PART_KEYS):
        mesh=trimesh.creation.box(extents=[4,5,2]);mesh.apply_translation([10*index,0,1])
        parts.append(Part(key,key,mesh,'#272729' if key=='nose' or key.startswith('eye-') else ['#AA4411','#BB5533','#CC6644','#DD7755'][index%4],assembly_direction=[0,0,1]))
    plates=pack_mochi_parts(parts)
    assert len(plates)==2
    assert {i['part_id'] for i in plates[0]['placements']}=={'body','right-ear','left-ear','tail'}
    assert {i['part_id'] for i in plates[1]['placements']}=={'nose','eye-1','eye-2','eye-3','eye-4'}
    assert [p['physical_spool_count'] for p in plates]==[2,1]
    assert all(i['height_mm']==pytest.approx(2) for i in plates[1]['placements'])


def test_part_preview_keeps_local_recipes_and_marks_new_internal_faces_gray():
    import base64
    from figuraforge.geometry.types import Part
    from figuraforge.services.mochi_pipeline import build_mochi_parts_preview
    source=unrelated_surface();n=len(source.mesh.faces)
    source.corner_rgb=np.repeat(np.repeat(np.linspace(0,1,n)[:,None],3,axis=1)[:,None,:],3,axis=1)
    inner=trimesh.creation.box(extents=[.2,.2,.2]);mesh=trimesh.util.concatenate([source.mesh,inner])
    part=Part('body','Body',mesh,'#FFFFFF')
    plan={'face_count':n,'face_regions':[0]*n,'regions':[{'id':0,'strategy':'body','color_mode':'mixed','color':'#888888'}],
          'filament_ids':['black','white'],'ratio_step_percent':5}
    stock=[{'id':'black','hex':'#000000','material':'PLA','allowed':True}, {'id':'white','hex':'#FFFFFF','material':'PLA','allowed':True}]
    vertices=mesh.vertices.copy()
    preview,warnings=build_mochi_parts_preview([part],source,plan,stock,plan)
    record=preview['meshes'][0]
    assert record['exterior_face_count']==n and record['hidden_face_count']==len(inner.faces)
    colors=np.frombuffer(base64.b64decode(record['colors']),dtype='<f4').reshape(-1,3,3)
    assert len(np.unique(colors[:n,0,:],axis=0))>5
    np.testing.assert_allclose(colors[n:,0,:],np.repeat([[.53,.57,.62]],len(inner.faces),axis=0),atol=1e-6)
    np.testing.assert_array_equal(vertices,mesh.vertices)
    assert warnings and preview['geometry_modified'] is False


def test_near_surface_socket_wall_is_hidden_even_within_legacy_point03_tolerance():
    import base64
    from figuraforge.geometry.types import Part
    from figuraforge.services.mochi_pipeline import build_mochi_parts_preview
    source=unrelated_surface();n=len(source.mesh.faces)
    # A new inner wall 0.01 mm behind an original outer face must not inherit
    # its black surface color and become a third physical spool on the body.
    wall=trimesh.Trimesh(vertices=[[-.2,-.2,.49],[.2,-.2,.49],[0,.2,.49]],faces=[[0,1,2]],process=False)
    part=Part('body','Body',wall,'#FFFFFF')
    plan={'face_count':n,'face_regions':[0]*n,'regions':[{'id':0,'strategy':'body','color_mode':'solid','color':'#000000','filament_id':'black'}],
          'filament_ids':['black','white'],'ratio_step_percent':5}
    stock=[{'id':'black','hex':'#000000','material':'PLA','allowed':True},{'id':'white','hex':'#FFFFFF','material':'PLA','allowed':True}]
    preview,_=build_mochi_parts_preview([part],source,plan,stock,plan)
    record=preview['meshes'][0]
    assert record['exterior_face_count']==0 and record['hidden_face_count']==1
    colors=np.frombuffer(base64.b64decode(record['colors']),dtype='<f4').reshape(-1,3)
    np.testing.assert_allclose(colors,np.repeat([[.53,.57,.62]],3,axis=0),atol=1e-6)


def test_normal_geometry_worker_dispatches_anatomy_before_color_refinement(tmp_path,monkeypatch):
    from figuraforge.services.geometry_task import execute
    import figuraforge.geometry.io as io
    import figuraforge.geometry.refine as refine
    import figuraforge.services.mochi_pipeline as pipeline
    from figuraforge.models import Settings
    surface=unrelated_surface();reference={'source':'immutable reference'}
    monkeypatch.setattr(io,'load_surface',lambda *_:surface)
    def forbidden(*args,**kwargs):
        pytest.fail('Anatomical source must not be refined or relabeled first')
    monkeypatch.setattr(refine,'refine_with_plan',forbidden)
    class Dispatched(Exception):pass
    def constructor(actual,plan,settings,*,reference_plan):
        assert actual is surface and reference_plan is reference
        raise Dispatched
    monkeypatch.setattr(pipeline,'construct_mochi',constructor)
    with pytest.raises(Dispatched):
        execute({'operation':'segment','source':'unused.glb','out':str(tmp_path),
            'settings':Settings().model_dump(),'color_plan':{'construction_preset':'mochi-anatomical-v1'},
            'construction_reference_plan':reference},lambda _:None)


def test_native_plate_process_preserves_profiles_and_marks_gui_overrides():
    from figuraforge.services.mochi_pipeline import configure_mochi_plate
    source={'layer_height':'0.12','raft_layers':'0','brim_type':'auto_brim','nozzle_temperature':['220','220'],
            'filament_colour':['#805947','#F7E6DE','#272729'],'filament_is_mixed':['0','0','0'],
            'different_settings_to_system':['layer_height','filament_colour','','',''],
            'nozzle_diameter':['0.4','0.4']}
    saved=deepcopy(source)
    black=configure_mochi_plate(source,{'placements':[{'part_id':'nose'},{'part_id':'eye-1'}]})
    body=configure_mochi_plate(source,{'placements':[{'part_id':'body'},{'part_id':'tail'}]})
    assert source==saved
    assert black['raft_layers']=='3' and black['brim_type']=='outer_only'
    assert body['raft_layers']=='0' and body['brim_type']=='auto_brim'
    assert 'raft_layers' in black['different_settings_to_system'][0].split(';')
    assert 'brim_type' in black['different_settings_to_system'][0].split(';')
    assert black['different_settings_to_system'][1:]==source['different_settings_to_system'][1:]
    assert black['nozzle_temperature']==source['nozzle_temperature']
    assert black['filament_colour']==source['filament_colour']
    assert black['support_filament']==black['support_interface_filament']=='0'
    with pytest.raises(GeometryError,match='getrennt'):
        configure_mochi_plate(source,{'placements':[{'part_id':'body'},{'part_id':'nose'}]})
