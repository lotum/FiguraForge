"""Versioned local V2 source adoption: new files and snapshot, never old-file edits."""
from pathlib import Path
import json,shutil
from ..db import Conflict,digest,uid,now
from ..models import ColorPlanDocument
from ..security import safe_asset_path
from .workflow import file_hash,write_json,invalidate
from . import mochi_pipeline as v1,mochi_detail_pipeline as v2

CANDIDATE='benchmarks/mochi-eye-detail-20261016/weighted-eyes-150k.glb'
REVIEW='benchmarks/mochi-eye-detail-20261016/v2-draft-218d971813354ec1a4b70c7ce9f81fb4'


def prepare_adoption(project,root,config,filaments,request):
    """Prepare reviewable files; caller commits project state with revision/idle CAS."""
    mesh=project.get('artifacts',{}).get('mesh',{});old_plan=project.get('artifacts',{}).get('plan',{})
    if (project['revision']!=request.expected_revision or mesh.get('hash')!=request.expected_mesh_hash
            or old_plan.get('hash')!=request.expected_plan_hash):
        raise Conflict('Mesh, Farbplan oder Projekt wurde geaendert; aktuellen Stand laden.')
    settings=project['settings']
    if (mesh.get('hash')!=v1.MESH_HASH or mesh.get('source',{}).get('sha256')!=v1.SOURCE_SHA256
            or settings.get('height_mm')!=180 or settings.get('up_axis')!='Y' or settings.get('printer_id')!='h2d-dual'):
        raise Conflict('Dieser Detailentwurf gehoert nur zum geprueften Mochi-v1-Quellstand bei 180 mm/Y-up/H2D.')
    old_source=safe_asset_path(root,mesh['source']['path'])
    if not old_source.is_file() or file_hash(old_source)!=v1.SOURCE_SHA256:raise Conflict('Vorhandene Mochi-Quelle wurde geaendert; Uebernahme abgebrochen.')
    old_document=safe_asset_path(root,old_plan['document'])
    if not old_document.is_file():raise Conflict('Gespeicherter Farbplan fehlt; Uebernahme abgebrochen.')
    try:current=json.loads(old_document.read_text())
    except (OSError,ValueError):raise Conflict('Gespeicherter Farbplan ist unlesbar; Uebernahme abgebrochen.') from None
    if digest(current)!=old_plan['hash']:raise Conflict('Gespeicherter Farbplan wurde geaendert; Uebernahme abgebrochen.')
    candidate=config.root/CANDIDATE;review_dir=config.root/REVIEW
    if not candidate.is_file() or file_hash(candidate)!=v2.SOURCE_SHA256:
        raise Conflict('Die separat gepruefte lokale Detail-v2-Datei fehlt oder wurde geaendert.')
    try:verification=json.loads((review_dir/'verification.json').read_text())
    except (OSError,ValueError):raise Conflict('Der lokale Detail-v2-Pruefnachweis fehlt oder ist unlesbar.') from None
    construction=verification.get('construction',{});quality=construction.get('quality',{})
    if (verification.get('source_sha256')!=v2.SOURCE_SHA256 or verification.get('mesh_hash')!=v2.MESH_HASH
            or len(quality)!=9 or any(not q.get('valid') or q.get('components')!=1 for q in quality.values())
            or construction.get('pins')!=7 or len(construction.get('combined_path_checks',[]))!=10):
        raise Conflict('Der lokale Detail-v2-Konstruktionsnachweis ist unvollstaendig; keine Uebernahme.')
    from ..geometry.io import load_surface
    from ..geometry.preview import surface_preview
    from ..geometry.validation import validate_mesh
    from .color_plan import plan_preview,save_plan
    surface=load_surface(candidate,180,'Y');reference=v2.create_detail_reference(surface)
    new_settings=dict(settings,pin_clearance_mm=.05)
    canonical,proposal=v2.suggest_mochi_detail_plan(surface,reference,new_settings,v2.MESH_HASH,filaments,current_plan=current)
    canonical=ColorPlanDocument.model_validate(canonical).model_dump()
    token=uid();directory=root/'versions'/token;directory.mkdir(parents=True)
    snapshot=directory/'previous-project.json';write_json(snapshot,project)
    source_path=directory/'detail-source.glb';shutil.copyfile(candidate,source_path)
    if file_hash(source_path)!=v2.SOURCE_SHA256:raise Conflict('Lokale Dateikopie stimmt nicht mit dem geprueften Detailmesh ueberein.')
    write_json(directory/'construction-reference.json',reference)
    write_json(directory/'mesh-preview.json',surface_preview(surface))
    write_json(directory/'proposal.json',proposal)
    plan_dir=directory/'plan';plan_hash=save_plan(plan_dir,canonical,plan_preview(surface,canonical))
    relative=lambda p:p.relative_to(root).as_posix()
    source={'path':relative(source_path),'sha256':v2.SOURCE_SHA256,'provider':'local-weighted-eye-detail-v2','name':'Mochi – Augendetails V2.glb',
            'derived_from_source_sha256':v1.SOURCE_SHA256,'originals_preserved':True}
    mesh_artifact={'hash':v2.MESH_HASH,'source':source,'quality':validate_mesh(surface.mesh),
                   'preview':relative(directory/'mesh-preview.json'),'preview_format':'uv-texture-v1','height_mm':180,
                   'warnings':['Neue lokale Detailkopie; Mesh und Farben erneut pruefen. Vorhandene Originale und alter Projektstand sind gesichert.'],
                   'construction_readiness':{'ready':True,'construction_preset':v2.PRESET,
                                            'message':'Quellgebundener 9-Teile-Entwurf lokal geprueft; Druck-/Farb-/Passungsfreigaben separat.'}}
    plan_artifact={'hash':plan_hash,'mesh_hash':v2.MESH_HASH,'regions':canonical['regions'],'face_count':canonical['face_count'],
                   'filament_ids':canonical['filament_ids'],'nozzle_count':2,'construction_preset':v2.PRESET,'validated':True,
                   'document':relative(plan_dir/'color-plan.json'),'preview':relative(plan_dir/'plan-preview.json'),
                   'reference_document':relative(plan_dir/'color-plan.json'),'reference_sha256':file_hash(plan_dir/'color-plan.json'),
                   'construction_reference_document':relative(directory/'construction-reference.json'),
                   'construction_reference_sha256':file_hash(directory/'construction-reference.json')}
    history={'id':token,'at':now(),'snapshot':relative(snapshot),'old_mesh_hash':mesh['hash'],'old_plan_hash':old_plan['hash'],
             'new_mesh_hash':v2.MESH_HASH,'new_source_sha256':v2.SOURCE_SHA256,'automatic_approval':False,
             'reason':'Separately checked eye-detail source; .05-mm accepted radial starting fit; isolated support plates.'}
    return {'source':source,'mesh':mesh_artifact,'plan':plan_artifact,'settings':new_settings,'history':history}


def apply_adoption(current,prepared,request):
    if (current['revision']!=request.expected_revision
            or current['artifacts'].get('mesh',{}).get('hash')!=request.expected_mesh_hash
            or current['artifacts'].get('plan',{}).get('hash')!=request.expected_plan_hash):
        raise Conflict('Projekt wurde waehrend der Detailvorbereitung geaendert; keine Uebernahme.')
    invalidate(current,'mesh')
    current.update(source=prepared['source'],settings=prepared['settings'])
    current['artifacts'].update(mesh=prepared['mesh'],plan=prepared['plan'])
    current.setdefault('source_history',[]).append(prepared['history'])
