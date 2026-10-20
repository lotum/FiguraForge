import json
import httpx
import pytest
from figuraforge.models import Settings
from figuraforge.providers.planning import OpenAIPlanner
from figuraforge.providers.base import ProviderError


def planner_client(changes):
    def handler(request):
        body=json.loads(request.content)
        assert body['model']=='gpt-6-astra' and body['store'] is False
        assert body['text']['format']['strict'] is True
        return httpx.Response(200,json={'id':'mock-response','usage':{'output_tokens':25},'output':[
            {'type':'message','content':[{'type':'output_text','text':json.dumps({
                'summary':'Einstellungen zur Pruefung','changes':changes,'warnings':[]})}]}]})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_advice_is_typed_and_does_not_modify_input():
    settings=Settings().model_dump();before=dict(settings)
    planner=OpenAIPlanner('test-key',client=planner_client([{'key':'mesh_target_faces','value_json':'120000','reason':'Reserve fuer Farbgrenzen'}]))
    result=planner.suggest('mesh',{'settings':settings},[])
    assert result['changes'][0]['after']==120000 and settings==before


@pytest.mark.parametrize('change',[
    {'key':'budget_eur','value_json':'10000','reason':'Not permitted'},
    {'key':'mesh_target_faces','value_json':'9999999','reason':'Out of bounds'},
])
def test_advice_cannot_raise_spending_or_bypass_geometry_bounds(change):
    planner=OpenAIPlanner('test-key',client=planner_client([change]))
    with pytest.raises(ProviderError,match='ungueltige'):
        planner.suggest('mesh',{'settings':Settings().model_dump()},[])


def test_advice_is_applied_only_after_explicit_click_and_rejects_stale_basis(client,monkeypatch):
    from figuraforge.services import jobs
    class MockPlanner(OpenAIPlanner):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,client=planner_client([{'key':'prompt','value_json':'"Stehend, Blick nach vorn"','reason':'Klare Pose'}]),**kwargs)
    monkeypatch.setattr(jobs,'OpenAIPlanner',MockPlanner)
    p=client.post('/api/projects',json={'title':'Advice preview'}).json()
    state=client.app.state;state.vault.set('openai','mock-key-for-test')
    j=state.store.new_job(p['id'],'advise',{'advice_stage':'pose','confirm_cloud_upload':True})
    state.runner.run(j['id'])
    saved=state.store.get(p['id'])
    assert state.store.job(j['id'])['status']=='succeeded'
    assert saved['settings']['prompt']=='' and saved['approvals']=={} and saved['artifacts']=={}
    assert saved['suggestions']['pose']['changes'][0]['after']=='Stehend, Blick nach vorn'
    result=client.post('/api/projects/'+p['id']+'/suggestions/pose/apply',json={})
    assert result.status_code==200 and result.json()['settings']['prompt']=='Stehend, Blick nach vorn'
    # Applying twice after settings changed must never silently reuse old advice.
    assert client.post('/api/projects/'+p['id']+'/suggestions/pose/apply',json={}).status_code==409


def test_advice_requires_cloud_consent(client):
    p=client.post('/api/projects',json={'title':'No consent'}).json()
    r=client.post('/api/projects/'+p['id']+'/jobs',json={'operation':'advise','advice_stage':'pose'})
    assert r.status_code==409
