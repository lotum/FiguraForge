import io,json,base64
import httpx,pytest
from PIL import Image
from figuraforge.providers.base import Provider,ProviderError
from figuraforge.providers.images import OpenAIImages,GeminiImages
from figuraforge.providers.meshy import Meshy
from figuraforge.providers.tripo import Tripo
from figuraforge.providers.review import OpenAIReview

@pytest.fixture
def image(tmp_path):
    p=tmp_path/'reference.png';Image.new('RGB',(16,20),(120,80,40)).save(p);return p


def test_openai_image_edits_real_multipart_contract(image,tmp_path):
    requests=[]
    def handler(r):
        requests.append(r)
        return httpx.Response(200,json={'data':[{'b64_json':base64.b64encode(image.read_bytes()).decode()}],'usage':{'output_tokens':11}})
    client=httpx.Client(transport=httpx.MockTransport(handler))
    result=OpenAIImages('test-key',client=client).generate('pose',[image],tmp_path/'out.png',model='gpt-image-1.5',quality='max')
    assert (tmp_path/'out.png').exists() and result['usage']['output_tokens']==11
    req=requests[0];assert req.url.path=='/v1/images/edits'
    assert b'name="image[]"' in req.content and b'name="input_fidelity"' in req.content
    assert b'\r\n\r\nhigh\r\n' in req.content


def test_openai_v25_does_not_send_unsupported_fidelity(image,tmp_path):
    sent=[]
    def h(r):sent.append(r);return httpx.Response(200,json={'data':[{'b64_json':base64.b64encode(image.read_bytes()).decode()}]})
    OpenAIImages('key',client=httpx.Client(transport=httpx.MockTransport(h))).generate('pose',[image],tmp_path/'x.png')
    assert b'input_fidelity' not in sent[0].content


def test_no_duplicate_paid_post_on_timeout():
    count=[]
    def h(r):count.append(r);raise httpx.ReadTimeout('timeout',request=r)
    p=Provider('key',client=httpx.Client(transport=httpx.MockTransport(h)))
    with pytest.raises(ProviderError) as exc:p.post('https://api.example.com/task',json={})
    assert exc.value.ambiguous and len(count)==1


def test_meshy_submission_records_task_before_poll(image):
    checkpoints=[];sent=[]
    def h(r):sent.append(json.loads(r.content));return httpx.Response(200,json={'result':'task-123'})
    p=Meshy('key',client=httpx.Client(transport=httpx.MockTransport(h)),checkpoint=lambda **kw:checkpoints.append(kw))
    assert p.submit([image,image])=='task-123'
    assert sent[0]['image_urls'][0].startswith('data:image/png;base64,')
    assert sent[0]['target_formats']==['glb']
    assert checkpoints[-1]['remote_task_id']=='task-123'


def test_tripo_four_view_slots_order(image):
    requests=[]
    def h(r):
        if r.url.path.endswith('/upload'):return httpx.Response(200,json={'data':{'image_token':'image-token'}})
        requests.append(json.loads(r.content));return httpx.Response(200,json={'data':{'task_id':'task-456'}})
    p=Tripo('key',client=httpx.Client(transport=httpx.MockTransport(h)))
    assert p.submit({'front':image,'back':image})=='task-456'
    payload=requests[0]
    assert payload['type']=='multiview_to_model' and len(payload['files'])==4
    assert payload['files'][0]['file_token']=='image-token' and payload['files'][1]=={'type':'png'}
    assert payload['files'][2]['file_token']=='image-token'


def test_gemini_legacy_image_payload_and_return(image,tmp_path):
    sent=[]
    def h(r):
        sent.append(json.loads(r.content));return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'inlineData':{'data':base64.b64encode(image.read_bytes()).decode()}}]}}]})
    p=GeminiImages('key',client=httpx.Client(transport=httpx.MockTransport(h)))
    p.generate('front',[image],tmp_path/'out.png',model='configured-model',legacy=True)
    assert sent[0]['contents'][0]['parts'][1]['inlineData']['mimeType']=='image/png'
    assert (tmp_path/'out.png').exists()


def test_review_invalid_scores_blocked(image):
    def h(r):return httpx.Response(200,json={'output':[{'content':[{'type':'output_text','text':json.dumps({'identity_score':200,'pose_score':80,'multiview_score':80})}]}]})
    with pytest.raises(ProviderError):OpenAIReview('key',client=httpx.Client(transport=httpx.MockTransport(h))).review([image],[image],'pose','configured-model')


def test_gemini_interactions_final_model_output_not_thought(image,tmp_path):
    raw=base64.b64encode(image.read_bytes()).decode()
    def h(r):return httpx.Response(200,json={'steps':[{'type':'thought','summary':[{'type':'image','data':'NOT_AN_IMAGE'}]},{'type':'model_output','content':[{'type':'image','data':raw}]}]})
    p=GeminiImages('key',client=httpx.Client(transport=httpx.MockTransport(h)))
    p.generate('front',[image],tmp_path/'result.png',model='gemini-nano-banana-2.1')
    assert (tmp_path/'result.png').exists()


@pytest.mark.parametrize('payload,expected',[
    ({'error':{'code':'insufficient_quota','message':'secret-must-not-leak'}},'API-Guthaben'),
    ({'error':{'code':'rate_limit_exceeded','message':'secret-must-not-leak'}},'Anfragelimit erreicht'),
    ({'error':'secret-must-not-leak'},'genaue Ursache wurde nicht erkannt'),
])
def test_submission_429_distinguishes_quota_and_rate_without_retry(payload,expected):
    requests=[]
    def handler(request):
        requests.append(request)
        return httpx.Response(429,json=payload)
    provider=Provider('key',client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(ProviderError) as exc:
        provider.post('https://api.example.com/task',json={})
    assert expected in str(exc.value)
    assert 'secret-must-not-leak' not in str(exc.value)
    assert len(requests)==1


def test_rejection_preserves_diagnostic_identifiers_without_echoing_inputs():
    def handler(request):
        return httpx.Response(400,headers={'x-request-id':'req_test123'},json={'error':{
            'code':'invalid_image','param':'image[0]','type':'invalid_request_error',
            'message':'secret-canary and private-reference-image-bytes'}})
    provider=Provider('secret-canary',client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(ProviderError) as exc:
        provider.post('https://api.openai.com/v1/images/edits',json={})
    message=str(exc.value)
    assert 'code=invalid_image' in message and 'param=image[0]' in message
    assert 'request_id=req_test123' in message
    assert 'secret-canary' not in message and 'private-reference' not in message


def test_pose_failure_keeps_partial_view_and_encrypted_diagnostics(client,image,monkeypatch):
    from figuraforge.services import jobs
    count=[]
    def handler(request):
        count.append(request)
        if len(count)==1:
            return httpx.Response(200,json={'data':[{'b64_json':base64.b64encode(image.read_bytes()).decode()}]})
        return httpx.Response(400,headers={'x-request-id':'req_second_view'},json={'error':{
            'code':'invalid_image','param':'image[0]','message':'private-error-canary'}})
    class MockImages(OpenAIImages):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,client=httpx.Client(transport=httpx.MockTransport(handler)),**kwargs)
    monkeypatch.setattr(jobs,'OpenAIImages',MockImages)
    p=client.post('/api/projects',json={'title':'Partial pose diagnostic'}).json()
    client.post('/api/projects/'+p['id']+'/references',files={'files':('ref.png',image.read_bytes(),'image/png')})
    store=client.app.state.store;vault=client.app.state.vault
    vault.set('openai','mock-api-key')
    job=store.new_job(p['id'],'pose',{'confirm_cloud_upload':True})
    client.app.state.runner.run(job['id'])
    saved=store.job(job['id'])
    assert saved['status']=='failed' and len(count)==2
    views=saved['checkpoint']['pose_views']
    assert len(views)==1 and views[0]['view']=='front'
    assert (store.project_dir(p['id'])/views[0]['path']).is_file()
    encrypted=(store.project_dir(p['id'])/saved['checkpoint']['provider_error_file']).read_bytes()
    assert b'private-error-canary' not in encrypted
    record=json.loads(vault.cipher.decrypt(encrypted))
    assert record['request_id']=='req_second_view' and 'private-error-canary' in record['body']
    assert 'private-error-canary' not in saved['error']
    assert 'pose' not in store.get(p['id'])['artifacts']


def test_meshy_new_generation_requests_bounded_triangle_mesh(image):
    from figuraforge.providers.meshy import mesh_target_for_budget
    sent=[]
    def handler(request):
        sent.append(json.loads(request.content));return httpx.Response(200,json={'result':'bounded-task'})
    target=mesh_target_for_budget(350000)
    provider=Meshy('key',client=httpx.Client(transport=httpx.MockTransport(handler)))
    provider.submit([image],target_polycount=target)
    assert sent[0]['should_remesh'] is True and sent[0]['topology']=='triangle'
    assert sent[0]['target_polycount']==150000 and target<350000/2
    assert mesh_target_for_budget(10000)==4500
    assert mesh_target_for_budget(1000000)==150000


def test_meshy_remesh_checkpoints_and_polls_correct_endpoint(tmp_path):
    sent=[];checkpoints=[]
    def handler(request):
        sent.append(request)
        if request.method=='POST':
            assert request.url.path.endswith('/remesh')
            assert json.loads(request.content)['target_polycount']==150000
            return httpx.Response(200,json={'result':'remesh-task'})
        assert request.url.path.endswith('/remesh/remesh-task')
        return httpx.Response(200,json={'status':'SUCCEEDED','model_urls':{'glb':'https://assets.meshy.ai/model.glb'},'consumed_credits':5})
    provider=Meshy('key',client=httpx.Client(transport=httpx.MockTransport(handler)),checkpoint=lambda **kw:checkpoints.append(kw))
    provider.download=lambda url,path,domains:path.write_bytes(b'local-test-model')
    task=provider.submit_remesh('https://assets.meshy.ai/original.glb')
    result=provider.poll(task,tmp_path/'out.glb',kind='remesh')
    assert checkpoints[-1]['remote_kind']=='remesh' and result['consumed_credits']==5
    assert len(sent)==2
