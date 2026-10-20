"""Reproduce the local Mochi geometry experiment; never mutate approvals/projects.

Run from the repository root with PYTHONPATH=backend and --project PROJECT_ID.
This intentionally model-specific experiment is not the general UI constructor.
The working GLB, reference color plan and 180-mm scale are pinned. Anatomical
contours are computed from the source geometry; saved masks are not prerequisites.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sqlite3
import numpy as np
from figuraforge.config import Config
from figuraforge.db import uid,digest
from figuraforge.geometry.compare import nearest
from figuraforge.geometry.mochi_masks import mochi_masks
from figuraforge.geometry.construct import make_inlays
from figuraforge.geometry.io import load_surface
from figuraforge.geometry.packing import pack_parts
from figuraforge.geometry.planned_parts import _combined_checks
from figuraforge.geometry.split import clip_half
from figuraforge.geometry.surface_parts import make_surface_parts
from figuraforge.geometry.types import Part,GeometryError
from figuraforge.geometry.validation import validate_mesh
from figuraforge.services.export import export_bundle,validate_3mf
from figuraforge.security import safe_asset_path

SOURCE_SHA256='c8b50eee6cce4bf76ca8ef17050c44694e6db0ee7d18bdd47cf48507fc065643'


def fit_coupon(body,nose,directory):
    """Crop the real socket; keep the exact mating nose and pin geometry."""
    mesh=body.copy()
    for axis,low,high in [(1,-70.000137,-57.000137),(2,122.000137,139.000137),(0,-9.000137,9.000137)]:
        mesh=clip_half(mesh,axis,low,True);mesh=clip_half(mesh,axis,high,False)
    parts=[Part('socket-coupon','Original-Nasentasche – Passungsprobe',mesh,'#EFB27C',role='body'),nose]
    quality={p.id:validate_mesh(p.mesh) for p in parts}
    if any(not q['valid'] or q['components']!=1 for q in quality.values()):
        raise GeometryError('Fit coupon must contain exactly two closed, connected objects')
    checks=_combined_checks(parts,10)
    plates=pack_parts(parts,volume=(300,320,320),margin=6,max_colors=2)
    world_bounds={}
    for plate in plates:
        for placement in plate['placements']:
            placement['transform'][0][3]+=25;placement['rect'][0]+=25
            part=next(p for p in parts if p.id==placement['part_id']);tf=np.asarray(placement['transform'])
            vertices=part.mesh.vertices@tf[:3,:3].T+tf[:3,3]
            low=vertices.min(axis=0);high=vertices.max(axis=0)
            if (low<np.array([25,0,0])-1e-6).any() or (high>np.array([325,320,320])+1e-6).any():
                raise GeometryError('Fit coupon leaves the verified shared H2D envelope')
            world_bounds[part.id]=[low.tolist(),high.tolist()]
    metadata={'purpose':'Small physical fit test; exact original nose, pin and cropped original socket',
        'quality':quality,'checks':checks,'plate_x_offset_mm':25,'plate_bounds_mm':world_bounds,
        'physical_print_verified':False,'native_machine_profile':False}
    directory.mkdir(parents=True)
    (directory/'geometry-check.json').write_text(json.dumps(metadata,indent=2)+'\n')
    for part in parts:part.save(directory/'parts')
    export_bundle(parts,plates,directory,metadata=metadata)


def remap_report_ids(value,mapping):
    if isinstance(value,dict):
        return {key:mapping.get(item,item) if key=='part_id' and isinstance(item,str)
                else remap_report_ids(item,mapping) for key,item in value.items()}
    if isinstance(value,list):return [remap_report_ids(item,mapping) for item in value]
    return value


def source_labels(surface,current_mesh,face_ids):
    distances,nearest_ids,_=nearest(surface,current_mesh.triangles_center)
    return ((distances<=.03)&np.isin(nearest_ids,face_ids)).astype(int)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',required=True)
    parser.add_argument('--output-root',type=Path,default=Path('benchmarks/mochi-construction'))
    parser.add_argument('--skip-fit-coupon',action='store_true')
    args=parser.parse_args()
    config=Config()
    with sqlite3.connect(f'file:{config.data_dir / "forge.sqlite3"}?mode=ro',uri=True) as connection:
        row=connection.execute('SELECT data FROM projects WHERE id=?',(args.project,)).fetchone()
    if not row:raise GeometryError('Requested source project does not exist')
    project=json.loads(row[0]);project_root=config.data_dir/'projects'/args.project
    mesh_artifact=project['artifacts'].get('mesh');plan_artifact=project['artifacts'].get('plan')
    if not mesh_artifact or not plan_artifact:raise GeometryError('Verified source mesh and original reference color plan required')
    source_path=safe_asset_path(project_root,mesh_artifact['source']['path'])
    if hashlib.sha256(source_path.read_bytes()).hexdigest()!=SOURCE_SHA256 or mesh_artifact['source']['sha256']!=SOURCE_SHA256:
        raise GeometryError('This experiment only applies to the verified Mochi working GLB')
    if project['settings']['height_mm']!=180 or project['settings']['up_axis']!='Y':
        raise GeometryError('This anatomical experiment requires height 180 mm and Y-up source')
    document=json.loads(safe_asset_path(project_root,plan_artifact['document']).read_text())
    if digest(document)!=plan_artifact['hash'] or document['mesh_hash']!=mesh_artifact['hash'] or plan_artifact['mesh_hash']!=mesh_artifact['hash']:
        raise GeometryError('Color-plan hash or source mesh binding changed; review before repeating')
    surface=load_surface(source_path,180,'Y');source=surface.mesh
    masks,anatomical_report=mochi_masks(surface,document)
    out=args.output_root/('anatomy-review-'+uid());out.mkdir(parents=True)
    (out/'anatomical-proposal.json').write_text(json.dumps(anatomical_report,indent=2)+'\n')
    for name,indices in masks.items():np.save(out/(name+'-source-face-ids.npy'),indices)
    remaining=source.copy();parts=[];cut_reports={};nose_body=None
    # Nose uses the user's real test dimensions. Other appendages use the
    # separately verified smaller keys. No remembered cutting planes are used.
    for name,radius,length,color in [('nose',1.5,3.,'#090505'),('right-ear',1.2,2.5,'#EFB27C'),
                                      ('left-ear',1.2,2.5,'#EFB27C'),('tail',1.2,2.5,'#EFB27C')]:
        labels=source_labels(surface,remaining,masks[name])
        built,report=make_surface_parts(remaining,labels,['#AF440A',color],
            pin_radius_mm=radius,pin_length_mm=length,pin_clearance_mm=.2,connector_shape='keyed',
            min_region_area_mm2=0,validate_paths=True)
        cores=[part for part in built if part.role=='body'];appendages=[part for part in built if part.role!='body']
        expected_pins=1 if name=='nose' else 2
        if len(cores)!=1 or len(appendages)!=1 or len(appendages[0].connectors)!=expected_pins:
            raise GeometryError(f'{name} must be one connected part with {expected_pins} safe pins')
        part=appendages[0];old_id=part.id;part.id=name
        part.name={'nose':'Mochi Nase – gesamte dunkle Nasenregion','tail':'Mochi Schwanz – anatomische Wurzel',
                   'right-ear':'Mochi rechtes Ohr – anatomische Wurzel','left-ear':'Mochi linkes Ohr – anatomische Wurzel'}[name]
        cut_reports[name]=remap_report_ids(report,{old_id:name,'body':'body'})
        remaining=cores[0].mesh;parts.append(part)
        if name=='nose':nose_body=remaining.copy()
        (out/(name+'-construction-report.json')).write_text(json.dumps(cut_reports[name],indent=2)+'\n')
    eye_keys=anatomical_report['eye_part_keys']
    eye_faces=np.unique(np.concatenate([masks[key] for key in eye_keys]))
    labels=source_labels(surface,remaining,eye_faces)
    built,eye_report=make_inlays(remaining,labels,['#AF440A','#090505'],depth_mm=1,
        seam_mm=0,pin_radius_mm=1.5,pin_length_mm=1.5,pin_clearance_mm=.2,
        min_region_area_mm2=3,adaptive_small_pins=True,validate_paths=True)
    cores=[part for part in built if part.role=='body'];eyes=[part for part in built if part.role!='body']
    if len(cores)!=1 or len(eyes)!=4:raise GeometryError('Expected one core and four separate dark eye inserts')
    eye_mapping={};assigned=set()
    for eye in eyes:
        distances,source_ids,_=nearest(surface,eye.mesh.triangles_center)
        original=source_ids[distances<=1e-5]
        scores={key:int(np.isin(original,masks[key]).sum()) for key in eye_keys}
        name=max(scores,key=scores.get)
        if not scores[name] or name in assigned:raise GeometryError('Eye source-mask identity is ambiguous')
        assigned.add(name);eye_mapping[eye.id]=name;eye.id=name
        eye.name=f'Mochi {name} – Klebeteil';eye.role='glue-inlay'
        if eye.connectors:raise GeometryError('Unexpected eye connector: revise retention assessment')
        eye.warnings.append('Klebeteil ohne Steckstift; Kleberetention und Klebespiel nicht physisch geprueft')
    eye_report=remap_report_ids(eye_report,eye_mapping)
    core=cores[0];core.id='body';core.name='Mochi Koerper – anatomische Geometrieprobe'
    parts=[core,*parts,*eyes]
    checks=_combined_checks(parts,30)
    quality={part.id:validate_mesh(part.mesh) for part in parts}
    if len(quality)!=len(parts) or any(not row['valid'] or row['components']!=1 for row in quality.values()):
        raise GeometryError('Every exported item must be one uniquely identified closed connected solid')
    metadata={'purpose':'Model-specific anatomical geometry experiment; no approvals, regional filament assignments or native machine profile',
        'source_project':args.project,'source_sha256':SOURCE_SHA256,'mesh_hash':mesh_artifact['hash'],'plan_hash':plan_artifact['hash'],
        'source_volume_mm3':float(source.volume),'parts_volume_mm3':sum(float(part.mesh.volume) for part in parts),
        'quality':quality,'anatomical_proposal':anatomical_report,'combined_path_checks':checks,
        'construction_order':['nose','right-ear','left-ear','tail','eyes'],
        'nose_report':cut_reports['nose'],'appendage_reports':cut_reports,'eye_inlays':eye_report,
        'warnings':['Core geometry export uses simplified display colors, not approved native mixed-filament assignments.',
                    'Eye inserts are glue-only; the exact zero-seam reference is not a calibrated physical clearance.',
                    'This anatomical nose differs from the earlier color-only nose test; earlier outputs and ongoing prints remain untouched.'],
        'physical_print_verified':False,'bambu_gui_verified':False}
    metadata['clearance_void_mm3']=metadata['source_volume_mm3']-metadata['parts_volume_mm3']
    if metadata['clearance_void_mm3']<-.01:raise GeometryError('Parts exceed original source volume')
    for part in parts:part.save(out/'parts')
    result=export_bundle(parts,pack_parts(parts,volume=(300,320,320),margin=6),out,metadata=metadata)
    roundtrips={path.name:validate_3mf(path) for path in out.glob('*.3mf')}
    if not roundtrips or not all(row.get('bambu_printable_items') for row in roundtrips.values()):
        raise GeometryError('Every 3MF build item must retain numeric printable=1')
    metadata['three_mf_roundtrips']=roundtrips
    (out/'geometry-check.json').write_text(json.dumps(metadata,indent=2)+'\n')
    if not args.skip_fit_coupon:
        nose=next(part for part in parts if part.id=='nose')
        fit_coupon(nose_body,nose,out/'nose-fit')
    print(json.dumps({'output':str(out),'parts':len(parts),'plates':result['plates'],
        'pins':sum(len(part.connectors) for part in parts),'glue_inserts':len(eyes),'path_checks':len(checks),
        'anatomical_masks_recomputed':True,'numeric_printable_items':True,'fit_coupon':not args.skip_fit_coupon}),flush=True)


if __name__=='__main__':main()
