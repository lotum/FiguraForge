"""Read-only comparison of two actual warm Mochi inventory pairs; no plan adoption."""
from pathlib import Path
import argparse,json,sqlite3,uuid,hashlib
from copy import deepcopy
import numpy as np
import trimesh
from figuraforge.config import Config
from figuraforge.geometry.io import load_surface
from figuraforge.geometry.colors import hex_rgb,srgb_to_lab,delta_e_2000
from figuraforge.services.mixed_preview import build_mixed_preview
from figuraforge.services.mochi_pipeline import SOURCE_SHA256

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-root',type=Path,default=Path('benchmarks/mochi-material-comparison'));args=parser.parse_args()
config=Config();source=config.data_dir/'projects/1b0e2fdd463d4f15ac64f1c7b3e8acc7/inputs/working-copy.glb'
assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA256
surface=load_surface(source,180,'Y');reference=json.loads(Path('benchmarks/mochi-production/draft-9372a14613a141a888aac191637a22e4/color-plan.json').read_text())
with sqlite3.connect(f'file:{config.data_dir/"forge.sqlite3"}?mode=ro',uri=True) as connection:stock=[json.loads(row[0]) for row in connection.execute('SELECT data FROM filaments')]
lookup={s['id']:s for s in stock};work=args.output_root/('comparison-'+uuid.uuid4().hex);work.mkdir(parents=True)
report={'method':'Identical original Mochi source triangles and 19 linear-light estimated palette colors, nearest CIEDE2000, same immutable color baseline','uncalibrated':True,'project_plan_modified':False,'source_sha256':SOURCE_SHA256,'variants':{}}
for brown in [29,28]:
 name=f'brown-{brown}';plan=deepcopy(reference);plan['filament_ids']=['richard-inventory-202609-31',f'richard-inventory-202609-{brown}']
 preview=build_mixed_preview(surface,plan,stock,reference_plan=reference,include_geometry=False);indices=np.asarray(preview['face_recipe_indices']);mixed=indices>=0
 rgb=np.zeros((len(indices),3));palette=np.array([hex_rgb(row['color']) for row in preview['recipe_palette']]);rgb[mixed]=palette[indices[mixed]]
 for region in plan['regions']:
  if region['color_mode']!='mixed':rgb[np.asarray(plan['face_regions'])==region['id']]=hex_rgb(lookup[region['filament_id']]['hex'])
 errors=delta_e_2000(srgb_to_lab(surface.sample()[mixed]),srgb_to_lab(rgb[mixed]));areas=surface.mesh.area_faces[mixed]
 regions={}
 for region in plan['regions']:
  if region['color_mode']!='mixed':continue
  mask=np.asarray(plan['face_regions'])[mixed]==region['id'];regions[region['name']]={'area_weighted_mean':float(np.average(errors[mask],weights=areas[mask])),'median':float(np.median(errors[mask])),'p95':float(np.quantile(errors[mask],.95))}
 report['variants'][name]={'spools':[{'id':s['id'],'name':s['name'],'hex':s['hex'],'material':s['material']} for s in [lookup[i] for i in plan['filament_ids']]],'mixed_faces':int(mixed.sum()),'area_weighted_mean_delta_e_2000':float(np.average(errors,weights=areas)),'median_delta_e_2000':float(np.median(errors)),'p95_delta_e_2000':float(np.quantile(errors,.95)),'per_region':regions,'used_recipe_counts':np.bincount(indices[mixed],minlength=19).tolist()}
 linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);rgba=np.column_stack([np.rint(np.clip(linear,0,1)*255).astype(np.uint8),np.full(len(rgb),255,dtype=np.uint8)]);rgba=np.repeat(rgba,3,axis=0)
 mesh=trimesh.Trimesh(vertices=surface.mesh.triangles.reshape(-1,3),faces=np.arange(len(rgb)*3).reshape(-1,3),vertex_normals=surface.mesh.vertex_normals[surface.mesh.faces].reshape(-1,3),vertex_colors=rgba,process=False)
 mesh.apply_transform(np.array([[.001,0,0,0],[0,0,.001,0],[0,-.001,0,0],[0,0,0,1]]));(work/f'{name}.glb').write_bytes(mesh.export(file_type='glb'));(work/f'{name}-plan-draft.json').write_text(json.dumps(plan,indent=2)+'\n')
(work/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'output':str(work),'variants':{k:{f:v[f] for f in ['area_weighted_mean_delta_e_2000','median_delta_e_2000','p95_delta_e_2000']} for k,v in report['variants'].items()}},indent=2))
