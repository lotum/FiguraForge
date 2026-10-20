import json,time,zipfile,io
from pathlib import Path
import pytest
from conftest import ROOT
from figuraforge.models import Settings


def await_job(client,job,max_seconds=50):
    assert 'id' in job,job
    start=time.monotonic()
    while time.monotonic()-start<max_seconds:
        state=client.get('/api/jobs/'+job['id']).json()
        if state['status'] not in ('running','queued'):
            assert state['status']=='succeeded',state
            return state
        time.sleep(.05)
    raise AssertionError('Job timed out')


def test_demo_import_to_colored_print_package(client):
    p=client.post('/api/projects',json={'title':'End to end demo'}).json();base='/api/projects/'+p['id']
    await_job(client,client.post(base+'/demo').json())
    p=client.get(base).json();assert p['artifacts']['mesh']['quality']['valid']
    assert client.post(base+'/jobs',json={'operation':'segment'}).status_code==409
    assert client.post(base+'/approve',json={'stage':'mesh','artifact_hash':p['artifacts']['mesh']['hash'],'warnings_acknowledged':True}).status_code==200
    await_job(client,client.post(base+'/jobs',json={'operation':'segment'}).json())
    p=client.get(base).json();seg=p['artifacts']['segments'];assert len(seg['parts'])==6
    assert all(x['watertight'] for x in seg['parts']) and seg['geometry_report']['packing']['passed']
    assert all(c['passed'] for c in seg['geometry_report']['construction']['insertion_checks'])
    assert p['artifacts']['colors']['complete']
    assert any('not a purchasable filament' in w for w in p['artifacts']['colors']['warnings'])
    assert client.post(base+'/jobs',json={'operation':'export'}).status_code==409
    assert client.post(base+'/approve',json={'stage':'colors','artifact_hash':p['artifacts']['colors']['hash'],'warnings_acknowledged':True}).status_code==200
    await_job(client,client.post(base+'/jobs',json={'operation':'export'}).json())
    p=client.get(base).json();ex=p['artifacts']['export'];r=client.get(base+'/files/'+ex['bundle'])
    assert r.status_code==200
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        assert {'assembly.3mf','assembly.glb','MONTAGE.md','manifest.json','validation.json'}.issubset(z.namelist())
        report=json.loads(z.read('validation.json'));assert all(v['passed'] for v in report.values())
    # A later dimension change cannot reuse either mesh or color approval.
    settings=p['settings'];settings['height_mm']=200
    client.patch(base+'/settings',json=settings)
    assert client.post(base+'/jobs',json={'operation':'export'}).status_code==409
