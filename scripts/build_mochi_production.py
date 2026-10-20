"""Build/review an offline source-bound Mochi draft; never mutate project state.

Run PYTHONPATH=backend .venv/bin/python scripts/build_mochi_production.py --project ID
Optional --native-template points to an actual matching H2D project. No cloud,
printer or approval calls. Outputs always use a new directory; sources survive.
"""
from pathlib import Path
import argparse,hashlib,json,sqlite3,time
import numpy as np
from figuraforge.config import Config
from figuraforge.db import uid,digest
from figuraforge.geometry.io import load_surface
from figuraforge.geometry.packing import pack_parts
from figuraforge.geometry.preview import parts_preview
from figuraforge.services.export import export_bundle,validate_3mf
from figuraforge.services.mochi_pipeline import suggest_mochi_plan,construct_mochi,pack_mochi_parts,build_mochi_parts_preview,configure_mochi_plate,SOURCE_SHA256
from figuraforge.services.mixed_preview import build_mixed_preview
from figuraforge.services.plan_materials import prepare_native_materials
from figuraforge.services.mixed_filament import inspect_template,read_native_template,build_native_from_parts,native_bed_bounds
from figuraforge.security import safe_asset_path


def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--project',required=True)
    parser.add_argument('--output-root',type=Path,default=Path('benchmarks/mochi-production'))
    parser.add_argument('--native-template',type=Path)
    args=parser.parse_args();config=Config();began=time.monotonic()
    with sqlite3.connect(f'file:{config.data_dir/"forge.sqlite3"}?mode=ro',uri=True) as connection:
        row=connection.execute('SELECT data FROM projects WHERE id=?',(args.project,)).fetchone()
        filaments=[json.loads(r[0]) for r in connection.execute('SELECT data FROM filaments')]
    if not row:raise ValueError('Source project does not exist')
    project=json.loads(row[0]);root=config.data_dir/'projects'/project['id'];mesh=project['artifacts']['mesh'];artifact=project['artifacts']['plan']
    source=safe_asset_path(root,mesh['source']['path'])
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA256:raise ValueError('Mochi original SHA changed')
    reference=json.loads(safe_asset_path(root,artifact.get('construction_reference_document',artifact.get('reference_document',artifact['document']))).read_text())
    current=json.loads(safe_asset_path(root,artifact['document']).read_text())
    surface=load_surface(source,180,'Y')
    plan,proposal=suggest_mochi_plan(surface,reference,project['settings'],mesh['hash'],filaments,current_plan=current)
    output=args.output_root/('draft-'+uid());output.mkdir(parents=True)
    write(output/'source-reference-plan.json',reference);write(output/'color-plan.json',plan);write(output/'color-reference-plan.json',plan)
    write(output/'anatomical-proposal.json',proposal)
    print(json.dumps({'output':str(output),'phase':'construct','plan_hash':digest(plan)}),flush=True)
    parts,construction=construct_mochi(surface,plan,project['settings'],reference_plan=reference)
    for part in parts:part.save(output/'parts')
    preview=build_mixed_preview(surface,plan,filaments,reference_plan=plan)
    appearance,appearance_warnings=build_mochi_parts_preview(parts,surface,plan,filaments,plan)
    write(output/'mixed-preview.json',preview);write(output/'parts-preview.json',appearance)
    write(output/'appearance-warnings.json',appearance_warnings)
    import base64,trimesh
    scene=trimesh.Scene()
    for record in appearance['meshes']:
        positions=np.frombuffer(base64.b64decode(record['positions']),dtype='<f4').reshape(-1,3)
        normals=np.frombuffer(base64.b64decode(record['normals']),dtype='<f4').reshape(-1,3)
        rgb=np.frombuffer(base64.b64decode(record['colors']),dtype='<f4').reshape(-1,3)
        linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
        rgba=np.column_stack([np.rint(np.clip(linear,0,1)*255).astype(np.uint8),np.full(len(rgb),255,dtype=np.uint8)])
        mesh_preview=trimesh.Trimesh(vertices=positions,faces=np.arange(len(positions)).reshape(-1,3),vertex_normals=normals,vertex_colors=rgba,process=False)
        scene.add_geometry(mesh_preview,node_name=record['id'],geom_name=record['id'])
    scene.apply_transform(np.array([[.001,0,0,0],[0,0,.001,0],[0,-.001,0,0],[0,0,0,1]]))
    (output/'appearance-preview.glb').write_bytes(scene.export(file_type='glb'))
    plates=pack_mochi_parts(parts,volume=(300,320,320),margin=8)
    metadata={'kind':'Mochi source-bound anatomical production draft','source_project':project['id'],
              'source_sha256':SOURCE_SHA256,'mesh_hash':mesh['hash'],'plan_hash':digest(plan),
              'source_reference_hash':digest(reference),'construction':construction,
              'selected_basis':proposal['selected_basis'],'black_filament':proposal['black_filament'],
              'approval_created':False,'physical_fit_verified':False,'physical_color_verified':False,
              'native_gui_verified':False,'originals_modified':False}
    export_bundle(parts,plates,output/'core-export',metadata)
    roundtrips={p.name:validate_3mf(p) for p in (output/'core-export').glob('*.3mf')}
    write(output/'geometry-check.json',{'metadata':metadata,'parts':[p.summary() for p in parts],
                                     'plates':plates,'three_mf_roundtrips':roundtrips})
    if args.native_template:
        native_dir=output/'native-export';native_dir.mkdir()
        template=inspect_template(args.native_template);native_settings,_=read_native_template(args.native_template)
        faces,material_report,prepared=prepare_native_materials(parts,surface,plan,template,filaments,
            native_settings=native_settings,reference_plan=plan,return_settings=True)
        write(native_dir/'material-mapping.json',material_report)
        origin=np.array(native_bed_bounds(prepared)['min'])
        for plate in plates:
            chosen=[p for p in parts if p.id in {r['part_id'] for r in plate['placements']}]
            placements=[]
            for row in plate['placements']:
                item=dict(row);transform=np.asarray(row['transform']).copy();transform[:3,3]+=origin;item['transform']=transform.tolist();placements.append(item)
            report=build_native_from_parts(args.native_template,native_dir/f'plate-{plate["id"]:02d}.3mf',chosen,placements,configure_mochi_plate(prepared,plate),{p.id:faces[p.id] for p in chosen})
            write(native_dir/f'plate-{plate["id"]:02d}-verification.json',report)
    write(output/'run-summary.json',{'output':str(output),'seconds':time.monotonic()-began,'parts':len(parts),
          'pins':construction['pins'],'glue_parts':construction['glue_parts'],'plates':len(plates),
          'native_template_used':str(args.native_template) if args.native_template else None,'physical_fit_verified':False})
    print(json.dumps({'output':str(output),'phase':'complete','seconds':time.monotonic()-began,'parts':len(parts),'pins':construction['pins'],'plates':len(plates)}),flush=True)


if __name__=='__main__':main()
