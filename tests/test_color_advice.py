import json
import httpx
import pytest
from figuraforge.models import Settings
from figuraforge.providers.planning import OpenAIPlanner
from figuraforge.providers.base import ProviderError
from figuraforge.services.workflow import build_colors


def assignments():
    return [{'part_id':'core','filament_id':'black','reason':'Briefing: dunkler Koerper'},
            {'part_id':'ear','filament_id':'white','reason':'Kontrast fuer Ohr'}]


def mock_client(rows,seen=None):
    def handle(request):
        body=json.loads(request.content)
        if seen is not None:seen.append(body)
        assert 'assignments' in body['text']['format']['schema']['required']
        return httpx.Response(200,json={'id':'mock','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'summary':'Bestandsfarben vorgeschlagen','changes':[],'warnings':[],'assignments':rows})}]}]})
    return httpx.Client(transport=httpx.MockTransport(handle))


def test_colors_advice_assigns_actual_parts_and_is_editable_before_apply(client,monkeypatch):
    from figuraforge.services import jobs
    seen=[]
    class MockPlanner(OpenAIPlanner):
        def __init__(self,*args,**kwargs):super().__init__(*args,client=mock_client(assignments(),seen),**kwargs)
    monkeypatch.setattr(jobs,'OpenAIPlanner',MockPlanner)
    state=client.app.state;p=client.post('/api/projects',json={'title':'Colors advice','settings':{'owned_filaments_only':True}}).json()
    state.store.save_filaments([{'id':i,'brand':'Test','name':i,'hex':c,'material':'PLA','owned':True,'allowed':ok} for i,c,ok in [('black','#000000',True),('white','#FFFFFF',True),('blocked','#FF0000',False)]])
    parts=[{'id':'core','name':'Koerper','dimensions_mm':[10,10,10],'color':'#888888'},
           {'id':'ear','name':'Ohr','dimensions_mm':[5,5,5],'color':'#FFFFFF'}]
    def initial(current):
        current['artifacts']['segments']={'hash':'1'*64,'parts':parts,'plates':[]}
        current['artifacts']['colors']=build_colors(current,state.store.filaments(),{'core':'white','ear':'white'})
        current['artifacts']['export']={'hash':'2'*64}
        current['approvals']['colors']={'artifact_hash':current['artifacts']['colors']['hash']}
    state.store.mutate(p['id'],initial);state.vault.set('openai','mock-key-never-used-live')
    job=state.store.new_job(p['id'],'advise',{'advice_stage':'colors','advice_prompt':'Dunkler Koerper, helles Ohr','confirm_cloud_upload':True})
    state.runner.run(job['id'])
    assert state.store.job(job['id'])['status']=='succeeded'
    context=json.loads(seen[0]['input'][0]['content'][0]['text'])
    assert {p['id'] for p in context['parts']}=={'core','ear'}
    assert 'blocked' not in {f['id'] for f in context['filaments']}
    saved=state.store.get(p['id']);proposal=saved['suggestions']['colors']
    assert saved['artifacts']['colors']['assignments']=={'core':'white','ear':'white'}
    assert proposal['assignments'][0]['part_name']=='Koerper' and proposal['assignments'][0]['before']=='white'
    url=f'/api/projects/{p["id"]}/suggestions/colors/apply'
    assert client.post(url,json={'assignments':[]}).status_code==422
    assert client.post(url,json={'assignments':[{'part_id':'core','filament_id':'blocked'},{'part_id':'ear','filament_id':'white'}]}).status_code==422
    assert client.post(url,json={'assignments':[{'part_id':'foreign','filament_id':'black'},{'part_id':'ear','filament_id':'white'}]}).status_code==422
    applied=client.post(url,json={'assignments':[{'part_id':'core','filament_id':'white'},{'part_id':'ear','filament_id':'black'}]})
    assert applied.status_code==200,applied.text
    result=applied.json()
    assert result['artifacts']['colors']['assignments']=={'core':'white','ear':'black'}
    assert result['artifacts']['colors']['complete']
    assert 'export' not in result['artifacts'] and 'colors' not in result['approvals']
    assert client.post(url,json={}).status_code==409


@pytest.mark.parametrize('rows',[
    [{'part_id':'core','filament_id':'black','reason':'Missing ear'}],
    [{'part_id':'core','filament_id':'black','reason':'First'},{'part_id':'core','filament_id':'white','reason':'Duplicate'}],
    [{'part_id':'foreign','filament_id':'black','reason':'Unknown'},{'part_id':'ear','filament_id':'white','reason':'Ear'}],
    [{'part_id':'core','filament_id':'blocked','reason':'Not allowed'},{'part_id':'ear','filament_id':'white','reason':'Ear'}],
])
def test_provider_rejects_missing_duplicate_foreign_or_blocked_assignments(rows):
    context={'settings':Settings().model_dump(),'parts':[{'id':'core','name':'Koerper'},{'id':'ear','name':'Ohr'}],
             'filaments':[{'id':'black'},{'id':'white'}]}
    planner=OpenAIPlanner('mock',client=mock_client(rows))
    with pytest.raises(ProviderError,match='unvollstaendige Filamentzuordnungen'):
        planner.suggest('colors',context,[])
