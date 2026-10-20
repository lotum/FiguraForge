"""Construction decision and print-color technique are independent dimensions."""
from copy import deepcopy
import numpy as np
import pytest
import trimesh
from figuraforge.models import ColorRegion,AdviceRegionEdit,Settings
from figuraforge.geometry.types import Surface
from figuraforge.services.color_plan import is_mixed,validate_plan,construct_labels
from figuraforge.services.mixed_preview import build_mixed_preview
from figuraforge.providers.planning import apply_region_suggestion


def test_defaults_and_legacy_documents_migrate_without_mutation():
    raw={'id':1,'name':'Ear','strategy':'mixed','color':'#888888'};before=deepcopy(raw)
    row=ColorRegion.model_validate(raw).model_dump()
    assert row['strategy']=='body' and row['color_mode']=='mixed'
    assert raw==before and is_mixed(raw) and is_mixed(row)
    assert ColorRegion(id=2,name='Nose',strategy='part',color='#000000').color_mode=='solid'


def test_part_with_gradient_is_still_a_separate_geometric_label():
    mesh=trimesh.creation.box();n=len(mesh.faces)
    colors=np.linspace(0,1,n)[:,None]*np.ones((1,3))
    surface=Surface(mesh,np.zeros((n,3,2)),np.repeat(colors[:,None,:],3,axis=1),np.zeros(n,int))
    plan={'version':1,'mesh_hash':'a'*64,'face_count':n,'face_regions':[0]*(n//2)+[1]*(n-n//2),
          'regions':[{'id':0,'name':'Body','strategy':'body','color_mode':'solid','color':'#FFFFFF','filament_id':'white'},
                     {'id':1,'name':'Ear','strategy':'part','color_mode':'mixed','color':'#888888','part_group':4,'cut_type':'whole'}],
          'nozzle_count':2,'filament_ids':['black','white'],'ratio_step_percent':5}
    stock=[{'id':'black','hex':'#000000','material':'PLA','allowed':True,'owned':True},
           {'id':'white','hex':'#FFFFFF','material':'PLA','allowed':True,'owned':True}]
    plan=validate_plan(plan,'a'*64,n,Settings().model_dump(),stock)
    labels,palette=construct_labels(surface,plan)
    assert set(labels[:n//2])=={0}
    assert set(labels[n//2:])=={1}
    assert len(palette)==2
    preview=build_mixed_preview(surface,plan,stock)
    assert preview['per_region'][1]['strategy']=='part'
    assert preview['per_region'][1]['color_mode']=='mixed'
    assert preview['per_region'][1]['used_recipe_count']>1
    assert preview['face_recipe_indices'][0]==-1


def test_ai_apply_preserves_part_geometry_and_adds_color_mode():
    original={'face_regions':[0,1],'regions':[{'id':1,'strategy':'part','color_mode':'solid','filament_id':'white','part_group':4,'cut_type':'whole'}]}
    before=deepcopy(original)
    changed=apply_region_suggestion(original,[{'id':1,'strategy':'part','color_mode':'mixed',
        'filament_id':None,'part_group':4,'cut_type':'whole','reason':'Separate ear with gradient'}],['white','black'])
    assert changed['regions'][0]['strategy']=='part'
    assert changed['regions'][0]['color_mode']=='mixed'
    assert changed['face_regions']==original['face_regions']
    assert original==before
    assert AdviceRegionEdit(id=1,strategy='part',color_mode='mixed',filament_id=None,part_group=4,cut_type='whole').color_mode=='mixed'
