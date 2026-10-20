from __future__ import annotations
import io
import json
import mimetypes
import zipfile
import secrets
import shutil
from xml.etree.ElementTree import ParseError
from xml.parsers.expat import ExpatError
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from fastapi import FastAPI,Request,UploadFile,File,HTTPException
from fastapi.responses import FileResponse,JSONResponse,HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image,UnidentifiedImageError
from .config import Config
from .db import Store,Conflict,NotFound,uid,digest
from .security import Vault,safe_asset_path,validate_public_url
from .models import AdviceApplyRequest,ColorPlanUpdate,DetailMeshAdoptRequest,Settings,NewProject,JobRequest,ApprovalRequest,SecretRequest,Filament,ColorAssignment,CalibrationRequest
from .services.workflow import apply_settings,invalidate,approve,file_hash,build_colors,advice_basis
from .services.jobs import Runner
from .services.filaments import normalize_spoolmandb,normalize_spoolman,rank_filaments
from .geometry.io import validate_glb_bytes
from .geometry.types import GeometryError


def create_app(config:Config|None=None):
    config=config or Config(); store=Store(config.data_dir); vault=Vault(config.data_dir); runner=Runner(store,vault,config)
    @asynccontextmanager
    async def lifespan(app):
        store.recover()
        if not store.filaments(): store.save_filaments(json.loads((config.assets/'filaments.sample.json').read_text()))
        yield
        runner.shutdown()
    app=FastAPI(title='FiguraForge',version='0.1.0',lifespan=lifespan,docs_url=None,redoc_url=None)
    app.state.store=store; app.state.runner=runner; app.state.config=config; app.state.vault=vault

    @app.middleware('http')
    async def security(request:Request,call_next):
        if request.url.path.startswith('/api'):
            if config.api_token:
                auth=request.headers.get('authorization','').removeprefix('Bearer ')
                cookie=request.cookies.get('forge_token','')
                if not (secrets.compare_digest(auth,config.api_token) or secrets.compare_digest(cookie,config.api_token)):
                    return JSONResponse({'detail':'Authentication required'},status_code=401)
            if request.method not in ('GET','HEAD','OPTIONS'):
                origin=request.headers.get('origin')
                origin_bad=bool(origin and urlsplit(origin).netloc!=request.headers.get('host'))
                if origin_bad or request.headers.get('sec-fetch-site')=='cross-site':
                    return JSONResponse({'detail':'Cross-origin writes are not allowed'},status_code=403)
            if not config.api_token and request.url.hostname not in ('localhost','127.0.0.1','::1','testserver'):
                return JSONResponse({'detail':'Set FORGE_API_TOKEN before exposing the server beyond localhost'},status_code=403)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
        if request.url.path.startswith('/api'): response.headers['Cache-Control']='no-store'
        return response

    for cls,code in ((Conflict,409),(NotFound,404),(GeometryError,422)):
        async def handler(request,exc,status=code): return JSONResponse({'detail':str(exc)},status_code=status)
        app.add_exception_handler(cls,handler)

    def idle(pid):
        store.get(pid)
        if store.active_job(pid): raise Conflict('A project job is active. Wait for completion or cancel it before editing.')

    @app.get('/docs',response_class=HTMLResponse)
    def docs():
        from html import escape
        rows=''.join('<tr><td>'+escape(method.upper())+'</td><td><code>'+escape(path)+'</code></td><td>'+escape(item.get('summary',''))+'</td></tr>'
                     for path,methods in app.openapi()['paths'].items() for method,item in methods.items())
        return '<!doctype html><html lang="de"><head><title>FiguraForge API</title><link rel="stylesheet" href="/style.css"></head><body style="padding:35px"><h1>FiguraForge API</h1><p>Lokale REST-API. <a href="/openapi.json">Vollstaendiges OpenAPI-Schema</a> / <a href="/">Workspace</a></p><table style="border-spacing:14px">'+rows+'</table></body></html>'

    @app.get('/api/health')
    def health(): return {'ok':True,'version':'0.1.0','mode':'local single-user','paid_integrations_live_tested':False}

    @app.get('/api/config')
    def configuration():
        return {'printers':json.loads((config.assets/'printers.json').read_text()),'providers':vault.status(),
            'capabilities':{'color_planning':True,'geometric_part_groups':True,'native_template_import':True,'organic_inlays':True,'whole_color_surface_parts':True,'material_aware_plates':True,'full_semantic_body_partition':False,'native_bambu_project':True,
                'core_3mf_per_plate':True,'rigging':False,'mixed_filament_native':True,'retail_stock_lookup':False},
            'limits':{'max_upload_mb':config.max_upload_mb},'default_settings':Settings().model_dump()}

    @app.post('/session')
    async def login(request:Request):
        if request.headers.get('origin') and urlsplit(request.headers['origin']).netloc!=request.headers.get('host'):
            raise HTTPException(403,'Cross-origin login rejected')
        body=await request.json(); token=body.get('token','')
        if not config.api_token or not secrets.compare_digest(token,config.api_token): raise HTTPException(401,'Invalid token')
        r=JSONResponse({'ok':True}); r.set_cookie('forge_token',token,httponly=True,samesite='strict',secure=request.url.scheme=='https')
        return r

    @app.post('/api/secrets')
    def secret_set(body:SecretRequest): vault.set(body.provider,body.key); return vault.status()
    @app.delete('/api/secrets/{provider}')
    def secret_delete(provider:str): vault.delete(provider); return vault.status()

    @app.get('/api/projects')
    def projects(): return store.list_projects()
    @app.post('/api/projects')
    def new_project(body:NewProject): return store.create_project(body.title,body.settings.model_dump())
    @app.get('/api/projects/{pid}')
    def project(pid:str):
        from .services.plan_presets import available_presets
        current=store.get(pid)
        basis=advice_basis(current)
        suggestions={stage:{**proposal,'stale':not proposal.get('applied',False) and proposal.get('basis_hash')!=basis}
                     for stage,proposal in current.get('suggestions',{}).items()}
        return {**current,'suggestions':suggestions,'construction_options':available_presets(current),'jobs':store.jobs(pid),'events':store.events(pid)}
    @app.patch('/api/projects/{pid}/settings')
    def settings(pid:str,body:Settings):
        idle(pid); return store.mutate(pid,lambda p:apply_settings(p,body.model_dump()),require_idle=True)

    @app.post('/api/projects/{pid}/mochi-detail-v2/adopt')
    def adopt_mochi_detail(pid:str,body:DetailMeshAdoptRequest):
        from .services.mochi_detail_adoption import prepare_adoption,apply_adoption
        idle(pid);p=store.get(pid);root=store.project_dir(pid)
        prepared=prepare_adoption(p,root,config,store.filaments(),body)
        result=store.mutate(pid,lambda current:apply_adoption(current,prepared,body),
                            expected_revision=body.expected_revision,require_idle=True)
        store.event(pid,'source-version','Gepruefte lokale Augendetail-Kopie als neue Meshversion uebernommen; alte Quelle/Plan gesichert, keine automatische Freigabe.')
        return result

    @app.post('/api/projects/{pid}/bambu-template')
    async def bambu_template(pid:str,file:UploadFile=File(...)):
        from .services.mixed_filament import inspect_template,make_profile_template
        from .db import uid
        idle(pid);root=store.project_dir(pid);directory=root/'templates'/uid();directory.mkdir(parents=True)
        data=await upload_bytes(file);path=directory/'h2d-template.3mf';path.write_bytes(data)
        try:
            info=inspect_template(path)
            profile_path=directory/'h2d-profiles-only.3mf'
            make_profile_template(path,profile_path)
        except (ValueError,zipfile.BadZipFile,ParseError,ExpatError) as exc:raise HTTPException(422,'Ungueltige 3MF-Vorlage: '+str(exc)) from exc
        saved={'path':profile_path.relative_to(root).as_posix(),'sha256':file_hash(profile_path),
               'original_sha256':file_hash(path),'info':info}
        return store.mutate(pid,lambda p:p.update(bambu_template=saved),require_idle=True)

    @app.post('/api/projects/{pid}/color-plan/variants')
    def color_plan_variants(pid:str,body:ColorPlanUpdate):
        from .services.color_variants import generate_variants
        idle(pid);p=store.get(pid);artifact=p['artifacts'].get('plan');mesh=p['artifacts'].get('mesh')
        document=body.document.model_dump()
        if not artifact or not mesh or artifact['hash']!=body.expected_hash:
            raise Conflict('Farbplan wurde geaendert; aktuellen Stand laden.')
        if document['mesh_hash']!=mesh['hash'] or document['face_count']!=artifact['face_count'] or len(document['face_regions'])!=artifact['face_count']:
            raise Conflict('Farbplan gehoert zu einer anderen Meshversion.')
        return generate_variants(document)

    @app.post('/api/projects/{pid}/color-plan/mixed-preview')
    def color_plan_mixed_preview(pid:str,body:ColorPlanUpdate):
        from .services.color_plan import validate_plan
        from .services.mixed_preview import build_mixed_preview
        from .geometry.io import load_surface
        idle(pid);p=store.get(pid);artifact=p['artifacts'].get('plan');mesh=p['artifacts'].get('mesh')
        if not artifact or not mesh or artifact['hash']!=body.expected_hash:
            raise Conflict('Farbplan wurde geaendert; aktuellen Stand laden.')
        plan=validate_plan(body.document.model_dump(),mesh['hash'],artifact['face_count'],p['settings'],store.filaments())
        root=store.project_dir(pid)
        source=root/mesh['source']['path']
        if file_hash(source)!=mesh['source']['sha256']:
            raise Conflict('Meshdatei wurde seit der Pruefung geaendert; erneut importieren.')
        surface=load_surface(source,p['settings']['height_mm'],p['settings']['up_axis'])
        native_settings=None;layer_height=.2
        template=p.get('bambu_template')
        if template:
            from .services.mixed_filament import _template_settings
            template_path=root/template['path']
            if file_hash(template_path)!=template['sha256']:
                raise Conflict('Native Vorlage wurde geaendert; erneut importieren.')
            native_settings=_template_settings(template_path)
            layer_height=float(native_settings.get('layer_height',.2))
        if plan.get('construction_preset') in ('mochi-anatomical-v1','mochi-anatomical-detail-v2','pip-anatomical-v1'):layer_height=.2
        reference_path=safe_asset_path(root,artifact.get('reference_document',artifact['document']))
        if artifact.get('reference_sha256') and file_hash(reference_path)!=artifact['reference_sha256']:
            raise Conflict('Unveraenderliche Farbreferenz wurde geaendert; erneut planen.')
        reference_plan=json.loads(reference_path.read_text())
        result=build_mixed_preview(surface,plan,store.filaments(),layer_height_mm=layer_height,
                                   native_settings=native_settings,reference_plan=reference_plan)
        original_regions={r.id:r for r in body.document.regions}
        for region in plan['regions']:
            original=original_regions[region['id']]
            if region['strategy']=='body' and not original.filament_id and region.get('filament_id'):
                spool=next(f for f in store.filaments() if f['id']==region['filament_id'])
                result['warnings'].append(f"{region['name']}: automatische Grundfarbe aus dem Basispaar: {spool.get('brand','')} {spool.get('name',spool['id'])}. Beim Speichern wird diese Zuordnung uebernommen.")
        current=store.get(pid)
        if current['artifacts'].get('mesh',{}).get('hash')!=mesh['hash'] or current['artifacts'].get('plan',{}).get('hash')!=artifact['hash']:
            raise Conflict('Mesh oder Farbplan wurde waehrend der Vorschau geaendert.')
        return result

    @app.post('/api/projects/{pid}/color-plan/anatomical-proposal')
    def anatomical_proposal(pid:str,body:ColorPlanUpdate):
        from .services.plan_presets import prepare_proposal
        idle(pid);p=store.get(pid);artifact=p['artifacts'].get('plan');mesh=p['artifacts'].get('mesh')
        document=body.document.model_dump()
        if not artifact or not mesh or artifact['hash']!=body.expected_hash:
            raise Conflict('Farbplan wurde geaendert; aktuellen Stand laden.')
        if document['mesh_hash']!=mesh['hash'] or document['face_count']!=artifact['face_count']:
            raise Conflict('Farbplan gehoert zu einer anderen Meshversion.')
        proposed,report=prepare_proposal(p,store.project_dir(pid),document,store.filaments())
        if store.get(pid)['revision']!=p['revision']:
            raise Conflict('Projekt wurde waehrend der Berechnung geaendert; erneut pruefen.')
        return {'document':proposed,'report':report,'expected_hash':artifact['hash'],
                'automatic_approval':False,'saved':False}

    @app.put('/api/projects/{pid}/color-plan')
    def update_color_plan(pid:str,body:ColorPlanUpdate):
        import base64
        import numpy as np
        from .services.color_plan import validate_plan,save_plan
        from .geometry.colors import hex_rgb
        from .db import uid
        idle(pid);p=store.get(pid);artifact=p['artifacts'].get('plan');mesh=p['artifacts'].get('mesh')
        if not artifact or not mesh or artifact['hash']!=body.expected_hash:
            raise Conflict('Farbplan wurde geaendert; aktuellen Stand laden.')
        plan=validate_plan(body.document.model_dump(),mesh['hash'],artifact['face_count'],p['settings'],store.filaments())
        root=store.project_dir(pid);directory=root/'plans'/uid()
        transition=plan.get('construction_preset')!=artifact.get('construction_preset')
        construction_reference=None
        if plan.get('construction_preset'):
            from .services.plan_presets import prepare_proposal,validate_preset_geometry,read_reference
            proposed,_=prepare_proposal(p,root,plan,store.filaments())
            validate_preset_geometry(plan,proposed)
            _,reference_path,reference_sha=read_reference(root,artifact,construction=True)
            construction_reference=(reference_path,reference_sha)
        preview=json.loads((root/artifact['preview']).read_text())
        labels=np.asarray(plan['face_regions'],dtype='<u4');byid={r['id']:r for r in plan['regions']}
        for r in plan['regions']:r['face_count']=int(np.sum(labels==r['id']))
        colors=np.asarray([hex_rgb(byid[int(i)]['color']) for i in labels],dtype='<f4')
        preview['meshes'][0]['colors']=base64.b64encode(np.repeat(colors,3,axis=0).tobytes()).decode()
        preview['meshes'][0]['face_region_ids']=base64.b64encode(labels.tobytes()).decode()
        if artifact.get('validated') and digest(plan)==artifact['hash']:
            return p
        plan_hash=save_plan(directory,plan,preview)
        new={**artifact,'validated':True,'hash':plan_hash,'regions':plan['regions'],'filament_ids':plan['filament_ids'],
            'reference_document':artifact.get('reference_document',artifact['document']),
            'reference_sha256':artifact.get('reference_sha256',file_hash(root/artifact['document'])),
            'nozzle_count':plan['nozzle_count'],'document':(directory/'color-plan.json').relative_to(root).as_posix(),
            'preview':(directory/'plan-preview.json').relative_to(root).as_posix()}
        new['construction_preset']=plan.get('construction_preset')
        if construction_reference:
            new.update(construction_reference_document=construction_reference[0],
                       construction_reference_sha256=construction_reference[1])
            if transition:
                # New semantic region IDs need their own immutable color baseline.
                # Keep the original four-color analysis separately for geometry.
                new.update(reference_document=new['document'],reference_sha256=file_hash(directory/'color-plan.json'))
        def apply(current):
            if current['artifacts'].get('plan',{}).get('hash')!=body.expected_hash or current['artifacts'].get('mesh',{}).get('hash')!=plan['mesh_hash']:
                raise Conflict('Mesh oder Farbplan wurde waehrend des Speicherns geaendert.')
            invalidate(current,'segments');current['artifacts']['plan']=new
        return store.mutate(pid,apply,expected_revision=p['revision'],require_idle=True)

    @app.post('/api/projects/{pid}/suggestions/{stage}/apply')
    def apply_suggestion(pid:str,stage:str,body:AdviceApplyRequest|None=None):
        from .providers.planning import FIELDS,apply_region_suggestion
        if stage not in FIELDS: raise HTTPException(422,'Unbekannter Schritt')
        idle(pid);snapshot=store.get(pid)
        proposal=snapshot.get('suggestions',{}).get(stage)
        if not proposal or proposal.get('applied') or proposal.get('basis_hash')!=advice_basis(snapshot):
            raise Conflict('Eingaben wurden geaendert. KI-Vorschlag bitte neu erstellen.')
        changes=([r.model_dump() for r in body.changes] if body and body.changes is not None else proposal['changes'])
        if len({c['key'] for c in changes})!=len(changes):raise Conflict('Doppelte Einstellungsfelder im KI-Vorschlag')
        settings=dict(snapshot['settings'])
        for change in changes:
            if change['key'] not in FIELDS[stage]:raise Conflict('KI-Vorschlag enthaelt ein unzulaessiges Feld')
            settings[change['key']]=change['after']
        try:settings=Settings.model_validate(settings).model_dump()
        except ValueError as exc:raise HTTPException(422,'Ungueltige bearbeitete Einstellungen') from exc
        new_plan=None;new_colors=None
        if stage=='plan':
            from .services.color_plan import validate_plan,save_plan
            artifact=snapshot['artifacts'].get('plan');mesh=snapshot['artifacts'].get('mesh')
            if not artifact or not mesh or artifact['hash']!=proposal.get('plan_hash'):
                raise Conflict('Farbplan wurde geaendert. Vorschlag neu erstellen.')
            root=store.project_dir(pid)
            draft_info=proposal.get('plan_draft')
            if draft_info:
                try:path=safe_asset_path(root,draft_info['document'])
                except (ValueError,FileNotFoundError) as exc:raise Conflict('Gespeicherter Farbplan-Entwurf fehlt oder ist ungueltig') from exc
                if file_hash(path)!=draft_info['sha256']:raise Conflict('Gespeicherter Farbplan-Entwurf wurde veraendert')
                document=json.loads(path.read_text())
                if digest(document)!=draft_info['hash']:raise Conflict('Gespeicherter Farbplan-Entwurf ist nicht identisch')
            else:document=json.loads((root/artifact['document']).read_text())
            edits=([r.model_dump() for r in body.region_changes] if body and body.region_changes is not None else proposal.get('region_changes',[]))
            selected=body.filament_ids if body and body.filament_ids is not None else proposal.get('filament_ids',document['filament_ids'])
            try:
                candidate=apply_region_suggestion(document,edits,selected)
                candidate=validate_plan(candidate,mesh['hash'],artifact['face_count'],settings,store.filaments())
            except ValueError as exc:raise HTTPException(422,'Ungueltige bearbeitete Farbregionen: '+str(exc)) from exc
            directory=root/'plans'/uid()
            preview=json.loads((root/artifact['preview']).read_text())
            if draft_info:
                import base64
                import numpy as np
                from .geometry.colors import hex_rgb
                region_ids=np.asarray(candidate['face_regions'],dtype='<u4');byid={r['id']:r for r in candidate['regions']}
                for region in candidate['regions']:region['face_count']=int(np.sum(region_ids==region['id']))
                colors=np.asarray([hex_rgb(byid[int(i)]['color']) for i in region_ids],dtype='<f4')
                preview['meshes'][0]['colors']=base64.b64encode(np.repeat(colors,3,axis=0).tobytes()).decode()
                preview['meshes'][0]['face_region_ids']=base64.b64encode(region_ids.tobytes()).decode()
            plan_hash=save_plan(directory,candidate,preview)
            new_plan={**artifact,'validated':True,'hash':plan_hash,'regions':candidate['regions'],
                      'reference_document':artifact.get('reference_document',artifact['document']),
                      'reference_sha256':artifact.get('reference_sha256',file_hash(root/artifact['document'])),
                      'filament_ids':candidate['filament_ids'],'nozzle_count':candidate['nozzle_count'],
                      'document':(directory/'color-plan.json').relative_to(root).as_posix(),
                      'preview':(directory/'plan-preview.json').relative_to(root).as_posix()}
        elif body and (body.region_changes is not None or body.filament_ids is not None):
            raise HTTPException(422,'Regionsaenderungen sind nur im Farbplan erlaubt')
        if stage=='colors':
            from copy import deepcopy
            from .providers.planning import advice_assignments
            selected=([r.model_dump() for r in body.assignments] if body and body.assignments is not None else proposal.get('assignments',[]))
            try:
                assignment_map=advice_assignments(selected,snapshot['artifacts'].get('segments',{}).get('parts',[]))
                candidate_project=deepcopy(snapshot);apply_settings(candidate_project,settings)
                new_colors=build_colors(candidate_project,store.filaments(),assignment_map)
            except ValueError as exc:raise HTTPException(422,'Ungueltige Filamentzuordnung: '+str(exc)) from exc
        elif body and body.assignments is not None:
            raise HTTPException(422,'Bauteil-Filamentzuordnung ist nur im Filamentschritt erlaubt')
        def apply(p):
            current=p.get('suggestions',{}).get(stage)
            if not current or current.get('applied') or current.get('basis_hash')!=advice_basis(p):
                raise Conflict('Eingaben wurden geaendert. KI-Vorschlag bitte neu erstellen.')
            apply_settings(p,settings)
            if new_plan is not None:
                invalidate(p,'segments');p['artifacts']['plan']=new_plan
            if new_colors is not None:
                invalidate(p,'colors');p['artifacts']['colors']=new_colors
            current['applied']=True
        return store.mutate(pid,apply,expected_revision=snapshot['revision'],require_idle=True)

    async def upload_bytes(file:UploadFile,limit=None):
        limit=limit or config.max_upload_mb*1024*1024; chunks=[]; size=0
        while block:=await file.read(1024*1024):
            size+=len(block)
            if size>limit: raise HTTPException(413,'Upload exceeds configured size limit')
            chunks.append(block)
        return b''.join(chunks)

    @app.post('/api/projects/{pid}/references')
    async def references(pid:str,files:list[UploadFile]=File(...)):
        idle(pid); p=store.get(pid)
        if len(p['references'])+len(files)>16: raise HTTPException(422,'Maximum 16 reference images per project')
        directory=store.project_dir(pid)/'references'; directory.mkdir(exist_ok=True)
        items=[]
        for file in files:
            data=await upload_bytes(file,20*1024*1024)
            try:
                with Image.open(io.BytesIO(data)) as im:
                    if im.width*im.height>40_000_000: raise ValueError('Image exceeds 40 megapixels')
                    from PIL import ImageOps
                    rgba=ImageOps.exif_transpose(im).convert('RGBA')
                    image=Image.alpha_composite(Image.new('RGBA',rgba.size,'white'),rgba).convert('RGB')
                    image.thumbnail((4096,4096))
                    ident=uid(); path=directory/(ident+'.png'); image.save(path)
            except (OSError,ValueError,UnidentifiedImageError) as exc: raise HTTPException(422,'Invalid or excessively large image') from exc
            items.append({'id':ident,'name':Path(file.filename or 'reference').name[:120],'path':'references/'+path.name,'sha256':file_hash(path)})
        def apply(project): project['references'].extend(items); invalidate(project,'pose')
        return store.mutate(pid,apply,require_idle=True)

    @app.post('/api/projects/{pid}/pose/import')
    async def import_pose(pid:str,front:UploadFile=File(...),left:UploadFile|None=File(None),
                          back:UploadFile|None=File(None),right:UploadFile|None=File(None)):
        """Import existing single-view images without generation or implicit approval."""
        idle(pid)
        directory=store.project_dir(pid)/'poses'/uid(); directory.mkdir(parents=True)
        views=[]
        for view,file in [('front',front),('left',left),('back',back),('right',right)]:
            if file is None: continue
            data=await upload_bytes(file,20*1024*1024)
            try:
                with Image.open(io.BytesIO(data)) as im:
                    if im.width*im.height>40_000_000: raise ValueError('Image too large')
                    from PIL import ImageOps
                    rgba=ImageOps.exif_transpose(im).convert('RGBA')
                    image=Image.alpha_composite(Image.new('RGBA',rgba.size,'white'),rgba).convert('RGB')
                    image.thumbnail((4096,4096)); path=directory/(view+'.png'); image.save(path)
            except (OSError,ValueError,UnidentifiedImageError) as exc:
                raise HTTPException(422,'Invalid or excessively large pose image') from exc
            views.append({'view':view,'path':str(path.relative_to(store.project_dir(pid))),
                          'sha256':file_hash(path)})
        def apply(project):
            invalidate(project,'pose')
            project['artifacts']['pose']={'views':views,'provider':'manual-import','model':None,
                'attempt':1,'review':None,
                'hash':digest({'views':views,'prompt':project['settings']['prompt'],
                               'identity':project['settings']['identity_notes']}),
                'warnings':['Imported views need human identity, pose and camera-direction review. '
                            'Use one character per image; a reference sheet is not a single camera view.']}
        return store.mutate(pid,apply,require_idle=True)

    @app.delete('/api/projects/{pid}/references/{rid}')
    def remove_reference(pid:str,rid:str):
        idle(pid)
        def change(p): p['references']=[r for r in p['references'] if r['id']!=rid]; invalidate(p,'pose')
        return store.mutate(pid,change,require_idle=True)

    @app.post('/api/projects/{pid}/mesh')
    async def import_mesh(pid:str,file:UploadFile=File(...)):
        idle(pid); data=await upload_bytes(file); suffix=Path(file.filename or '').suffix.lower()
        if suffix not in ('.glb','.stl','.ply'): raise HTTPException(422,'Use a self-contained GLB, STL or PLY')
        if suffix=='.glb':
            try: validate_glb_bytes(data)
            except (ValueError,GeometryError) as exc: raise HTTPException(422,str(exc)) from exc
        root=store.project_dir(pid); directory=root/'imports'; directory.mkdir(exist_ok=True)
        path=directory/(uid()+suffix); path.write_bytes(data)
        source={'path':str(path.relative_to(root)),'sha256':file_hash(path),'provider':'manual-import','name':Path(file.filename).name,
                'pose_bypassed':True}
        def apply(p): invalidate(p,'mesh'); p['source']=source
        store.mutate(pid,apply,require_idle=True)
        return runner.submit(pid,JobRequest(operation='inspect').model_dump())

    @app.post('/api/projects/{pid}/demo')
    def demo(pid:str):
        idle(pid); root=store.project_dir(pid); directory=root/'imports'; directory.mkdir(exist_ok=True)
        path=directory/(uid()+'.glb'); shutil.copyfile(config.root/'examples/teddy-source.glb',path)
        def apply(p):
            invalidate(p,'mesh'); p['source']={'path':str(path.relative_to(root)),'sha256':file_hash(path),'provider':'procedural-demo','pose_bypassed':True}
        store.mutate(pid,apply,require_idle=True)
        return runner.submit(pid,JobRequest(operation='inspect').model_dump())

    @app.post('/api/projects/{pid}/jobs')
    def job_create(pid:str,body:JobRequest): return runner.submit(pid,body.model_dump())
    @app.get('/api/jobs/{jid}')
    def job(jid:str): return store.job(jid)
    @app.post('/api/jobs/{jid}/cancel')
    def cancel(jid:str):
        j=store.job(jid)
        if j['status'] not in ('queued','running'): raise Conflict('Job is not active')
        return store.update_job(jid,cancel_requested=True,message='Abbruch angefordert; ein externer Auftrag kann weiterlaufen')
    @app.post('/api/jobs/{jid}/resume')
    def resume(jid:str,body:JobRequest):
        j=store.job(jid)
        if j['status'] not in ('failed','interrupted','cancelled') or j['operation']!='reconstruct': raise Conflict('Only an interrupted/failed 3D remote task can be resumed')
        if not j['checkpoint'].get('remote_task_id'): raise Conflict('No known remote task ID; check the provider dashboard before resubmitting')
        body.operation='reconstruct'
        return runner.submit(j['project_id'],body.model_dump(),resume_task=j['checkpoint'])

    @app.post('/api/projects/{pid}/approve')
    def approval(pid:str,body:ApprovalRequest):
        idle(pid)
        return store.mutate(pid,lambda p:approve(p,body.stage,body.artifact_hash,body.warnings_acknowledged),require_idle=True)

    @app.post('/api/projects/{pid}/colors/recommend')
    def recommend_colors(pid:str):
        idle(pid); p=store.get(pid); p['artifacts'].pop('colors',None)
        artifact=build_colors(p,store.filaments())
        def apply(project): invalidate(project,'colors'); project['artifacts']['colors']=artifact
        return store.mutate(pid,apply,require_idle=True)

    @app.post('/api/projects/{pid}/colors')
    def colors(pid:str,body:ColorAssignment):
        idle(pid); p=store.get(pid); artifact=build_colors(p,store.filaments(),body.assignments)
        def apply(project): invalidate(project,'colors'); project['artifacts']['colors']=artifact
        return store.mutate(pid,apply,require_idle=True)

    @app.get('/api/projects/{pid}/files/{relative:path}')
    def asset(pid:str,relative:str):
        try: path=safe_asset_path(store.project_dir(pid),relative)
        except (ValueError,FileNotFoundError) as exc: raise HTTPException(404,'File not found') from exc
        allowed={'.png','.jpg','.webp','.glb','.3mf','.zip','.json','.md','.stl','.ply'}
        if path.suffix.lower() not in allowed: raise HTTPException(403,'File type is not exposed')
        media={'.glb':'model/gltf-binary','.3mf':'model/3mf','.json':'application/json','.md':'text/plain'}.get(path.suffix)
        return FileResponse(path,media_type=media,filename=path.name if path.suffix in ('.zip','.3mf','.glb') else None)

    @app.post('/api/calibration')
    def calibration(body:CalibrationRequest):
        from .services.calibration import create_calibration
        if not runner.geometry_lock.acquire(blocking=False):
            raise Conflict('The geometry worker is busy; finish the active construction first')
        try:
            directory=config.data_dir/'calibration'/uid()
            result=create_calibration(directory,shape=body.shape,radius=body.radius_mm,length=body.length_mm)
            return FileResponse(directory/result['bundle'],media_type='application/zip',filename='figuraforge-passung.zip')
        finally:
            runner.geometry_lock.release()

    @app.get('/api/filaments')
    def filaments(): return store.filaments()
    @app.post('/api/filaments')
    def filament(body:Filament): store.save_filaments([body.model_dump()]); return body
    @app.delete('/api/filaments/{ident}')
    def delete_filament(ident:str): store.delete_filament(ident); return {'ok':True}
    @app.get('/api/filaments/match/{color}')
    def match(color:str,owned:bool=False):
        try: return rank_filaments('#'+color.lstrip('#'),store.filaments(),owned_only=owned)
        except ValueError as exc: raise HTTPException(422,str(exc)) from exc
    @app.post('/api/filaments/import')
    async def import_filaments(request:Request):
        raw=await request.body()
        if len(raw)>20*1024*1024: raise HTTPException(413,'Catalog exceeds 20 MB')
        try:
            body=json.loads(raw); data=body.get('data'); mode=body.get('format','figuraforge')
            rows=normalize_spoolmandb(data) if mode=='spoolmandb' else normalize_spoolman(data) if mode=='spoolman' else data
            if not isinstance(rows,list) or len(rows)>30000: raise ValueError('Expected a list of at most 30000 entries')
            rows=[Filament.model_validate(x).model_dump() for x in rows]; store.save_filaments(rows)
        except (ValueError,TypeError) as exc: raise HTTPException(422,'Invalid filament catalog: '+str(exc)[:200]) from exc
        return {'imported':len(rows)}
    @app.post('/api/filaments/sync-spoolmandb')
    def sync_catalog():
        # Fixed destination only; no arbitrary server-side URL-fetch endpoint.
        url='https://donkie.github.io/SpoolmanDB/filaments.json'
        try:
            validate_public_url(url,allowed_domains=['donkie.github.io'])
            with httpx.Client(timeout=45,follow_redirects=False,trust_env=False) as client:
                with client.stream('GET',url) as response:
                    response.raise_for_status(); chunks=[]; size=0
                    for chunk in response.iter_bytes():
                        size+=len(chunk)
                        if size>20*1024*1024: raise ValueError('Catalog exceeds limit')
                        chunks.append(chunk)
                data=json.loads(b''.join(chunks))
            rows=normalize_spoolmandb(data)
            # Retain per-user allowed/owned flags across updates.
            old={f['id']:f for f in store.filaments()}
            for r in rows:
                for k in ('owned','allowed','lab_d65','measured'):
                    if k in old.get(r['id'],{}): r[k]=old[r['id']][k]
            store.save_filaments(rows)
        except Exception as exc: raise HTTPException(502,'Catalog sync failed. Import a downloaded JSON catalog instead.') from exc
        return {'imported':len(rows),'availability':'Catalog colors only; no live stock or prices'}

    if config.frontend.exists(): app.mount('/',StaticFiles(directory=config.frontend,html=True),name='web')
    return app


app=create_app()
