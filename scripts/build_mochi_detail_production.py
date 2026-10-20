"""Build a NEW source-bound Mochi detail-v2 draft; never mutate project/approvals."""
from pathlib import Path
import argparse,json,hashlib,sqlite3,time,uuid
from figuraforge.config import Config
from figuraforge.geometry.io import load_surface
from figuraforge.services.mochi_detail_pipeline import suggest_mochi_detail_plan,construct_mochi_detail,pack_mochi_detail_parts,MESH_HASH,SOURCE_SHA256
from figuraforge.services.mochi_pipeline import pack_mochi_parts,build_mochi_parts_preview,configure_mochi_plate
from figuraforge.services.export import export_bundle,validate_3mf


def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True,type=Path);parser.add_argument('--reference-plan',required=True,type=Path)
    parser.add_argument('--project',default='1b0e2fdd463d4f15ac64f1c7b3e8acc7')
    parser.add_argument('--output-root',type=Path,default=Path('benchmarks/mochi-detail-production'))
    parser.add_argument('--native-template',type=Path)
    args=parser.parse_args();began=time.monotonic();config=Config()
    if hashlib.sha256(args.source.read_bytes()).hexdigest()!=SOURCE_SHA256:raise ValueError('Detail-v2 source bytes differ from the reviewed copy')
    with sqlite3.connect(f'file:{config.data_dir/"forge.sqlite3"}?mode=ro',uri=True) as connection:
        row=connection.execute('SELECT data FROM projects WHERE id=?',(args.project,)).fetchone()
        stock=[json.loads(r[0]) for r in connection.execute('SELECT data FROM filaments')]
    if row is None:raise ValueError('Project inventory/settings context does not exist')
    project=json.loads(row[0]);settings=dict(project['settings'],pin_clearance_mm=.05)
    reference=json.loads(args.reference_plan.read_text());surface=load_surface(args.source,180,'Y')
    current=None;artifact=project['artifacts'].get('plan')
    if artifact:current=json.loads((config.data_dir/'projects'/args.project/artifact['document']).read_text())
    plan,proposal=suggest_mochi_detail_plan(surface,reference,settings,MESH_HASH,stock,current_plan=current)
    out=args.output_root/('draft-'+uuid.uuid4().hex);out.mkdir(parents=True)
    write(out/'plan.json',plan);write(out/'reference-plan.json',reference);write(out/'proposal.json',proposal)
    print(json.dumps({'phase':'construct','output':str(out)}),flush=True)
    parts,construction=construct_mochi_detail(surface,plan,settings,reference_plan=reference)
    for part in parts:part.save(out/'parts')
    plates=pack_mochi_detail_parts(parts,settings['build_volume_mm'],settings['plate_margin_mm'],settings['part_gap_mm'])
    preview,warnings=build_mochi_parts_preview(parts,surface,plan,stock,plan)
    write(out/'parts-preview.json',preview)
    report={'source_sha256':SOURCE_SHA256,'mesh_hash':MESH_HASH,'construction':construction,
            'parts':[part.summary() for part in parts],'plates':plates,'warnings':warnings,
            'settings':settings,'main_project_modified':False,'physical_fit_verified':False,'source_modified':False}
    export_bundle(parts,plates,out/'core-export',report)
    report['core_roundtrips']={f.name:validate_3mf(f) for f in (out/'core-export').glob('*.3mf')}
    if args.native_template:
        import numpy as np
        from figuraforge.services.mixed_filament import read_native_template,inspect_template,build_native_from_parts,native_bed_bounds
        from figuraforge.services.plan_materials import prepare_native_materials
        config_native,_=read_native_template(args.native_template)
        faces,mapping,prepared=prepare_native_materials(parts,surface,plan,inspect_template(args.native_template),stock,
            native_settings=config_native,reference_plan=plan,return_settings=True)
        directory=out/'native-export';directory.mkdir();write(directory/'material-mapping.json',mapping)
        origin=np.asarray(native_bed_bounds(prepared)['min'])
        for plate in plates:
            selected=[p for p in parts if p.id in {row['part_id'] for row in plate['placements']}]
            placements=[]
            for row in plate['placements']:
                transform=np.asarray(row['transform']).copy();transform[:3,3]+=origin
                placements.append({**row,'transform':transform.tolist()})
            verified=build_native_from_parts(args.native_template,directory/f'plate-{plate["id"]:02d}-native.3mf',
                selected,placements,configure_mochi_plate(prepared,plate),{part.id:faces[part.id] for part in selected})
            write(directory/f'plate-{plate["id"]:02d}-verification.json',verified)
    report['elapsed_seconds']=time.monotonic()-began;write(out/'verification.json',report)
    print(json.dumps({'phase':'done','output':str(out),'parts':len(parts),'pins':construction['pins'],'seconds':report['elapsed_seconds']}),flush=True)


if __name__=='__main__':main()
