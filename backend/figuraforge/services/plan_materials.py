"""Map constructed triangles to existing native profiles, never invented presets."""
from __future__ import annotations
import re
import numpy as np
from ..geometry.compare import nearest, unchanged_source_faces
from .mixed_filament import MixedFilamentError,validate_native_settings,validate_part_filament_limits
from .color_plan import is_mixed


def _hex(value):
    value=str(value).strip().upper()
    if re.fullmatch(r'#[0-9A-F]{8}',value) and value.endswith('FF'):value=value[:7]
    if not re.fullmatch(r'#[0-9A-F]{6}',value):
        raise MixedFilamentError('Native filament colors must be opaque #RRGGBB values')
    return value


def prepare_native_materials(parts,source_surface,plan,template_info,filaments,*,reference_plan=None,native_settings=None,return_settings=False,recipe_percentages=None):
    """Assign 1-based native slots; source-face decisions win on the exterior.

    Only unchanged exterior points within .03 mm inherit the plan. New hidden
    faces inherit the same part's area-dominant exterior slot. Mixed appearance
    uses exactly the same uncalibrated per-face ratios as the color preview.
    """
    if hasattr(plan,'model_dump'):plan=plan.model_dump()
    if plan.get('nozzle_count')!=2 or template_info.get('nozzle_count')!=2:
        raise MixedFilamentError('Native export currently verifies only the two-nozzle H2D contract')
    config=template_info.get('config',{})
    native=validate_native_settings(config)
    physical={int(r['slot']):r for r in template_info.get('basis_filaments',[])}
    if set(physical)!=set(native['physical_slots']):
        raise MixedFilamentError('Native template is missing physical filament profile identities')
    rows=filaments.values() if isinstance(filaments,dict) else filaments
    inventory={f['id']:f for f in rows}
    spool_slots={}
    def match_spool(ident):
        if ident in spool_slots:return spool_slots[ident]
        spool=inventory.get(ident)
        if not spool or not spool.get('allowed',True):
            raise MixedFilamentError(f'Filament {ident!r} fehlt oder ist nicht erlaubt. Eine konkrete Bestandsspule zuordnen.')
        material=str(spool.get('material','')).strip().casefold()
        color=_hex(spool.get('hex',''))
        matches=[slot for slot,row in physical.items() if _hex(row.get('color',''))==color
                 and str(row.get('material','')).strip().casefold()==material and material]
        if not matches:
            raise MixedFilamentError(f'Kein natives physisches Profil fuer {spool.get("name",ident)} ({color}, {spool.get("material","")}). Passende Spule in Bambu Studio konfigurieren und die Vorlage erneut speichern.')
        slot=min(matches);spool_slots[ident]=slot;return slot
    regions={r['id']:r for r in plan['regions']}
    if len(regions)!=len(plan['regions']):raise MixedFilamentError('Duplicate color-plan region IDs')
    face_regions=np.asarray(plan['face_regions'])
    ancestry=getattr(source_surface,'face_tags',None)
    if ancestry is None:ancestry=np.arange(len(source_surface.mesh.faces))
    ancestry=np.asarray(ancestry)
    if (ancestry.shape!=(len(source_surface.mesh.faces),) or not np.issubdtype(ancestry.dtype,np.integer)
            or (ancestry<0).any() or (ancestry>=len(face_regions)).any()):
        raise MixedFilamentError('Color-plan ancestry does not match the source mesh')
    original_regions=face_regions[ancestry]
    used=set(int(x) for x in original_regions)
    if used-set(regions):raise MixedFilamentError('Source face references an unknown color-plan region')
    fixed={}
    for ident in sorted(used):
        region=regions[ident]
        if is_mixed(region):continue
        if not region.get('filament_id'):
            raise MixedFilamentError(f'Bereich {region.get("name",ident)} braucht eine konkrete Filamentzuordnung vor dem nativen Export.')
        fixed[ident]=match_spool(region['filament_id'])
    mixed_used=any(is_mixed(regions[i]) for i in used)
    mixed_candidates=[];basis_slots=[]
    if mixed_used:
        selected=plan.get('filament_ids',[])
        if len(selected)!=2 or len(set(selected))!=2:
            raise MixedFilamentError('Mixed-Flaechen benoetigen genau zwei ausgewaehlte Basisfilamente')
        basis_slots=[match_spool(i) for i in selected]
        if len(set(basis_slots))!=2:raise MixedFilamentError('Die zwei Basisfilamente muessen zwei verschiedene native physische Slots belegen')
        materials={str(inventory[i]['material']).strip().casefold() for i in selected}
        if len(materials)!=1:raise MixedFilamentError('Mixed-Basisfilamente muessen dieselbe Materialart haben')
        recipe_slots=[r['slot'] for r in native['mixed_slots'] if set(r['component_slots'])==set(basis_slots)]
        if not recipe_slots:
            raise MixedFilamentError('Die native Vorlage hat keine vorhandene Mischung fuer das ausgewaehlte Filamentpaar. Mischslot in Bambu Studio anlegen und Vorlage erneut speichern.')
        mixed_candidates=sorted(set(basis_slots+recipe_slots))
    allocated_settings=native_settings if native_settings is not None else config
    preview=None;recipe_allocation=None;source_recipe_slots=None
    if mixed_used:
        from .mixed_preview import build_mixed_preview
        from .native_recipe_library import allocate_native_recipes
        preview_plan={**plan,'face_regions':original_regions.tolist(),'face_count':len(original_regions)}
        reference={**reference_plan,'face_count':len(original_regions)} if reference_plan else None
        preview=build_mixed_preview(source_surface,preview_plan,list(inventory.values()),
            layer_height_mm=float(allocated_settings.get('layer_height',.2)),reference_plan=reference,include_geometry=False,
            recipe_percentages=recipe_percentages)
        recipe_indices=np.asarray(preview['face_recipe_indices'])
        required=[preview['recipe_palette'][i] for i in np.unique(recipe_indices[recipe_indices>=0])]
        allocation=allocate_native_recipes(allocated_settings,basis_slots,required)
        allocated_settings=allocation['settings'];recipe_allocation=allocation['report']
        source_recipe_slots=np.zeros(len(original_regions),int)
        for index,recipe in enumerate(preview['recipe_palette']):
            if recipe['first_percent'] in allocation['percent_to_slot']:
                source_recipe_slots[recipe_indices==index]=allocation['percent_to_slot'][recipe['first_percent']]
    groups=[]
    for region in plan['regions']:
        if region['strategy']=='part':
            key=region.get('part_group') or region['id']+10001
            if key not in groups:groups.append(key)
    def hidden_only_slot(part):
        matching=[]
        if part.color_index>0 and part.color_index<=len(groups):
            key=groups[part.color_index-1]
            matching=[r for r in plan['regions'] if r['strategy']=='part' and (r.get('part_group') or r['id']+10001)==key]
        elif part.role=='body':matching=[r for r in plan['regions'] if r['strategy']=='body']
        for region in sorted(matching,key=lambda r:_hex(r['color'])!=_hex(part.color)):
            if region['id'] in fixed:return fixed[region['id']]
        # Never add a new material just because an internal cap has a color.
        explicit=[slot for slot in spool_slots.values() if _hex(physical[slot]['color'])==_hex(part.color)]
        if explicit:return min(explicit)
        if mixed_used and part.role=='body':return basis_slots[0]
        raise MixedFilamentError(f'Bauteil {part.id} hat keine zuordenbare Aussenflaeche oder passende explizite Basisfilamentzuordnung')
    exterior_limit=.00003 if plan.get('construction_preset')=='pip-anatomical-v1' else .0001 if plan.get("construction_preset") in ("mochi-anatomical-v1","mochi-anatomical-detail-v2") else .03
    face_slots={};part_reports={}
    for part in parts:
        if part.id in face_slots:raise MixedFilamentError('Part IDs must be unique before native material mapping')
        distance,face_ids,_=nearest(source_surface,part.mesh.triangles_center)
        if plan.get('construction_preset')=='pip-anatomical-v1':
            from .pip_pipeline import exterior_face_mapping
            exterior,face_ids,_=exterior_face_mapping(source_surface,part)
        elif plan.get('construction_preset') in ('mochi-anatomical-detail-v2','mochi-unified-head-v1'):
            exterior=unchanged_source_faces(source_surface,part.mesh,face_ids,tolerance_mm=1e-6)
        elif plan.get('construction_preset')=='buddy-anatomical-v1':
            exterior=(distance<=.03)&((part.mesh.face_normals*source_surface.mesh.face_normals[face_ids]).sum(axis=1)>.95)
        else:
            exterior=distance<=exterior_limit
        slots=np.zeros(len(part.mesh.faces),dtype=int)
        assigned_regions=original_regions[face_ids]
        for ident in np.unique(assigned_regions[exterior]):
            mask=exterior&(assigned_regions==ident);region=regions[int(ident)]
            if not is_mixed(region):slots[mask]=fixed[int(ident)];continue
            # Inherit exactly the recipe shown for this original face. Do not
            # silently re-quantize against a smaller template palette or ignore
            # the user's reference-bound color correction during export.
            slots[mask]=source_recipe_slots[face_ids[mask]]
        if exterior.any():
            weights=np.bincount(slots[exterior],weights=part.mesh.area_faces[exterior])
            fallback=int(np.argmax(weights))
        else:fallback=hidden_only_slot(part)
        slots[~exterior]=fallback
        if not len(slots) or (slots<1).any():raise MixedFilamentError(f'Bauteil {part.id} hat unvollstaendige native Materialzuordnung')
        face_slots[part.id]=slots.tolist()
        part_reports[part.id]={'exterior_faces':int(exterior.sum()),'hidden_faces':int((~exterior).sum()),
                               'hidden_fallback_slot':fallback,'used_slots':sorted(int(x) for x in np.unique(slots))}
    limits=validate_part_filament_limits(config,face_slots,maximum_physical_filaments=plan['nozzle_count'])
    result={'mapping':'exact per-face preview recipes in existing native virtual slots',
                        'filament_slots':spool_slots,'mixed_candidate_slots':mixed_candidates,
                        'parts':part_reports,'filament_limits':limits,'exterior_distance_limit_mm':exterior_limit,
                        'exterior_mapping':('triangle identity within 1e-6 mm' if plan.get('construction_preset')=='mochi-anatomical-detail-v2' else 'nearest surface distance'),
                        'mixed_delta_e_2000':preview['matching_error_delta_e'] if preview else None,
                        'recipe_allocation':recipe_allocation,'preview_recipe_parity':bool(mixed_used),
                        'color_calibrated':False,'new_profiles_created':False,'new_recipes_created':False,
                        'warnings':['Mischfarben sind unkalibrierte optische Schaetzungen. Gedruckte Mischproben sind fuer eine Farbabnahme erforderlich.',
                                    'Vorhandene Druck- und Filamentprofile bleiben erhalten; Materialtyp und HEX ersetzen keine physische Temperatur-/Haftungspruefung.'],
                        'slicing_verified':False,'physical_print_verified':False}
    return (face_slots,result,allocated_settings) if return_settings else (face_slots,result)
