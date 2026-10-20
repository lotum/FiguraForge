"""Source-bound local construction proposals; no approvals or provider calls."""
from __future__ import annotations
import json
from ..db import Conflict
from ..security import safe_asset_path
from .workflow import file_hash


def available_presets(project):
    from . import mochi_pipeline as original,mochi_detail_pipeline as detail,pip_pipeline as pip,buddy_pipeline as buddy
    mesh=project.get('artifacts',{}).get('mesh',{});settings=project['settings']
    for binding in (original,detail,pip,buddy):
        if (mesh.get('source',{}).get('sha256')==binding.SOURCE_SHA256 and mesh.get('hash')==binding.MESH_HASH
                and settings['height_mm']==(1000 if binding is buddy else 180) and settings['up_axis']=='Y'
                and settings['printer_id']=='h2d-dual'):
            if binding is buddy:
                return [{'id':buddy.PRESET,'title':'Anatomische Buddy-Bauteile vorschlagen','description':'1000-mm-Buddy mit ganzen Ohren, Schwanzansatz und Halsband-Montagefolge; 37 Teile, Klebeaugen und 0,05 mm Radialspiel. Physische Großmontage offen.'}]
            if binding is pip:
                return [{'id':pip.PRESET,'title':'Anatomische Pip-Bauteile vorschlagen','description':'Zehn Teile: Kiefer, Rumpffront, Boden, Schwanzunterseite und steckbare Augen. 0,05 mm Radialspiel, lokale Montagefolge geprueft; Druck/Passung offen.'}]
            return [{'id':binding.PRESET,'title':'Anatomische Bauteile vorschlagen'+(' · Augendetails V2' if binding is detail else ''),
                     'description':'Ganze Ohren, Schwanzansatz und vollständige Nase; vier kleine Augen zum Kleben. Lokal, ohne Cloudkosten.'}]
    return []


def read_reference(root, artifact, *, construction=False):
    key='construction_reference_document' if construction else 'reference_document'
    checksum='construction_reference_sha256' if construction else 'reference_sha256'
    path_value=artifact.get(key)
    if path_value is None:
        path_value=artifact.get('reference_document',artifact['document'])
        checksum='reference_sha256'
    path=safe_asset_path(root,path_value)
    if artifact.get(checksum) and file_hash(path)!=artifact[checksum]:
        raise Conflict('Unveraenderliche Planreferenz wurde geaendert; erneut planen.')
    return json.loads(path.read_text()),path_value,file_hash(path)


def prepare_proposal(project, root, document, filaments):
    from ..geometry.io import load_surface
    from ..models import ColorPlanDocument
    options=available_presets(project)
    if not options:
        raise Conflict('Fuer dieses Mesh und diesen Massstab liegt noch kein gepruefter anatomischer Konstruktionsvorschlag vor.')
    if options[0]['id']=='buddy-anatomical-v1':
        from .buddy_pipeline import suggest_buddy_plan as suggest_mochi_plan
    elif options[0]['id']=='pip-anatomical-v1':
        from .pip_pipeline import suggest_pip_plan as suggest_mochi_plan
    elif options[0]['id']=='mochi-anatomical-detail-v2':
        from .mochi_detail_pipeline import suggest_mochi_detail_plan as suggest_mochi_plan
    else:from .mochi_pipeline import suggest_mochi_plan
    mesh=project['artifacts']['mesh'];artifact=project['artifacts']['plan']
    source=safe_asset_path(root,mesh['source']['path'])
    if file_hash(source)!=mesh['source']['sha256']:
        raise Conflict('Meshdatei wurde seit der Pruefung geaendert; erneut importieren.')
    reference,_,_=read_reference(root,artifact,construction=True)
    surface=load_surface(source,project['settings']['height_mm'],project['settings']['up_axis'])
    candidate,report=suggest_mochi_plan(surface,reference,project['settings'],mesh['hash'],filaments,current_plan=document)
    return ColorPlanDocument.model_validate(candidate).model_dump(),report


def validate_preset_geometry(candidate, proposed):
    """A fixed verified kernel must never silently ignore brush/group edits."""
    if candidate['face_regions']!=proposed['face_regions']:
        raise Conflict('Die anatomischen Schnittmasken wurden geaendert. Fuer freie Schnitte zuerst den Anatomieentwurf aufheben.')
    keys=('id','strategy','part_group','cut_type')
    actual={r['id']:tuple(r[k] for k in keys) for r in candidate['regions']}
    expected={r['id']:tuple(r[k] for k in keys) for r in proposed['regions']}
    if actual!=expected:
        raise Conflict('Bauteilgruppen oder Schnittarten passen nicht zum Anatomieentwurf. Farbtechnik und Farben bleiben editierbar.')
