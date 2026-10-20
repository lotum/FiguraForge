from copy import deepcopy
import pytest
from figuraforge.db import Conflict
from figuraforge.services.jobs import validate_plan_plate_capacity


def project():
    return {'settings':{'colors_per_plate':1},'artifacts':{'plan':{'filament_ids':['brown','cream'],'regions':[
        {'id':0,'strategy':'body','color_mode':'mixed'},
        {'id':1,'strategy':'part','part_group':1,'color_mode':'solid','filament_id':'black'}]}}}


def test_mixed_part_rejected_before_geometry_when_plate_allows_only_one_real_spool():
    with pytest.raises(Conflict,match='mindestens 2'):
        validate_plan_plate_capacity(project())


def test_three_spools_across_separate_parts_are_not_counted_as_three_on_every_plate():
    p=project();p['settings']['colors_per_plate']=2
    validate_plan_plate_capacity(p)


def test_two_solid_colors_in_same_part_need_two_plate_spools():
    p=project();p['artifacts']['plan']['regions']=[
        {'id':0,'strategy':'part','part_group':4,'color_mode':'solid','filament_id':'brown'},
        {'id':1,'strategy':'part','part_group':4,'color_mode':'solid','filament_id':'cream'}]
    with pytest.raises(Conflict,match='mindestens 2'):validate_plan_plate_capacity(p)
    p['artifacts']['plan']['regions'][1]['part_group']=5
    validate_plan_plate_capacity(p)


@pytest.mark.parametrize('representation',['document','artifact'])
def test_unused_mixed_region_never_blocks_single_spool_plan(representation):
    p=project();plan=p['artifacts']['plan'];plan['regions']=[
        {'id':0,'strategy':'body','filament_id':'brown','color_mode':'solid','face_count':12},
        {'id':1,'strategy':'part','part_group':1,'color_mode':'mixed','face_count':0}]
    if representation=='document':
        plan['face_regions']=[0]*12
        # Actual face IDs take precedence even over stale region metadata.
        plan['regions'][1]['face_count']=5
    validate_plan_plate_capacity(p)


def test_document_face_ids_take_precedence_over_stale_zero_count():
    p=project();p['artifacts']['plan']['face_regions']=[0];p['artifacts']['plan']['regions'][0]['face_count']=0
    with pytest.raises(Conflict,match='mindestens 2'):validate_plan_plate_capacity(p)


def test_missing_face_count_remains_conservative_for_legacy_artifact():
    with pytest.raises(Conflict,match='mindestens 2'):validate_plan_plate_capacity(project())


def test_implicit_zero_part_group_means_individual_region_not_shared_group():
    p=project();p['artifacts']['plan']['regions']=[
        {'id':0,'strategy':'part','part_group':0,'color_mode':'solid','filament_id':'brown'},
        {'id':1,'strategy':'part','part_group':0,'color_mode':'solid','filament_id':'cream'}]
    validate_plan_plate_capacity(p)
