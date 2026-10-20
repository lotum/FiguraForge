from __future__ import annotations
import os,time
from pathlib import Path
from urllib.parse import quote
from .base import Provider,ProviderError,data_uri


def mesh_target_for_budget(max_refined_faces,requested_faces=150000):
    """Leave > half of the downstream face budget for conforming color cuts."""
    if max_refined_faces<1000: raise ProviderError('Color refinement budget is too small')
    return min(requested_faces,300000,max(100,int(max_refined_faces*.45)))


class Meshy(Provider):
    base='https://api.meshy.ai/openapi/v1'
    def submit(self,images,model='latest',target_polycount=150000):
        if not 1<=len(images)<=4: raise ProviderError('Meshy multiview accepts 1 to 4 views of the same pose')
        if not 100<=target_polycount<=300000: raise ProviderError('Meshy target_polycount must be 100..300000')
        result=self.post(self.base+'/multi-image-to-3d',headers={'Authorization':f'Bearer {self.key}'},json={
            'image_urls':[data_uri(p) for p in images],'ai_model':model,'should_texture':True,
            'enable_pbr':True,'target_formats':['glb'],'should_remesh':True,
            'topology':'triangle','target_polycount':target_polycount})
        task=result.get('result')
        if not task: raise ProviderError('Meshy response has no task ID',True)
        self.checkpoint(provider='meshy',remote_task_id=task,remote_kind='multi-image-to-3d',submission_started=False)
        return task

    def submit_remesh(self,model_url,target_polycount=150000):
        if not 100<=target_polycount<=300000: raise ProviderError('Meshy target_polycount must be 100..300000')
        result=self.post(self.base+'/remesh',headers={'Authorization':f'Bearer {self.key}'},json={
            'model_url':model_url,'target_formats':['glb'],'topology':'triangle',
            'target_polycount':target_polycount})
        task=result.get('result')
        if not task: raise ProviderError('Meshy remesh response has no task ID',True)
        self.checkpoint(provider='meshy',remote_task_id=task,remote_kind='remesh',submission_started=False)
        return task

    def poll(self,task,output:Path,interval=5,max_seconds=3600,kind='multi-image-to-3d'):
        if kind not in ('multi-image-to-3d','remesh'): raise ProviderError('Unsupported Meshy task kind')
        start=time.monotonic(); headers={'Authorization':f'Bearer {self.key}'}
        while time.monotonic()-start<max_seconds:
            result=self.get(f'{self.base}/{kind}/{quote(task,safe="")}',headers=headers)
            state=result.get('status'); self.progress(f'Meshy: {state}, {result.get("progress",0)}%')
            if state=='SUCCEEDED':
                url=result.get('model_urls',{}).get('glb')
                if not url: raise ProviderError('Meshy finished without a GLB')
                domains=os.getenv('FORGE_MESHY_CDN_DOMAINS','meshy.ai,amazonaws.com,cloudfront.net').split(',')
                self.download(url,output,domains)
                return {'path':str(output),'provider':'meshy','task_id':task,'consumed_credits':result.get('consumed_credits')}
            if state in ('FAILED','CANCELED'): raise ProviderError(f'Meshy task ended: {state}')
            time.sleep(interval)
        raise ProviderError('Meshy poll time limit reached; resume the existing task instead of submitting again')
