import json,concurrent.futures
import pytest
from figuraforge.db import Store,Conflict,digest
from figuraforge.models import Settings
from figuraforge.services.workflow import approve,apply_settings,require_approval,build_colors
from figuraforge.security import safe_asset_path,validate_public_url,Vault


def fake_project():
    return {'settings':Settings().model_dump(),'artifacts':{k:{'hash':digest(k)} for k in ('pose','mesh','segments','colors','export')},'approvals':{k:{'artifact_hash':digest(k)} for k in ('pose','mesh','colors')}}

@pytest.mark.parametrize('key,value,kept',[('prompt','new',[]),('height_mm',240,['pose']),('inlay_depth_mm',5,['pose','mesh']),('owned_filaments_only',True,['pose','mesh','segments'])])
def test_settings_invalidate_downstream_only(key,value,kept):
    p=fake_project();s=dict(p['settings']);s[key]=value;apply_settings(p,s)
    assert set(p['artifacts'])==set(kept)

def test_budget_change_keeps_geometry():
    p=fake_project();s=dict(p['settings']);s['budget_eur']=150;apply_settings(p,s)
    assert len(p['artifacts'])==5

def test_stale_approval_rejected():
    p=fake_project()
    with pytest.raises(Conflict):approve(p,'mesh','0'*64,True)

def test_warnings_need_explicit_acknowledgement():
    p=fake_project();p['artifacts']['mesh']['warnings']=['No physical test']
    with pytest.raises(Conflict):approve(p,'mesh',digest('mesh'),False)
    approve(p,'mesh',digest('mesh'),True)

def test_store_single_active_job_and_budget(tmp_path):
    store=Store(tmp_path);p=store.create_project('X',Settings(budget_eur=100).model_dump())
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        def attempt(_):
            try:return store.new_job(p['id'],'inspect',{})['id']
            except Conflict:return None
        jobs=list(pool.map(attempt,range(8)))
    assert len([j for j in jobs if j])==1
    store.reserve(p['id'],jobs[0],99,'a')
    with pytest.raises(Conflict):store.reserve(p['id'],jobs[0],2,'b')
    store.recover();assert not store.active_job(p['id'])

@pytest.mark.parametrize('url',['http://example.com/a','https://127.0.0.1/a','https://10.0.0.1/a','https://169.254.169.254/a','https://localhost/a','https://example.com:8080/a','https://user:secret@example.com/a','file:///etc/passwd'])
def test_ssrf_rejected(url):
    with pytest.raises(ValueError):validate_public_url(url,resolve=False)

def test_path_traversal_and_symlink(tmp_path):
    root=tmp_path/'project';root.mkdir();secret=tmp_path/'secret';secret.write_text('private')
    (root/'link').symlink_to(secret)
    for name in ('../secret','link'):
        with pytest.raises(ValueError):safe_asset_path(root,name)

def test_vault_never_returns_key_status(tmp_path):
    v=Vault(tmp_path);v.set('meshy','canary-secret-key')
    assert v.get('meshy')=='canary-secret-key'
    assert v.status()['meshy'] is True
    assert b'canary-secret-key' not in (tmp_path/'secrets.enc').read_bytes()

def test_api_origin_and_missing_key(client):
    r=client.post('/api/projects',json={'title':'X'},headers={'Origin':'https://evil.example'})
    assert r.status_code==403
    p=client.post('/api/projects',json={'title':'X'}).json()
    r=client.post('/api/projects/'+p['id']+'/jobs',json={'operation':'pose'})
    assert r.status_code==409
    assert client.get('/api/config').json()['capabilities']['rigging'] is False

def test_api_key_not_exposed(client):
    r=client.post('/api/secrets',json={'provider':'openai','key':'canary-never-return-me'})
    assert r.status_code==200
    assert 'canary-never-return-me' not in r.text+client.get('/api/config').text


def test_idle_precondition_is_atomic(tmp_path):
    from figuraforge.db import Store,Conflict
    from figuraforge.models import Settings
    store=Store(tmp_path); p=store.create_project('Race test',Settings().model_dump())
    store.new_job(p['id'],'inspect',{})
    with pytest.raises(Conflict): store.mutate(p['id'],lambda x:x.update(title='stale'),require_idle=True)
    assert store.get(p['id'])['title']=='Race test'


def test_vault_concurrent_updates_do_not_drop_keys(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from figuraforge.security import Vault
    vault=Vault(tmp_path)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda i:vault.set('provider'+str(i),'key'+str(i)),range(20)))
    assert all(vault.get('provider'+str(i))=='key'+str(i) for i in range(20))


def test_material_aware_plates_split_identical_hex_different_spools():
    from figuraforge.services.workflow import material_plates
    plates=[{'id':1,'volume_mm':[300,320,325],'placements':[{'part_id':'a','transform':[[1,0,0,10],[0,1,0,20],[0,0,1,0],[0,0,0,1]]},{'part_id':'b','transform':[[1,0,0,40],[0,1,0,20],[0,0,1,0],[0,0,0,1]]},{'part_id':'c','transform':[[1,0,0,70],[0,1,0,20],[0,0,1,0],[0,0,0,1]]}]}]
    assignments={'a':'spool-a','b':'spool-b','c':'spool-c'}
    filaments={key:{'hex':'#AABBCC'} for key in assignments}
    one=material_plates(plates,assignments,filaments,1)
    two=material_plates(plates,assignments,filaments,2)
    assert len(one)==3 and len(two)==2
    assert all(len(p['material_ids'])<=2 for p in two)
    assert two[1]['placements'][0]['transform']==plates[0]['placements'][2]['transform']


def test_new_settings_defaults_do_not_discard_existing_mesh():
    p=fake_project()
    for field in ('mesh_target_faces','precision_mode'):p['settings'].pop(field)
    apply_settings(p,Settings.model_validate(p['settings']).model_dump())
    assert 'mesh' in p['artifacts'] and 'mesh' in p['approvals']


def test_new_projects_have_no_invented_default_spending_cap(tmp_path):
    store=Store(tmp_path);p=store.create_project('No implicit budget',Settings().model_dump())
    assert p['settings']['budget_eur'] is None
    j=store.new_job(p['id'],'pose',{})
    store.reserve(p['id'],j['id'],101,'test estimates only')
    assert len(store.get(p['id'])['ledger'])==1


def test_anatomical_colors_keep_two_basis_spools_and_separate_black_plate():
    p=fake_project();p['settings']['colors_per_plate']=2
    p['artifacts']['segments'].update(parts=[{'id':'body','color_index':0,'color':'#A04B15'},
        {'id':'ear','color_index':1,'color':'#C98C60'},{'id':'nose','color_index':2,'color':'#272729'}],
        plates=[{'id':1,'placements':[{'part_id':'body'},{'part_id':'ear'},{'part_id':'nose'}]}])
    p['artifacts']['plan']={'construction_preset':'mochi-anatomical-v1','filament_ids':['beige','brown'],
        'regions':[{'id':0,'color_mode':'mixed'},{'id':1,'color_mode':'mixed'},
                   {'id':2,'color_mode':'solid','filament_id':'black'}]}
    stock=[{'id':ident,'name':ident,'brand':'test','material':'PLA','owned':True,'allowed':True,'hex':hexcode}
        for ident,hexcode in [('beige','#F7E6DE'),('brown','#805947'),('black','#272729'),('green','#00FF00')]]
    result=build_colors(p,stock)
    assert result['complete']
    assert result['planned_materials']['body']['filament_ids']==['beige','brown']
    assert [x['material_ids'] for x in result['plates']]==[['beige','brown'],['black']]
    assert result['assignments']['nose']=='black'
    assert 'green' not in result['assignments'].values()
    p['artifacts']['colors']=result
    with pytest.raises(Conflict,match='Verlauf verlieren'):
        build_colors(p,stock,{'body':'green','ear':'beige','nose':'black'})
    blocked=[dict(f,allowed=f['id']!='brown') for f in stock]
    with pytest.raises(Conflict,match='Basisfilament'):
        build_colors(p,blocked)


def test_anatomical_multiregion_parts_union_actual_spools_and_enforce_nozzles():
    p=fake_project();p['settings']['colors_per_plate']=2
    p['artifacts']['segments'].update(parts=[{'id':'jaw','color_index':99,'color':'#00AA00'}],
        plates=[{'id':1,'placements':[{'part_id':'jaw'}]}],
        geometry_report={'construction':{'part_region_ids':{'jaw':[4,7]}}})
    p['artifacts']['plan']={'nozzle_count':2,'regions':[
        {'id':4,'color_mode':'solid','filament_id':'green'},
        {'id':7,'color_mode':'solid','filament_id':'cream'},
        {'id':8,'color_mode':'solid','filament_id':'black'}]}
    stock=[{'id':ident,'name':ident,'brand':'test','material':'PLA','owned':True,'allowed':True,'hex':color}
        for ident,color in [('green','#00AA00'),('cream','#F7E6DE'),('black','#272729')]]
    result=build_colors(p,stock)
    assert result['planned_materials']['jaw']['filament_ids']==['green','cream']
    assert result['planned_materials']['jaw']['region_ids']==[4,7]
    assert result['plates'][0]['material_ids']==['cream','green']
    p['artifacts']['segments']['geometry_report']['construction']['part_region_ids']['jaw']=[4,7,8]
    with pytest.raises(Conflict,match='mehr Basisfilamente'):
        build_colors(p,stock)
    p['artifacts']['segments']['geometry_report']['construction']['part_region_ids']['jaw']=[]
    with pytest.raises(Conflict,match='Farbplan'):
        build_colors(p,stock)
