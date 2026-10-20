"""Reproduce the reviewed Buddy service directly from its saved local source.

Read-only project/inventory access. Every run writes a new benchmark directory;
no approvals, paid calls, printer submission or changes to project state.
"""
from pathlib import Path
import argparse,hashlib,json,sqlite3,time,copy
from figuraforge.config import Config
from figuraforge.db import uid
from figuraforge.security import safe_asset_path
from figuraforge.geometry.io import load_surface
from figuraforge.geometry.packing import validate_packing
from figuraforge.services.buddy_pipeline import (
    MESH_HASH,SOURCE_SHA256,suggest_buddy_plan,construct_buddy,pack_buddy_parts)
from figuraforge.services.export import export_bundle,validate_3mf

PROJECT='2c9a7959d13a438fbeb5b8340d8eefd4'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root',type=Path,default=Path('benchmarks/buddy-production'))
    args=parser.parse_args();config=Config()
    with sqlite3.connect(f'file:{config.data_dir/"forge.sqlite3"}?mode=ro',uri=True) as db:
        row=db.execute('SELECT data FROM projects WHERE id=?',(PROJECT,)).fetchone()
        stock=[json.loads(r[0]) for r in db.execute('SELECT data FROM filaments')]
    if row is None:raise ValueError('Reviewed local Buddy project missing')
    project=json.loads(row[0]);root=config.data_dir/'projects'/PROJECT;mesh=project['artifacts']['mesh']
    source=safe_asset_path(root,mesh['source']['path'])
    if mesh['hash']!=MESH_HASH or mesh['source']['sha256']!=SOURCE_SHA256 or hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA256:
        raise ValueError('Buddy source changed; a fresh anatomical review is required')
    reference=json.loads(safe_asset_path(root,project['artifacts']['plan']['document']).read_text())
    settings=dict(project['settings']);settings.update(pin_clearance_mm=.05,build_volume_mm=[300,320,320],plate_margin_mm=10,part_gap_mm=20)
    surface=load_surface(source,settings['height_mm'],settings['up_axis'])
    out=args.output_root/('service-'+uid());out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    plan,suggestion=suggest_buddy_plan(surface,reference,settings,MESH_HASH,stock,
        current_plan=reference if reference.get('construction_preset')=='buddy-anatomical-v1' else None)
    (out/'material-proposal.json').write_text(json.dumps(plan,indent=2)+'\n')
    (out/'suggestion-report.json').write_text(json.dumps(suggestion,indent=2)+'\n')
    print(out,flush=True)
    parts,report=construct_buddy(surface,plan,settings,reference_plan=reference,workdir=out)
    plates=pack_buddy_parts(parts,construction_report=report)
    for part in parts:part.save(out/'parts')
    report.update(source_project=PROJECT,source_sha256=SOURCE_SHA256,seconds=time.monotonic()-start,
        plates=plates,settings_overrides={'pin_clearance_mm':.05,'build_volume_mm':[300,320,320],'plate_margin_mm':10,'part_gap_mm':20},
        actual_max_world_z_mm=max(item['height_mm'] for plate in plates for item in plate['placements']))
    core_plates=copy.deepcopy(plates)
    for plate in core_plates:
        plate['volume_mm']=[350,320,320]
        for item in plate['placements']:
            item['transform'][0][3]+=25;item['rect'][0]+=25
    if not validate_packing(parts,core_plates)['passed']:raise ValueError('Invalid shared-envelope Core plate packing')
    report['native_local_plates']=plates;report['plates']=core_plates;report['core_hardware_x_offset_mm']=25
    report['core_geometry_only']=True;report['native_color_verified']=False
    export_bundle(parts,core_plates,out,metadata=report)
    report['three_mf']={p.name:validate_3mf(p) for p in out.glob('*.3mf')}
    (out/'geometry-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'output':str(out),'parts':len(parts),'plates':len(plates),'seconds':report['seconds']}),flush=True)


if __name__=='__main__':main()
