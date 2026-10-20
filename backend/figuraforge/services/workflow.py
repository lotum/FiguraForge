from __future__ import annotations
import hashlib
import json
from pathlib import Path
from ..db import Conflict,digest,now

STAGES=('pose','mesh','plan','segments','colors','export')
POSE_FIELDS={'prompt','identity_notes','image_provider','image_model','image_quality','image_size','image_views','model_type'}
MESH_FIELDS={'height_mm','up_axis','mesh_provider','mesh_model','mesh_target_faces'}
COLOR_FIELDS={'owned_filaments_only','preferred_brands'}
OPERATIONAL_FIELDS={'budget_eur','image_call_estimate_eur','mesh_call_estimate_eur','review_call_estimate_eur','review_model','review_effort','auto_image_retries','advice_model'}


def advice_basis(project):
    return digest({'settings':project['settings'],'references':project['references'],
                   'artifacts':{key:value.get('hash') for key,value in project['artifacts'].items()}})


def file_hash(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def invalidate(p,stage):
    start=STAGES.index(stage)
    for key in STAGES[start:]:
        p['artifacts'].pop(key,None)
        p['approvals'].pop(key,None)
    # A newly reconstructed/imported mesh has not been approved yet.
    if start<=3: p['approvals'].pop('colors',None)


def apply_settings(p,settings):
    from ..models import Settings
    previous=Settings.model_validate(p['settings']).model_dump()
    changed={k for k,v in settings.items() if previous.get(k)!=v}
    if changed & POSE_FIELDS: invalidate(p,'pose')
    elif changed & MESH_FIELDS:
        # Source bytes survive scaling or provider changes; inspection must be repeated.
        invalidate(p,'mesh')
    elif changed-COLOR_FIELDS-OPERATIONAL_FIELDS:
        invalidate(p,'plan' if changed & {'palette','palette_size','base_color'} else 'segments')
    elif changed & COLOR_FIELDS: invalidate(p,'colors')
    p['settings']=settings


def require_approval(p,stage):
    a=p['artifacts'].get(stage); approved=p['approvals'].get(stage)
    if not a or not approved or a.get('hash')!=approved.get('artifact_hash'):
        raise Conflict(f'Current {stage} approval is required')


def approve(p,stage,artifact_hash,warnings_acknowledged=False):
    a=p['artifacts'].get(stage)
    if not a or a['hash']!=artifact_hash: raise Conflict('Artifact changed. Review the current version before approving.')
    if a.get('warnings') and not warnings_acknowledged: raise Conflict('The displayed warnings must be acknowledged explicitly')
    if stage=='colors':
        require_approval(p,'mesh')
        if not p['artifacts'].get('segments'): raise Conflict('Construct the parts first')
        if not a.get('complete'): raise Conflict('Assign an allowed filament to every part first')
    p['approvals'][stage]={'artifact_hash':artifact_hash,'at':now(),'warnings_acknowledged':warnings_acknowledged}


def material_plates(plates,assignments,filaments,max_materials=1,planned_materials=None):
    """Keep approved placement coordinates; split a plate when real spools differ.

    Matching display RGB is not the same as sharing a filament/material. This
    prevents a two-nozzle plan from silently becoming a three-spool plate.
    """
    import copy
    output=[]
    for source in plates:
        if planned_materials:
            batches=[]
            for item in source['placements']:
                required=set(planned_materials[item['part_id']]['filament_ids'])
                if len(required)>max_materials:
                    raise Conflict('Ein Bauteil braucht mehr Basisfilamente als das Druckprofil erlaubt.')
                for batch in batches:
                    if len(batch[0]|required)<=max_materials:
                        batch[0].update(required);batch[1].append(item);break
                else:batches.append([required,[item]])
            for materials,items in batches:
                plate=copy.deepcopy(source)
                plate.update(id=len(output)+1,source_plate_id=source['id'],material_ids=sorted(materials),
                             physical_spool_count=len(materials),placements=copy.deepcopy(items))
                if 'material_batch' in plate:
                    plate['source_material_batch']=plate.pop('material_batch')
                plate['colors']=list(dict.fromkeys(filaments[item['part_id']]['hex'] for item in items))
                output.append(plate)
            continue
        groups={}
        for item in source['placements']:
            key=assignments.get(item['part_id'],'unassigned-'+item['part_id'])
            groups.setdefault(key,[]).append(item)
        keys=list(groups)
        for start in range(0,len(keys),max_materials):
            chosen=keys[start:start+max_materials]; plate=copy.deepcopy(source)
            plate.update(id=len(output)+1,source_plate_id=source['id'],material_ids=chosen,
                placements=[copy.deepcopy(item) for key in chosen for item in groups[key]])
            plate['colors']=list(dict.fromkeys(filaments[item['part_id']]['hex'] for item in plate['placements'] if item['part_id'] in filaments))
            output.append(plate)
    return output


def build_colors(p,filaments,assignments=None):
    from .filaments import rank_filaments
    segments=p['artifacts'].get('segments')
    if not segments: raise Conflict('No constructed parts are available')
    byid={f['id']:f for f in filaments}
    previous=p['artifacts'].get('colors',{}).get('assignments',{})
    selected=dict(previous if assignments is None else assignments)
    warnings=[]; choices={}; snapshots={}
    plan=p['artifacts'].get('plan',{})
    planned={}
    region_mapping=segments.get('part_region_ids') or segments.get('geometry_report',{}).get('construction',{}).get('part_region_ids')
    if region_mapping or plan.get('construction_preset') in ('mochi-anatomical-v1','mochi-anatomical-detail-v2'):
        from .color_plan import is_mixed
        regions={r['id']:r for r in plan['regions']}
        for part in segments['parts']:
            region_ids=region_mapping.get(part['id'],[]) if region_mapping else [part.get('color_index')]
            if not region_ids or any(ident not in regions for ident in region_ids):
                raise Conflict('Bauteil passt nicht mehr zum anatomischen Farbplan. Konstruktion erneuern.')
            part_regions=[regions[ident] for ident in region_ids]
            ids=[]
            for region in part_regions:
                required=list(plan.get('filament_ids',[])) if is_mixed(region) else [region.get('filament_id')]
                if not required or any(not ident for ident in required):
                    raise Conflict('Im Farbplan konkrete Basisfilamente zuordnen.')
                ids.extend(ident for ident in required if ident not in ids)
            if len(ids)>plan.get('nozzle_count',2):
                raise Conflict('Ein Bauteil benoetigt mehr Basisfilamente als verfuegbare Duesen. Farbplan oder Teilung anpassen.')
            planned[part['id']]={'color_mode':'mixed' if any(is_mixed(r) for r in part_regions) else 'solid',
                'filament_ids':ids,'region_ids':list(region_ids)}
    known={part['id'] for part in segments['parts']}
    if set(selected)-known: raise Conflict('Color assignments contain unknown part IDs')
    for part in segments['parts']:
        ranked=rank_filaments(part['color'],filaments,owned_only=p['settings']['owned_filaments_only'],preferred_brands=p['settings']['preferred_brands'])
        choices[part['id']]=ranked[:8]
        ident=selected.get(part['id'])
        if part['id'] in planned:
            ids=planned[part['id']]['filament_ids']
            # A single representative is needed by Core 3MF companions. The
            # native per-face export and UI retain every actual basis spool.
            ident=ids[0]
            if assignments is not None and selected.get(part['id'])!=ident:
                raise Conflict('Filamente dieses Bauteils im Farbplan bearbeiten; eine Einzelzuordnung wuerde den Verlauf verlieren.')
            selected[part['id']]=ident
            for basis_id in ids:
                basis=byid.get(basis_id)
                if not basis or not basis.get('allowed',True) or p['settings']['owned_filaments_only'] and not basis.get('owned'):
                    raise Conflict('Ein Basisfilament des Farbplans fehlt oder ist durch den Bestandsfilter gesperrt.')
            planned[part['id']]['filaments']=[dict(byid[basis_id]) for basis_id in ids]
        elif ident is None and assignments is None and ranked:
            ident=ranked[0]['id']; selected[part['id']]=ident
        if ident:
            if ident not in byid or not byid[ident].get('allowed',True): raise Conflict('Chosen filament is absent or blocked')
            f=byid[ident]
            if p['settings']['owned_filaments_only'] and not f.get('owned'): raise Conflict('Owned-only filter excludes a chosen filament')
            snapshots[part['id']]=dict(f)
            if not f.get('measured'): warnings.append('Catalog RGB colors are not calibrated physical color measurements.')
            if f.get('brand','').casefold()=='demo': warnings.append('The selected DEMO palette is not a purchasable filament. Replace it for a real print.')
    # Bind actual spool properties, not only mutable inventory IDs.
    plates=material_plates(segments['plates'],selected,snapshots,p['settings']['colors_per_plate'],planned)
    payload={'segments_hash':segments['hash'],'assignments':selected,'filaments':snapshots,'plates':plates}
    if planned:payload['planned_materials']=planned
    return {**payload,'hash':digest(payload),'recommendations':choices,
            'complete':known==set(snapshots),'warnings':sorted(set(warnings)),
            'preview_note':'Screen preview is an sRGB approximation, not a calibrated print proof.'}


def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf-8')
