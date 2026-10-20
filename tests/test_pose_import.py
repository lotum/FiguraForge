import io
from PIL import Image


def png(color=(255,0,0,255)):
    out=io.BytesIO();Image.new('RGBA',(40,60),color).save(out,format='PNG')
    return out.getvalue()


def test_existing_views_require_approval_and_preserve_source_images(client):
    project=client.post('/api/projects',json={'title':'Existing character views'}).json()
    base='/api/projects/'+project['id']
    response=client.post(base+'/pose/import',files={
        'front':('front.png',png(),'image/png'),'back':('back.png',png(),'image/png')})
    assert response.status_code==200
    p=response.json();pose=p['artifacts']['pose']
    assert pose['provider']=='manual-import'
    assert [v['view'] for v in pose['views']]==['front','back']
    assert not p['approvals']
    assert client.post(base+'/jobs',json={'operation':'reconstruct','confirm_cloud_upload':True}).status_code==409
    assert client.post(base+'/approve',json={'stage':'pose','artifact_hash':pose['hash'],
        'warnings_acknowledged':True}).status_code==200
    old_path=pose['views'][0]['path']
    updated=client.post(base+'/pose/import',files={'front':('front.png',png((0,255,0,255)),'image/png')}).json()
    assert updated['artifacts']['pose']['hash']!=pose['hash']
    assert 'pose' not in updated['approvals']
    assert client.get(base+'/files/'+old_path).status_code==200
    assert updated['ledger']==[]


def test_pose_import_bad_view_does_not_replace_approved_candidate(client):
    p=client.post('/api/projects',json={'title':'Atomic import'}).json();base='/api/projects/'+p['id']
    pose=client.post(base+'/pose/import',files={'front':('front.png',png(),'image/png')}).json()['artifacts']['pose']
    response=client.post(base+'/pose/import',files={
        'front':('front.png',png(),'image/png'),'back':('bad.png',b'not an image','image/png')})
    assert response.status_code==422
    assert client.get(base).json()['artifacts']['pose']==pose
    assert client.post(base+'/pose/import',files={'back':('back.png',png(),'image/png')}).status_code==422


def test_transparent_reference_and_pose_have_white_background(client):
    p=client.post('/api/projects',json={'title':'Transparent PNG'}).json();base='/api/projects/'+p['id']
    raw=png((0,0,0,0))
    pose=client.post(base+'/pose/import',files={'front':('front.png',raw,'image/png')}).json()['artifacts']['pose']
    refs=client.post(base+'/references',files={'files':('ref.png',raw,'image/png')}).json()['references']
    for path in [pose['views'][0]['path'],refs[0]['path']]:
        image=Image.open(io.BytesIO(client.get(base+'/files/'+path).content))
        assert image.mode=='RGB' and image.getpixel((0,0))==(255,255,255)
