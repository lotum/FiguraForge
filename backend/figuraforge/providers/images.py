from __future__ import annotations
from pathlib import Path
from urllib.parse import quote
from .base import Provider,ProviderError,image_b64,save_b64_image,data_uri


class OpenAIImages(Provider):
    def generate(self,prompt,refs:list[Path],output:Path,model='gpt-image-2.5-sunburst',quality='max',size='1024x1536'):
        headers={'Authorization':f'Bearer {self.key}'}
        if quality=='max' and not model.startswith('gpt-image-2.5'): quality='high'
        payload={'model':model,'prompt':prompt,'n':'1','size':size,'quality':quality,'output_format':'png','background':'opaque'}
        if refs:
            if model in ('gpt-image-1','gpt-image-1.5'): payload['input_fidelity']='high'
            files=[('image[]',(p.name,p.read_bytes(),image_b64(p)[0])) for p in refs[:16]]
            result=self.post('https://api.openai.com/v1/images/edits',headers=headers,data=payload,files=files)
        else:
            payload['n']=1
            result=self.post('https://api.openai.com/v1/images/generations',headers=headers,json=payload)
        try: encoded=result['data'][0]['b64_json']
        except (KeyError,IndexError,TypeError) as e: raise ProviderError('OpenAI returned no image; inspect policy/quota/model availability') from e
        save_b64_image(encoded,output)
        return {'path':str(output),'provider':'openai','model':model,'usage':result.get('usage'),
                'quality':result.get('quality',quality),'revised_prompt':result.get('data',[{}])[0].get('revised_prompt')}


class GeminiImages(Provider):
    def generate(self,prompt,refs,output,model='gemini-3-pro-image',quality='max',size='1024x1536',legacy=False):
        if legacy:
            parts=[{'text':prompt}]+[{'inlineData':{'mimeType':image_b64(p)[0],'data':image_b64(p)[1]}} for p in refs[:14]]
            payload={'contents':[{'parts':parts}], 'generationConfig':{'responseModalities':['TEXT','IMAGE'],
                       'imageConfig':{'aspectRatio':'2:3','imageSize':'2K'}}}
            result=self.post(f'https://generativelanguage.googleapis.com/v1beta/models/{quote(model,safe="")}:generateContent',
                             headers={'x-goog-api-key':self.key},json=payload)
            chunks=[part for c in result.get('candidates',[]) for part in c.get('content',{}).get('parts',[])]
            encoded=next((p.get('inlineData',p.get('inline_data',{})).get('data') for p in chunks if 'inlineData' in p or 'inline_data' in p),None)
        else:
            inputs=[{'type':'text','text':prompt}]+[{'type':'image','mime_type':image_b64(p)[0],'data':image_b64(p)[1]} for p in refs[:14]]
            result=self.post('https://generativelanguage.googleapis.com/v1beta/interactions',
                headers={'x-goog-api-key':self.key},json={'model':model,'input':inputs,
                    'response_format':{'type':'image','mime_type':'image/png','aspect_ratio':'2:3','image_size':'2K'}})
            image=result.get('output_image') or {}
            encoded=image.get('data')
            if not encoded:
                encoded=next((o.get('data') for o in result.get('outputs',[]) if o.get('type')=='image'),None)
            if not encoded:
                final_images=[block.get('data') for step in result.get('steps',[]) if step.get('type')=='model_output'
                              for block in step.get('content',[]) if block.get('type')=='image' and block.get('data')]
                encoded=final_images[-1] if final_images else None
        if not encoded: raise ProviderError('Gemini returned no image. Check model/API compatibility and safety feedback.')
        save_b64_image(encoded,output)
        return {'path':str(output),'provider':'gemini-legacy' if legacy else 'gemini','model':model,
                'usage':result.get('usage',result.get('usageMetadata'))}


def pose_prompt(user_prompt:str,identity_notes:str,view:str,has_front=False,model_type='figurine'):
    views={
        'front':'front view, looking toward the camera as specified',
        'left':"strict anatomical LEFT side profile: camera on the character's own left side, not the viewer's left; for a forward-facing head the nose or snout points toward the LEFT edge of the image",
        'back':'strict rear view',
        'right':"strict anatomical RIGHT side profile: camera on the character's own right side, not the viewer's right; for a forward-facing head the nose or snout points toward the RIGHT edge of the image",
    }
    framing={'figurine':'full-body collectible with all reference extremities inside the image','bust':'head-and-shoulders sculptural bust on a flat base','relief':'shallow sculptural relief with a coherent flat backing','custom':'collectible matching the requested crop and format'}[model_type]
    return (f'Create one reference image of a {framing}, {views[view]}. '
            f'User requested pose and style: {user_prompt}. Identity constraints: {identity_notes}. '
            'Preserve the character identity, costume, proportions and distinctive features in the references. '
            'Preserve the reference anatomy, exact limb count and attachment points; do not add or remove limbs or invent a different stance. '
            'Rotate the camera around the same character; never mirror a reference to invent the opposite view. '
            'Keep asymmetrical markings and accessories on their original anatomical side. '
            + ('The FIRST reference is the selected front design for this exact pose; rotate the camera around that pose, not the limbs. ' if has_front else '')
            +'One character only, complete requested object visible, plain neutral background, orthographic-like camera, '
             'soft flat lighting, no baked shadows in surface color, no text, no frame, no contact sheet. '
             'Keep the same pose, expression, clothing, accessories and color layout across all views. '
             'The result is concept art, not a claim of mechanically validated printability.')
