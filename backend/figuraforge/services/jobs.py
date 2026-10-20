from __future__ import annotations
import json
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from ..db import Conflict,digest,uid
from ..geometry.io import validate_glb_bytes
from ..providers.images import OpenAIImages,GeminiImages,pose_prompt
from ..providers.meshy import Meshy,mesh_target_for_budget
from ..providers.tripo import Tripo
from ..providers.local import LocalGateway
from ..providers.review import OpenAIReview
from ..providers.planning import OpenAIPlanner
from ..providers.base import ProviderError,save_b64_image
from .workflow import require_approval,invalidate,file_hash,build_colors,write_json,advice_basis
from .native_jobs import run_native


class Cancelled(RuntimeError): pass


def validate_advice_plan_draft(document,project):
    from ..models import ColorPlanDocument
    draft=ColorPlanDocument.model_validate(document).model_dump()
    artifact=project['artifacts'].get('plan');mesh=project['artifacts'].get('mesh')
    if not artifact or not mesh or draft['mesh_hash']!=mesh['hash'] or draft['face_count']!=artifact['face_count'] or len(draft['face_regions'])!=artifact['face_count']:
        raise Conflict('Farbplan-Entwurf gehoert zu einer anderen Meshversion.')
    ids=[r['id'] for r in draft['regions']]
    if len(ids)!=len(set(ids)) or set(draft['face_regions'])-set(ids):
        raise Conflict('Ungueltige Bereichszuordnung im Farbplan-Entwurf.')
    return draft


def validate_plan_plate_capacity(project):
    """Reject a declared multi-spool part before starting expensive geometry."""
    from .color_plan import is_mixed
    plan=project.get('artifacts',{}).get('plan')
    if not plan:return
    groups={}
    used=set(plan['face_regions']) if 'face_regions' in plan else None
    for region in plan.get('regions',[]):
        if (used is not None and region['id'] not in used) or (used is None and region.get('face_count')==0):
            continue
        key=('part',region.get('part_group') or region['id']+10001) if region['strategy']=='part' else ('body',0)
        ids=plan.get('filament_ids',[]) if is_mixed(region) else [region.get('filament_id')]
        groups.setdefault(key,set()).update(ident for ident in ids if ident)
    required=max((len(ids) for ids in groups.values()),default=0)
    capacity=project['settings']['colors_per_plate']
    if required>capacity:
        raise Conflict(f'Der Farbplan benötigt {required} reale Basisfilamente auf einer Platte. Im Schritt Konstruktion „Farben je Platte“ auf mindestens {required} setzen (aktuell {capacity}), bevor Bauteile berechnet werden.')


def color_export_inventory(colors,inventory):
    """Bind native export to every approved physical spool, including mixed bases."""
    from copy import deepcopy
    snapshots={}
    candidates=list(colors.get('filaments',{}).values())
    for planned in colors.get('planned_materials',{}).values():
        rows=planned.get('filaments',[])
        if set(planned.get('filament_ids',[]))!={row['id'] for row in rows}:
            raise Conflict('Gespeicherte Filamentzuordnung ist unvollständig. Im Schritt Filamente neu zuordnen und speichern.')
        candidates.extend(rows)
    current={row['id']:row for row in inventory}
    for snapshot in candidates:
        ident=snapshot['id']
        if ident in snapshots and snapshots[ident]!=snapshot:
            raise Conflict('Gespeicherte Filamentzuordnungen widersprechen sich. Im Schritt Filamente neu zuordnen und speichern.')
        snapshots[ident]=snapshot
        if current.get(ident)!=snapshot:
            label=snapshot.get('name',ident)
            raise Conflict(f'Filament „{label}“ wurde seit der Zuordnung geändert oder entfernt. Im Schritt Filamente neu zuordnen und speichern; danach erneut exportieren.')
    # Freeze the exact checked values before the potentially queued worker starts.
    return deepcopy(inventory)


class Runner:
    """One durable record per job; worker execution is single-process, not distributed.

    On restart, in-flight operations are marked interrupted, never blindly billed again.
    Remote task IDs are checkpointed and can be resumed explicitly.
    """
    def __init__(self,store,vault,config):
        self.store=store; self.vault=vault; self.config=config
        self.pool=ThreadPoolExecutor(max_workers=2,thread_name_prefix='figuraforge')
        self.geometry_lock=threading.Lock()
        self.stopping=threading.Event()

    def shutdown(self):
        self.stopping.set()
        self.pool.shutdown(wait=False,cancel_futures=True)

    def submit(self,project_id,request,resume_task=None):
        p=self.store.get(project_id); op=request['operation']; s=p['settings']
        if op=='advise' and not request.get('advice_stage'): raise Conflict('Schritt fuer den KI-Vorschlag fehlt')
        if op in ('pose','review_pose','reconstruct','rig','advise'):
            if not request.get('confirm_cloud_upload') and not (op=='reconstruct' and s['mesh_provider']=='local'):
                raise Conflict('Explicit consent to upload references to the selected cloud provider is required')
        if op=='pose' and not p['references']: raise Conflict('Upload character reference images first')
        if op=='reconstruct': require_approval(p,'pose')
        if op=='segment':
            require_approval(p,'mesh');validate_plan_plate_capacity(p)
        if op in ('plan','preview') and not p['artifacts'].get('mesh'):raise Conflict('Zuerst ein 3D-Modell pruefen.')
        if op=='export':
            require_approval(p,'colors');color_export_inventory(p['artifacts']['colors'],self.store.filaments())
        if op=='review_pose' and not p['artifacts'].get('pose'): raise Conflict('Generate pose views first')
        if op=='inspect' and not p.get('source'): raise Conflict('Import or generate a source mesh first')
        if op=='rig': raise Conflict('Rigging is reserved as an extension point, not enabled in this release. Import a posed GLB instead.')
        if op in ('pose','review_pose','reconstruct','advise'):
            provider=('openai' if op in ('review_pose','advise') else s['image_provider'] if op=='pose' else s['mesh_provider']).replace('-legacy','')
            if provider!='local' and not self.vault.get(provider): raise Conflict(f'Configure the {provider} API key first')
        request=dict(request);draft=request.pop('advice_plan_document',None)
        if draft is not None:
            if op!='advise' or request.get('advice_stage')!='plan':raise Conflict('Farbplan-Entwurf ist nur fuer die Farbplan-KI erlaubt')
            draft=validate_advice_plan_draft(draft,p)
        j=self.store.new_job(project_id,op,request)
        state=dict(resume_task or {})
        if draft is not None:
            root=self.store.project_dir(project_id);out=root/'runs'/j['id'];out.mkdir(parents=True,exist_ok=True)
            path=out/'advice-plan-draft.json';write_json(path,draft)
            state['plan_draft']={'document':str(path.relative_to(root)),'sha256':file_hash(path),'hash':digest(draft)}
        if state:self.store.update_job(j['id'],checkpoint=state)
        self.pool.submit(self.run,j['id'])
        return self.store.job(j['id'])

    def run(self,job_id):
        j=self.store.job(job_id); pid=j['project_id']; root=self.store.project_dir(pid)
        out=root/'runs'/job_id; out.mkdir(parents=True,exist_ok=True)
        self.store.update_job(job_id,status='running',message='Gestartet')
        self.store.event(pid,'job',f"{j['operation']}: gestartet")
        clients=[]
        def progress(message):
            if self.stopping.is_set(): raise Cancelled('Server shutdown requested; local worker stopped')
            if self.store.job(job_id).get('cancel_requested'):
                local=j['operation'] in ('inspect','segment','export','plan','preview')
                raise Cancelled('Lokale Berechnung abgebrochen; keine API-Kosten.' if local else 'Auftrag lokal abgebrochen; ein bereits gestarteter Anbieterauftrag kann weiterlaufen und Kosten verursachen.')
            self.store.update_job(job_id,message=str(message))
        def checkpoint(**items):
            old=self.store.job(job_id)['checkpoint']; old.update(items)
            self.store.update_job(job_id,checkpoint=old)
        def provider(cls,key):
            obj=cls(self.vault.get(key),progress=progress,checkpoint=checkpoint)
            def record_error(response):
                directory=out/'provider-errors'; directory.mkdir(exist_ok=True)
                path=directory/(uid()+'.enc')
                # Retain response diagnostics encrypted, never request headers or images.
                record={'status':response.status_code,'provider':key,
                        'request_id':response.headers.get('x-request-id'),
                        'body':response.text[:2_000_000]}
                path.write_bytes(self.vault.cipher.encrypt(json.dumps(record).encode()))
                checkpoint(provider_error_file=str(path.relative_to(root)))
            obj.error_recorder=record_error
            clients.append(obj); return obj
        def charge(amount,op):
            self.store.reserve(pid,job_id,amount,op,j['request'].get('budget_override',False))
        def rel(path): return str(Path(path).relative_to(root))
        def put(stage,artifact):
            def apply(p):
                invalidate(p,stage); p['artifacts'][stage]=artifact
            self.store.mutate(pid,apply)
        try:
            p=self.store.get(pid); s=p['settings']; op=j['operation']
            if op=='advise':
                stage=j['request']['advice_stage']
                progress('Astra analysiert Referenzen und Einstellungen; keine Generierung')
                context={'project':p['title'],'settings':s,'user_briefing':j['request'].get('advice_prompt',''),
                         'quality':p['artifacts'].get('mesh',{}).get('quality'),
                         'construction_readiness':p['artifacts'].get('mesh',{}).get('construction_readiness'),
                         'parts':[{'id':part['id'],'name':part['name'],'dimensions_mm':part['dimensions_mm'],'color':part['color'],
                                   'filament_id':p['artifacts'].get('colors',{}).get('assignments',{}).get(part['id'])} for part in p['artifacts'].get('segments',{}).get('parts',[])],
                         'filaments':[{k:f.get(k) for k in ('id','brand','name','material','hex','measured')}
                                      for f in self.store.filaments() if f.get('allowed',True) and (not s['owned_filaments_only'] or f.get('owned'))][:100] if stage in ('colors','plan') else []}
                if stage=='plan':
                    artifact=p['artifacts'].get('plan')
                    if not artifact:raise Conflict('Zuerst einen lokalen Farbplan erstellen.')
                    draft_info=j.get('checkpoint',{}).get('plan_draft')
                    if draft_info:
                        from ..security import safe_asset_path
                        path=safe_asset_path(root,draft_info['document'])
                        if file_hash(path)!=draft_info['sha256']:raise Conflict('Farbplan-Entwurf wurde veraendert.')
                        document=validate_advice_plan_draft(json.loads(path.read_text()),p)
                        if digest(document)!=draft_info['hash']:raise Conflict('Farbplan-Entwurf ist nicht mehr identisch.')
                    else:document=json.loads((root/artifact['document']).read_text())
                    context['color_plan']={k:v for k,v in document.items() if k!='face_regions'}
                images=[root/r['path'] for r in p['references'][:2]]+[root/v['path'] for v in p['artifacts'].get('pose',{}).get('views',[])[:4]]
                screenshot=j['request'].get('advice_view_png')
                if screenshot:
                    if not screenshot.startswith('data:image/png;base64,'): raise Conflict('Vorschau muss ein PNG sein')
                    view=out/'advice-view.png';save_b64_image(screenshot.split(',',1)[1],view)
                    images=[view]+images[:5]
                planner=provider(OpenAIPlanner,'openai')
                charge(s['review_call_estimate_eur'],'AI settings suggestion (estimate, not invoice)')
                proposal=planner.suggest(stage,context,images,s.get('advice_model','gpt-6-astra'))
                if stage=='plan':
                    from ..providers.planning import apply_region_suggestion
                    from .color_plan import validate_plan
                    candidate=apply_region_suggestion(document,proposal.get('region_changes',[]),proposal.get('filament_ids',document['filament_ids']))
                    validate_plan(candidate,p['artifacts']['mesh']['hash'],artifact['face_count'],s,self.store.filaments())
                    proposal['plan_hash']=artifact['hash']
                    if draft_info:proposal['plan_draft']=dict(draft_info)
                if stage=='colors':
                    from copy import deepcopy
                    from ..models import Settings
                    from ..providers.planning import advice_assignments
                    from .workflow import apply_settings
                    candidate_project=deepcopy(p);candidate_settings=dict(s)
                    for change in proposal['changes']:candidate_settings[change['key']]=change['after']
                    apply_settings(candidate_project,Settings.model_validate(candidate_settings).model_dump())
                    assignments=advice_assignments(proposal.get('assignments',[]),p['artifacts'].get('segments',{}).get('parts',[]))
                    build_colors(candidate_project,self.store.filaments(),assignments)
                proposal['user_briefing']=j['request'].get('advice_prompt','')
                proposal['settings_hash']=digest(s)
                proposal['basis_hash']=advice_basis(p)
                self.store.mutate(pid,lambda project:project.setdefault('suggestions',{}).update({stage:proposal}))
            elif op in ('pose','review_pose'):
                refs=[root/r['path'] for r in p['references']]
                if op=='review_pose':
                    charge(s['review_call_estimate_eur'],'visual review')
                    critic=provider(OpenAIReview,'openai')
                    views=[root/v['path'] for v in p['artifacts']['pose']['views']]
                    report=critic.review(refs,views,s['prompt'],s['review_model'],s['review_effort'])
                    def attach(project): project['artifacts']['pose']['review']=report
                    self.store.mutate(pid,attach)
                else:
                    cls=OpenAIImages if s['image_provider']=='openai' else GeminiImages
                    image=provider(cls,s['image_provider'].replace('-legacy',''))
                    critic=provider(OpenAIReview,'openai') if s['review_model'] else None
                    prompt=s['prompt']; last=None
                    for attempt in range(s['auto_image_retries']+1):
                        views=[]; paths=[]
                        for index,view in enumerate(s['image_views']):
                            progress(f'Bildansicht {view}, Versuch {attempt+1}')
                            charge(s['image_call_estimate_eur'],f'image {view} attempt {attempt+1}')
                            path=out/f'pose-{attempt}-{view}.png'
                            references=([paths[0]]+refs[:13]) if paths else refs[:14]
                            kw={'model':s['image_model'],'quality':s['image_quality'],'size':s['image_size']}
                            if cls is GeminiImages: kw['legacy']=s['image_provider']=='gemini-legacy'
                            result=image.generate(pose_prompt(prompt,s['identity_notes'],view,bool(paths),s['model_type']),references,path,**kw)
                            paths.append(path); views.append({'view':view,'path':rel(path),'sha256':file_hash(path),'usage':result.get('usage')})
                            checkpoint(pose_views=list(views),pose_attempt=attempt+1)
                        report=None
                        if critic:
                            charge(s['review_call_estimate_eur'],'visual review')
                            report=critic.review(refs,paths,prompt,s['review_model'],s['review_effort'])
                        last={'views':views,'provider':s['image_provider'],'model':s['image_model'],'attempt':attempt+1,'review':report,
                              'warnings':['Generated views are inferred, not measured geometry. Please check identity and pose.']}
                        last['hash']=digest({'views':views,'prompt':s['prompt'],'identity':s['identity_notes']})
                        put('pose',last)
                        if not report or min(report['identity_score'],report['pose_score'],report['multiview_score'])>=85: break
                        prompt=s['prompt']+' Corrections from visual review: '+report['repair_instruction']
                        progress('Visuelle Pruefung fordert eine neue Kandidatenrunde an')
            elif op in ('reconstruct','inspect'):
                if op=='reconstruct':
                    cls={'meshy':Meshy,'tripo':Tripo,'local':LocalGateway}[s['mesh_provider']]
                    remote=provider(cls,s['mesh_provider'])
                    state=self.store.job(job_id)['checkpoint']; task=state.get('remote_task_id')
                    if task and state.get('provider')!=s['mesh_provider']: raise Conflict('Provider changed; cannot resume this remote task')
                    if task:
                        if state.get('pose_hash')!=p['artifacts']['pose']['hash']: raise Conflict('Pose changed; cannot resume a task for a different approved pose')
                    else:
                        if s['mesh_provider']!='local': charge(s['mesh_call_estimate_eur'],'3D generation')
                        checkpoint(pose_hash=p['artifacts']['pose']['hash'])
                        views=p['artifacts']['pose']['views']; images=[root/v['path'] for v in views]
                        model=s['mesh_model']
                        if cls is Tripo:
                            if model=='latest': model='v3.1-20260211'
                            task=remote.submit({v['view']:root/v['path'] for v in views},model=model)
                        elif cls is Meshy:
                            target=mesh_target_for_budget(s['max_refined_faces'],s.get('mesh_target_faces',150000))
                            checkpoint(target_polycount=target)
                            task=remote.submit(images,model=model,target_polycount=target)
                        else: task=remote.submit(images,model=model)
                    path=out/'generated.glb'
                    remote_result=(remote.poll(task,path,kind=state.get('remote_kind','multi-image-to-3d'))
                                   if cls is Meshy else remote.poll(task,path))
                    validate_glb_bytes(path.read_bytes())
                    source={'path':rel(path),'sha256':file_hash(path),'provider':s['mesh_provider'],'remote_task_id':task,
                            'model':s['mesh_model'],'credits':remote_result.get('credits',remote_result.get('consumed_credits')),'pose_hash':p['artifacts']['pose']['hash']}
                    self.store.mutate(pid,lambda project:project.update(source=source))
                else:
                    source=p['source']; path=root/source['path']
                    while source.get('original_source'):
                        source=source['original_source'];path=root/source['path']
                    if source.get('pose_hash') and source['pose_hash']!=p['artifacts'].get('pose',{}).get('hash'):
                        raise Conflict('Generated source belongs to a different pose. Generate a new mesh or explicitly re-import the source.')
                progress('Mesh laden, Einheiten normalisieren und Topologie pruefen')
                with self.geometry_lock:
                    result=run_native({'operation':'inspect','source':str(path.resolve()),'settings':s},out,progress)
                prepared=result.pop('prepared_source',None)
                if prepared:
                    path=Path(prepared)
                    source={'path':rel(path),'sha256':file_hash(path),'provider':'local-blender-decimate',
                            'original_source':source,'pose_hash':source.get('pose_hash'),
                            'preparation_report':rel(out/'preparation-quality.json')}
                artifact={'preview_format':'uv-texture-v1','hash':digest({'source':source['sha256'],'height':s['height_mm'],'up':s['up_axis']}),
                          'source':source,'preview':rel(out/'mesh-preview.json'),**result,'height_mm':s['height_mm']}
                self.store.mutate(pid,lambda project:project.update(source=source))
                put('mesh',artifact)
            elif op=='preview':
                mesh=p['artifacts']['mesh']
                with self.geometry_lock:
                    run_native({'operation':'preview','source':str((root/mesh['source']['path']).resolve()),'settings':s},out,progress)
                def update_preview(current):
                    if current['artifacts'].get('mesh',{}).get('hash')!=mesh['hash']:raise Conflict('Mesh wurde geaendert.')
                    current['artifacts']['mesh'].update(preview=rel(out/'mesh-preview.json'),preview_format='uv-texture-v1')
                self.store.mutate(pid,update_preview)
            elif op=='plan':
                mesh=p['artifacts']['mesh']
                with self.geometry_lock:
                    result=run_native({'operation':'plan','source':str((root/mesh['source']['path']).resolve()),
                        'mesh_hash':mesh['hash'],'settings':s},out,progress)
                put('plan',{**result,'validated':False,'document':rel(out/'color-plan.json'),
                    'reference_document':rel(out/'color-plan.json'),'reference_sha256':file_hash(out/'color-plan.json'),
                    'preview':rel(out/'plan-preview.json')})
            elif op=='segment':
                source=p['artifacts']['mesh']['source']; path=root/source['path']
                if file_hash(path)!=source['sha256']:
                    raise Conflict('Meshdatei wurde seit der Pruefung geaendert. Erneut importieren und pruefen.')
                with self.geometry_lock:
                    plan=p['artifacts'].get('plan')
                    document=json.loads((root/plan['document']).read_text()) if plan else None
                    if document and digest(document)!=plan['hash']:
                        raise Conflict('Gespeicherter Farbplan wurde ausserhalb der Anwendung geaendert. Erneut speichern.')
                    if plan and plan['mesh_hash']!=p['artifacts']['mesh']['hash']:raise Conflict('Farbplan ist veraltet.')
                    if document:
                        from .color_plan import validate_plan
                        document=validate_plan(document,p['artifacts']['mesh']['hash'],plan['face_count'],s,self.store.filaments())
                    construction_reference=None;color_reference=None
                    if plan and document and document.get('construction_preset'):
                        from .plan_presets import read_reference
                        construction_reference,_,_=read_reference(root,plan,construction=True)
                        color_reference,_,_=read_reference(root,plan)
                    result=run_native({'operation':'segment','source':str(path.resolve()),'settings':s,'color_plan':document,
                        'construction_reference_plan':construction_reference,'color_reference_plan':color_reference,
                        'inventory':self.store.filaments()},out,progress)
                artifact={'hash':digest({'mesh':p['artifacts']['mesh']['hash'],'settings':s,'parts':result['parts']}),
                          'plan_hash':p['artifacts'].get('plan',{}).get('hash'),**result,'parts_dir':rel(out/'parts'),'report':rel(out/'geometry-report.json'),
                          'regions':rel(out/'regions.glb'),'preview':rel(out/'parts-preview.json')}
                put('segments',artifact)
                fresh=self.store.get(pid); colors=build_colors(fresh,self.store.filaments())
                self.store.mutate(pid,lambda project:project['artifacts'].update(colors=colors))
            elif op=='export':
                seg=p['artifacts']['segments']; colors=p['artifacts']['colors']
                export_inventory=color_export_inventory(colors,self.store.filaments())
                if colors['segments_hash']!=seg['hash']: raise Conflict('Color approval refers to a previous part construction')
                plan_artifact=p['artifacts'].get('plan')
                export_plan=json.loads((root/plan_artifact['document']).read_text()) if plan_artifact else None
                mesh_source=p['artifacts']['mesh']['source']
                if file_hash(root/mesh_source['path'])!=mesh_source['sha256']:
                    raise Conflict('Meshdatei wurde seit der Konstruktion geaendert. Erneut importieren und bauen.')
                if export_plan and digest(export_plan)!=plan_artifact['hash']:
                    raise Conflict('Gespeicherter Farbplan wurde ausserhalb der Anwendung geaendert. Erneut speichern und bauen.')
                color_reference_plan=None
                if plan_artifact:
                    reference=root/plan_artifact.get('reference_document',plan_artifact['document'])
                    if plan_artifact.get('reference_sha256') and file_hash(reference)!=plan_artifact['reference_sha256']:
                        raise Conflict('Unveraenderliche Farbreferenz wurde geaendert; erneut planen.')
                    color_reference_plan=json.loads(reference.read_text())
                template=p.get('bambu_template')
                if template and file_hash(root/template['path'])!=template['sha256']:
                    raise Conflict('Native Profilvorlage wurde geaendert. Vorlage erneut importieren und pruefen.')
                if export_plan:
                    if seg.get('plan_hash')!=plan_artifact['hash']:raise Conflict('Farbplan wurde nach der Konstruktion geaendert. Bauteile erneut bauen.')
                    used=set(export_plan['face_regions']);groups={}
                    for region in export_plan['regions']:
                        if region['id'] not in used:continue
                        group=('part',region.get('part_group') or region['id']+10001) if region['strategy']=='part' else ('core',0)
                        groups.setdefault(group,set()).add(region.get('filament_id') or region['color'].upper())
                    from .color_plan import is_mixed
                    requires_native=any(is_mixed(r) and r['id'] in used for r in export_plan['regions']) or any(len(v)>1 for v in groups.values())
                    if requires_native and not template:raise Conflict('Mixed Filament oder mehrfarbige Bauteile brauchen eine native Bambu-H2D-3MF-Vorlage. Einfarbiger Ersatzexport wurde blockiert.')
                progress('3MF-Volumen schreiben und Export erneut einlesen')
                with self.geometry_lock:
                    result=run_native({'operation':'export','parts_dir':str((root/seg['parts_dir']).resolve()),
                        'parts':seg['parts'],'filaments':colors['filaments'],'plates':colors.get('plates',seg['plates']),
                        'color_plan':export_plan,'color_reference_plan':color_reference_plan,
                        'native_template':str((root/template['path']).resolve()) if template else None,
                        'inventory':export_inventory,'source':str((root/p['artifacts']['mesh']['source']['path']).resolve()) if export_plan else None,'settings':s,
                        'manifest':{'project':p['title'],'project_id':pid,'approvals':p['approvals'],'colors':colors,
                            'source_sha256':p['source']['sha256'],'geometry_report':seg['geometry_report'],
                            'warnings':seg['warnings']+colors['warnings']}},out,progress)
                artifact={'hash':digest({'segments':seg['hash'],'colors':colors['hash'],'bundle':file_hash(out/'export'/result['bundle'])}),
                          'directory':rel(out/'export'),'bundle':rel(out/'export'/result['bundle']),**result}
                artifact['bundle']=rel(out/'export'/result['bundle']); put('export',artifact)
            else: raise Conflict('Unsupported operation')
            progress('Abgeschlossen')
            self.store.update_job(job_id,status='succeeded',message='Abgeschlossen')
            self.store.event(pid,'success',f'{op}: abgeschlossen')
        except Cancelled as exc:
            self.store.update_job(job_id,status='cancelled',error=str(exc),message='Abgebrochen')
            self.store.event(pid,'cancelled',str(exc))
        except Exception as exc:
            # Do not persist raw provider responses, reference bytes or secrets in logs.
            message=str(exc)[:1200]
            for provider_name in ('openai','gemini','meshy','tripo','local'):
                key=self.vault.get(provider_name)
                if key: message=message.replace(key,'[REDACTED]')
            self.store.update_job(job_id,status='failed',error=message,message='Pruefung / Verarbeitung fehlgeschlagen',
                                  ambiguous_submission=bool(getattr(exc,'ambiguous',False)))
            self.store.event(pid,'error',message)
        finally:
            for client in clients: client.client.close()
