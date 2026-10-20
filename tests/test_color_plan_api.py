"""Real HTTP boundaries for local planning and native-template uploads.

Only the process launcher is replaced: planning itself executes real geometry
code on a tiny local GLB. No cloud client is created.
"""
from copy import deepcopy
import io
import json
import time
import zipfile
import warnings
import pytest
import trimesh
from fastapi.testclient import TestClient
from figuraforge.db import digest
from figuraforge.services.color_plan import save_plan


@pytest.fixture
def seeded(client):
    project=client.post('/api/projects',json={'title':'Farbplan API'}).json()
    pid=project['id'];store=client.app.state.store;root=store.project_dir(pid)
    mesh=trimesh.creation.box(extents=[20,25,30]);source=root/'source.glb';source.write_bytes(mesh.export(file_type='glb'))
    count=len(mesh.faces)
    document={'version':1,'mesh_hash':'a'*64,'face_count':count,'face_regions':[0]*count,
              'regions':[{'id':0,'name':'Grundkoerper','strategy':'body','color':'#AA5533'}],
              'nozzle_count':2,'filament_ids':[],'ratio_step_percent':5}
    preview={'format':'figuraforge-mesh-v1','meshes':[{'name':'Farbplan','colors':''}]}
    old_dir=root/'plans'/'original';plan_hash=save_plan(old_dir,document,preview)
    artifact={'hash':plan_hash,'mesh_hash':'a'*64,'face_count':count,'regions':document['regions'],
              'document':'plans/original/color-plan.json','preview':'plans/original/plan-preview.json'}
    def apply(p):
        p['source']={'path':'source.glb','sha256':digest('source')}
        p['artifacts']={'pose':{'hash':'p'*64},'mesh':{'hash':'a'*64,'source':p['source'],'quality':{'valid':True}},
                        'plan':artifact,'segments':{'hash':'s'*64},'colors':{'hash':'c'*64},'export':{'hash':'e'*64}}
        p['approvals']={'pose':{'hash':'p'*64},'mesh':{'hash':'a'*64},'colors':{'hash':'c'*64}}
    store.mutate(pid,apply)
    return {'id':pid,'base':'/api/projects/'+pid,'root':root,'document':document,'hash':plan_hash}


def body(seed):
    return {'expected_hash':seed['hash'],'document':deepcopy(seed['document'])}


def wait_job(client,job):
    deadline=time.monotonic()+5
    while time.monotonic()<deadline:
        state=client.get('/api/jobs/'+job['id']).json()
        if state['status'] not in ('queued','running'):
            assert state['status']=='succeeded',state
            return state
        time.sleep(.01)
    pytest.fail('Local plan job did not finish')


def test_plan_job_builds_independent_artifact_without_constructing_parts(client,seeded,monkeypatch):
    from figuraforge.services.geometry_task import execute
    calls=[]
    def native(request,out,progress):
        calls.append(request['operation'])
        return execute({**request,'out':str(out)},progress)
    monkeypatch.setattr('figuraforge.services.jobs.run_native',native)
    response=client.post(seeded['base']+'/jobs',json={'operation':'plan'})
    assert response.status_code==200,response.text
    wait_job(client,response.json())
    current=client.get(seeded['base']).json()
    assert calls==['plan']
    assert current['artifacts']['mesh']['hash']=='a'*64
    assert current['artifacts']['pose']['hash']=='p'*64
    assert not {'segments','colors','export'} & current['artifacts'].keys()
    plan=current['artifacts']['plan']
    assert plan['mesh_hash']=='a'*64 and plan['validated'] is False
    assert (seeded['root']/plan['document']).is_file()
    assert (seeded['root']/plan['preview']).is_file()
    assert not list((seeded['root']/plan['document']).parent.glob('*.stl'))
    assert current['ledger']==[]


def test_plan_job_requires_mesh(client):
    project=client.post('/api/projects',json={'title':'No mesh'}).json()
    response=client.post('/api/projects/'+project['id']+'/jobs',json={'operation':'plan'})
    assert response.status_code==409


def test_save_plan_is_immutable_and_invalidates_only_downstream(client,seeded):
    before=client.get(seeded['base']).json();old=seeded['root']/before['artifacts']['plan']['document'];old_bytes=old.read_bytes()
    request=body(seeded);request['document']['regions'][0]['name']='Bewusst geplanter Koerper'
    response=client.put(seeded['base']+'/color-plan',json=request)
    assert response.status_code==200,response.text
    updated=response.json();new=updated['artifacts']['plan']
    assert updated['revision']==before['revision']+1
    assert new['hash']!=seeded['hash'] and new['document']!=before['artifacts']['plan']['document']
    assert old.read_bytes()==old_bytes
    assert json.loads((seeded['root']/new['document']).read_text())['regions'][0]['name']=='Bewusst geplanter Koerper'
    assert new['validated'] is True
    assert not {'segments','colors','export'} & updated['artifacts'].keys()
    assert not {'segments','colors','export'} & updated['approvals'].keys()
    assert updated['artifacts']['mesh']==before['artifacts']['mesh']
    assert updated['artifacts']['pose']==before['artifacts']['pose']
    assert updated['approvals']['mesh']==before['approvals']['mesh']


@pytest.mark.parametrize('target',['expected_hash','mesh_hash'])
def test_save_rejects_stale_plan_or_mesh_without_state_change(client,seeded,target):
    before=client.get(seeded['base']).json();request=body(seeded)
    if target=='expected_hash':request['expected_hash']='b'*64
    else:request['document']['mesh_hash']='b'*64
    response=client.put(seeded['base']+'/color-plan',json=request)
    assert response.status_code==409,response.text
    after=client.get(seeded['base']).json()
    assert after['revision']==before['revision']
    assert after['artifacts']==before['artifacts']


def test_save_rejects_active_job(client,seeded):
    store=client.app.state.store
    job=store.new_job(seeded['id'],'inspect',{'operation':'inspect'})
    try:
        assert client.put(seeded['base']+'/color-plan',json=body(seeded)).status_code==409
        assert client.post(seeded['base']+'/bambu-template',files={'file':('x.3mf',b'bad')}).status_code==409
    finally:store.update_job(job['id'],status='cancelled')


def test_concurrent_revision_change_rejects_save_atomically(client,seeded,monkeypatch):
    store=client.app.state.store;original=store.mutate;seen=[]
    def mutate(pid,fn,expected_revision=None,require_idle=False):
        if expected_revision is not None and not seen:
            seen.append(expected_revision)
            original(pid,lambda p:p.update(title='Concurrent edit'))
        return original(pid,fn,expected_revision=expected_revision,require_idle=require_idle)
    monkeypatch.setattr(store,'mutate',mutate)
    response=client.put(seeded['base']+'/color-plan',json=body(seeded))
    assert response.status_code==409,response.text
    current=store.get(seeded['id'])
    assert seen and current['title']=='Concurrent edit'
    assert current['artifacts']['plan']['hash']==seeded['hash']
    assert current['artifacts']['segments']['hash']=='s'*64


def archive(entries):
    output=io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',UserWarning)
        with zipfile.ZipFile(output,'w') as z:
            for name,value in entries:z.writestr(name,value)
    return output.getvalue()


@pytest.mark.parametrize('payload',[
    b'not a zip archive',
    b'PK\x03\x04truncated',
    archive([('../outside.txt','escape')]),
    archive([('Metadata/project_settings.config','{}'),('Metadata/project_settings.config','{}')]),
    archive([('C:/outside.txt','escape')]),
    archive([('Metadata/project_settings.config','{invalid json'),('Metadata/model_settings.config','<config/>')]),
])
def test_invalid_native_upload_returns_422_not_server_error(client,seeded,payload):
    no_raise=TestClient(client.app,raise_server_exceptions=False)
    try:response=no_raise.post(seeded['base']+'/bambu-template',files={'file':('test.3mf',payload,'application/octet-stream')})
    finally:no_raise.close()
    assert response.status_code==422,response.text
    assert 'bambu_template' not in client.app.state.store.get(seeded['id'])


def native_template(model=b'<broken',**changes):
    settings={'printer_model':'Bambu Lab H2D','nozzle_diameter':['0.4','0.4'],
              'enable_mixed_color_sublayer':'1','filament_colour':['#112233','#DDCCBB','#887766'],
              'filament_is_mixed':['0','0','1'],'filament_mixed_components':['','','1,2'],
              'filament_mixed_sublayer_ratios':['','','0.50,0.50'],
              'filament_mixed_gradient':['0']*3,'filament_mixed_gradient_range':['']*3,
              'filament_mixed_gradient_curve':['']*3,'filament_mixed_gradient_per_part':['0']*3,
              'machine_start_gcode':'PRIVATE PROFILE TEXT','account_user':'private user'}
    settings.update(changes)
    return archive([('Metadata/project_settings.config',json.dumps(settings)),
                    ('Metadata/model_settings.config','<config/>'),('3D/3dmodel.model',model)])


def test_malformed_model_xml_returns_422_not_500(client,seeded):
    no_raise=TestClient(client.app,raise_server_exceptions=False)
    try:response=no_raise.post(seeded['base']+'/bambu-template',files={'file':('bad-xml.3mf',native_template())})
    finally:no_raise.close()
    assert response.status_code==422,response.text


def test_valid_template_import_preserves_file_and_returns_sanitized_summary(client,seeded):
    model=b'<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources><object id="1"><mesh><triangles><triangle v1="0" v2="1" v3="2"/></triangles></mesh></object></resources></model>'
    data=native_template(model)
    response=client.post(seeded['base']+'/bambu-template',files={'file':('safe.3mf',data)})
    assert response.status_code==200,response.text
    saved=response.json()['bambu_template']
    derived=seeded['root']/saved['path']
    assert (derived.parent/'h2d-template.3mf').read_bytes()==data
    with zipfile.ZipFile(derived) as archive:
        assert not any(name.startswith('Auxiliaries/') for name in archive.namelist())
        assert b'<triangle ' not in archive.read('3D/3dmodel.model')
    assert saved['info']['printer_model']=='Bambu Lab H2D'
    assert saved['info']['nozzle_count']==2
    assert saved['info']['native_roundtrip_verified'] is False
    assert saved['info']['slicing_verified'] is False
    assert 'PRIVATE PROFILE TEXT' not in response.text and 'private user' not in response.text
    second=client.post(seeded['base']+'/bambu-template',files={'file':('same-name.3mf',data)}).json()['bambu_template']
    assert second['path']!=saved['path']
    assert (derived.parent/'h2d-template.3mf').read_bytes()==data


def mixed_preview_request(client,seeded):
    from figuraforge.services.workflow import file_hash
    store=client.app.state.store
    store.save_filaments([{'id':'dark','hex':'#000000','material':'PLA','owned':True,'allowed':True},
                          {'id':'light','hex':'#FFFFFF','material':'PLA','owned':True,'allowed':True}])
    store.mutate(seeded['id'],lambda p:p['artifacts']['mesh']['source'].update(sha256=file_hash(seeded['root']/'source.glb')))
    request=body(seeded);request['document']['regions'][0]['strategy']='mixed'
    request['document']['filament_ids']=['dark','light']
    return request


def test_mixed_preview_is_local_read_only_and_returns_two_spool_recipes(client,seeded):
    request=mixed_preview_request(client,seeded)
    before=client.get(seeded['base']).json()
    response=client.post(seeded['base']+'/color-plan/mixed-preview',json=request)
    assert response.status_code==200,response.text
    result=response.json()
    assert result['physical_filament_count']==2 and len(result['recipe_palette'])==19
    assert len(result['face_recipe_indices'])==12
    assert all(sum(r['sublayer_thickness_mm'])==pytest.approx(.2) for r in result['recipe_palette'])
    assert client.get(seeded['base']).json()==before


def test_mixed_preview_uses_immutable_color_baseline_after_multiple_saves(client,seeded):
    request=mixed_preview_request(client,seeded)
    first=client.post(seeded['base']+'/color-plan/mixed-preview',json=request).json()
    request['document']['regions'][0]['color']='#FFFFFF'
    saved=client.put(seeded['base']+'/color-plan',json=request)
    assert saved.status_code==200,saved.text
    artifact=saved.json()['artifacts']['plan'];baseline=artifact['reference_document']
    assert baseline=='plans/original/color-plan.json'
    request['expected_hash']=artifact['hash']
    second=client.post(seeded['base']+'/color-plan/mixed-preview',json=request)
    assert second.status_code==200,second.text
    assert second.json()['face_recipe_indices']!=first['face_recipe_indices']
    request['document']['regions'][0]['name']='Renamed only'
    saved_again=client.put(seeded['base']+'/color-plan',json=request).json()
    assert saved_again['artifacts']['plan']['reference_document']==baseline
    request['expected_hash']=saved_again['artifacts']['plan']['hash']
    third=client.post(seeded['base']+'/color-plan/mixed-preview',json=request)
    assert third.status_code==200,third.text
    assert third.json()['face_recipe_indices']==second.json()['face_recipe_indices']


def test_mixed_preview_rejects_changed_source_and_stale_plan(client,seeded):
    request=mixed_preview_request(client,seeded)
    stale=deepcopy(request);stale['expected_hash']='b'*64
    assert client.post(seeded['base']+'/color-plan/mixed-preview',json=stale).status_code==409
    source=seeded['root']/'source.glb';source.write_bytes(source.read_bytes()+b'changed')
    result=client.post(seeded['base']+'/color-plan/mixed-preview',json=request)
    assert result.status_code==409 and 'Meshdatei' in result.json()['detail']


def test_anatomical_proposal_is_read_only_and_bound_to_current_plan(client,seeded,monkeypatch):
    calls=[]
    def proposal(project,root,document,filaments):
        calls.append(document['mesh_hash'])
        return {**document,'construction_preset':'mochi-anatomical-v1'},{'automatic_approval':False}
    monkeypatch.setattr('figuraforge.services.plan_presets.prepare_proposal',proposal)
    before=client.app.state.store.get(seeded['id'])
    response=client.post(seeded['base']+'/color-plan/anatomical-proposal',json=body(seeded))
    assert response.status_code==200,response.text
    assert response.json()['saved'] is False and response.json()['automatic_approval'] is False
    assert client.app.state.store.get(seeded['id'])==before
    stale=body(seeded);stale['expected_hash']='f'*64
    assert client.post(seeded['base']+'/color-plan/anatomical-proposal',json=stale).status_code==409
    assert calls==['a'*64]


def test_anatomical_save_separates_geometry_and_color_references(client,seeded,monkeypatch):
    monkeypatch.setattr('figuraforge.services.plan_presets.prepare_proposal',lambda p,r,d,f:(deepcopy(d),{}))
    request=body(seeded);request['document']['construction_preset']='mochi-anatomical-v1'
    old_bytes=(seeded['root']/'plans/original/color-plan.json').read_bytes()
    saved=client.put(seeded['base']+'/color-plan',json=request)
    assert saved.status_code==200,saved.text
    project=saved.json();artifact=project['artifacts']['plan']
    assert artifact['construction_reference_document']=='plans/original/color-plan.json'
    assert artifact['reference_document']==artifact['document']
    assert artifact['reference_document']!=artifact['construction_reference_document']
    assert (seeded['root']/'plans/original/color-plan.json').read_bytes()==old_bytes
    assert set(project['approvals'])=={'pose','mesh'}
    next_document=json.loads((seeded['root']/artifact['document']).read_text())
    next_document['regions'][0]['color']='#BB7755'
    again=client.put(seeded['base']+'/color-plan',json={'expected_hash':artifact['hash'],'document':next_document})
    assert again.status_code==200,again.text
    new=again.json()['artifacts']['plan']
    assert new['reference_document']==artifact['reference_document']
    assert new['construction_reference_document']==artifact['construction_reference_document']


def test_anatomical_save_rejects_geometry_changes_without_mutating_project(client,seeded,monkeypatch):
    expected=deepcopy(seeded['document'])
    expected['regions'][0].update(part_group=0,cut_type='inlay')
    monkeypatch.setattr('figuraforge.services.plan_presets.prepare_proposal',lambda p,r,d,f:(expected,{}))
    request=body(seeded);request['document']['construction_preset']='mochi-anatomical-v1'
    request['document']['regions'][0]['strategy']='part'
    before=client.app.state.store.get(seeded['id'])
    response=client.put(seeded['base']+'/color-plan',json=request)
    assert response.status_code==409,response.text
    assert client.app.state.store.get(seeded['id'])==before


def test_unregistered_mesh_does_not_offer_anatomical_preset(client,seeded):
    project=client.get(seeded['base']).json()
    assert project['construction_options']==[]
    response=client.post(seeded['base']+'/color-plan/anatomical-proposal',json=body(seeded))
    assert response.status_code==409
    assert 'noch kein' in response.json()['detail']


def test_saving_identical_validated_plan_preserves_completed_construction(client,seeded):
    response=client.put(seeded['base']+'/color-plan',json={'expected_hash':seeded['hash'],'document':seeded['document']})
    assert response.status_code==200,response.text
    p=response.json();artifact=p['artifacts']['plan'];store=client.app.state.store
    document=json.loads((seeded['root']/artifact['document']).read_text())
    store.mutate(seeded['id'],lambda p:p['artifacts'].update(segments={'hash':'built'},colors={'hash':'assigned'}))
    before=store.get(seeded['id'])
    response=client.put(seeded['base']+'/color-plan',json={'expected_hash':artifact['hash'],'document':document})
    assert response.status_code==200,response.text
    after=store.get(seeded['id'])
    assert after==before
    assert after['artifacts']['segments']['hash']=='built'

def test_solid_only_native_template_upload_needs_no_fake_mixed_profile(client,seeded):
    model=b'<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources/></model>'
    data=native_template(model,enable_mixed_color_sublayer='0',filament_is_mixed=['0']*3,filament_mixed_components=['']*3,filament_mixed_sublayer_ratios=['']*3)
    response=client.post(seeded['base']+'/bambu-template',files={'file':('physical-only.3mf',data)})
    assert response.status_code==200,response.text
    info=response.json()['bambu_template']['info']
    assert info['physical_only'] and not info['mixed_supported'] and info['mixed_slots']==[]
    assert len(info['basis_filaments'])==3
