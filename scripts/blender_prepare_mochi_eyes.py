"""Experimental new 150k copy: preserve eye/nose geometry in original coordinates."""
from pathlib import Path
import bpy,bmesh,numpy as np,time,json,argparse,sys,uuid
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-root',type=Path,default=ROOT/'benchmarks/mochi-eye-preparation');args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);WORK=args.output_root.resolve()/('eyes-'+uuid.uuid4().hex);WORK.mkdir(parents=True);output=WORK/'weighted-eyes-150k.glb'
if output.exists():raise ValueError('Never overwrite review files')
start=time.monotonic();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(ROOT/'data/projects/1b0e2fdd463d4f15ac64f1c7b3e8acc7/inputs/original-source.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];points=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box];mins=np.array([min(p[i] for p in points) for i in range(3)]);maxs=np.array([max(p[i] for p in points) for i in range(3)]);scale=180/(maxs[2]-mins[2]);center=np.array([(maxs[0]+mins[0])/2,(maxs[1]+mins[1])/2,mins[2]])
before=0
for ob in meshes:ob.data.calc_loop_triangles();before+=len(ob.data.loop_triangles)
rows=[]
for ob in meshes:
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()
 v=np.empty(len(ob.data.vertices)*3);ob.data.vertices.foreach_get('co',v);v=v.reshape(-1,3);m=np.asarray(ob.matrix_world);v=(v@m[:3,:3].T+m[:3,3]-center)*scale
 radius=np.full(len(v),10.)
 for origin,axes in [((-12.5,-53.5,140),(8,10,10)),((12.5,-53.5,140),(8,10,10)),((0,-66,129),(6,6,6))]:radius=np.minimum(radius,np.linalg.norm((v-np.array(origin))/np.array(axes),axis=1))
 # Zero weights never collapse (official bmesh_decimate_collapse.cc). A narrow
 # graded band relaxes protection before the unchanged body weight1 region.
 weights=np.clip((radius-1)/.25,0,1);group=ob.vertex_groups.new(name='Collapse allowance - eye nose preservation');group.add(list(range(len(v))),1.,'REPLACE')
 for index in range(21):
  mask=(np.rint(weights*20)==index);ids=np.flatnonzero(mask)
  if len(ids):group.add(ids.tolist(),index/20,'REPLACE')
 bpy.context.view_layer.objects.active=ob;ob.select_set(True);mod=ob.modifiers.new('Experimental eye detail allocation','DECIMATE');mod.decimate_type='COLLAPSE';mod.ratio=150000/before;mod.use_collapse_triangulate=True;mod.vertex_group=group.name;mod.vertex_group_factor=1.;bpy.ops.object.modifier_apply(modifier=mod.name);ob.select_set(False);ob.data.calc_loop_triangles()
 rows.append({'object':ob.name,'protected_vertices':int((weights==0).sum()),'transition_vertices':int(((weights>0)&(weights<1)).sum()),'output_faces':len(ob.data.loop_triangles)})
bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',export_image_format='AUTO',export_materials='EXPORT',export_texcoords=True,export_normals=True)
(WORK/'weighted-preparation.json').write_text(json.dumps({'input_faces':before,'target_faces':150000,'objects':rows,'seconds':time.monotonic()-start,'original_preserved':True,'main_plan_modified':False,'known_anatomy_preset_valid_for_new_copy':False,'protection':'Original ellipsoids around two eyes and nose; zero collapse allowance, .25-radius transition. Raw geometry and UV coordinates exported; no shape smoothing/remeshing.','threads':2},indent=2)+'\n');print('WEIGHTED_PREPARATION_DONE',rows,flush=True)
