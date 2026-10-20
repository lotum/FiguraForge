from __future__ import annotations
import base64
import re
import time
from pathlib import Path
from urllib.parse import urljoin
import httpx
from ..security import validate_public_url


class ProviderError(RuntimeError):
    def __init__(self,message,ambiguous=False): super().__init__(message); self.ambiguous=ambiguous


class Provider:
    def __init__(self,key=None,client=None,checkpoint=None,progress=None):
        self.key=key
        self.client=client or httpx.Client(timeout=httpx.Timeout(240,connect=20),follow_redirects=False,trust_env=False)
        self.checkpoint=checkpoint or (lambda **kw: None)
        self.progress=progress or (lambda message: None)
        self.error_recorder=lambda response: None

    def rejection_detail(self,response):
        """Expose bounded structured diagnostics, never complete response bodies."""
        try:
            error=response.json().get('error',{})
        except (ValueError,AttributeError): return ''
        if not isinstance(error,dict): return ''
        details=[]
        for field in ('code','param','type'):
            value=error.get(field)
            if isinstance(value,str) and re.fullmatch(r'[a-zA-Z0-9_.\[\]-]{1,100}',value):
                details.append(f'{field}={value}')
        # Free-form messages may echo inputs; only return structured identifiers.
        request_id=response.headers.get('x-request-id','')
        if re.fullmatch(r'[a-zA-Z0-9_-]{1,100}',request_id): details.append('request_id='+request_id)
        detail='; '.join(details)
        if self.key: detail=detail.replace(self.key,'[REDACTED]')
        return (' '+detail) if detail else ''

    def post(self,url,**kwargs):
        # Do NOT retry a paid POST automatically after an ambiguous timeout.
        self.checkpoint(submission_started=True)
        try: r=self.client.post(url,**kwargs)
        except httpx.HTTPError as e: raise ProviderError('Provider submission failed or timed out. It may have been accepted; check the provider dashboard before retrying.',True) from e
        if r.status_code>=400: self.error_recorder(r)
        if r.status_code==429:
            # Classify known codes only; never expose arbitrary provider payloads or keys.
            try:
                error=r.json().get('error',{})
                codes={error.get('code'),error.get('type')} if isinstance(error,dict) else set()
            except (ValueError,AttributeError,TypeError): codes=set()
            if codes & {'insufficient_quota','billing_hard_limit_reached','billing_not_active','organization_usage_limit_exceeded','usage_limit_reached','credits_exhausted'}:
                raise ProviderError('HTTP 429: API-Guthaben oder Nutzungskontingent erschoepft. Abrechnung und Limits beim Anbieter pruefen; erneutes Starten behebt das nicht.')
            if codes & {'rate_limit_exceeded','rate_limit_error','slow_down'}:
                raise ProviderError('HTTP 429: Anfragelimit erreicht. Vor einem erneuten manuellen Versuch warten und die Modell-Limits beim Anbieter pruefen.')
            raise ProviderError('HTTP 429: Anbieter lehnt die Anfrage wegen eines Anfrage- oder Kontingentlimits ab. API-Guthaben und Modell-Limits pruefen; genaue Ursache wurde nicht erkannt.')
        if r.status_code>=400: raise ProviderError(f'Provider rejected the request (HTTP {r.status_code}).'+self.rejection_detail(r)+' Check model access, key, quota and request settings.')
        try: return r.json()
        except ValueError as e: raise ProviderError('Provider returned invalid JSON',True) from e

    def get(self,url,**kwargs):
        for attempt in range(4):
            try: r=self.client.get(url,**kwargs)
            except httpx.HTTPError as e:
                if attempt==3: raise ProviderError('Provider status polling failed; the remote task may still be running') from e
                time.sleep(min(2**attempt,8)); continue
            if r.status_code in (429,500,502,503,504) and attempt<3:
                time.sleep(min(2**attempt,8)); continue
            if r.status_code>=400: raise ProviderError(f'Provider status request failed (HTTP {r.status_code})')
            return r.json()
        raise ProviderError('Polling failed')

    def download(self,url,path:Path,allowed_domains=None,max_bytes=100*1024*1024):
        for _ in range(4):
            validate_public_url(url,allowed_domains=allowed_domains)
            with self.client.stream('GET',url,headers={}) as r:
                if r.is_redirect:
                    url=urljoin(url,r.headers.get('location','')); continue
                if r.status_code!=200: raise ProviderError(f'Asset download failed (HTTP {r.status_code})')
                if int(r.headers.get('content-length',0))>max_bytes: raise ProviderError('Provider asset exceeds size limit')
                path.parent.mkdir(parents=True,exist_ok=True); size=0
                with path.open('wb') as f:
                    for chunk in r.iter_bytes():
                        size+=len(chunk)
                        if size>max_bytes: raise ProviderError('Provider asset exceeds size limit')
                        f.write(chunk)
                return path
        raise ProviderError('Too many asset redirects')


def data_uri(path:Path):
    mime={'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp'}.get(path.suffix.lower(),'image/png')
    return f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode('ascii')


def image_b64(path:Path):
    uri=data_uri(path); head,data=uri.split(',',1)
    return head[5:].split(';')[0],data


def save_b64_image(data:str,path:Path):
    import io
    from PIL import Image
    try:
        raw=base64.b64decode(data,validate=True)
        if len(raw)>50*1024*1024: raise ProviderError('Generated image exceeds size limit')
        image=Image.open(io.BytesIO(raw))
        if image.width*image.height>40_000_000: raise ProviderError('Generated image pixel limit exceeded')
        image.load()
        image.convert('RGB').save(path,'PNG')
    except (ValueError,OSError) as e: raise ProviderError('Invalid image payload from provider') from e
    return path
