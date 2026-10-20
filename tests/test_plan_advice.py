import json
from copy import deepcopy
import httpx
import pytest
from pydantic import ValidationError
from figuraforge.models import JobRequest,Settings
from figuraforge.providers.planning import OpenAIPlanner
from figuraforge.providers.base import ProviderError
from figuraforge.db import digest


def response_client(proposal,seen=None):
    def handler(request):
        data=json.loads(request.content)
        if seen is not None:seen.append(data)
        return httpx.Response(200,json={'id':'mock','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(proposal)}]}]})
    return httpx.Client(transport=httpx.MockTransport(handler))


def plan_document():
    return {'version':1,'mesh_hash':'1'*64,'face_count':2,'face_regions':[0,1],
            'regions':[{'id':0,'name':'Grundfarbe','strategy':'body','color':'#FFFFFF','part_group':0,'cut_type':'inlay','filament_id':'white'},
                       {'id':1,'name':'Kontrastbereich','strategy':'mixed','color':'#000000','part_group':0,'cut_type':'inlay','filament_id':None}],
            'nozzle_count':2,'filament_ids':['black','white'],'ratio_step_percent':5,'note':''}


def proposal():
    return {'summary':'Kontrastbereich als Ganzteil','changes':[],'warnings':['Eine Farbregion kann mehrere anatomische Stellen enthalten.'],
            'region_changes':[{'id':1,'strategy':'part','filament_id':'black','part_group':1,'cut_type':'whole','reason':'Kontur besser montierbar pruefen'}],
            'filament_ids':[]}


def setup_project(client):
    state=client.app.state;p=client.post('/api/projects',json={'title':'Plan advice'}).json();root=state.store.project_dir(p['id'])
    document=plan_document();(root/'plan.json').write_text(json.dumps(document));(root/'preview.json').write_text(json.dumps({'meshes':[{}]}))
    state.store.save_filaments([{'id':key,'brand':'Test','name':key,'hex':color,'material':'PLA','owned':True,'allowed':True} for key,color in [('black','#000000'),('white','#FFFFFF'),('red','#FF0000')]])
    state.store.mutate(p['id'],lambda current:current['artifacts'].update(mesh={'hash':'1'*64},plan={'hash':digest(document),'mesh_hash':'1'*64,'face_count':2,'document':'plan.json','preview':'preview.json'}))
    state.vault.set('openai','mock-key-no-live-api');return p,document


def test_briefing_is_bounded():
    assert JobRequest(operation='advise',advice_prompt='Bitte Augen erhalten').advice_prompt=='Bitte Augen erhalten'
    with pytest.raises(ValidationError):JobRequest(operation='advise',advice_prompt='x'*6001)


def test_plan_advice_sends_briefing_and_regions_without_face_array(client,monkeypatch):
    from figuraforge.services import jobs
    seen=[]
    class MockPlanner(OpenAIPlanner):
        def __init__(self,*args,**kwargs):super().__init__(*args,client=response_client(proposal(),seen),**kwargs)
    monkeypatch.setattr(jobs,'OpenAIPlanner',MockPlanner)
    p,original=setup_project(client);state=client.app.state
    job=state.store.new_job(p['id'],'advise',{'advice_stage':'plan','advice_prompt':'Schwanzverlauf behalten, Brust separat','confirm_cloud_upload':True})
    state.runner.run(job['id'])
    assert state.store.job(job['id'])['status']=='succeeded'
    context=json.loads(seen[0]['input'][0]['content'][0]['text'])
    assert context['user_briefing']=='Schwanzverlauf behalten, Brust separat'
    assert 'face_regions' not in context['color_plan']
    assert {'black','white'}<=set(f['id'] for f in context['filaments'])
    saved=state.store.get(p['id']);suggestion=saved['suggestions']['plan']
    assert suggestion['region_changes'][0]['after']['cut_type']=='whole'
    assert json.loads((state.store.project_dir(p['id'])/'plan.json').read_text())==original
    edited={'region_changes':[{'id':1,'strategy':'part','filament_id':'black','part_group':4,'cut_type':'inlay'}], 'filament_ids':[]}
    result=client.post(f'/api/projects/{p["id"]}/suggestions/plan/apply',json=edited)
    assert result.status_code==200,result.text
    changed=result.json();artifact=changed['artifacts']['plan']
    candidate=json.loads((state.store.project_dir(p['id'])/artifact['document']).read_text())
    assert candidate['regions'][1]['part_group']==4 and candidate['regions'][1]['cut_type']=='inlay'
    assert candidate['face_regions']==original['face_regions']
    assert artifact['document']!='plan.json' and artifact['validated']
    assert client.post(f'/api/projects/{p["id"]}/suggestions/plan/apply',json={}).status_code==409


@pytest.mark.parametrize('edit',[{'id':999,'strategy':'part','filament_id':'black','part_group':1,'cut_type':'whole','reason':'Bad region'},
                                 {'id':1,'strategy':'part','filament_id':'unknown','part_group':1,'cut_type':'whole','reason':'Bad spool'}])
def test_provider_rejects_unknown_regions_and_filaments(edit):
    document=plan_document();data=proposal();data['region_changes']=[edit]
    planner=OpenAIPlanner('mock',client=response_client(data))
    context={'settings':Settings().model_dump(),'color_plan':{k:v for k,v in document.items() if k!='face_regions'},'filaments':[{'id':'black'},{'id':'white'}]}
    with pytest.raises(ProviderError,match='ungueltige Farbregionen'):planner.suggest('plan',context,[])


def test_edited_settings_apply_validates_types_and_disallowed_fields(client):
    state=client.app.state;p=client.post('/api/projects',json={'title':'Edit settings'}).json()
    basis=digest({'settings':p['settings'],'references':p['references'],'artifacts':{}})
    state.store.mutate(p['id'],lambda current:current.update(suggestions={'mesh':{'basis_hash':basis,'changes':[{'key':'mesh_target_faces','after':120000}]}}))
    url=f'/api/projects/{p["id"]}/suggestions/mesh/apply'
    assert client.post(url,json={'changes':[{'key':'budget_eur','after':999}]}).status_code==409
    assert client.post(url,json={'changes':[{'key':'mesh_target_faces','after':9999999}]}).status_code==422
    good=client.post(url,json={'changes':[{'key':'mesh_target_faces','after':100000}]})
    assert good.status_code==200 and good.json()['settings']['mesh_target_faces']==100000


def test_plan_apply_rejects_face_array_injection_and_stale_plan(client):
    p,document=setup_project(client);state=client.app.state;saved=state.store.get(p['id'])
    basis=digest({'settings':saved['settings'],'references':saved['references'],'artifacts':{k:v.get('hash') for k,v in saved['artifacts'].items()}})
    state.store.mutate(p['id'],lambda current:current.update(suggestions={'plan':{'basis_hash':basis,'plan_hash':digest(document),'changes':[],'region_changes':[],'filament_ids':['black','white']}}))
    url=f'/api/projects/{p["id"]}/suggestions/plan/apply'
    assert client.post(url,json={'face_regions':[1,0]}).status_code==422
    state.store.mutate(p['id'],lambda current:current['artifacts']['plan'].update(hash='2'*64))
    assert client.post(url,json={}).status_code==409


@pytest.mark.parametrize('with_template',[False,True])
def test_export_never_silently_drops_mixed_plan(client,monkeypatch,with_template):
    from figuraforge.services import jobs
    p,document=setup_project(client);state=client.app.state;captured=[]
    from figuraforge.services.workflow import file_hash
    root=state.store.project_dir(p['id'])
    (root/'source.glb').write_bytes(b'locally hashed mock source; native worker is mocked')
    (root/'templates').mkdir()
    (root/'templates/native.3mf').write_bytes(b'locally hashed mock template')
    def configure(current):
        current['source']={'sha256':'5'*64}
        current['artifacts']['mesh']['source']={'path':'source.glb','sha256':file_hash(root/'source.glb')}
        current['artifacts']['segments']={'hash':'3'*64,'plan_hash':digest(document),'parts_dir':'parts','parts':[],'plates':[],'geometry_report':{},'warnings':[]}
        current['artifacts']['colors']={'segments_hash':'3'*64,'filaments':{},'warnings':[]}
        if with_template:current['bambu_template']={'path':'templates/native.3mf','sha256':file_hash(root/'templates/native.3mf')}
    state.store.mutate(p['id'],configure)
    def native(request,*args):
        captured.append(request);raise RuntimeError('payload captured without slicing')
    monkeypatch.setattr(jobs,'run_native',native)
    job=state.store.new_job(p['id'],'export',{})
    state.runner.run(job['id'])
    if not with_template:
        assert captured==[]
        assert 'Einfarbiger Ersatzexport wurde blockiert' in state.store.job(job['id'])['error']
    else:
        assert captured[0]['color_plan']==document
        assert captured[0]['native_template'].endswith('/templates/native.3mf')
        assert captured[0]['source'].endswith('/source.glb')
        assert {'black','white'}<=set(f['id'] for f in captured[0]['inventory'])
        assert captured[0]['settings']['printer_id']=='h2d-dual'


@pytest.mark.parametrize('tamper_draft',[False,True])
def test_unsaved_painted_draft_can_receive_missing_basis_pair_before_full_validation(client,monkeypatch,tamper_draft):
    import base64
    import numpy as np
    from figuraforge.services import jobs
    p,original=setup_project(client);state=client.app.state;seen=[]
    data={'summary':'Basisfilamente ergaenzt','changes':[],'warnings':[],'region_changes':[],'filament_ids':['black','white']}
    class MockPlanner(OpenAIPlanner):
        def __init__(self,*args,**kwargs):super().__init__(*args,client=response_client(data,seen),**kwargs)
    monkeypatch.setattr(jobs,'OpenAIPlanner',MockPlanner)
    monkeypatch.setattr(state.runner.pool,'submit',lambda *args,**kwargs:None)
    draft=deepcopy(original);draft['filament_ids']=[];draft['face_regions']=[1,0]
    request=JobRequest(operation='advise',advice_stage='plan',confirm_cloud_upload=True,
                       advice_plan_document=draft,advice_prompt='Waehle zwei passende Bestandsspulen').model_dump()
    job=state.runner.submit(p['id'],request)
    assert 'advice_plan_document' not in job['request']
    info=job['checkpoint']['plan_draft'];root=state.store.project_dir(p['id'])
    assert json.loads((root/info['document']).read_text())['face_regions']==[1,0]
    assert 'face_regions' not in info
    state.runner.run(job['id'])
    assert state.store.job(job['id'])['status']=='succeeded'
    context=json.loads(seen[0]['input'][0]['content'][0]['text'])
    assert context['color_plan']['filament_ids']==[] and 'face_regions' not in context['color_plan']
    saved=state.store.get(p['id'])
    assert saved['artifacts']['plan']['document']=='plan.json'
    assert json.loads((root/'plan.json').read_text())==original
    if tamper_draft:
        (root/info['document']).write_text(json.dumps(original))
        assert client.post(f'/api/projects/{p["id"]}/suggestions/plan/apply',json={}).status_code==409
        return
    applied=client.post(f'/api/projects/{p["id"]}/suggestions/plan/apply',json={})
    assert applied.status_code==200,applied.text
    artifact=applied.json()['artifacts']['plan'];actual=json.loads((root/artifact['document']).read_text())
    assert actual['face_regions']==[1,0] and actual['filament_ids']==['black','white']
    preview=json.loads((root/artifact['preview']).read_text())
    assert np.frombuffer(base64.b64decode(preview['meshes'][0]['face_region_ids']),dtype='<u4').tolist()==[1,0]
    assert applied.json()['approvals']=={}
