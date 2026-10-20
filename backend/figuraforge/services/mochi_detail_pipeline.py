"""Model-bound, offline Mochi proposal and anatomical construction kernel.

No filesystem, database, approval, cloud or printer side effects. The geometry
signature, 180-mm scale, immutable original four-color analysis and mesh hash
bind this preset to one inspected source. Other characters are never inferred
from a title. Returned geometry remains a draft pending physical fit/color QA.
"""
from __future__ import annotations
from copy import deepcopy
import numpy as np
from ..db import digest
from ..geometry.colors import rgb_hex
from ..geometry.compare import nearest
from ..geometry.mochi_detail_masks import mochi_detail_masks as mochi_masks,geometry_signature,REFERENCE_SIGNATURE
from ..geometry.construct import make_inlays
from ..geometry.surface_parts import make_surface_parts
from ..geometry.types import GeometryError
from ..geometry.validation import validate_mesh
from ..geometry.planned_parts import _combined_checks
from .color_plan import is_mixed

PRESET='mochi-anatomical-detail-v2'
MESH_HASH='8b3049e9f9bd3d0ad66be9d1be5e8ed9cae045fa246ff1fd06f63c6583fc3548'
SOURCE_SHA256='bdb9e145f308d7c9a1a6a49ba2111f1bbea658f1bfdf00f9ead2b353e50f29e7'
PART_KEYS=('body','nose','right-ear','left-ear','tail','eye-1','eye-2','eye-3','eye-4')
PAIR=('richard-inventory-202609-31','richard-inventory-202609-29')
BLACK='richard-inventory-202609-30'
NAMES={'body':'Mochi Grundkoerper','nose':'Mochi gesamte Nase – schwarz',
       'right-ear':'Mochi rechtes Ohr – ganze Ohrwurzel','left-ear':'Mochi linkes Ohr – ganze Ohrwurzel',
       'tail':'Mochi Schwanz – ganze Schwanzwurzel',
       **{f'eye-{i}':f'Mochi Augeneinsatz {i} – Klebeteil ohne Stift' for i in range(1,5)}}


def _guard(surface,reference_plan,settings,mesh_hash):
    if hasattr(reference_plan,'model_dump'):reference_plan=reference_plan.model_dump()
    if hasattr(settings,'model_dump'):settings=settings.model_dump()
    if mesh_hash!=MESH_HASH or reference_plan.get('mesh_hash')!=MESH_HASH:
        raise GeometryError('Mochi-Anatomievorschlag gehoert nur zur verifizierten Meshversion; eine andere Quelle braucht eine neue Pruefung.')
    if abs(float(settings.get('height_mm',0))-180)>1e-6 or settings.get('up_axis')!='Y':
        raise GeometryError('Mochi-Anatomiepreset ist fuer 180 mm und Y-up verifiziert; Skalierung separat pruefen.')
    if geometry_signature(surface.mesh)!=REFERENCE_SIGNATURE:
        raise GeometryError('Mochi-Anatomiepreset braucht die unveraenderte 150k-Arbeitskopie vor Farbgrenzen-Verfeinerung.')
    masks,analysis=mochi_masks(surface,reference_plan)
    if tuple(analysis['eye_part_keys'])!=('eye-1','eye-2','eye-3','eye-4'):
        raise GeometryError('Mochi braucht genau vier getrennte schwarze Augeneinsaetze.')
    return masks,analysis


def _semantic_labels(surface,masks):
    labels=np.zeros(len(surface.mesh.faces),dtype=int)
    for region_id,key in enumerate(PART_KEYS[1:],1):labels[masks[key]]=region_id
    return labels


def suggest_mochi_detail_plan(surface,reference_plan,settings,mesh_hash,filaments,*,current_plan=None):
    """Return (canonical document, JSON-safe report); never applies the proposal.

    current_plan contributes the existing user-chosen pair only. The immutable
    original reference_plan supplies anatomical analysis, not current edits.
    """
    if hasattr(settings,'model_dump'):settings=settings.model_dump()
    if hasattr(reference_plan,'model_dump'):reference_plan=reference_plan.model_dump()
    if hasattr(current_plan,'model_dump'):current_plan=current_plan.model_dump()
    masks,analysis=_guard(surface,reference_plan,settings,mesh_hash)
    rows=filaments.values() if isinstance(filaments,dict) else filaments
    stock={f['id']:f for f in rows}
    selection=(current_plan or reference_plan).get('filament_ids',[])
    if not selection:selection=list(PAIR)
    if len(selection)!=2 or len(set(selection))!=2:raise GeometryError('Mochi braucht genau zwei konkrete Basisfilamente fuer seine regionalen Verlaeufe.')
    selected=[]
    for ident in [*selection,BLACK]:
        spool=stock.get(ident)
        if not spool or not spool.get('allowed',True) or settings.get('owned_filaments_only',True) and not spool.get('owned'):
            raise GeometryError(f'Mochi-Bestandsspule {ident} fehlt oder ist gesperrt; keine Ersatzspule erfunden.')
        if not spool.get('hex'):raise GeometryError('Mochi-Bestandsspule hat keine gueltige Farbangabe.')
        selected.append(spool)
    if len({str(s.get('material','')).casefold() for s in selected})!=1 or not selected[0].get('material'):
        raise GeometryError('Mochi-Basis und schwarze Kleinteile muessen kompatible konkrete Materialarten verwenden.')
    labels=_semantic_labels(surface,masks);samples=surface.sample();regions=[]
    for region_id,key in enumerate(PART_KEYS):
        mask=labels==region_id
        if not mask.any():raise GeometryError(f'Mochi-Anatomieregion {key} ist leer.')
        dark=key=='nose' or key.startswith('eye-')
        color=stock[BLACK]['hex'] if dark else rgb_hex(np.average(samples[mask],axis=0,weights=surface.mesh.area_faces[mask]))
        regions.append({'id':region_id,'name':NAMES[key],'strategy':'body' if key=='body' else 'part',
                        'color_mode':'solid' if dark else 'mixed','color':color,'part_group':region_id,
                        'cut_type':'inlay' if key.startswith('eye-') else 'whole',
                        'filament_id':BLACK if dark else None,
                        'face_count':int(mask.sum()),'area_mm2':round(float(surface.mesh.area_faces[mask].sum()),6),
                        'reason':'Modellgebundener lokaler Anatomievorschlag; Masken aus unveraendertem Quellmesh. '
                                 +('Kleben ohne Stift; Klebespiel physisch pruefen.' if key.startswith('eye-') else
                                   'Gesamte Nase inklusive angrenzender ehemals heller Dreiecke einheitlich schwarz.' if key=='nose' else
                                   'Zwei reale Basisfilamente; lokale Original-Albedo wird in virtuelle Mischrezepte umgesetzt.')})
    document={'version':1,'mesh_hash':mesh_hash,'face_count':len(labels),'face_regions':labels.tolist(),
              'regions':regions,'nozzle_count':2,'filament_ids':list(selection),'ratio_step_percent':5,
              'construction_preset':PRESET,
              'note':'Modellgebundener Mochi-Entwurf: 9 Teile, 7 Stifte, 4 Klebe-Augeneinsaetze. Keine physische Passungs- oder Farbfreigabe.'}
    return document,{'construction_preset':PRESET,'source_sha256_required':SOURCE_SHA256,
                     'mesh_hash':mesh_hash,'reference_plan_hash':digest(reference_plan),
                     'source_signature':REFERENCE_SIGNATURE,'anatomical_analysis':analysis,
                     'selected_basis':[{k:s.get(k) for k in ('id','brand','name','hex','material','measured')} for s in selected[:2]],
                     'black_filament':{k:selected[2].get(k) for k in ('id','brand','name','hex','material','measured')},
                     'expected_part_ids':list(PART_KEYS),'expected_pins':7,'glue_parts':[f'eye-{i}' for i in range(1,5)],
                     'anatomical_face_masks_editable':False,'colors_and_print_modes_editable':True,
                     'automatic_approval':False,'source_modified':False,'physical_fit_verified':False,
                     'recommended_radial_clearance_mm':.05,
                     'mouth_material_proposal':'Separate source mouth line near Z122 remains original body geometry, approximated with Brown/Beige; no black mouth part or black color preservation claimed.'}


def _labels_on_current(surface,current,mask):
    distance,source_ids,_=nearest(surface,current.triangles_center)
    return ((distance<=.03)&np.isin(source_ids,mask)).astype(int)


def _rename_report(value,mapping):
    if isinstance(value,dict):return {k:mapping.get(v,v) if k=='part_id' and isinstance(v,str) else _rename_report(v,mapping) for k,v in value.items()}
    if isinstance(value,list):return [_rename_report(v,mapping) for v in value]
    return value


def detail_clearance(settings):
    """The accepted 0.05-mm radial fit is a fixed starting point for this draft."""
    try:clearance=float(settings.get('pin_clearance_mm',.05))
    except (TypeError,ValueError):raise GeometryError('Mochi Detail-v2 braucht 0,05 mm radiales Spiel.') from None
    if not np.isfinite(clearance) or abs(clearance-.05)>1e-9:
        raise GeometryError('Mochi Detail-v2 verwendet den real erprobten radialen Nasenabstand 0,05 mm; keine stillschweigende engere oder weitere Passung.')
    return clearance


def construct_mochi_detail(surface,plan,settings,*,reference_plan):
    """Return (parts,report) with source-bound reviewed seams and checks.

    Pins: nose radius1.5/length3 mm; ears/tail radius1.2/length2.5 mm. The active
    pin_clearance_mm is honored. Eye inlays retain the source-bound zero-seam,
    one-mm-depth experiment and are explicitly glue-only, not certified fits.
    Generic pin-size/depth controls are superseded by this documented preset.
    Geometry decision edits must clear/rebuild the preset, never be ignored.
    """
    if hasattr(plan,'model_dump'):plan=plan.model_dump()
    if hasattr(settings,'model_dump'):settings=settings.model_dump()
    clearance=detail_clearance(settings)
    masks,analysis=_guard(surface,reference_plan,settings,plan.get('mesh_hash'))
    if plan.get('construction_preset')!=PRESET:raise GeometryError('Mochi-Anatomiekernel braucht den ausdruecklich gewaehlten Presetplan.')
    labels=np.asarray(plan.get('face_regions',[]));expected=_semantic_labels(surface,masks)
    if labels.shape!=expected.shape or not np.array_equal(labels,expected):
        raise GeometryError('Mochi-Anatomiemasken wurden geaendert; Preset neu vorschlagen oder allgemeine Konstruktion waehlen.')
    regions={r['id']:r for r in plan['regions']}
    for region_id,key in enumerate(PART_KEYS):
        row=regions.get(region_id)
        if (not row or row['strategy']!=('body' if key=='body' else 'part')
                or row.get('part_group')!=region_id
                or row.get('cut_type')!=('inlay' if key.startswith('eye-') else 'whole')):
            raise GeometryError('Geometrische Gruppierung passt nicht zum Mochi-Preset. Farben bleiben editierbar; fuer andere Schnitte den Preset aufheben.')
    remaining=surface.mesh.copy();parts=[];cut_reports={}
    for key,radius,length,region_id in [('nose',1.5,3.,1),('right-ear',1.2,2.5,2),('left-ear',1.2,2.5,3),('tail',1.2,2.5,4)]:
        try:
            built,report=make_surface_parts(remaining,_labels_on_current(surface,remaining,masks[key]),
                [regions[0]['color'],regions[region_id]['color']],pin_radius_mm=radius,pin_length_mm=length,
                pin_clearance_mm=clearance,connector_shape='keyed',min_region_area_mm2=0,validate_paths=True)
        except GeometryError as exc:raise GeometryError(f'Mochi Detail-v2 {key}: {exc}') from exc
        cores=[p for p in built if p.role=='body'];appendages=[p for p in built if p.role!='body']
        expected_pins=1 if key=='nose' else 2
        if len(cores)!=1 or len(appendages)!=1 or len(appendages[0].connectors)!=expected_pins:
            raise GeometryError(f'Mochi {key}: erwartet ein geschlossenes Teil mit {expected_pins} sicheren Stiften.')
        part=appendages[0];old=part.id;part.id=key;part.name=NAMES[key];part.color_index=region_id
        cut_reports[key]=_rename_report(report,{old:key,'body':'body'})
        parts.append(part);remaining=cores[0].mesh
    eye_faces=np.unique(np.concatenate([masks[key] for key in PART_KEYS[5:]]))
    built,eye_report=make_inlays(remaining,_labels_on_current(surface,remaining,eye_faces),
        [regions[0]['color'],regions[5]['color']],depth_mm=1,seam_mm=0,pin_radius_mm=1.5,pin_length_mm=1.5,
        pin_clearance_mm=clearance,min_region_area_mm2=3,adaptive_small_pins=False,connector_mode='glue',validate_paths=True)
    cores=[p for p in built if p.role=='body'];eyes=[p for p in built if p.role!='body']
    if len(cores)!=1 or len(eyes)!=4:raise GeometryError('Mochi erwartet einen Grundkoerper und vier schwarze Klebe-Augeneinsaetze.')
    eye_mapping={};seen=set()
    for eye in eyes:
        distance,source_ids,_=nearest(surface,eye.mesh.triangles_center);original=source_ids[distance<=1e-5]
        scores={key:int(np.isin(original,masks[key]).sum()) for key in PART_KEYS[5:]};key=max(scores,key=scores.get)
        if not scores[key] or key in seen or eye.connectors:raise GeometryError('Mochi-Augeneinsatz ist anatomisch nicht eindeutig oder besitzt unerwartete Stifte.')
        seen.add(key);eye_mapping[eye.id]=key;eye.id=key;eye.name=NAMES[key];eye.role='glue-inlay';eye.color_index=PART_KEYS.index(key)
        eye.color=regions[eye.color_index]['color'];eye.warnings.append('Klebeteil ohne Stift; Null-Referenzspiel ist kein physisch kalibriertes Klebespiel. Nicht gewaltsam einpressen.')
    core=cores[0];core.id='body';core.name=NAMES['body'];core.color_index=0
    parts=[core,*parts,*sorted(eyes,key=lambda p:p.id)]
    checks=_combined_checks(parts,30)
    quality={p.id:validate_mesh(p.mesh) for p in parts}
    if set(quality)!=set(PART_KEYS) or any(not q['valid'] or q['components']!=1 for q in quality.values()):raise GeometryError('Mochi-Teile sind nicht genau neun geschlossene Einzelkoerper.')
    source_volume=float(surface.mesh.volume);total=float(sum(p.mesh.volume for p in parts))
    if total>source_volume+max(.01,source_volume*1e-7):raise GeometryError('Mochi-Teile ueberschreiten das urspruengliche Volumen.')
    return parts,{'strategy':'source-bound Mochi detail-v2 anatomical preset','construction_preset':PRESET,
        'source_signature':REFERENCE_SIGNATURE,'source_sha256_required':SOURCE_SHA256,'mesh_hash':plan['mesh_hash'],
        'reference_plan_hash':digest(reference_plan),'plan_hash':digest(plan),'anatomical_analysis':analysis,
        'construction_order':['nose','right-ear','left-ear','tail','eyes'],'appendage_reports':cut_reports,
        'eye_inlays':_rename_report(eye_report,eye_mapping),'combined_path_checks':checks,
        'quality':quality,'source_volume_mm3':source_volume,'parts_volume_mm3':total,
        'clearance_void_mm3':source_volume-total,'pins':sum(len(p.connectors) for p in parts),'glue_parts':list(PART_KEYS[5:]),
        'preset_parameters':{'nose':{'pin_radius_mm':1.5,'pin_length_mm':3},'ears_tail':{'pin_radius_mm':1.2,'pin_length_mm':2.5},
                             'radial_clearance_mm':clearance,'eyes':{'depth_mm':1,'seam_mm':0,'retention':'glue only'}},
        'parameter_policy':'Model-bound pin sizes/inlay depth supersede generic construction controls; active radial clearance is honored.',
        'automatic_approval':False,'physical_fit_verified':False,'physical_color_verified':False,
        'warnings':['Vier Augeneinsaetze sind reine Klebeteile ohne Stift. Klebespiel und Halt muessen physisch geprueft werden.',
                    'Diskrete Kollisionspfade und geschlossene Volumen ersetzen keinen realen Passungs- und Belastungstest.',
                    'Druckausrichtung, Supportkontakte und native regionale Rezeptfarben werden separat geprueft.',
                    'Die dunkle Mundlinie bleibt als vertiefte Koerpergeometrie erhalten, wird aber mit Braun/Beige angenaehert; kein separates schwarzes Mundteil und keine schwarze Farberhaltung behauptet.']}



def pack_mochi_detail_parts(parts,volume=(300,320,320),margin=25,gap=12):
    """One large mixed object per plate prevents cross-object tree conflicts.

    The earlier compact body/tail arrangement produced a real Bambu G-code
    conflict. Model-box spacing alone cannot certify support envelopes. Keep
    the black low-profile raft group separate and still require slicer QA.
    """
    from .mochi_pipeline import pack_mochi_parts
    from ..geometry.packing import pack_parts,validate_packing
    margin=max(25.,float(margin));gap=max(12.,float(gap));lookup={p.id:p for p in parts}
    original=pack_mochi_parts(parts,volume,margin,gap)
    result=[]
    for key in ('body','right-ear','left-ear','tail'):
        plate=pack_parts([lookup[key]],volume=volume,margin=margin,gap=gap,max_colors=1)[0]
        plate.update(id=len(result)+1,material_batch='Beige/EarthBrown one-object support isolation',
                     physical_spool_count=2,support_isolation_policy='One large object per plate; cross-object tree paths excluded by layout',
                     support_collision_verified=False)
        result.append(plate)
    black=original[-1];black['id']=len(result)+1
    black['support_collision_verified']=False;result.append(black)
    check=validate_packing(parts,result)
    if not check['passed']:raise GeometryError('Detail-v2 support-isolated plate layout failed: '+str(check['problems']))
    return result


def create_detail_reference(surface):
    """Recreate the immutable four-class source analysis for this exact V2 mesh."""
    from ..geometry.colors import classify,srgb_to_lab
    from ..geometry.mochi_detail_masks import REFERENCE_CLASSES_SHA256
    import hashlib
    if geometry_signature(surface.mesh)!=REFERENCE_SIGNATURE:
        raise GeometryError('Detail-v2 reference requires the exact reviewed source geometry')
    palette=['#AF440A','#852F06','#EFB27C','#090505'];samples=surface.sample();lab=srgb_to_lab(samples)
    labels=classify(samples,palette[:3]);labels[(lab[:,0]<22)&(np.linalg.norm(lab[:,1:],axis=1)<12)]=3
    if hashlib.sha256(labels.astype('<u4').tobytes()).hexdigest()!=REFERENCE_CLASSES_SHA256:
        raise GeometryError('Detail-v2 source albedo classes differ from the reviewed immutable mask')
    return {'version':1,'mesh_hash':MESH_HASH,'face_count':len(labels),'face_regions':labels.tolist(),
            'regions':[{'id':i,'name':f'Originalmaterialklasse {i+1}','strategy':'body' if i==0 else 'part',
                        'color_mode':'solid','color':color,'part_group':0,'cut_type':'inlay','filament_id':None,
                        'face_count':int((labels==i).sum()),'area_mm2':float(surface.mesh.area_faces[labels==i].sum()),
                        'reason':'Immutable original three-color palette plus neutral dark L<22/chroma<12 reservation.'}
                       for i,color in enumerate(palette)],
            'filament_ids':list(PAIR),'nozzle_count':2,'ratio_step_percent':5,
            'note':'Detail-v2 immutable source analysis; semantic anatomy and color baseline stored separately.'}
