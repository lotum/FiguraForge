"""Manufacturing decisions remain independent from texture/color clustering."""
from copy import deepcopy
import numpy as np
import pytest
import trimesh
from pydantic import ValidationError
from figuraforge.db import Conflict
from figuraforge.geometry.types import Surface
from figuraforge.geometry.refine import split_marked_edges
from figuraforge.models import ColorPlanDocument,Settings
from figuraforge.services.color_plan import validate_plan,construct_labels

MESH_HASH='a'*64
COLORS=['#113355','#AABBCC','#F07020']


@pytest.fixture
def stock():
    return [dict(id=ident,material='PLA',owned=True,allowed=True,hex=color)
            for ident,color in zip(('a','b','c'),COLORS)]


@pytest.fixture
def settings():
    return Settings(printer_id='h2d-dual',owned_filaments_only=True).model_dump()


def region(ident,strategy='part',group=0,filament=None,color=None):
    return dict(id=ident,name=f'Bereich {ident}',strategy=strategy,
                color=color or COLORS[ident%3],part_group=group,filament_id=filament)


def document(regions=None,faces=None,**overrides):
    regions=regions or [region(0,'body',filament='a')]
    faces=faces if faces is not None else [r['id'] for r in regions]
    return dict(version=1,mesh_hash=MESH_HASH,face_count=len(faces),
                face_regions=faces,regions=regions,nozzle_count=2,
                filament_ids=[],ratio_step_percent=5,**overrides)


def validate(plan,settings,stock):
    return validate_plan(plan,MESH_HASH,len(plan['face_regions']),settings,stock)


def test_current_mesh_plan_is_valid_and_input_is_not_mutated(settings,stock):
    plan=document();before=deepcopy(plan)
    saved=validate(plan,settings,stock)
    assert saved['mesh_hash']==MESH_HASH
    assert plan==before


def test_other_mesh_hash_is_rejected(settings,stock):
    plan=document();plan['mesh_hash']='b'*64
    with pytest.raises(Conflict,match='Meshversion'):
        validate(plan,settings,stock)


def test_changed_actual_face_count_is_rejected(settings,stock):
    with pytest.raises(Conflict,match='Meshversion'):
        validate_plan(document(),MESH_HASH,2,settings,stock)


def test_false_declared_face_count_is_rejected(settings,stock):
    plan=document();plan['face_count']=99
    with pytest.raises((Conflict,ValidationError)):
        validate(plan,settings,stock)


@pytest.mark.parametrize('face_id',[-1,17])
def test_face_cannot_reference_missing_region(face_id,settings,stock):
    plan=document();plan['face_regions']=[face_id]
    with pytest.raises((Conflict,ValidationError)):
        validate(plan,settings,stock)


def test_duplicate_region_ids_are_rejected(settings,stock):
    plan=document(regions=[region(0,'body',filament='a'),region(0,'part',filament='b')])
    with pytest.raises(Conflict,match='Bereichszuordnung'):
        validate(plan,settings,stock)


@pytest.mark.parametrize('nozzles',[3,4])
def test_h2d_dual_rejects_more_than_two_nozzles(nozzles,settings,stock):
    plan=document();plan['nozzle_count']=nozzles
    with pytest.raises(Conflict,match='hoechstens zwei'):
        validate(plan,settings,stock)


def test_h2d_single_requires_one_nozzle(settings,stock):
    settings['printer_id']='h2d-single'
    with pytest.raises(Conflict,match='Einzelduesen'):
        validate(document(),settings,stock)
    plan=document();plan['nozzle_count']=1
    assert validate(plan,settings,stock)['nozzle_count']==1


def test_two_colors_can_share_one_physical_part(settings,stock):
    plan=document([region(0,'body',filament='a'),region(1,group=7,filament='a'),
                   region(2,group=7,filament='b')])
    saved=validate(plan,settings,stock)
    assert saved['regions'][1]['part_group']==saved['regions'][2]['part_group']==7


def test_third_filament_in_same_part_is_rejected(settings,stock):
    plan=document([region(0,'body',filament='a'),region(1,group=7,filament='a'),
                   region(2,group=7,filament='b'),region(3,group=7,filament='c')])
    with pytest.raises(Conflict,match='mehr Basisfilamente'):
        validate(plan,settings,stock)


def test_three_filaments_across_separate_parts_are_allowed(settings,stock):
    plan=document([region(0,'body',filament='a'),region(1,group=7,filament='b'),
                   region(2,group=8,filament='c')])
    assert len(validate(plan,settings,stock)['regions'])==3


@pytest.mark.parametrize('basis',[[],['a']])
def test_mixed_region_requires_two_selected_basis_filaments(basis,settings,stock):
    plan=document([region(0,'body',filament='a'),region(1,'mixed')]);plan['filament_ids']=basis
    with pytest.raises(Conflict,match='zwei Basisfilamente'):
        validate(plan,settings,stock)


def test_mixed_region_and_base_share_two_basis_filaments(settings,stock):
    plan=document([region(0,'body',filament='a'),region(1,'mixed')]);plan['filament_ids']=['a','b']
    assert validate(plan,settings,stock)['filament_ids']==['a','b']


def test_single_nozzle_cannot_use_two_basis_filaments(settings,stock):
    settings['printer_id']='h2d-single'
    plan=document([region(0,'mixed')]);plan['nozzle_count']=1;plan['filament_ids']=['a','b']
    with pytest.raises(Conflict,match='vorhandene Duesen'):
        validate(plan,settings,stock)


def test_mixed_palette_cannot_have_three_basis_filaments():
    plan=document();plan['filament_ids']=['a','b','c']
    with pytest.raises(ValidationError):
        ColorPlanDocument.model_validate(plan)


def test_duplicate_basis_filament_is_rejected(settings,stock):
    plan=document([region(0,'mixed')]);plan['filament_ids']=['a','a']
    with pytest.raises(Conflict):
        validate(plan,settings,stock)


@pytest.mark.parametrize('change',[{'allowed':False},{'owned':False},{'material':'PETG'}])
def test_mixed_filaments_must_be_available_and_material_compatible(change,settings,stock):
    stock[1].update(change)
    plan=document([region(0,'mixed')]);plan['filament_ids']=['a','b']
    with pytest.raises(Conflict):
        validate(plan,settings,stock)


def test_nonstock_filament_allowed_only_when_stock_filter_disabled(settings,stock):
    stock[1]['owned']=False
    plan=document([region(0,'mixed')]);plan['filament_ids']=['a','b']
    settings['owned_filaments_only']=False
    assert validate(plan,settings,stock)['filament_ids']==['a','b']


def test_construct_labels_group_by_part_identity_instead_of_color():
    surface=type('SurfaceStub',(),{'mesh':type('MeshStub',(),{'faces':[0]*6})(),'face_tags':None})()
    # Same-colored ears are distinct parts; two colors of one chest are one part.
    regions=[region(0,'body'),region(1,group=10,color='#AA3300'),
             region(2,group=11,color='#AA3300'),region(3,group=12,color='#FFFFFF'),
             region(4,group=12,color='#111111'),region(5,'mixed')]
    labels,palette=construct_labels(surface,document(regions))
    assert labels[0]==labels[5]==0
    assert labels[1]!=labels[2]
    assert labels[3]==labels[4]!=0
    assert len(palette)==4


def test_default_part_groups_do_not_merge_unrelated_regions():
    surface=type('SurfaceStub',(),{'mesh':type('MeshStub',(),{'faces':[0,1]})(),'face_tags':None})()
    labels,_=construct_labels(surface,document([region(1,color='#123456'),region(2,color='#123456')]))
    assert labels[0]!=labels[1]


def test_refinement_preserves_face_ancestry_and_user_manufacturing_choices():
    mesh=trimesh.creation.box(extents=[20,20,20]);count=len(mesh.faces)
    surface=Surface(mesh,np.zeros((count,3,2)),np.ones((count,3,3)),np.zeros(count,dtype=int),
                    face_tags=np.arange(count))
    regions=[region(0,'body'),region(1,group=2),region(2,'mixed')]
    original_faces=np.arange(count)%3
    plan=document(regions,faces=original_faces.tolist())
    marked=np.zeros(count,bool);marked[[0,4]]=True
    refined=split_marked_edges(surface,marked)
    refined_twice=split_marked_edges(refined,np.arange(len(refined.mesh.faces))%5==0)
    assert len(refined_twice.mesh.faces)>len(refined.mesh.faces)>count
    assert refined_twice.face_tags.shape==(len(refined_twice.mesh.faces),)
    # Refinement reorders faces, so positional reuse of original labels is wrong.
    labels,_=construct_labels(refined_twice,plan)
    np.testing.assert_array_equal(labels,(original_faces[refined_twice.face_tags]==1).astype(int))
    np.testing.assert_allclose(
        np.bincount(refined_twice.face_tags,weights=refined_twice.mesh.area_faces,minlength=count),
        mesh.area_faces,rtol=1e-12,atol=1e-12)
    assert refined_twice.mesh.is_watertight
    assert refined_twice.mesh.volume==pytest.approx(mesh.volume)


def test_small_neutral_dark_details_survive_a_small_palette():
    import numpy as np
    import trimesh
    from figuraforge.geometry.types import Surface
    from figuraforge.models import Settings
    from figuraforge.services.color_plan import suggest_plan
    mesh=trimesh.creation.icosphere(subdivisions=1)
    rgb=np.tile([.65,.25,.06],(len(mesh.faces),3,1));rgb[0]=.015
    surface=Surface(mesh,np.zeros((len(mesh.faces),3,2)),rgb,np.zeros(len(mesh.faces),dtype=int))
    settings=Settings(palette=['#AF440A','#EFB27C']).model_dump()
    result=suggest_plan(surface,settings,'a'*64)
    region=next(r for r in result['regions'] if r['id']==result['face_regions'][0])
    assert region['color']=='#040404' and region['strategy']=='part'
    assert result['face_regions'][0]!=result['face_regions'][1]


def test_unassigned_base_uses_nearest_selected_spool_without_inventing_third_color(settings,stock):
    plan=document([region(0,'body',color=COLORS[1]),region(1,'mixed')]);plan['filament_ids']=['a','b']
    saved=validate(plan,settings,stock)
    assert saved['regions'][0]['filament_id']=='b'
    assert plan['regions'][0]['filament_id'] is None


def test_explicit_third_base_spool_is_not_silently_reassigned(settings,stock):
    plan=document([region(0,'body',filament='c'),region(1,'mixed')]);plan['filament_ids']=['a','b']
    with pytest.raises(Conflict,match='mehr Basisfilamente'):
        validate(plan,settings,stock)
