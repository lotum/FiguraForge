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
from ..geometry.mochi_masks import mochi_masks,geometry_signature,REFERENCE_SIGNATURE
from ..geometry.construct import make_inlays
from ..geometry.surface_parts import make_surface_parts
from ..geometry.types import GeometryError
from ..geometry.validation import validate_mesh
from ..geometry.planned_parts import _combined_checks
from .color_plan import is_mixed

PRESET='mochi-anatomical-v1'
MESH_HASH='56c3e3b339a0710a9eab9392cc657b5f4c1d7b6c7d9e37866074fd32ee089d17'
SOURCE_SHA256='c8b50eee6cce4bf76ca8ef17050c44694e6db0ee7d18bdd47cf48507fc065643'
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


def suggest_mochi_plan(surface,reference_plan,settings,mesh_hash,filaments,*,current_plan=None):
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
                     'automatic_approval':False,'source_modified':False,'physical_fit_verified':False}


def _labels_on_current(surface,current,mask):
    distance,source_ids,_=nearest(surface,current.triangles_center)
    return ((distance<=.03)&np.isin(source_ids,mask)).astype(int)


def _rename_report(value,mapping):
    if isinstance(value,dict):return {k:mapping.get(v,v) if k=='part_id' and isinstance(v,str) else _rename_report(v,mapping) for k,v in value.items()}
    if isinstance(value,list):return [_rename_report(v,mapping) for v in value]
    return value


def construct_mochi(surface,plan,settings,*,reference_plan):
    """Return (parts,report) with source-bound reviewed seams and checks.

    Pins: nose radius1.5/length3 mm; ears/tail radius1.2/length2.5 mm. The active
    pin_clearance_mm is honored. Eye inlays retain the source-bound zero-seam,
    one-mm-depth experiment and are explicitly glue-only, not certified fits.
    Generic pin-size/depth controls are superseded by this documented preset.
    Geometry decision edits must clear/rebuild the preset, never be ignored.
    """
    if hasattr(plan,'model_dump'):plan=plan.model_dump()
    if hasattr(settings,'model_dump'):settings=settings.model_dump()
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
    clearance=float(settings.get('pin_clearance_mm',.2))
    if not np.isfinite(clearance) or not .05<=clearance<=.8:raise GeometryError('Mochi-Preset braucht ein positives, geprueftes radiales Spiel von 0,05 bis 0,8 mm.')
    remaining=surface.mesh.copy();parts=[];cut_reports={}
    for key,radius,length,region_id in [('nose',1.5,3.,1),('right-ear',1.2,2.5,2),('left-ear',1.2,2.5,3),('tail',1.2,2.5,4)]:
        built,report=make_surface_parts(remaining,_labels_on_current(surface,remaining,masks[key]),
            [regions[0]['color'],regions[region_id]['color']],pin_radius_mm=radius,pin_length_mm=length,
            pin_clearance_mm=clearance,connector_shape='keyed',min_region_area_mm2=0,validate_paths=True)
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
        pin_clearance_mm=clearance,min_region_area_mm2=3,adaptive_small_pins=False,validate_paths=True,connector_mode='glue')
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
    return parts,{'strategy':'source-bound Mochi anatomical preset','construction_preset':PRESET,
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
                    'Druckausrichtung, Supportkontakte und native regionale Rezeptfarben werden separat geprueft.']}


def pack_mochi_parts(parts,volume=(300,320,320),margin=8,gap=8):
    """Separate the two-spool warm body batch from the one-spool black batch.

    Recipe/display-color count is not physical spool count. Eye pieces print
    with their hidden curved backs approximately horizontal, not as tall tiny
    upright strips. Nose pins point up; the curved nose needs raft/support.
    These are deterministic model-specific proposals, not sliced support QA.
    """
    from ..geometry.packing import pack_parts,validate_packing
    from ..geometry.topology import frame
    lookup={p.id:p for p in parts}
    if set(lookup)!=set(PART_KEYS):raise GeometryError('Mochi-Druckplanung erwartet genau die neun Anatomieteile.')
    mixed=[lookup[k] for k in ('body','right-ear','left-ear','tail')]
    plates=pack_parts(mixed,volume=volume,margin=margin,gap=gap,max_colors=len(mixed))
    for plate in plates:
        plate.update(material_batch='Beige/EarthBrown mixed parts',physical_spool_count=2)
    black={'id':len(plates)+1,'colors':[lookup['nose'].color],'placements':[],'volume_mm':list(volume),
           'material_batch':'Black nose and glue eye inserts','physical_spool_count':1}
    x=float(margin);y=float(margin);row_height=0.
    for key in ('nose','eye-1','eye-2','eye-3','eye-4'):
        part=lookup[key]
        if not part.assembly_direction:raise GeometryError('Mochi-Kleinteil braucht eine bekannte Fuegerichtung fuer die Druckorientierung.')
        normal=np.asarray(part.assembly_direction,float)
        # Nose visible face down/pin up, eyes hidden back down/visible side up.
        rotation=frame(-normal if key=='nose' else normal).T
        transformed=part.mesh.vertices@rotation.T;low=transformed.min(axis=0);extent=np.ptp(transformed,axis=0)
        if extent[2]>volume[2] or extent[0]+2*margin>volume[0] or extent[1]+2*margin>volume[1]:raise GeometryError('Mochi-Kleinteil passt nicht in die sichere Druckorientierung.')
        if x+extent[0]+margin>volume[0]:x=float(margin);y+=row_height+gap;row_height=0.
        if y+extent[1]+margin>volume[1]:raise GeometryError('Mochi-Kleinteilplatte passt nicht ohne Ueberlappung.')
        transform=np.eye(4);transform[:3,:3]=rotation;transform[:3,3]=-low+[x,y,0]
        black['placements'].append({'part_id':key,'transform':transform.tolist(),'rect':[x,y,float(extent[0]),float(extent[1])],
            'height_mm':float(extent[2]),'color':part.color,'support_status':'Raft/support required for curved nose and review all curved glue backs',
            'orientation_reason':'nose pins up, visible curved nose down' if key=='nose' else 'glue insert hidden curved back down, visible surface up'})
        x+=float(extent[0])+gap;row_height=max(row_height,float(extent[1]))
    black['utilization_percent']=round(sum(p['rect'][2]*p['rect'][3] for p in black['placements'])/(volume[0]*volume[1])*100,1)
    plates.append(black)
    check=validate_packing(parts,plates)
    if not check['passed']:raise GeometryError('Mochi-Plattenvorschlag ist ungueltig: '+str(check['problems']))
    return plates


def build_mochi_parts_preview(parts,surface,plan,filaments,reference_plan,native_settings=None,*,recipe_percentages=None):
    """Return (assembly preview JSON, warnings) with honest local recipe colors.

    Exterior faces inherit the same original-face recipe as native export.
    Newly created hidden caps/pins are gray, never falsely textured as fur.
    Original interpolated smooth normals affect only exterior shading; hidden
    engineering faces retain their geometric normals. Vertices are unchanged.
    """
    import base64
    from ..geometry.colors import hex_rgb
    from ..geometry.preview import mesh_preview
    from .mixed_preview import build_mixed_preview
    from .color_plan import is_mixed
    rows=filaments.values() if isinstance(filaments,dict) else filaments
    stock={r['id']:r for r in rows}
    recipe=build_mixed_preview(surface,plan,list(stock.values()),layer_height_mm=float((native_settings or {}).get('layer_height',.2)),reference_plan=reference_plan,
                               native_settings=native_settings,include_geometry=False,recipe_percentages=recipe_percentages)
    indices=np.asarray(recipe['face_recipe_indices']);labels=np.asarray(plan['face_regions'])
    regions={r['id']:r for r in plan['regions']}
    source_colors=np.empty((len(labels),3),float)
    for region_id,region in regions.items():
        mask=labels==region_id
        if is_mixed(region):
            selected=indices[mask]
            if (selected<0).any():raise GeometryError('Mochi-Vorschau hat unvollstaendige Mischrezeptzuordnung.')
            source_colors[mask]=np.array([hex_rgb(recipe['recipe_palette'][i]['color']) for i in selected])
        else:
            spool=stock.get(region.get('filament_id'))
            source_colors[mask]=hex_rgb(spool['hex'] if spool else region['color'])
    meshes=[]
    for part in parts:
        distances,face_ids,bary=nearest(surface,part.mesh.triangles_center)
        if plan.get('construction_preset')=='pip-anatomical-v1':
            from .pip_pipeline import exterior_face_mapping
            exterior,face_ids,bary=exterior_face_mapping(surface,part)
        elif plan.get('construction_preset') in ('mochi-anatomical-detail-v2','mochi-unified-head-v1'):
            from ..geometry.compare import unchanged_source_faces
            exterior=unchanged_source_faces(surface,part.mesh,face_ids,tolerance_mm=1e-6)
        else:exterior=distances<=.0001
        colors=np.repeat([[.53,.57,.62]],len(part.mesh.faces),axis=0)
        colors[exterior]=source_colors[face_ids[exterior]]
        record=mesh_preview(part.mesh,face_rgb=colors,ident=part.id,name=part.name,
                            role=part.role,direction=part.assembly_direction)
        normals=np.repeat(part.mesh.face_normals[:,None,:],3,axis=1)
        # Use each exact exterior corner's source interpolation. Do not round
        # connector edges or smooth freshly generated cap/side-wall normals.
        if exterior.any():
            corners=part.mesh.triangles[exterior].reshape(-1,3)
            _,corner_ids,corner_bary=nearest(surface,corners)
            tri_normals=surface.mesh.vertex_normals[surface.mesh.faces[corner_ids]]
            smooth=np.einsum('fvc,fv->fc',tri_normals,corner_bary)
            length=np.linalg.norm(smooth,axis=1);valid=length>1e-10
            smooth[valid]/=length[valid,None]
            normals[exterior]=smooth.reshape(-1,3,3)
        record['normals']=base64.b64encode(np.asarray(normals,dtype='<f4').tobytes()).decode()
        record.update(exterior_face_count=int(exterior.sum()),hidden_face_count=int((~exterior).sum()),
                      source_color_mapping=('exact source-triangle corner identity within 1e-6 mm; hidden interfaces gray' if plan.get('construction_preset')=='mochi-anatomical-detail-v2' else 'unchanged original-face recipe within .0001 mm; hidden interfaces gray'))
        meshes.append(record)
    physical_ids=set()
    for region in plan['regions']:
        if not np.any(labels==region['id']):continue
        physical_ids.update(plan['filament_ids'] if is_mixed(region) else [region.get('filament_id')])
    physical_ids.discard(None)
    preview={'format':'figuraforge-mesh-v1','unit':'millimeter','up_axis':'Z','meshes':meshes,
             'recipe_palette':recipe['recipe_palette'],'physical_filament_count':len(physical_ids),
             'mixed_basis_filament_count':2,
             'hidden_interfaces_color':'#87919E','color_model':recipe['color_model'],
             'export_coverage':recipe['export_coverage'],'geometry_modified':False,
             'preview_scope':'Two chosen basis filaments for mixed regions plus separately assigned black glue/nose parts.'}
    return preview,[*recipe['warnings'],'Graue Flaechen sind neue innere Passungs-/Stiftflaechen; Aussenfarben folgen dem lokalen Rezeptplan, keine Mittelwertfarbe pro Teil.']


def configure_mochi_plate(config,plate):
    """Return explicit local support/process choices for a packed Mochi plate.

    No filament/printer/thermal or nozzle settings change. AUTO supports resolve
    through the native builder's actual physical per-object material default.
    Curved black nose/eye parts need three raft layers; this is a slicer proposal,
    not a physical adhesion/fit approval. Preserve explicit process diff keys so
    the native GUI cannot restore system-preset defaults during import.
    """
    from .mixed_filament import mark_explicit_process_overrides
    source=deepcopy(config);settings=deepcopy(config)
    keys={row['part_id'] for row in plate.get('placements',[])}
    mixed={'body','right-ear','left-ear','tail'};black={'nose','eye-1','eye-2','eye-3','eye-4'}
    if not keys or not (keys<=mixed or keys<=black):
        raise GeometryError('Mochi-Druckplatte muss Mischteile und schwarze Kleinteile getrennt halten.')
    settings.update(layer_height='0.2',initial_layer_print_height='0.2',
                    enable_support='1',support_type='tree(auto)',
                    support_on_build_plate_only='1',support_threshold_angle='20',
                    support_top_z_distance='0.2',brim_type='auto_brim',brim_width='5',
                    raft_layers='0',support_filament='0',support_interface_filament='0')
    if keys<=black:settings.update(raft_layers='3',brim_type='outer_only')
    return mark_explicit_process_overrides(settings,source)
