from copy import deepcopy
from pathlib import Path
import json,shutil,hashlib
import pytest
from fastapi.testclient import TestClient
from figuraforge.app import create_app
from figuraforge.config import Config,ROOT
from figuraforge.db import digest
from figuraforge.models import Settings,ColorPlanDocument
from figuraforge.services.mochi_pipeline import MESH_HASH as OLD_HASH,SOURCE_SHA256 as OLD_SHA
from figuraforge.services.mochi_detail_pipeline import MESH_HASH as NEW_HASH,SOURCE_SHA256 as NEW_SHA,PRESET
from figuraforge.services.plan_presets import available_presets


def test_options_and_schema_bind_each_version_to_its_own_source():
    from figuraforge.services.mochi_pipeline import PRESET as OLD_PRESET
    base={'settings':Settings(height_mm=180,up_axis='Y',printer_id='h2d-dual').model_dump(),'artifacts':{}}
    for sha,mesh,preset in [(OLD_SHA,OLD_HASH,OLD_PRESET),(NEW_SHA,NEW_HASH,PRESET)]:
        project=deepcopy(base);project['artifacts']['mesh']={'hash':mesh,'source':{'sha256':sha}}
        assert [row['id'] for row in available_presets(project)]==[preset]
        project['artifacts']['mesh']['source']['sha256']='f'*64
        assert available_presets(project)==[]


def test_detail_packing_isolates_all_large_objects_for_real_tree_support_conflict():
    import trimesh
    from figuraforge.geometry.types import Part
    from figuraforge.services.mochi_pipeline import PART_KEYS
    from figuraforge.services.mochi_detail_pipeline import pack_mochi_detail_parts
    parts=[Part(key,key,trimesh.creation.box(extents=[4,5,2]),'#272729' if key=='nose' or key.startswith('eye-') else '#805947',assembly_direction=[0,0,1]) for key in PART_KEYS]
    plates=pack_mochi_detail_parts(parts,margin=6,gap=8)
    assert len(plates)==5
    assert [len(row['placements']) for row in plates]==[1,1,1,1,5]
    assert [{row['part_id'] for row in p['placements']} for p in plates[:4]]==[{'body'},{'right-ear'},{'left-ear'},{'tail'}]
    assert all(row['rect'][0]>=25 and row['rect'][1]>=25 for p in plates for row in p['placements'])


@pytest.fixture()
def versioned_client(tmp_path):
    original=ROOT/'data/projects/1b0e2fdd463d4f15ac64f1c7b3e8acc7/inputs/working-copy.glb'
    old_plan_path=ROOT/'benchmarks/mochi-production/draft-9372a14613a141a888aac191637a22e4/color-plan.json'
    if not original.exists() or not old_plan_path.exists():pytest.skip('Optional local reviewed source files are unavailable')
    # If the main project later switches source, its old immutable working file
    # remains available. The test never mutates that project or its database.
    app=create_app(Config(root=ROOT,data_dir=tmp_path/'data',api_token='test-local-token'))
    with TestClient(app,headers={'Authorization':'Bearer test-local-token'}) as client:
        store=app.state.store
        stock=[{'id':f'richard-inventory-202609-{ident}','name':name,'brand':brand,'hex':color,'material':'PLA','owned':True,'allowed':True,'measured':False}
               for ident,name,brand,color in [(31,'Beige','Bambu','#F7E6DE'),(29,'Matte EarthBrown','ELEGOO','#805947'),(30,'ePLA-Lite Black','eSUN','#272729')]]
        store.save_filaments(stock)
        project=store.create_project('Mochi detail adoption regression',Settings(height_mm=180,up_axis='Y',printer_id='h2d-dual').model_dump());root=store.project_dir(project['id']);(root/'inputs').mkdir()
        shutil.copyfile(original,root/'inputs/v1.glb');assert hashlib.sha256((root/'inputs/v1.glb').read_bytes()).hexdigest()==OLD_SHA
        old=json.loads(old_plan_path.read_text());(root/'old-plan.json').write_text(json.dumps(old))
        def populate(p):
            source={'path':'inputs/v1.glb','sha256':OLD_SHA};p['source']=source
            p['artifacts']={'pose':{'hash':'a'*64},'mesh':{'hash':OLD_HASH,'source':source},'plan':{'hash':digest(old),'document':'old-plan.json'},'segments':{'hash':'b'*64},'colors':{'hash':'c'*64},'export':{'hash':'d'*64}}
            p['approvals']={key:{'artifact_hash':value['hash']} for key,value in p['artifacts'].items()}
        project=store.mutate(project['id'],populate)
        yield client,store,project,root


def test_adoption_is_versioned_resets_mesh_color_gates_and_keeps_originals(versioned_client):
    client,store,before,root=versioned_client;old_bytes=(root/'inputs/v1.glb').read_bytes();old_document=(root/'old-plan.json').read_bytes()
    response=client.post(f'/api/projects/{before["id"]}/mochi-detail-v2/adopt',json={'expected_revision':before['revision'],'expected_mesh_hash':OLD_HASH,'expected_plan_hash':before['artifacts']['plan']['hash']})
    assert response.status_code==200,response.text
    after=response.json();assert after['artifacts']['mesh']['hash']==NEW_HASH and after['source']['sha256']==NEW_SHA
    assert after['settings']['pin_clearance_mm']==.05
    quality=after['artifacts']['mesh']['quality']
    assert quality['triangles']==150000 and quality['vertices']>0 and quality['valid']
    assert quality['boundary_edges']==0 and quality['nonmanifold_edges']==0
    assert set(after['artifacts'])=={'pose','mesh','plan'}
    assert set(after['approvals'])=={'pose'}
    assert (root/'inputs/v1.glb').read_bytes()==old_bytes and (root/'old-plan.json').read_bytes()==old_document
    snapshot=json.loads((root/after['source_history'][-1]['snapshot']).read_text());assert snapshot==before
    artifact=after['artifacts']['plan'];assert artifact['reference_document']!=artifact['construction_reference_document']
    canonical=ColorPlanDocument.model_validate_json((root/artifact['document']).read_text());assert canonical.construction_preset==PRESET
    assert [row['id'] for row in available_presets(after)]==[PRESET]
    assert canonical.mesh_hash==NEW_HASH


def test_stale_adoption_writes_no_snapshot_and_changes_no_project(versioned_client):
    client,store,before,root=versioned_client
    response=client.post(f'/api/projects/{before["id"]}/mochi-detail-v2/adopt',json={'expected_revision':before['revision'],'expected_mesh_hash':'0'*64,'expected_plan_hash':before['artifacts']['plan']['hash']})
    assert response.status_code==409
    assert store.get(before['id'])==before
    assert not (root/'versions').exists()
