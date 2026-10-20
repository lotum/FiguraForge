from __future__ import annotations
import io
import json
import struct
from pathlib import Path
import numpy as np
import trimesh
from .types import Surface, GeometryError

# Current provider output can exceed 500k faces without remeshing. Inspection
# stays in the killable native worker; retain a bounded one-million-face cap.
MAX_FACES=1_000_000


def validate_glb_bytes(data: bytes) -> dict:
    if len(data)<20 or data[:4] != b'glTF':
        raise GeometryError('Invalid GLB header')
    _,version,length=struct.unpack_from('<III',data)
    if version!=2 or length != len(data):
        raise GeometryError('Only complete GLB version 2 files are supported')
    size,kind=struct.unpack_from('<II',data,12)
    if kind != 0x4E4F534A or size > len(data)-20:
        raise GeometryError('Missing GLB JSON chunk')
    doc=json.loads(data[20:20+size])
    for key in ('images','buffers'):
        for item in doc.get(key,[]):
            uri=item.get('uri','')
            if uri and not uri.startswith('data:'):
                raise GeometryError('External GLB resources are disabled; embed textures and buffers')
    unsupported=set(doc.get('extensionsRequired',[])) & {'KHR_draco_mesh_compression','EXT_meshopt_compression','KHR_texture_basisu'}
    if unsupported:
        raise GeometryError('Re-export an uncompressed GLB; unsupported required extensions: '+', '.join(sorted(unsupported)))
    if len(doc.get('nodes',[]))>10000:
        raise GeometryError('Too many scene nodes')
    return doc


def load_surface(path: Path, height_mm: float=180, up_axis: str='Y', *, max_faces=None) -> Surface:
    data=path.read_bytes()
    ext=path.suffix.lower()
    if ext=='.glb': validate_glb_bytes(data)
    elif ext not in ('.stl','.ply'):
        raise GeometryError('Import GLB (with colors), STL or PLY')
    scene=trimesh.load(io.BytesIO(data),file_type=ext[1:],force='scene',process=False)
    vertices=[]; faces=[]; uvs=[]; rgbs=[]; ids=[]; textures=[]; factors=[]; offset=0
    for node in scene.graph.nodes_geometry:
        tf,name=scene.graph.get(node)
        m=scene.geometry[name]
        if not isinstance(m,trimesh.Trimesh) or not len(m.faces): continue
        v=trimesh.transform_points(m.vertices,tf)
        if np.linalg.det(tf[:3,:3])<0:
            m=m.copy(); m.faces=m.faces[:,::-1]
        vertices.append(v); faces.append(m.faces+offset); offset+=len(v)
        visual=m.visual
        if getattr(visual,'kind',None)=='texture':
            mats=getattr(visual.material,'materials',None) or [visual.material]
            fm=getattr(visual,'face_materials',None)
            fm=np.zeros(len(m.faces),dtype=int) if fm is None else np.asarray(fm)
            mid_base=len(textures)
            ids.append(fm+mid_base)
            uv=np.asarray(visual.uv) if visual.uv is not None else np.zeros((len(v),2))
            uvs.append(uv[m.faces])
            corner=np.ones((len(m.faces),3,3))
            for j,mat in enumerate(mats):
                img=getattr(mat,'baseColorTexture',None)
                if img is None: img=getattr(mat,'image',None)
                factor=getattr(mat,'baseColorFactor',None)
                if factor is None: factor=getattr(mat,'diffuse',np.array([255,255,255,255]))
                factor=np.asarray(factor,float)
                if factor.max()>1: factor/=255
                if len(factor)==3: factor=np.r_[factor,1]
                textures.append(img); factors.append(factor)
                if img is None:
                    # A baseColorFactor without a texture is linear RGB in glTF.
                    color=np.where(factor[:3]<=.0031308,12.92*factor[:3],1.055*factor[:3]**(1/2.4)-.055)
                    corner[fm==j]=color
            rgbs.append(corner)
        else:
            ids.append(np.full(len(m.faces),len(textures)))
            textures.append(None); factors.append(np.ones(4))
            uvs.append(np.zeros((len(m.faces),3,2)))
            if visual.kind=='vertex':
                c=np.asarray(visual.vertex_colors)[:,:3]/255
                rgbs.append(c[m.faces])
            elif visual.kind=='face':
                c=np.asarray(visual.face_colors)[:,:3]/255
                rgbs.append(np.repeat(c[:,None,:],3,axis=1))
            else: rgbs.append(np.full((len(m.faces),3,3),.68))
    if not faces: raise GeometryError('No triangular mesh found')
    f=np.concatenate(faces); v=np.concatenate(vertices)
    limit=MAX_FACES if max_faces is None else max_faces
    if len(f)>limit: raise GeometryError(f'Mesh has {len(f):,} faces; remesh below {limit:,} before import')
    if not np.isfinite(v).all(): raise GeometryError('Mesh contains non-finite coordinates')
    if up_axis.upper()=='Y': v=v[:,[0,2,1]]; v[:,1]*=-1
    elif up_axis.upper()=='X': v=v[:,[1,2,0]]
    elif up_axis.upper()!='Z': raise GeometryError('up_axis must be X, Y or Z')
    span=np.ptp(v,axis=0)
    if span[2]<=1e-9: raise GeometryError('The selected up-axis has zero extent')
    v*=height_mm/span[2]
    v[:,0]-=(v[:,0].max()+v[:,0].min())/2
    v[:,1]-=(v[:,1].max()+v[:,1].min())/2
    v[:,2]-=v[:,2].min()
    mesh=trimesh.Trimesh(v,f,process=False)
    # Weld positional UV seams but retain per-corner UVs separately.
    mesh.merge_vertices(digits_vertex=7)
    valid_faces=mesh.nondegenerate_faces(height=1e-8) & mesh.unique_faces()
    warnings=[]
    if not valid_faces.all():
        warnings.append(f'Removed {int((~valid_faces).sum())} zero-area/duplicate triangles without remeshing.')
        mesh.update_faces(valid_faces)
        mesh.remove_unreferenced_vertices()
    if ext=='.stl': warnings.append('STL contains no reliable standard color data. Assign a palette or use GLB.')
    if ext=='.glb': warnings.append('Texture sampling assumes standard UV0/base color. Texture transforms and custom samplers require baking before import.')
    return Surface(mesh,np.concatenate(uvs)[valid_faces],np.concatenate(rgbs)[valid_faces],np.concatenate(ids)[valid_faces],textures,factors,warnings)


def save_colored_glb(mesh: trimesh.Trimesh, labels: np.ndarray, palette: list[str], path: Path):
    from .colors import hex_rgb
    c=np.array([np.r_[hex_rgb(x)*255,255] for x in palette],dtype=np.uint8)
    out=mesh.copy(); out.visual=trimesh.visual.ColorVisuals(out,face_colors=c[labels])
    path.write_bytes(out.export(file_type='glb'))
