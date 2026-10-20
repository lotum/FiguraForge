import base64
from copy import deepcopy
import numpy as np
import pytest
import trimesh
from figuraforge.geometry.types import Surface,GeometryError
from figuraforge.services.mixed_preview import build_mixed_preview,MixedPreviewError


def fixture():
    mesh=trimesh.creation.box();n=len(mesh.faces)
    linear=np.linspace(0,1,n)
    rgb=np.repeat((np.where(linear<=.0031308,12.92*linear,1.055*linear**(1/2.4)-.055))[:,None],3,axis=1)
    surface=Surface(mesh,np.zeros((n,3,2)),np.repeat(rgb[:,None,:],3,axis=1),np.zeros(n,int))
    plan={'mesh_hash':'a'*64,'face_count':n,'face_regions':[0]*n,'ratio_step_percent':5,
          'regions':[{'id':0,'strategy':'mixed','color':'#888888'}], 'filament_ids':['black','white']}
    filaments=[{'id':'black','hex':'#000000','material':'PLA','allowed':True},
               {'id':'white','hex':'#FFFFFF','material':'PLA','allowed':True}]
    return surface,plan,filaments


def test_twenty_explicit_native_safe_values_keep_pure_endpoints_and_exact_nominal_thickness():
    from figuraforge.services.mochi_unified import PERCENTAGES
    surface,plan,filaments=fixture()
    result=build_mixed_preview(surface,plan,filaments,recipe_percentages=PERCENTAGES,include_geometry=False)
    assert result['recipe_count']==20
    assert [r['first_percent'] for r in result['recipe_palette']]==list(PERCENTAGES)
    assert sum(r['kind']=='mixed' for r in result['recipe_palette'])==18
    assert next(r for r in result['recipe_palette'] if r['first_percent']==19)['sublayer_thickness_mm']==[.038,.162]
    assert result['explicit_recipe_percentages']==list(PERCENTAGES)


@pytest.mark.parametrize('values', [[0,5,100],[0,95,100],[0,10,10,100],[0,100,10],[10,50,90],[0,True,100],[0,'10',100],[0,10.5,100]])
def test_explicit_recipe_values_reject_non_native_or_ambiguous_lists(values):
    surface,plan,filaments=fixture()
    with pytest.raises(MixedPreviewError):
        build_mixed_preview(surface,plan,filaments,recipe_percentages=values)


def native():
    ratios=[85,75,65,55,45,35,25,15]
    return {'enable_mixed_color_sublayer':'1','filament_colour':['#000000','#FFFFFF']+['#888888']*8,
            'filament_is_mixed':['0','0']+['1']*8,
            'filament_mixed_components':['','']+['1,2']*8,
            'filament_mixed_sublayer_ratios':['','']+[f'{p/100},{1-p/100:.2f}' for p in ratios],
            'filament_mixed_gradient':['0']*10,'filament_mixed_gradient_range':['']*10,
            'filament_mixed_gradient_curve':['']*10,'filament_mixed_gradient_per_part':['0']*10}


def test_single_pair_yields_many_local_face_recipes_and_nineteen_palette_colors():
    surface,plan,filaments=fixture();result=build_mixed_preview(surface,plan,filaments)
    assert result['physical_filament_count']==2
    assert result['recipe_count']==19
    assert result['per_region'][0]['used_recipe_count']>5
    assert result['face_recipe_indices'][0]!=result['face_recipe_indices'][-1]
    assert result['recipe_palette'][result['face_recipe_indices'][0]]['color']=='#000000'
    assert result['recipe_palette'][result['face_recipe_indices'][-1]]['color']=='#FFFFFF'
    half=next(r for r in result['recipe_palette'] if r['first_percent']==50)
    assert half['color']=='#BCBCBC' # Linear-light optical estimate, not RGB #808080.
    assert half['sublayer_thickness_mm']==[.1,.1]
    ten=next(r for r in result['recipe_palette'] if r['first_percent']==10)
    assert ten['sublayer_thickness_mm']==[.02,.18]
    encoded=result['preview']['meshes'][0]['colors']
    preview=np.frombuffer(base64.b64decode(encoded),dtype='<f4').reshape(-1,3,3)
    assert len(np.unique(preview[:,0,:],axis=0))>5
    assert result['export_coverage']['status']=='not_checked'
    assert not result['export_coverage']['all_used_recipes_available']


def test_original_geometry_and_input_plan_unchanged_and_part_region_color_retained():
    surface,plan,filaments=fixture();plan['regions'].append({'id':1,'strategy':'part','color':'#FF0000'})
    plan['face_regions'][0]=1;original=deepcopy(plan);vertices=surface.mesh.vertices.copy()
    result=build_mixed_preview(surface,plan,filaments)
    assert result['face_recipe_indices'][0]==-1
    colors=np.frombuffer(base64.b64decode(result['preview']['meshes'][0]['colors']),dtype='<f4').reshape(-1,3,3)
    np.testing.assert_allclose(colors[0],np.repeat([[1,0,0]],3,axis=0))
    assert original==plan;np.testing.assert_array_equal(vertices,surface.mesh.vertices)


def test_exact_native_coverage_reports_eight_presets_vs_seventeen_theoretical():
    surface,plan,filaments=fixture();result=build_mixed_preview(surface,plan,filaments,native_settings=native())
    coverage=result['export_coverage']
    assert coverage['available_native_mixed_slots']==8
    assert coverage['matching_mixed_recipe_count']==8
    assert len([r for r in result['recipe_palette'] if r['kind']=='mixed'])==17
    assert coverage['used_missing_recipes']
    assert not coverage['all_used_recipes_available']


def test_template_pair_color_mismatch_is_never_hidden():
    surface,plan,filaments=fixture();settings=native();settings['filament_colour'][0]='#FF0000'
    result=build_mixed_preview(surface,plan,filaments,native_settings=settings)
    assert result['export_coverage']['matching_mixed_recipe_count']==0


@pytest.mark.parametrize('change', ['missing_pair','unknown','bad_hex','material','disallowed'])
def test_invalid_basis_pair_raises_geometry_error(change):
    surface,plan,filaments=fixture()
    if change=='missing_pair':plan['filament_ids']=[]
    elif change=='unknown':plan['filament_ids'][0]='missing'
    elif change=='bad_hex':filaments[0]['hex']='unknown'
    elif change=='material':filaments[0]['material']='PETG'
    elif change=='disallowed':filaments[0]['allowed']=False
    with pytest.raises(GeometryError):build_mixed_preview(surface,plan,filaments)


@pytest.mark.parametrize('height',[0,-1,float('nan'),float('inf')])
def test_invalid_layer_height(height):
    with pytest.raises(MixedPreviewError):build_mixed_preview(*fixture(),layer_height_mm=height)


def test_current_color_change_relative_to_immutable_reference_changes_recipes():
    surface,plan,filaments=fixture();reference=deepcopy(plan)
    original=build_mixed_preview(surface,plan,filaments,reference_plan=reference)
    plan['regions'][0]['color']='#CCCCCC'
    changed=build_mixed_preview(surface,plan,filaments,reference_plan=reference)
    first_before=[original['recipe_palette'][i]['first_percent'] for i in original['face_recipe_indices']]
    first_after=[changed['recipe_palette'][i]['first_percent'] for i in changed['face_recipe_indices']]
    assert np.mean(first_after)<np.mean(first_before) # More white after brightening.
    assert changed['region_color_adjustments_applied']
    assert reference['regions'][0]['color']=='#888888'
    assert len(set(changed['face_recipe_indices']))>2 # No region-average collapse.


def test_same_inventory_colors_cannot_invent_a_gradient():
    surface,plan,filaments=fixture();filaments[1]['hex']='#000000'
    with pytest.raises(MixedPreviewError,match='dieselbe'):build_mixed_preview(surface,plan,filaments)


@pytest.mark.parametrize(('step','count'),[(5,19),(10,11),(20,7)])
def test_supported_recipe_spacings(step,count):
    surface,plan,filaments=fixture();plan['ratio_step_percent']=step
    result=build_mixed_preview(surface,plan,filaments)
    assert result['recipe_count']==count
    assert all(r['first_percent'] in (0,100) or 10<=r['first_percent']<=90 for r in result['recipe_palette'])
