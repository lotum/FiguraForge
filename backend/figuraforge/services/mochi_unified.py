"""Explicit local Mochi revision: one warm body, only black details detached.

This does not replace an existing project or weaken its source-bound preset.
The caller supplies a reviewed head surface and its exact V2 face ancestry.
"""
import numpy as np
from ..geometry.types import GeometryError
from ..geometry.surface_parts import make_surface_parts
from ..geometry.construct import make_inlays,face_components
from ..geometry.compare import nearest
from ..geometry.validation import validate_mesh
from ..geometry.planned_parts import _combined_checks
from ..geometry.packing import validate_packing
from ..geometry.topology import frame
from .mochi_detail_pipeline import create_detail_reference, BLACK, PAIR
from ..geometry.mochi_detail_masks import mochi_detail_masks
from ..geometry.colors import rgb_hex,srgb_to_lab

PRESET='mochi-unified-head-v1'
PERCENTAGES=(0,10,15,19,24,29,34,38,43,48,52,57,62,66,71,76,81,85,90,100)
KEYS=('body','nose','eye-1','eye-2','eye-3','eye-4')


def source_labels(v2,surface,ancestry):
    ancestry=np.asarray(ancestry)
    if (ancestry.shape!=(len(surface.mesh.faces),) or not np.issubdtype(ancestry.dtype,np.integer)
            or (ancestry<0).any() or (ancestry>=len(v2.mesh.faces)).any()):
        raise GeometryError('Kopfverfeinerung braucht gültige V2-Flächenherkunft.')
    masks,_=mochi_detail_masks(v2,create_detail_reference(v2))
    old=np.zeros(len(v2.mesh.faces),int)
    # The nose keeps its reviewed anatomical boundary. Eye silhouettes are
    # re-sampled from the refined original albedo, otherwise subdivision alone
    # would preserve the old coarse black/iris colour boundary unchanged.
    old[masks['nose']]=1
    labels=old[ancestry]
    lab=srgb_to_lab(surface.sample())
    dark=(lab[:,0]<22)&(np.linalg.norm(lab[:,1:],axis=1)<12)
    eyes=[];areas=surface.mesh.area_faces;centers=surface.mesh.triangles_center
    for ids in face_components(surface.mesh,dark):
        area=areas[ids].sum();center=np.average(centers[ids],axis=0,weights=areas[ids])
        if area>=3 and center[1]<-45 and 134<center[2]<145:eyes.append((center,ids))
    if len(eyes)!=4:raise GeometryError('Feinere Texturabtastung muss genau vier schwarze Augenregionen ergeben.')
    eyes.sort(key=lambda row:(row[0][0],row[0][2]))
    for ident,(_,ids) in enumerate(eyes,2):
        if labels[ids].any():raise GeometryError('Augenregion überschneidet die Nase.')
        labels[ids]=ident
    return labels


def make_plan(surface,labels,mesh_hash,stock):
    inventory={r['id']:r for r in stock}
    for ident in (*PAIR,BLACK):
        if ident not in inventory or not inventory[ident].get('owned') or not inventory[ident].get('allowed',True):
            raise GeometryError('Konkrete vorhandene Mochi-Spule fehlt oder ist gesperrt: '+ident)
    samples=surface.sample();regions=[]
    for i,key in enumerate(KEYS):
        mask=labels==i
        if not mask.any():raise GeometryError('Erwartete Schwarzregion fehlt: '+key)
        color=inventory[BLACK]['hex'] if i else rgb_hex(np.average(samples[mask],axis=0,weights=surface.mesh.area_faces[mask]))
        regions.append(dict(id=i,name='Mochi · ganzer Körper' if not i else 'Mochi · schwarze Nase' if i==1 else f'Mochi · schwarzer Augeneinsatz {i-1}',
            strategy='body' if not i else 'part',color_mode='mixed' if not i else 'solid',color=color,
            part_group=i,cut_type='whole' if i==1 else 'inlay',filament_id=BLACK if i else None,
            face_count=int(mask.sum()),area_mm2=float(surface.mesh.area_faces[mask].sum()),
            reason='Rumpf, Beine, Schwanz, Ohren und Kopf bleiben verbunden; nur schwarze Details separat.'))
    return dict(version=1,mesh_hash=mesh_hash,face_count=len(labels),face_regions=labels.tolist(),regions=regions,
                nozzle_count=2,filament_ids=list(PAIR),ratio_step_percent=5,construction_preset=PRESET,
                mixed_recipe_percentages=list(PERCENTAGES),
                note='20 Zielfarbwerte aus Beige31/Braun29; schwarze Nase und vier Augeneinsätze separat.')


def construct(surface,plan):
    labels=np.asarray(plan['face_regions']);regions=plan['regions']
    built,nose_report=make_surface_parts(surface.mesh,(labels==1).astype(int),[regions[0]['color'],regions[1]['color']],
        pin_radius_mm=1.5,pin_length_mm=3,pin_clearance_mm=.05,connector_shape='keyed',
        min_region_area_mm2=0,validate_paths=True)
    cores=[p for p in built if p.role=='body'];noses=[p for p in built if p.role!='body']
    if len(cores)!=1 or len(noses)!=1 or len(noses[0].connectors)!=1:
        raise GeometryError('Erwartet eine schwarze Stecknase und einen verbundenen Körper.')
    nose=noses[0];nose.id='nose';nose.name=regions[1]['name'];nose.color_index=1
    current=cores[0].mesh;dist,ids,_=nearest(surface,current.triangles_center)
    eye_labels=((dist<=.03)&(labels[ids]>=2)).astype(int)
    built,eye_report=make_inlays(current,eye_labels,[regions[0]['color'],regions[2]['color']],
        depth_mm=1,seam_mm=0,pin_radius_mm=1.5,pin_length_mm=1.5,pin_clearance_mm=.05,
        min_region_area_mm2=3,adaptive_small_pins=False,connector_mode='glue',validate_paths=True)
    bodies=[p for p in built if p.role=='body'];eyes=[p for p in built if p.role!='body']
    if len(bodies)!=1 or len(eyes)!=4:raise GeometryError('Erwartet genau vier schwarze Klebeeinsätze.')
    seen=set()
    for eye in eyes:
        d,ids,_=nearest(surface,eye.mesh.triangles_center)
        scores={i:int(np.sum((d<=1e-6)&(labels[ids]==i))) for i in range(2,6)}
        i=max(scores,key=scores.get)
        if not scores[i] or i in seen or eye.connectors:raise GeometryError('Augeneinsatz nicht eindeutig.')
        seen.add(i);eye.id=KEYS[i];eye.name=regions[i]['name'];eye.role='glue-inlay';eye.color_index=i
        eye.warnings.append('Klebeeinsatz ohne Stift; Passung und Kleberauftrag real prüfen.')
    body=bodies[0];body.id='body';body.name=regions[0]['name'];body.color_index=0
    parts=[body,nose,*sorted(eyes,key=lambda p:p.id)]
    quality={p.id:validate_mesh(p.mesh) for p in parts}
    if any(not q['valid'] or q['components']!=1 for q in quality.values()):
        raise GeometryError('Alle sechs Teile müssen geschlossene Einzelkörper sein.')
    checks=_combined_checks(parts,30)
    return parts,dict(quality=quality,combined_path_checks=checks,nose=nose_report,eyes=eye_report,
        pins=1,glue_parts=list(KEYS[2:]),body_includes=['torso','legs','head','ears','tail'],
        physical_fit_verified=False,physical_color_verified=False)


def pack(parts):
    """Separate two-spool single body and the one-spool black detail group."""
    lookup={p.id:p for p in parts};volume=(300,320,320)
    # Preserve the figure's upright pose; a bounding-box heuristic can put
    # the detailed face on supports even when the whole figure fits upright.
    mesh=lookup['body'].mesh;extent=mesh.extents;xy=(np.asarray(volume[:2])-extent[:2])/2
    tf=np.eye(4);tf[:3,3]=-mesh.bounds[0]+[*xy,0]
    body=dict(id=1,colors=[lookup['body'].color],volume_mm=list(volume),physical_spool_count=2,
        placements=[dict(part_id='body',transform=tf.tolist(),rect=[*xy.tolist(),*extent[:2].tolist()],height_mm=float(extent[2]),
            color=lookup['body'].color,orientation_reason='Aufrecht auf den Füßen; Gesicht nicht auf die Druckplatte legen.')])
    black=dict(id=2,colors=[lookup['nose'].color],placements=[],volume_mm=list(volume),physical_spool_count=1)
    x=35.;y=50.;gap=20.
    for key in KEYS[1:]:
        part=lookup[key];normal=np.asarray(part.assembly_direction)
        rotation=frame(-normal if key=='nose' else normal).T
        vv=part.mesh.vertices@rotation.T;low=vv.min(axis=0);extent=np.ptp(vv,axis=0)
        tf=np.eye(4);tf[:3,:3]=rotation;tf[:3,3]=-low+[x,y,0]
        black['placements'].append(dict(part_id=key,transform=tf.tolist(),rect=[x,y,*extent[:2].tolist()],height_mm=float(extent[2]),color=part.color))
        x+=extent[0]+gap
    plates=[body,black];proof=validate_packing(parts,plates)
    if not proof['passed']:raise GeometryError('Mochi-Einteilplatten passen nicht: '+str(proof))
    return plates
