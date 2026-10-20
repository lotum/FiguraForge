"""New two-color/two-plate Mochi project from immutable printed six-part geometry."""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,uuid
import numpy as np
from figuraforge.geometry.types import load_part
from figuraforge.geometry.colors import classify
from figuraforge.geometry.compare import nearest,unchanged_source_faces
from figuraforge.services.mixed_filament import read_native_template,build_native_from_parts,native_bed_bounds,mark_explicit_process_overrides
from figuraforge.services.mochi_pipeline import configure_mochi_plate
from figuraforge.services.native_plates import merge_two_native_plates


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')


def solid_face_slots(parts,surface):
    # Classify against the original three material hues, not against actual
    # spool shades: both brown classes merge, the original cream stays Beige.
    source=np.where(classify(surface.sample(),['#AF440A','#852F06','#EFB27C'])==2,2,1)
    result={};proof={}
    for part in parts:
        if part.id!='body':slots=np.full(len(part.mesh.faces),3);exterior=np.zeros(len(slots),bool)
        else:
            _,ids,_=nearest(surface,part.mesh.triangles_center)
            exterior=unchanged_source_faces(surface,part.mesh,ids,tolerance_mm=1e-6)
            slots=np.ones(len(ids),int);slots[exterior]=source[ids[exterior]]
        result[part.id]=slots.tolist();proof[part.id]={'faces':len(slots),'slot_face_counts':{str(s):int(np.sum(slots==s)) for s in np.unique(slots)},'exterior_faces':int(exterior.sum())}
    if set(result['body'])!={1,2}:raise ValueError('Body must retain both pure colors')
    return result,proof


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--template',type=Path,required=True);p.add_argument('--output-root',type=Path,default=Path('benchmarks/mochi-solid-production'));args=p.parse_args()
    src=args.source;out=args.output_root/('build-'+uuid.uuid4().hex);out.mkdir(parents=True)
    preserved={str(f):sha(f) for f in src.glob('*.3mf')}
    data=json.loads((src/'verification.json').read_text());parts=[load_part(src/'parts',r) for r in data['parts']]
    preserved.update({str(src/'parts'/f'{part.id}.npz'):sha(src/'parts'/f'{part.id}.npz') for part in parts})
    spec=importlib.util.spec_from_file_location('head',Path('scripts/build_mochi_head.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    surface=mod.load_refined_surface(Path(data['source_head']));faces,counts=solid_face_slots(parts,surface)
    write(out/'color-assignment.json',counts);print(json.dumps({'phase':'mapped','out':str(out),'counts':counts}),flush=True)
    config,_=read_native_template(args.template);origin=np.asarray(native_bed_bounds(config)['min']);files=[]
    for plate in data['plates']:
        selected=[part for part in parts if part.id in {r['part_id'] for r in plate['placements']}];placements=[]
        for row in plate['placements']:
            tf=np.asarray(row['transform']).copy();tf[:3,3]+=origin;placements.append({**row,'transform':tf.tolist()})
        settings=configure_mochi_plate(config,plate);updated=copy.deepcopy(settings)
        updated['layer_height']='0.16' if plate['id']==1 else '0.12';updated['support_top_z_distance']=updated['layer_height']
        # Same safe tower position on both source plates, even if black needs none.
        updated.update(wipe_tower_x=['235'],wipe_tower_y=['250'])
        settings=mark_explicit_process_overrides(updated,settings)
        file=out/('Koerper-Braun-Beige.3mf' if plate['id']==1 else 'Schwarze-Details.3mf')
        proof=build_native_from_parts(args.template,file,selected,placements,settings,{p.id:faces[p.id] for p in selected});write(out/f'native-{plate["id"]}.json',proof);files.append(file)
    project=out/'Mochi-Braun-Beige-H2D-2-Platten.3mf';merged=merge_two_native_plates(*files,project)
    if any(sha(Path(f))!=digest for f,digest in preserved.items()):raise ValueError('Immutable source changed')
    write(out/'verification.json',dict(source=str(src),source_files_sha256=preserved,source_preserved=True,parts=data['parts'],colors=counts,merge=merged,project=str(project),project_sha256=sha(project),paid_api_calls=0,printer_communication=False,physical_print_verified=False))
    print(json.dumps({'phase':'done','out':str(out),'project':str(project)}),flush=True)

if __name__=='__main__':main()
