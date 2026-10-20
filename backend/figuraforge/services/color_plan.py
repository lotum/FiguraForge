"""Local, editable surface decisions before any part construction.

Face indexes refer to the inspected working copy, never a screen projection.
Every edit is bound to the mesh and previous plan hash and saved separately.
"""
from pathlib import Path
import base64
import json
import numpy as np
from ..db import Conflict,digest
from ..geometry.colors import choose_palette,classify,hex_rgb,rgb_hex,delta_e_2000,srgb_to_lab
from ..geometry.preview import mesh_preview
from .workflow import write_json

STRATEGY_COLORS={'body':'#728197','part':'#00B2FF','mixed':'#CFFF00'}


def is_mixed(region):
    """Color technique is orthogonal to construction; accept old saved plans."""
    return region.get('color_mode')=='mixed' or region.get('strategy')=='mixed'


def suggest_plan(surface,settings,mesh_hash):
    samples=surface.sample(); palette=settings['palette'] or choose_palette(samples,settings['palette_size'],weights=surface.mesh.area_faces)
    labels=classify(samples,palette);areas=surface.mesh.area_faces
    # Weighted palette reduction can swallow tiny black eyes/nose. Reserve a
    # neutral very-dark region rather than painting those details brown.
    lab=srgb_to_lab(samples)
    dark=(lab[:,0]<22)&(np.linalg.norm(lab[:,1:],axis=1)<12)
    if dark.any() and not any(srgb_to_lab(hex_rgb(c))[0]<22 for c in palette):
        labels[dark]=len(palette)
        palette=[*palette,rgb_hex(np.median(samples[dark],axis=0))]
    dominant=int(np.bincount(labels,weights=areas,minlength=len(palette)).argmax())
    regions=[]
    for index,color in enumerate(palette):
        mask=labels==index
        if not mask.any():continue
        distance=float(delta_e_2000(srgb_to_lab(hex_rgb(color)),srgb_to_lab(hex_rgb(palette[dominant]))))
        color_mode='mixed' if index!=dominant and distance<20 else 'solid'
        strategy='body' if index==dominant or color_mode=='mixed' else 'part'
        regions.append({'id':index,'name':f'Farbbereich {index+1}','strategy':strategy,'color_mode':color_mode,'color':color,'cut_type':'inlay','part_group':0,'filament_id':None,
            'reason':'Grundfarbe mit groesster Oberflaeche' if index==dominant else
                     'Aehnliche Toene: Verlauf pruefen' if color_mode=='mixed' else 'Deutlicher Farbwechsel: Einzelteil pruefen',
            'face_count':int(mask.sum()),'area_mm2':round(float(areas[mask].sum()),2)})
    return {'version':1,'mesh_hash':mesh_hash,'face_count':len(labels),'face_regions':labels.tolist(),
        'regions':regions,'nozzle_count':2 if settings['printer_id']=='h2d-dual' else 1,
        'filament_ids':[],'ratio_step_percent':5,
        'note':'Lokaler Farbvorschlag, keine anatomische Erkennung. Gleiche Farben koennen mehrere getrennte Stellen umfassen. Mit dem Pinsel eigene Bereiche markieren.'}


def validate_plan(document,mesh_hash,face_count,settings,filaments):
    from ..models import ColorPlanDocument
    plan=ColorPlanDocument.model_validate(document).model_dump()
    if plan['mesh_hash']!=mesh_hash or plan['face_count']!=face_count or len(plan['face_regions'])!=face_count:
        raise Conflict('Farbplan gehoert zu einer anderen Meshversion. Neu planen.')
    ids=[r['id'] for r in plan['regions']]
    if len(set(ids))!=len(ids) or set(plan['face_regions'])-set(ids):raise Conflict('Ungueltige Bereichszuordnung')
    if settings['printer_id']=='h2d-dual' and plan['nozzle_count']>2:raise Conflict('H2D erlaubt hoechstens zwei Duesen.')
    if settings['printer_id']=='h2d-single' and plan['nozzle_count']!=1:raise Conflict('Einzelduesen-Profil hat eine Duese.')
    selected=plan['filament_ids']; byid={f['id']:f for f in filaments}
    if len(set(selected))!=len(selected) or len(selected)>min(2,plan['nozzle_count']):raise Conflict('Farbverlauf verwendet maximal zwei Basisfilamente und nicht mehr als vorhandene Duesen.')
    for ident in selected:
        f=byid.get(ident)
        if not f or not f.get('allowed',True) or settings['owned_filaments_only'] and not f.get('owned'):
            raise Conflict('Basisfilament fehlt oder ist durch den Bestandsfilter gesperrt.')
    used=set(plan['face_regions']); mixed=any(is_mixed(r) and r['id'] in used for r in plan['regions'])
    if mixed and len(selected)!=2:raise Conflict('Fuer markierte Verlaeufe zwei Basisfilamente auswaehlen.')
    if len(selected)==2 and byid[selected[0]]['material'].casefold()!=byid[selected[1]]['material'].casefold():
        raise Conflict('Mixed Filament braucht zueinander passende Materialien; verschiedene Materialarten werden nicht automatisch kombiniert.')
    if mixed and len(selected)==2:
        # The base left unassigned by the local draft uses one of the selected
        # physical spools; its target HEX must not masquerade as a third spool.
        # An explicit user assignment is always retained and checked below.
        for region in plan['regions']:
            if region['strategy']=='body' and not is_mixed(region) and not region.get('filament_id'):
                target=srgb_to_lab(hex_rgb(region['color']))
                region['filament_id']=min(selected,key=lambda ident:float(delta_e_2000(target,srgb_to_lab(hex_rgb(byid[ident]['hex'])))))
    groups={}
    for r in plan['regions']:
        if r['id'] not in used:continue
        group=('part',r['part_group'] or r['id']+10001) if r['strategy']=='part' else ('core',0)
        materials=set(selected) if is_mixed(r) else {r.get('filament_id') or r['color'].upper()}
        if r.get('filament_id'):
            f=byid.get(r['filament_id'])
            if not f or not f.get('allowed',True) or settings['owned_filaments_only'] and not f.get('owned'):
                raise Conflict('Ein Bereich verwendet ein nicht erlaubtes Filament.')
        groups.setdefault(group,set()).update(materials)
    cut_types={}
    for r in plan['regions']:
        if r['strategy']=='part' and r['id'] in used:
            cut_types.setdefault(r['part_group'] or r['id']+10001,set()).add(r['cut_type'])
    if any(len(v)>1 for v in cut_types.values()):raise Conflict('Alle Farben einer Bauteilgruppe muessen dieselbe Schnittart verwenden.')
    if any(len(v)>plan['nozzle_count'] for v in groups.values()):
        raise Conflict('Ein Bauteil benoetigt mehr Basisfilamente als Duesen vorhanden sind. Gruppe teilen oder Farben zuordnen.')
    return plan


def plan_preview(surface,plan):
    byid={r['id']:r for r in plan['regions']};labels=np.asarray(plan['face_regions'])
    colors=np.asarray([hex_rgb(byid[int(i)]['color']) for i in labels])
    preview=mesh_preview(surface.mesh,face_rgb=colors,name='Farbplan')
    preview['face_region_ids']=base64.b64encode(np.asarray(labels,dtype='<u4').tobytes()).decode()
    return {'format':'figuraforge-mesh-v1','unit':'millimeter','up_axis':'Z','meshes':[preview]}


def save_plan(directory,plan,preview):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    # Each directory is new. No original or previous plan is overwritten.
    write_json(directory/'color-plan.json',plan);write_json(directory/'plan-preview.json',preview)
    return digest(plan)


def construct_labels(surface,plan):
    """Mixed/base regions stay on the core; only explicit part regions are carved."""
    base=next((r['color'] for r in plan['regions'] if r['strategy']=='body'),'#AAAAAA')
    palette=[base];mapping={};groups={}
    for r in plan['regions']:
        if r['strategy']=='part':
            group=r.get('part_group') or r['id']+10001
            if group not in groups:groups[group]=len(palette);palette.append(r['color'])
            mapping[r['id']]=groups[group]
    if len(palette)>256:raise Conflict('Zu viele Bauteilgruppen.')
    ancestry=np.arange(len(surface.mesh.faces)) if surface.face_tags is None else surface.face_tags
    face_regions=np.asarray(plan['face_regions'])[ancestry]
    labels=np.asarray([mapping.get(int(i),0) for i in face_regions])
    return labels,palette


def whole_part_labels(plan):
    groups={};whole=set();next_label=1
    for r in plan['regions']:
        if r['strategy']!='part':continue
        key=r.get('part_group') or r['id']+10001
        if key not in groups:groups[key]=next_label;next_label+=1
        if r.get('cut_type','inlay')=='whole':whole.add(groups[key])
    return whole
