"""Reproducible, unpaid geometric benchmark on the included original fixture."""
from pathlib import Path
import argparse,json,time,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from figuraforge.geometry.io import load_surface
from figuraforge.geometry.colors import choose_palette
from figuraforge.geometry.refine import refine_for_color
from figuraforge.geometry.construct import make_inlays
from figuraforge.geometry.split import tile_parts
from figuraforge.geometry.packing import pack_parts,validate_packing
from figuraforge.geometry.types import Part
from figuraforge.services.export import export_bundle


def run(height,out):
    out.mkdir(parents=True,exist_ok=True);start=time.perf_counter();times={}
    def timed(name):times[name]=round(time.perf_counter()-start,3);print(name,times[name],flush=True)
    def progress(s):print(s,flush=True)
    surface=load_surface(ROOT/'examples/teddy-source.glb',height,'Y')
    palette=choose_palette(surface.sample(),3,weights=surface.mesh.area_faces);timed('import')
    # The large benchmark intentionally uses a coarser but explicit 2 mm color sampling.
    tolerance=2 if height>=500 else .65
    surface,labels,refinement=refine_for_color(surface,palette,tolerance,8 if height>=500 else 4,500000,progress)
    timed('refinement')
    parts,construction=make_inlays(surface.mesh,labels,palette,depth_mm=5 if height>=500 else 3.2,
        pin_radius_mm=2.5 if height>=500 else 1.5,pin_length_mm=7 if height>=500 else 4,validate_paths=True,progress=progress)
    original_parts=len(parts);timed('organic_construction')
    parts,tiling=tile_parts(parts,progress=progress);timed('structural_tiling')
    plates=pack_parts(parts,max_colors=1);timed('packing')
    snapshots=[p.save(out/'parts') for p in parts]
    result=export_bundle(parts,plates,out/'print',{'benchmark':True,'height_mm':height,'palette':palette,
                    'refinement':refinement,'construction':construction,'tiling':tiling,'actual_cloud_cost_eur':0})
    timed('export')
    report={'height_mm':height,'parts_before_tiling':original_parts,'final_parts':len(parts),'plates':len(plates),
        'all_parts_watertight':all(p.mesh.is_volume for p in parts),'components_per_part':{p.id:len(p.mesh.split(only_watertight=False)) for p in parts},
        'packing':validate_packing(parts,plates),'timings_cumulative_seconds':times,'refinement':refinement,
        'construction':construction,'tiling':tiling,'parts':snapshots,'export':result,'physical_print_test':False,
        'budget_notice':'No external API call; zero cloud cost for this procedural fixture.'}
    (out/'benchmark.json').write_text(json.dumps(report,indent=2))
    return report
if __name__=='__main__':
    import os, faulthandler
    if os.getenv('FORGE_DEBUG_STACKS'):
        faulthandler.dump_traceback_later(15, repeat=True)
    parser=argparse.ArgumentParser();parser.add_argument('--height',type=float,default=180);parser.add_argument('--output',type=Path)
    args=parser.parse_args();output=args.output or ROOT/'benchmarks'/str(int(args.height))
    try:report=run(args.height,output);print(json.dumps({k:report[k] for k in ('height_mm','final_parts','plates','all_parts_watertight')},indent=2))
    except Exception as exc:
        output.mkdir(parents=True,exist_ok=True);(output/'failure.json').write_text(json.dumps({'height_mm':args.height,'error':str(exc)},indent=2));raise
