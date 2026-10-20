from __future__ import annotations
import os,time
from pathlib import Path
from urllib.parse import quote
from .base import Provider,ProviderError,image_b64


class Tripo(Provider):
    base='https://api.tripo3d.ai/v2/openapi'
    def upload(self,path):
        r=self.post(self.base+'/upload',headers={'Authorization':f'Bearer {self.key}'},
                    files={'file':(path.name,path.read_bytes(),image_b64(path)[0])})
        token=r.get('data',{}).get('image_token')
        if not token: raise ProviderError('Tripo upload response has no image token')
        return {'type':{'image/jpeg':'jpg','image/webp':'webp'}.get(image_b64(path)[0],'png'),'file_token':token}

    def submit(self,views:dict[str,Path],model='v3.1-20260211'):
        files={k:self.upload(p) for k,p in views.items()}
        payload={'model_version':model,'texture':True,'pbr':True,'texture_quality':'detailed','texture_alignment':'geometry'}
        if len(files)==1:
            payload.update(type='image_to_model',file=next(iter(files.values())))
        else:
            if 'front' not in files: raise ProviderError('Tripo multiview requires a front image')
            payload.update(type='multiview_to_model',files=[files.get(v,{'type':'png'}) for v in ['front','left','back','right']])
        r=self.post(self.base+'/task',headers={'Authorization':f'Bearer {self.key}'},json=payload)
        task=r.get('data',{}).get('task_id')
        if not task: raise ProviderError('Tripo response has no task ID',True)
        self.checkpoint(provider='tripo',remote_task_id=task,submission_started=False)
        return task

    def poll(self,task,output:Path,interval=5,max_seconds=3600):
        start=time.monotonic()
        while time.monotonic()-start<max_seconds:
            r=self.get(f'{self.base}/task/{quote(task,safe="")}',headers={'Authorization':f'Bearer {self.key}'})
            d=r.get('data',{}); state=d.get('status'); self.progress(f'Tripo: {state}, {d.get("progress",0)}%')
            if state=='success':
                o=d.get('output',{}); model=o.get('pbr_model') or o.get('model') or o.get('base_model')
                url=model.get('url') if isinstance(model,dict) else model
                if not url: raise ProviderError('Tripo returned no downloadable model')
                domains=os.getenv('FORGE_TRIPO_CDN_DOMAINS','tripo3d.ai,tripo-data.com,amazonaws.com,cloudfront.net').split(',')
                self.download(url,output,domains)
                return {'path':str(output),'provider':'tripo','task_id':task,'credits':d.get('cost')}
            if state in ('failed','cancelled','banned','expired'): raise ProviderError(f'Tripo task ended: {state}')
            time.sleep(interval)
        raise ProviderError('Tripo poll time limit reached; resume the existing task instead of submitting again')

