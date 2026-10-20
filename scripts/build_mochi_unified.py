"""Build a new local single-body Mochi package; never mutate source projects."""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,sqlite3,time,uuid
import numpy as np
from figuraforge.geometry.io import load_surface
from figuraforge.geometry.preview import surface_preview
from figuraforge.services.mochi_unified import source_labels,make_plan,construct,pack,PERCENTAGES
from figuraforge.services.mochi_pipeline import build_mochi_parts_preview,configure_mochi_plate
from figuraforge.services.mixed_filament import read_native_template,inspect_template,build_native_from_parts,native_bed_bounds,mark_explicit_process_overrides
from figuraforge.services.plan_materials import prepare_native_materials
from figuraforge.services.mixed_preview import build_mixed_preview


def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def review(out,surface,appearance,plates,recipes):
    viewer=Path('frontend/viewer.js').read_text().split('\n',1)[1].replace('export class Viewer','class Viewer')
    html='''<!doctype html><meta charset="utf-8"><title>Mochi · ganzer Körper · 20 Farbwerte</title>
<style>body{margin:0;font:18px system-ui;background:#f1f3f5;color:#20242c}header{padding:12px 20px}button{font:inherit;padding:10px;margin:3px;border:1px solid #aeb6bf;border-radius:7px;background:white}canvas{display:block;width:100vw;height:75vh}details{padding:8px 20px}small{font-size:15px}.swatch{display:inline-block;padding:10px;margin:3px;border-radius:5px;border:1px solid #777}</style>
<header><b>Mochi · ein Körper + schwarze Details · 180 mm</b><p>Kopf, Ohren, Schwanz und Rumpf bleiben zusammen. Nur Nase und vier schwarze Augenteile sind separat.</p>
<button id="material">Druckfarben</button><button id="original">Originaltextur</button><button id="explode">Schwarze Teile abheben</button><button id="assembly">Zusammengebaut</button><button id="face">Gesicht prüfen</button><button id="turn">45° drehen</button><button id="light">Licht an/aus</button><button id="reset">Ganze Figur</button>
<p><a href="Mochi-Koerper-20-Farben-H2D.3mf" download>Körper · natives H2D-Projekt</a> · <a href="Mochi-Schwarze-Details-H2D.3mf" download>Schwarze Details · natives H2D-Projekt</a></p>
<small>Beige31 + EarthBrown29 · 20 unkalibrierte Farbwerte (18 Mischungen + 2 reine Farben). Schwarz30 auf eigener Platte. Ziehen: drehen · Rad: zoomen.</small></header><canvas id="view"></canvas><details><summary>20 Mischrezepte ansehen</summary><div id="recipes"></div></details><script>'''
    html+="const STRATEGY_COLORS={body:'#728197',part:'#00B2FF',mixed:'#CFFF00'};const isMixedRegion=r=>r?.strategy==='mixed'||r?.color_mode==='mixed';\n"+viewer
    # Keep large arrays outside the DOM so accessibility and browser transport
    # remain responsive. All requests remain on this local preview server.
    write(out/'source-preview.json',surface_preview(surface))
    write(out/'parts-preview.json',appearance)
    write(out/'review-plates.json',plates);write(out/'review-recipes.json',recipes)
    html+='''\nPromise.all(['source-preview.json','parts-preview.json','review-plates.json','review-recipes.json'].map(p=>fetch(p).then(r=>{if(!r.ok)throw new Error('Vorschau fehlt: '+p);return r.json()}))).then(([original,assembled,plates,recipes])=>{
const v=new Viewer(document.querySelector('#view'));v.setData(assembled);v.setPlates(plates);
document.querySelector('#original').onclick=()=>{v.mode='assembly';v.setData(original)};
for(const id of ['material','assembly','explode'])document.querySelector('#'+id).onclick=()=>{v.setData(assembled);v.setMode(id==='explode'?'explode':'assembly')};
document.querySelector('#turn').onclick=()=>{v.yaw+=Math.PI/4;v.draw()};document.querySelector('#reset').onclick=()=>v.reset();document.querySelector('#light').onclick=()=>{v.lighting=!v.lighting;v.draw()};
document.querySelector('#face').onclick=()=>{v.target=[0,-38,145];v.distance=105;v.radius=50;v.draw()};
document.querySelector('#recipes').innerHTML=recipes.map(r=>`<span class="swatch" style="background:${r.color};color:${r.first_percent>50?'#222':'white'}">${r.first_percent}% Beige / ${100-r.first_percent}% Braun</span>`).join('');
}).catch(e=>{document.querySelector('header').append(document.createTextNode('Vorschau konnte nicht geladen werden: '+e.message))});</script>'''
    (out/'Mochi-Vorschau.html').write_text(html)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--head',type=Path,required=True);parser.add_argument('--template',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,default=Path('benchmarks/mochi-unified-production'))
    args=parser.parse_args();start=time.monotonic();out=args.output_root/('build-'+uuid.uuid4().hex);out.mkdir(parents=True)
    spec=importlib.util.spec_from_file_location('mochi_head_builder',Path('scripts/build_mochi_head.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    surface=module.load_refined_surface(args.head);ancestry=surface.face_tags.copy()
    v2=load_surface(Path('benchmarks/mochi-eye-detail-20261016/weighted-eyes-150k.glb'),180,'Y')
    labels=source_labels(v2,surface,ancestry)
    # The new color plan is already in refined face order, not V2 ancestry order.
    surface.face_tags=None
    with sqlite3.connect('file:data/forge.sqlite3?mode=ro',uri=True) as conn:
        stock=[json.loads(row[0]) for row in conn.execute('SELECT data FROM filaments')]
    mesh_hash=sha(args.head/'surface.npz');plan=make_plan(surface,labels,mesh_hash,stock);write(out/'plan.json',plan)
    print(json.dumps({'phase':'construct','out':str(out)}),flush=True)
    parts,construction=construct(surface,plan)
    for part in parts:part.save(out/'parts')
    write(out/'construction.json',dict(construction=construction,parts=[p.summary() for p in parts]))
    plates=pack(parts);write(out/'plates.json',plates)
    config,_=read_native_template(args.template)
    config=mark_explicit_process_overrides({**config,'layer_height':'0.16'},config)
    faces,mapping,prepared=prepare_native_materials(parts,surface,plan,inspect_template(args.template),stock,
        reference_plan=plan,native_settings=config,return_settings=True,recipe_percentages=PERCENTAGES)
    write(out/'material-mapping.json',mapping)
    origin=np.asarray(native_bed_bounds(prepared)['min']);native=[]
    for plate in plates:
        selected=[p for p in parts if p.id in {row['part_id'] for row in plate['placements']}]
        placements=[]
        for row in plate['placements']:
            tf=np.asarray(row['transform']).copy();tf[:3,3]+=origin;placements.append({**row,'transform':tf.tolist()})
        settings=configure_mochi_plate(prepared,plate)
        # Fine decorative shell. Keep explicit profile inheritance differences.
        modified=copy.deepcopy(settings);modified['layer_height']='0.16' if plate['id']==1 else '0.12'
        modified['support_top_z_distance']=modified['layer_height']
        if plate['id']==1:modified.update(wipe_tower_x=['235']*len(modified['wipe_tower_x']),wipe_tower_y=['250']*len(modified['wipe_tower_y']))
        settings=mark_explicit_process_overrides(modified,settings)
        filename='Mochi-Koerper-20-Farben-H2D.3mf' if plate['id']==1 else 'Mochi-Schwarze-Details-H2D.3mf'
        proof=build_native_from_parts(args.template,out/filename,selected,placements,settings,{p.id:faces[p.id] for p in selected})
        write(out/f'native-{plate["id"]}-verification.json',proof);native.append(filename)
    appearance,warnings=build_mochi_parts_preview(parts,surface,plan,stock,plan,prepared,recipe_percentages=PERCENTAGES)
    write(out/'parts-preview.json',appearance)
    recipes=build_mixed_preview(surface,plan,stock,layer_height_mm=.16,reference_plan=plan,native_settings=prepared,recipe_percentages=PERCENTAGES,include_geometry=False)
    write(out/'mixed-recipes.json',{k:v for k,v in recipes.items() if k not in ('preview','face_recipe_indices')})
    review(out,surface,appearance,plates,recipes['recipe_palette'])
    metadata=dict(construction=construction,parts=[p.summary() for p in parts],plates=plates,source_head=str(args.head),source_sha256=mesh_hash,
        native_template=str(args.template),native_template_sha256=sha(args.template),native_files=native,warnings=warnings,
        seconds=time.monotonic()-start,project_modified=False,paid_api_calls=0,printer_communication=False,physical_print_verified=False)
    write(out/'verification.json',metadata)
    print(json.dumps({'phase':'done','out':str(out),'parts':len(parts),'native':native,'seconds':metadata['seconds']}),flush=True)


if __name__=='__main__':main()
