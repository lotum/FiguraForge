from __future__ import annotations
import os,time,base64
from pathlib import Path
from urllib.parse import urlsplit,quote
from .base import Provider,ProviderError,data_uri


class LocalGateway(Provider):
    """Explicitly documented adapter contract for Hunyuan/TRELLIS/custom workers.

    The URL is administrator-controlled, never taken from an uploaded document.
    Actual model inference remains the external worker's responsibility.
    """
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.base=os.getenv('FORGE_LOCAL_GATEWAY','').rstrip('/')
        if not self.base: raise ProviderError('Configure FORGE_LOCAL_GATEWAY for the local 3D model worker')
        u=urlsplit(self.base)
        if u.scheme not in ('http','https') or not u.hostname: raise ProviderError('Invalid configured local gateway')
    def submit(self,images,model):
        r=self.post(self.base+'/jobs',headers={'Authorization':f'Bearer {self.key or ""}'},json={
            'model':model,'images':[data_uri(p) for p in images],'output_format':'glb','texture':True})
        task=r.get('id')
        if not task: raise ProviderError('Local worker did not return a job ID')
        self.checkpoint(provider='local',remote_task_id=task,submission_started=False)
        return task
    def poll(self,task,output,interval=3,max_seconds=7200):
        for _ in range(max(1,int(max_seconds/interval))):
            r=self.get(self.base+'/jobs/'+quote(task,safe=''),headers={'Authorization':f'Bearer {self.key or ""}'})
            self.progress(f'Local 3D worker: {r.get("status")}')
            if r.get('status')=='failed': raise ProviderError('Local worker failed; consult its local logs')
            if r.get('status')=='succeeded':
                if 'glb_base64' in r:
                    raw=base64.b64decode(r['glb_base64'],validate=True)
                    if len(raw)>100*1024*1024: raise ProviderError('Local GLB too large')
                    Path(output).write_bytes(raw)
                else:
                    # Same-origin download only; no arbitrary local filesystem URL.
                    asset=r.get('asset_path','')
                    if not asset.startswith('/assets/') or '..' in asset: raise ProviderError('Invalid local asset path')
                    response=self.client.get(self.base+asset,headers={'Authorization':f'Bearer {self.key or ""}'})
                    response.raise_for_status()
                    if len(response.content)>100*1024*1024: raise ProviderError('Local GLB too large')
                    Path(output).write_bytes(response.content)
                return {'path':str(output),'provider':'local','task_id':task,'model':r.get('model')}
            time.sleep(interval)
        raise ProviderError('Local worker timeout')
