"""Offline A/B material-basis appearance proposal. No project/service mutation."""
from pathlib import Path
import json,sqlite3,hashlib,uuid
import numpy as np
import trimesh
from figuraforge.config import Config
from figuraforge.geometry.io import load_surface
from figuraforge.geometry.types import Surface
from figuraforge.geometry.colors import hex_rgb
from figuraforge.services.mixed_preview import build_mixed_preview
from figuraforge.services.mochi_pipeline import SOURCE_SHA256
config=Config();source=config.data_dir/'projects/1b0e2fdd463d4f15ac64f1c7b3e8acc7/inputs/working-copy.glb';assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA256
surface=load_surface(source,180,'Y');draft=Path('benchmarks/mochi-production/draft-9372a14613a141a888aac191637a22e4');plan=json.loads((draft/'color-plan.json').read_text());original=json.loads((draft/'source-reference-plan.json').read_text());labels=np.asarray(plan['face_regions']);classes=np.asarray(original['face_regions']);oldrgb=surface.sample();newrgb=oldrgb.copy();tail=labels==4;dark=(labels==1)|(labels>=5);unify=~tail&~dark
# Explicitly selected original palette classes, not a de-lighting estimate.
orange=hex_rgb(next(r['color'] for r in original['regions'] if r['id']==0));cream=hex_rgb(next(r['color'] for r in original['regions'] if r['id']==2))
newrgb[unify&np.isin(classes,[0,1])]=orange;newrgb[unify&(classes==2)]=cream
prototype=Surface(surface.mesh,np.zeros_like(surface.corner_uv),np.repeat(newrgb[:,None,:],3,axis=1),np.zeros(len(newrgb),int))
with sqlite3.connect(f'file:{config.data_dir/"forge.sqlite3"}?mode=ro',uri=True) as conn:stock=[json.loads(row[0]) for row in conn.execute('SELECT data FROM filaments')]
byid={s['id']:s for s in stock};work=Path('benchmarks/mochi-material-basis')/('prototype-'+uuid.uuid4().hex);work.mkdir(parents=True)
report={'prototype_only':True,'source_sha256':SOURCE_SHA256,'source_file_unchanged':True,'project_plan_modified':False,'service_modified':False,'basis_pair':plan['filament_ids'],'method':'Explicit original orange/dark-orange classes merged into orange #AF440A; cream class #EFB27C; tail original per-face RGB unchanged; black constructed parts unchanged. Same 19 optical recipes and immutable reference. No lighting separation inferred.','variants':{}}
assignments={}
for name,variant in [('original-albedo',surface),('material-basis-proposal',prototype)]:
 preview=build_mixed_preview(variant,plan,stock,reference_plan=plan,include_geometry=False);indices=np.asarray(preview['face_recipe_indices']);mixed=indices>=0;assignments[name]=indices
 palette=np.array([hex_rgb(r['color']) for r in preview['recipe_palette']]);rgb=np.zeros((len(indices),3));rgb[mixed]=palette[indices[mixed]]
 for region in plan['regions']:
  if region['color_mode']!='mixed':rgb[labels==region['id']]=hex_rgb(byid[region['filament_id']]['hex'])
 linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);rgba=np.column_stack([np.rint(np.clip(linear,0,1)*255).astype(np.uint8),np.full(len(rgb),255,dtype=np.uint8)]);rgba=np.repeat(rgba,3,axis=0)
 mesh=trimesh.Trimesh(vertices=surface.mesh.triangles.reshape(-1,3),faces=np.arange(len(rgb)*3).reshape(-1,3),vertex_normals=surface.mesh.vertex_normals[surface.mesh.faces].reshape(-1,3),vertex_colors=rgba,process=False);mesh.apply_transform(np.array([[.001,0,0,0],[0,0,.001,0],[0,-.001,0,0],[0,0,0,1]]));(work/f'{name}.glb').write_bytes(mesh.export(file_type='glb'))
 report['variants'][name]={'per_region_used_recipes':{region['name']:sorted(set(indices[labels==region['id']].tolist())-{-1}) for region in plan['regions']},'matching_error_against_own_target':preview['matching_error_delta_e']}
report.update(changed_recipe_faces=int((assignments['original-albedo']!=assignments['material-basis-proposal']).sum()),changed_body_recipe_faces=int(((assignments['original-albedo']!=assignments['material-basis-proposal'])&(labels==0)).sum()),tail_recipe_assignments_exactly_preserved=bool(np.array_equal(assignments['original-albedo'][tail],assignments['material-basis-proposal'][tail])),dark_recipe_assignments_exactly_preserved=bool(np.array_equal(assignments['original-albedo'][dark],assignments['material-basis-proposal'][dark])),geometry_vertices_exactly_preserved=bool(np.array_equal(surface.mesh.vertices,prototype.mesh.vertices)))
(work/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'output':str(work),'changed_faces':report['changed_recipe_faces'],'tail_unchanged':report['tail_recipe_assignments_exactly_preserved'],'body_recipe_counts':{k:len(v['per_region_used_recipes']['Mochi Grundkoerper']) for k,v in report['variants'].items()}},indent=2))
