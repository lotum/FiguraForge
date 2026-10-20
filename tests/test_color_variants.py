from copy import deepcopy
from figuraforge.services.color_variants import generate_variants


def plan():
    colors=['#B55317','#8F4010','#080808','#F6E5CF']
    return {'version':1,'mesh_hash':'a'*64,'face_count':4,'face_regions':[0,1,2,3],
        'regions':[{'id':i,'name':str(i),'strategy':'body' if i==0 else 'part','color':c,
        'area_mm2':100-i*25,'face_count':1,'reason':'Lokaler Vorschlag','filament_id':'spool'+str(i)} for i,c in enumerate(colors)],
        'nozzle_count':2,'filament_ids':[],'ratio_step_percent':5,'note':''}


def test_nine_variants_are_new_editable_documents_with_stable_face_ids():
    source=plan();before=deepcopy(source);variants=generate_variants(source)
    assert source==before and len(variants)==9
    assert len({(v['row'],v['column']) for v in variants})==9
    for v in variants:
        assert v['document']['face_regions']==source['face_regions']
        assert v['document']['mesh_hash']==source['mesh_hash']
        assert v['document']['regions'][2]['color']=='#080808'
        assert v['document']['regions'][2]['strategy']=='part'
        assert v['document']['regions'][3]['strategy']=='part'
    variants[0]['document']['regions'][0]['name']='Changed'
    assert variants[1]['document']['regions'][0]['name']=='0'


def test_shadow_hypothesis_merges_brown_without_merging_black_or_cream():
    variant=generate_variants(plan())[4]
    assert variant['merged_regions']==[1]
    assert variant['document']['regions'][1]['strategy']=='body'
    assert variant['document']['regions'][1]['color']=='#B55317'
    assert not variant['requires_filament_mapping']


def test_mixed_and_manually_painted_selections_are_not_merged():
    source=plan();source['regions'][1]['strategy']='mixed';source['regions'][1]['reason']='Manuell festgelegter Verlauf'
    assert 1 not in generate_variants(source)[3]['merged_regions']
    source['regions'][1]['strategy']='part';source['regions'][1]['reason']='Manuell auf der Oberfläche markiert'
    assert 1 not in generate_variants(source)[3]['merged_regions']


def test_brightness_variants_clear_stale_spool_mapping():
    variants=generate_variants(plan())
    assert variants[0]['document']['regions'][0]['filament_id'] is None
    assert variants[4]['document']['regions'][0]['filament_id']=='spool0'


def test_columns_still_differ_when_shade_merging_is_not_possible():
    source=plan();source['regions']=source['regions'][:1];source['face_regions']=[0]*4
    variants=generate_variants(source)
    assert len({v['document']['regions'][0]['color'] for v in variants})==9
