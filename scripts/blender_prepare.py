"""Create a separate textured, decimated GLB. Run using Blender --background."""
import argparse
import json
import sys
import time
from pathlib import Path


def main():
    import bpy
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--faces',type=int,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    source=Path(args.source).resolve();output=Path(args.output).resolve()
    if output.exists() or output==source: raise ValueError('Output must be a new file; original is preserved')
    if args.faces<1000: raise ValueError('Target must be at least 1000 triangles')
    started=time.monotonic()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    def count():
        total=0
        for obj in meshes:
            obj.data.calc_loop_triangles();total+=len(obj.data.loop_triangles)
        return total
    before=count();ratio=min(1.,args.faces/max(1,before))
    for obj in meshes:
        # GLB splits vertices at UV seams. Weld coincident positions before
        # collapse; UVs remain loop attributes. Otherwise both sides collapse
        # independently and may open cracks in a previously closed surface.
        import bmesh
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-8)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(obj.data);bm.free();obj.data.update()
        bpy.context.view_layer.objects.active=obj
        obj.select_set(True)
        modifier=obj.modifiers.new('FiguraForge working copy','DECIMATE')
        modifier.decimate_type='COLLAPSE';modifier.ratio=ratio;modifier.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        obj.select_set(False)
    output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',export_image_format='AUTO',
                              export_materials='EXPORT',export_texcoords=True,export_normals=True)
    report={'method':'Blender Decimate / COLLAPSE','blender_version':bpy.app.version_string,
            'input_faces':before,'target_faces':args.faces,'output_faces':count(),
            'seconds':round(time.monotonic()-started,3),'source_preserved':True,
            'note':'UVs/materials exported; shape, color and topology must be independently checked.'}
    output.with_suffix('.preparation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('FIGURAFORGE_PREPARATION '+json.dumps(report),flush=True)


if __name__=='__main__': main()
