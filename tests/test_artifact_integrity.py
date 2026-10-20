"""Approved artifacts must still be byte-identical when a local job starts."""
import json
import pytest
from figuraforge.db import digest
from figuraforge.services.workflow import file_hash


@pytest.mark.parametrize('operation,target',[
    ('segment','mesh'),('segment','plan'),('export','mesh'),('export','plan'),('export','template')])
def test_out_of_band_file_change_blocks_worker(client,monkeypatch,operation,target):
    store=client.app.state.store
    p=client.post('/api/projects',json={'title':'Integrity'}).json();pid=p['id'];root=store.project_dir(pid)
    files={name:root/(name+'.json') for name in ('mesh','plan','template')}
    document={'face_regions':[0],'regions':[]}
    for name,path in files.items():path.write_text(json.dumps(document) if name=='plan' else 'original')
    def seed(p):
        p['artifacts']={'mesh':{'hash':'mesh-hash','source':{'path':'mesh.json','sha256':file_hash(files['mesh'])}},
            'plan':{'hash':digest(document),'document':'plan.json','mesh_hash':'mesh-hash'},
            'segments':{'hash':'segments-hash'},'colors':{'segments_hash':'segments-hash'}}
        p['bambu_template']={'path':'template.json','sha256':file_hash(files['template'])}
    store.mutate(pid,seed)
    files[target].write_text(json.dumps({'changed':True}) if target=='plan' else 'changed')
    def forbidden(*args,**kwargs):pytest.fail('Changed file reached native worker')
    monkeypatch.setattr('figuraforge.services.jobs.run_native',forbidden)
    job=store.new_job(pid,operation,{'operation':operation})
    client.app.state.runner.run(job['id'])
    result=store.job(job['id'])
    assert result['status']=='failed'
    assert 'geaendert' in result['error']
    assert 'export' not in store.get(pid)['artifacts']
