from copy import deepcopy
import numpy as np
import pytest
import trimesh
from PIL import Image
from figuraforge.geometry.types import Surface,Part
from figuraforge.services.plan_materials import prepare_native_materials
from figuraforge.services.mixed_filament import MixedFilamentError,validate_native_settings


@pytest.fixture
def inputs():
    mesh=trimesh.creation.box(extents=[4,4,4]);n=len(mesh.faces)
    uv=np.tile([[0,0],[.5,0],[1,0]],(n,1,1))
    texture=Image.fromarray(np.array([[[0,0,0],[255,255,255]]],dtype=np.uint8))
    surface=Surface(mesh,uv,np.ones((n,3,3)),np.zeros(n,dtype=int),[texture],[np.ones(4)])
    config={'enable_mixed_color_sublayer':'1','filament_colour':['#000000','#FFFFFF','#808080','#FF0000'],
            'filament_is_mixed':['0','0','1','0'],
            'filament_mixed_components':['','','1,2',''],
            'filament_mixed_sublayer_ratios':['','','0.50,0.50',''],
            'filament_mixed_gradient':['0']*4,'filament_mixed_gradient_range':['']*4,
            'filament_mixed_gradient_curve':['']*4,'filament_mixed_gradient_per_part':['0']*4,
            'filament_type':['PLA']*4,'filament_vendor':['Bambu Lab']*4}
    template={'nozzle_count':2,'config':config,'basis_filaments':[
        {'slot':1,'color':'#000000','material':'PLA','vendor':'Bambu Lab'},
        {'slot':2,'color':'#FFFFFF','material':'PLA','vendor':'Bambu Lab'},
        {'slot':4,'color':'#FF0000','material':'PLA','vendor':'Bambu Lab'}],
        'mixed_slots':validate_native_settings(config)['mixed_slots']}
    stock=[{'id':'black','hex':'#000000','material':'PLA','allowed':True},
           {'id':'white','hex':'#FFFFFF','material':'PLA','allowed':True},
           {'id':'red','hex':'#FF0000','material':'PLA','allowed':True}]
    plan={'nozzle_count':2,'filament_ids':['black','white'],'face_regions':[0]*(n//2)+[1]*(n-n//2),
          'regions':[{'id':0,'name':'Core','strategy':'body','color':'#FFFFFF','filament_id':'white','part_group':0},
                     {'id':1,'name':'Gradient','strategy':'mixed','color':'#808080','filament_id':None,'part_group':0}]}
    part=Part('body','Core',mesh.copy(),'#FFFFFF',0,'body')
    return [part],surface,plan,template,stock


def test_textured_mixed_faces_use_only_existing_pair_recipe_and_fixed_profiles(inputs):
    parts,surface,plan,template,stock=inputs;before=deepcopy(template)
    slots,report,settings=prepare_native_materials(parts,surface,plan,template,stock,return_settings=True)
    assert slots['body']==[2]*6+[3]*6
    assert report['mixed_candidate_slots']==[1,2,3]
    assert report['filament_limits']['physical_slots_per_part']['body']==[1,2]
    assert not report['color_calibrated'] and not report['new_profiles_created'] and not report['new_recipes_created']
    from figuraforge.services.mixed_preview import build_mixed_preview
    preview=build_mixed_preview(surface,plan,stock,include_geometry=False)
    assert report['mixed_delta_e_2000']==preview['matching_error_delta_e']
    index=preview['face_recipe_indices'][-1]
    percent=preview['recipe_palette'][index]['first_percent']
    assert settings['filament_mixed_sublayer_ratios'][2]==f'{percent/100:.2f},{(100-percent)/100:.2f}'
    assert report['preview_recipe_parity'] is True
    assert template==before


def test_hidden_faces_inherit_area_dominant_exterior_slot(inputs):
    parts,surface,plan,template,stock=inputs
    inside=trimesh.Trimesh(vertices=[[0,0,0],[.1,0,0],[0,.1,0]],faces=[[0,1,2]],process=False)
    parts[0].mesh=trimesh.util.concatenate([parts[0].mesh,inside])
    slots,report=prepare_native_materials(parts,surface,plan,template,stock)
    assert slots['body'][-1]==2
    assert report['parts']['body']['hidden_faces']==1
    assert set(slots['body'])=={2,3}


def test_missing_fixed_filament_blocks_export(inputs):
    parts,surface,plan,template,stock=inputs;plan['regions'][0]['filament_id']=None
    with pytest.raises(MixedFilamentError,match='konkrete Filamentzuordnung'):
        prepare_native_materials(parts,surface,plan,template,stock)


@pytest.mark.parametrize('field,value',[('hex','#EFEFEF'),('material','PETG')])
def test_missing_matching_native_profile_blocks_export(inputs,field,value):
    parts,surface,plan,template,stock=inputs;stock[1][field]=value
    with pytest.raises(MixedFilamentError,match='Kein natives physisches Profil'):
        prepare_native_materials(parts,surface,plan,template,stock)


def test_recipe_for_different_pair_is_not_reused(inputs):
    parts,surface,plan,template,stock=inputs;template['config']['filament_mixed_components'][2]='1,4'
    with pytest.raises(MixedFilamentError,match='keine vorhandene Mischung'):
        prepare_native_materials(parts,surface,plan,template,stock)


def test_third_physical_filament_on_same_part_blocks_export(inputs):
    parts,surface,plan,template,stock=inputs;plan['regions'][0].update(color='#FF0000',filament_id='red')
    with pytest.raises(MixedFilamentError,match='3 physical filaments'):
        prepare_native_materials(parts,surface,plan,template,stock)


def test_multiple_parts_can_use_more_than_two_global_filaments(inputs):
    parts,surface,plan,template,stock=inputs
    red=surface.mesh.copy();red.apply_translation([20,0,0])
    parts.append(Part('red','Red piece',red,'#FF0000',1,'inlay'))
    plan['regions'].append({'id':2,'name':'Red piece','strategy':'part','color':'#FF0000','filament_id':'red','part_group':1})
    # The third spool is explicit even when this test's disconnected part has no source-exterior match.
    plan['face_regions'][0]=2
    parts[0].mesh=parts[0].mesh.submesh([np.arange(1,len(parts[0].mesh.faces))],append=True,repair=False)
    slots,report=prepare_native_materials(parts,surface,plan,template,stock)
    assert set(slots['red'])=={4}
    assert report['filament_limits']['physical_slots_per_part']=={'body':[1,2],'red':[4]}


def test_refined_source_ancestry_uses_original_plan_face_ids(inputs):
    parts,surface,plan,template,stock=inputs
    surface.face_tags=np.arange(len(surface.mesh.faces))[::-1]
    slots,_=prepare_native_materials(parts,surface,plan,template,stock)
    assert slots['body']==[3]*6+[2]*6


def test_single_nozzle_contract_is_explicitly_blocked(inputs):
    parts,surface,plan,template,stock=inputs;plan['nozzle_count']=1
    with pytest.raises(MixedFilamentError,match='two-nozzle'):
        prepare_native_materials(parts,surface,plan,template,stock)


def test_color_correction_and_export_use_identical_reference_bound_recipe(inputs):
    from figuraforge.services.mixed_preview import build_mixed_preview
    parts,surface,plan,template,stock=inputs;reference=deepcopy(plan)
    plan['regions'][1]['color']='#FFFFFF'
    slots,report,settings=prepare_native_materials(parts,surface,plan,template,stock,reference_plan=reference,return_settings=True)
    preview=build_mixed_preview(surface,plan,stock,reference_plan=reference,include_geometry=False)
    actual={row['slot']:row for row in validate_native_settings(settings)['mixed_slots']}
    for face in range(6,12):
        percent=preview['recipe_palette'][preview['face_recipe_indices'][face]]['first_percent']
        slot=slots['body'][face]
        if slot==1:assert percent==100
        elif slot==2:assert percent==0
        else:assert float(actual[slot]['ratios'][0])*100==pytest.approx(percent)
    assert report['recipe_allocation']['preview_palette_coarsened'] is False


def test_insufficient_native_palette_blocks_instead_of_coarsening_preview(inputs):
    parts,surface,plan,template,stock=inputs
    surface.textures=[];surface.factors=[]
    values=np.linspace(.1,.9,len(surface.mesh.faces))
    surface.corner_rgb=np.repeat(np.repeat(values[:,None,None],3,axis=1),3,axis=2)
    plan['face_regions']=[1]*len(surface.mesh.faces)
    with pytest.raises(MixedFilamentError,match='Vorschau benoetigt'):
        prepare_native_materials(parts,surface,plan,template,stock)


def test_separate_part_can_keep_native_mixed_recipes(inputs):
    parts,surface,plan,template,stock=inputs
    region=plan['regions'][1]
    region.update(strategy='part',color_mode='mixed',part_group=7,cut_type='whole')
    slots,report=prepare_native_materials(parts,surface,plan,template,stock)
    assert slots['body']==[2]*6+[3]*6
    assert report['preview_recipe_parity'] is True
    assert report['filament_limits']['physical_slots_per_part']['body']==[1,2]

def test_genuine_physical_only_template_maps_solid_plan_but_rejects_mixed_plan(inputs):
    parts,surface,plan,template,stock=inputs
    config=template['config'];config['enable_mixed_color_sublayer']='0';config['filament_is_mixed']=['0']*4;config['filament_mixed_components']=['']*4;config['filament_mixed_sublayer_ratios']=['']*4
    template['basis_filaments'].append({'slot':3,'color':'#808080','material':'PLA','vendor':'Bambu Lab'});template['mixed_slots']=[]
    with pytest.raises(MixedFilamentError,match='keine vorhandene Mischung'):
        prepare_native_materials(parts,surface,plan,template,stock)
    plan['regions'][1].update(strategy='body',color_mode='solid',filament_id='black',color='#000000')
    slots,report=prepare_native_materials(parts,surface,plan,template,stock)
    assert set(slots['body'])=={1,2} and not report['preview_recipe_parity']
    assert config['filament_is_mixed']==['0']*4 and template['mixed_slots']==[]
