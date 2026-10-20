"""Disposable geometry worker. JSON in/out; no provider credentials required.

This is a process boundary for crash recovery and cancellation, not a security
sandbox. Only the server creates its request files and chooses the operation.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys


def execute(request, progress):
    from ..geometry.io import load_surface, save_colored_glb
    from ..geometry.colors import choose_palette
    from ..geometry.validation import validate_mesh, require_solid, basic_stability
    from ..geometry.preview import mesh_preview, parts_preview, surface_preview
    from ..geometry.types import GeometryError, load_part
    from .workflow import write_json
    out=Path(request['out']); out.mkdir(parents=True,exist_ok=True)
    op=request['operation']; s=request.get('settings',{})
    if op=='inspect':
        from .mesh_preparation import prepare_source
        from ..geometry.refine import refine_with_plan
        path,preparation=prepare_source(Path(request['source']),out,s,progress)
        surface=load_surface(path,s['height_mm'],s['up_axis'])
        quality=validate_mesh(surface.mesh)
        if not quality['watertight']:
            surface.warnings.append('Mesh is not closed. Repair externally before constructing inlays.')
        palette=s['palette'] or choose_palette(surface.sample(),s['palette_size'],weights=surface.mesh.area_faces)
        if quality['valid']:
            progress('Farbgrenzen und Rechenbudget vorab pruefen')
            try:
                refined,labels,readiness=refine_with_plan(surface,palette,s,progress)
                if s.get('construction_strategy','inlays')=='inlays':
                    from ..geometry.construct import inspect_inlay_directions
                    readiness['assembly']=inspect_inlay_directions(refined.mesh,labels,s['base_color'],
                        s['min_region_area_mm2'],s['direction_overrides'])
            except GeometryError as exc:
                readiness={'ready':False,'message':str(exc)}
        else: readiness={'ready':False,'message':'Vor der Konstruktion ein geschlossenes, konsistent orientiertes Mesh reparieren.'}
        write_json(out/'mesh-preview.json',surface_preview(surface))
        return {'quality':quality,'palette':palette,'warnings':surface.warnings,'construction_readiness':readiness,
                'prepared_source':str(path.resolve()) if preparation else None,'preparation':preparation}
    if op=='preview':
        surface=load_surface(Path(request['source']),s['height_mm'],s['up_axis'])
        write_json(out/'mesh-preview.json',surface_preview(surface))
        return {'texture_preview':True}
    if op=='plan':
        from .color_plan import suggest_plan,plan_preview,save_plan
        surface=load_surface(Path(request['source']),s['height_mm'],s['up_axis'])
        progress('Farbregionen vorschlagen; noch keine Schnitte oder Steckverbinder')
        plan=suggest_plan(surface,s,request['mesh_hash'])
        plan_hash=save_plan(out,plan,plan_preview(surface,plan))
        return {'hash':plan_hash,'mesh_hash':plan['mesh_hash'],'regions':plan['regions'],
                'face_count':plan['face_count'],'nozzle_count':plan['nozzle_count'],
                'filament_ids':plan['filament_ids'],'note':plan['note']}
    if op=='segment':
        from ..geometry.refine import refine_with_plan
        from ..geometry.construct import make_inlays
        from ..geometry.surface_parts import make_surface_parts
        from ..geometry.split import tile_parts
        from ..geometry.packing import pack_parts, validate_packing
        progress('Farben analysieren und Farbgrenzen verfeinern')
        surface=load_surface(Path(request['source']),s['height_mm'],s['up_axis']); require_solid(surface.mesh)
        plan=request.get('color_plan')
        anatomical=bool(plan and plan.get('construction_preset'))
        if anatomical:
            if plan['construction_preset']=='buddy-anatomical-v1':
                from .buddy_pipeline import construct_buddy as construct_mochi,validate_buddy_pack_settings
                validate_buddy_pack_settings(s['build_volume_mm'],s['plate_margin_mm'],s['part_gap_mm'])
            elif plan['construction_preset']=='pip-anatomical-v1':
                from .pip_pipeline import construct_pip as construct_mochi
            elif plan['construction_preset']=='mochi-anatomical-detail-v2':
                from .mochi_detail_pipeline import construct_mochi_detail as construct_mochi
            elif plan['construction_preset']=='mochi-anatomical-v1':
                from .mochi_pipeline import construct_mochi
            else:raise GeometryError('Unknown source-bound construction preset')
            import numpy as np
            progress('Modellgebundene anatomische Bauteile und dokumentierte Montagefolge konstruieren')
            parts,construction=construct_mochi(surface,plan,s,reference_plan=request.get('construction_reference_plan'),
                **({'workdir':out} if plan['construction_preset']=='buddy-anatomical-v1' else {}))
            labels=np.asarray(plan['face_regions']);palette=[r['color'] for r in sorted(plan['regions'],key=lambda r:r['id'])]
            refinement={'construction_preset':plan['construction_preset'],'triangles':len(surface.mesh.faces),
                        'original_surface_unchanged':True,'color_boundary_refinement_required':False}
            if plan['construction_preset']=='buddy-anatomical-v1':
                refinement.update(original_surface_unchanged=False,source_file_preserved=True,
                    exterior_geometry_note='Anatomical/structural cuts with local Blender Float32 Boolean output; exact source-triangle identity is not claimed.')
            save_colored_glb(surface.mesh,labels,palette,out/'regions.glb')
        else:
            palette=s['palette'] or choose_palette(surface.sample(),s['palette_size'],weights=surface.mesh.area_faces)
            if s['base_color']>=len(palette): raise GeometryError('Base color index is outside the palette')
            surface.face_tags=__import__('numpy').arange(len(surface.mesh.faces))
            surface,labels,refinement=refine_with_plan(surface,palette,s,progress)
            if request.get('color_plan'):
                from .color_plan import construct_labels
                labels,palette=construct_labels(surface,request['color_plan'])
                s={**s,'base_color':0}
            save_colored_glb(surface.mesh,labels,palette,out/'regions.glb')
            constructor=make_surface_parts if s.get('construction_strategy')=='surface_parts' else make_inlays
            if request.get('color_plan'):
                from ..geometry.planned_parts import make_planned_parts
                from .color_plan import whole_part_labels
                from functools import partial
                constructor=partial(make_planned_parts,whole_labels=whole_part_labels(request['color_plan']))
            parts,construction=constructor(surface.mesh,labels,palette,base_color=s['base_color'],depth_mm=s['inlay_depth_mm'],
                seam_mm=s['seam_mm'],pin_radius_mm=s['pin_radius_mm'],pin_length_mm=s['pin_length_mm'],
                pin_clearance_mm=s['pin_clearance_mm'],connector_shape=s['connector_shape'],min_region_area_mm2=s['min_region_area_mm2'],
                validate_paths=s['validate_paths'],progress=progress,direction_overrides=s['direction_overrides'],adaptive_small_pins=s.get('adaptive_small_pins',True))
        tiling=[]
        if s['auto_tile'] and not (anatomical and plan['construction_preset']=='buddy-anatomical-v1'):
            parts,tiling=tile_parts(parts,s['build_volume_mm'],s['plate_margin_mm'],progress=progress,clearance=s['pin_clearance_mm'],shape=s['connector_shape'])
        progress('Druckausrichtungen und farbreine Druckplatten planen')
        if anatomical:
            if plan['construction_preset']=='buddy-anatomical-v1':
                from .buddy_pipeline import pack_buddy_parts
                pack_mochi_parts=lambda parts,volume,margin,gap:pack_buddy_parts(parts,construction_report=construction,volume=volume,margin=margin,gap=gap)
            elif plan['construction_preset']=='pip-anatomical-v1':
                from .pip_pipeline import pack_pip_parts as pack_mochi_parts
            elif plan['construction_preset']=='mochi-anatomical-detail-v2':
                from .mochi_detail_pipeline import pack_mochi_detail_parts as pack_mochi_parts
            else:from .mochi_pipeline import pack_mochi_parts
            plates=pack_mochi_parts(parts,s['build_volume_mm'],s['plate_margin_mm'],s['part_gap_mm'])
        else:
            plates=pack_parts(parts,s['build_volume_mm'],s['plate_margin_mm'],s['part_gap_mm'],s['colors_per_plate'])
        quality={part.id:validate_mesh(part.mesh) for part in parts}
        items=[part.save(out/'parts') for part in parts]
        preview=parts_preview(parts)
        if anatomical and request.get('inventory'):
            if plan['construction_preset']=='buddy-anatomical-v1':
                from .buddy_pipeline import build_buddy_parts_preview as build_mochi_parts_preview
            else:from .mochi_pipeline import build_mochi_parts_preview
            preview,preview_warnings=build_mochi_parts_preview(parts,surface,plan,request['inventory'],
                reference_plan=request.get('color_reference_plan'))
        else:preview_warnings=[]
        write_json(out/'parts-preview.json',preview)
        report={'construction':construction,'refinement':refinement,'tiling':tiling,'quality':quality,
                'packing':validate_packing(parts,plates),'stability_advisory':basic_stability(surface.mesh),
                'not_checked':['Exhaustive self-intersection detection','Physical fit/strength','Slicer support and purge zones']}
        write_json(out/'geometry-report.json',report)
        warnings=surface.warnings+preview_warnings+[w for part in parts for w in part.warnings]
        warnings+=['Assembly-path checks use finite samples, not a continuous collision proof.',
                   'Print support, dimensional calibration and physical assembly still require verification.']
        if not s['validate_paths']: warnings.append('Assembly-path collision checks were disabled.')
        summary={'parts':len(parts),'plates':len(plates),'pins':sum(len(part.connectors) for part in parts)}
        connections=construction.get('assembly_connections',{})
        if connections:
            summary.update(pins=connections['total_keys'],keyed_interfaces=connections['total_keyed_interfaces'])
        return {'parts':items,'palette':palette,'plates':plates,'warnings':sorted(set(warnings)),
                'plan_color_preview':bool(anatomical and request.get('inventory')),
                'summary':summary,'geometry_report':report}
    if op=='export':
        from .export import export_bundle
        parts=[load_part(Path(request['parts_dir']),item) for item in request['parts']]
        for part in parts:
            filament=request['filaments'][part.id]; part.color=filament['hex']; part.filament_id=filament['id']
        extra=[];manifest=dict(request['manifest']);plan=request.get('color_plan')
        if plan:
            from .mixed_filament import inspect_template,read_native_template,build_native_from_parts,native_bed_bounds
            from .plan_materials import prepare_native_materials
            if not request.get('native_template'):
                raise GeometryError('Fuer einen Farbplan ist eine passende native H2D-Vorlage erforderlich. Einfarbiger Core-Export wuerde die Bereichsfarben verlieren.')
            template=Path(request['native_template'])
            info=inspect_template(template);config,_=read_native_template(template)
            if plan.get('construction_preset') in ('mochi-anatomical-v1','mochi-anatomical-detail-v2','pip-anatomical-v1','buddy-anatomical-v1'):config['layer_height']='0.2'
            source=load_surface(Path(request['source']),s['height_mm'],s['up_axis'])
            slots,mapping,config=prepare_native_materials(parts,source,plan,info,request['inventory'],
                reference_plan=request.get('color_reference_plan'),native_settings=config,return_settings=True)
            bed=native_bed_bounds(config)
            directory=out/'export';directory.mkdir(parents=True,exist_ok=True)
            native_reports={}
            for plate in request['plates']:
                import numpy as np
                placements=[]
                for item in plate['placements']:
                    transform=np.asarray(item['transform'],dtype=float).copy()
                    # FiguraForge packs in a zero-based 300 mm dual-nozzle
                    # frame. H2D's shared physical frame begins at X=25 mm.
                    transform[:3,3]+=np.asarray(bed['min'])
                    placements.append({**item,'transform':transform.tolist()})
                selected=[next(p for p in parts if p.id==i['part_id']) for i in plate['placements']]
                name=f"plate-{plate['id']:02d}-native.3mf"
                progress(f"Native H2D-Farbzuordnung fuer Platte {plate['id']} schreiben")
                plate_config=config
                if plan.get('construction_preset') in ('mochi-anatomical-v1','mochi-anatomical-detail-v2','pip-anatomical-v1','buddy-anatomical-v1'):
                    if plan['construction_preset']=='buddy-anatomical-v1':
                        from .buddy_pipeline import configure_buddy_plate as configure_mochi_plate
                        plate={**plate,'native_physical_slots':sorted({mapping['filament_slots'][ident] for ident in plate['physical_filament_ids']})}
                    elif plan['construction_preset']=='pip-anatomical-v1':
                        from .pip_pipeline import configure_pip_plate as configure_mochi_plate
                    else:from .mochi_pipeline import configure_mochi_plate
                    plate_config=configure_mochi_plate(config,plate)
                native_reports[name]=build_native_from_parts(template,directory/name,selected,placements,plate_config,
                    {part.id:slots[part.id] for part in selected})
                extra.append(name)
            # Explicit provenance: the Core files remain geometry companions.
            manifest['native_color_export']={'mapping':mapping,'plates':native_reports,'bed_origin_offset_mm':bed['min'],
                'geometry_companions':'Core 3MF and GLB omit native per-face mixed recipes. Use plate-XX-native.3mf for color review.',
                'gui_verified':False,'slicing_verified':False}
        return export_bundle(parts,request['plates'],out/'export',manifest,additional_files=extra)
    raise GeometryError('Unsupported disposable geometry operation')


def main():
    if len(sys.argv)!=2: raise SystemExit('Usage: python -m figuraforge.services.geometry_task request.json')
    request_path=Path(sys.argv[1]); request=json.loads(request_path.read_text())
    result_path=request_path.with_name('worker-result.json')
    def progress(message):
        print(json.dumps({'progress':str(message)},ensure_ascii=True),flush=True)
    try:
        result={'ok':True,'result':execute(request,progress)}
    except Exception as exc:
        result={'ok':False,'error':str(exc)[:1500]}
    temporary=result_path.with_suffix('.tmp')
    temporary.write_text(json.dumps(result,allow_nan=False),encoding='utf-8'); temporary.replace(result_path)
    raise SystemExit(0 if result['ok'] else 2)

if __name__=='__main__': main()
