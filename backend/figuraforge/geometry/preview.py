from __future__ import annotations
import base64
import io
import numpy as np


def _encode(array):
    return base64.b64encode(np.asarray(array,dtype='<f4').tobytes()).decode('ascii')


def _corner_values(value,faces,name):
    array=np.asarray(value,dtype='<f4')
    if array.shape!=(faces,3,3) or not np.isfinite(array).all():
        raise ValueError(f'{name} must be a finite faces by 3 by 3 array')
    return array


def _mesh_record(positions,normals,colors,*,color,ident,name,role,direction):
    points=np.asarray(positions,dtype='<f4').reshape(-1,3)
    return {'id':ident,'name':name,'role':role,'color':color,
            'positions':_encode(points),'normals':_encode(normals),
            'colors':None if colors is None else _encode(colors),
            'vertex_count':len(points),'bounds':[points.min(axis=0).tolist(),points.max(axis=0).tolist()],
            'center':points.mean(axis=0).tolist(),'direction':direction}


def mesh_preview(mesh, color='#9CA3AF', face_rgb=None, ident='mesh', name='Mesh', role='model', direction=None,
                 *,corner_rgb=None,smooth_normals=False):
    """Legacy face-order-preserving preview; construction edges stay flat.

    ``corner_rgb`` is sRGB with shape (faces, 3, 3). Smooth normals are explicitly
    opt-in and never change mesh vertices, faces, or their order.
    """
    if not len(mesh.faces):raise ValueError('Cannot preview an empty mesh')
    if face_rgb is not None and corner_rgb is not None:
        raise ValueError('Specify face_rgb or corner_rgb, not both')
    positions=np.asarray(mesh.triangles,dtype='<f4')
    normals=(np.asarray(mesh.vertex_normals,dtype='<f4')[mesh.faces] if smooth_normals
             else np.repeat(np.asarray(mesh.face_normals,dtype='<f4')[:,None,:],3,axis=1))
    colors=None
    if corner_rgb is not None:colors=_corner_values(corner_rgb,len(mesh.faces),'corner_rgb')
    elif face_rgb is not None:
        values=np.asarray(face_rgb,dtype='<f4')
        if values.shape!=(len(mesh.faces),3) or not np.isfinite(values).all():
            raise ValueError('face_rgb must be a finite faces by 3 array')
        colors=np.repeat(values[:,None,:],3,axis=1)
    result=_mesh_record(positions,normals,colors,color=color,ident=ident,name=name,role=role,direction=direction)
    # Preserve legacy area-weighted center, used by the assembly/explode view.
    result['bounds']=mesh.bounds.tolist();result['center']=mesh.centroid.tolist()
    return result


def _texture_data_uri(image):
    from PIL import Image
    if not isinstance(image,Image.Image):raise ValueError('Texture must be a PIL image')
    # PNG keeps the decoded pixels lossless, including alpha. No resize/bake and
    # no new triangles. UVs retain their original glTF bottom-left convention.
    mode='RGBA' if 'A' in image.getbands() or 'transparency' in image.info else 'RGB'
    output=io.BytesIO();image.convert(mode).save(output,format='PNG',compress_level=4)
    return 'data:image/png;base64,'+base64.b64encode(output.getvalue()).decode('ascii')


def surface_preview(surface):
    """Textured model preview grouped by material without changing geometry.

    Fields: ``uvs`` is base64 little-endian float32, two values per vertex;
    ``texture`` is a PNG data URI in PIL top-row-first image orientation;
    ``texture_factor`` is linear RGB, applied *after* texture sRGB decoding.
    WebGL upload must use UNPACK_FLIP_Y_WEBGL for unchanged glTF UVs. Untextured
    corner colors already contain their material factor, so factor is unity.
    ``face_ids`` relates each subset triangle to its original surface face.
    Normal interpolation uses the full mesh, avoiding material-border seams.
    """
    mesh=surface.mesh;count=len(mesh.faces)
    if not count:raise ValueError('Cannot preview an empty surface')
    ids=np.asarray(surface.material_ids)
    if ids.shape!=(count,) or not np.issubdtype(ids.dtype,np.integer) or (ids<0).any():
        raise ValueError('Material IDs must be a nonnegative integer per face')
    uv=np.asarray(surface.corner_uv,dtype='<f4')
    if uv.shape!=(count,3,2) or not np.isfinite(uv).all():
        raise ValueError('Corner UVs must be a finite faces by 3 by 2 array')
    rgb=_corner_values(surface.corner_rgb,count,'corner_rgb')
    positions=np.asarray(mesh.triangles,dtype='<f4')
    normals=np.asarray(mesh.vertex_normals,dtype='<f4')[mesh.faces]
    fallback=surface.sample()
    meshes=[]
    for material in np.unique(ids):
        selected=np.flatnonzero(ids==material);index=int(material)
        image=surface.textures[index] if index<len(surface.textures) else None
        textured=image is not None
        colors=np.ones((len(selected),3,3),dtype='<f4') if textured else rgb[selected]
        item=_mesh_record(positions[selected],normals[selected],colors,color='#FFFFFF',
                          ident=f'material-{index}',name=f'Material {index+1}',role='model',direction=None)
        factor=np.asarray(surface.factors[index],dtype=float)[:3] if textured and index<len(surface.factors) else np.ones(3)
        if factor.shape!=(3,) or not np.isfinite(factor).all() or (factor<0).any():
            raise ValueError('Texture factor must contain three finite nonnegative values')
        item.update({'material_id':index,'face_ids':selected.tolist(),
                     'fallback_colors':_encode(np.repeat(fallback[selected,None,:],3,axis=1)),
                     'uvs':_encode(uv[selected]) if textured else None,
                     'texture':_texture_data_uri(image) if textured else None,
                     'texture_factor':factor.tolist()})
        meshes.append(item)
    return {'format':'figuraforge-mesh-v1','up_axis':'Z','unit':'millimeter','meshes':meshes}


def parts_preview(parts):
    return {'format':'figuraforge-mesh-v1','up_axis':'Z','unit':'millimeter',
            'meshes':[mesh_preview(p.mesh,p.color,ident=p.id,name=p.name,role=p.role,direction=p.assembly_direction) for p in parts]}
