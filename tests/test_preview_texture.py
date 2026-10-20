import base64
import io
import numpy as np
import pytest
import trimesh
from PIL import Image
from figuraforge.geometry.preview import mesh_preview,surface_preview
from figuraforge.geometry.types import Surface


def decoded(value,width=3):
    return np.frombuffer(base64.b64decode(value),dtype='<f4').reshape(-1,width)


def fixture_surface():
    mesh=trimesh.Trimesh(vertices=[[0,0,0],[1,0,0],[1,1,0],[0,1,1],[2,0,0]],
                         faces=[[0,1,2],[0,2,3],[1,4,2]],process=False)
    pixels=np.array([[[255,0,0],[0,255,0]],[[0,0,255],[255,255,255]]],dtype=np.uint8)
    image=Image.fromarray(pixels)
    uv=np.array([[[0,0],[1,0],[1,1]],[[0,0],[1,1],[0,1]],[[0,0],[1,0],[1,1]]],float)
    rgb=np.array([[[1,1,1]]*3,[[.2,.4,.6]]*3,[[1,1,1]]*3])
    return Surface(mesh,uv,rgb,np.array([0,1,0]),[image,None],[np.array([.5,.7,1,1]),np.ones(4)])


def test_checkerboard_pixels_uvs_and_linear_factor_are_preserved():
    s=fixture_surface();result=surface_preview(s);item=result['meshes'][0]
    assert result['format']=='figuraforge-mesh-v1'
    assert item['texture'].startswith('data:image/png;base64,')
    image=Image.open(io.BytesIO(base64.b64decode(item['texture'].split(',',1)[1])))
    np.testing.assert_array_equal(np.asarray(image),np.asarray(s.textures[0]))
    np.testing.assert_array_equal(decoded(item['uvs'],2),s.corner_uv[[0,2]].reshape(-1,2))
    assert item['texture_factor']==[.5,.7,1.]
    np.testing.assert_array_equal(decoded(item['colors']),np.ones((6,3)))


def test_material_subsets_preserve_face_order_positions_and_full_mesh_normals():
    s=fixture_surface();faces=s.mesh.faces.copy();vertices=s.mesh.vertices.copy()
    items=surface_preview(s)['meshes']
    assert [x['face_ids'] for x in items]==[[0,2],[1]]
    for item in items:
        selected=item['face_ids']
        np.testing.assert_allclose(decoded(item['positions']),s.mesh.triangles[selected].reshape(-1,3))
        np.testing.assert_allclose(decoded(item['normals']),s.mesh.vertex_normals[s.mesh.faces[selected]].reshape(-1,3),atol=1e-7)
    np.testing.assert_array_equal(s.mesh.faces,faces);np.testing.assert_array_equal(s.mesh.vertices,vertices)
    plain=items[1]
    assert plain['texture'] is None and plain['uvs'] is None and plain['texture_factor']==[1,1,1]
    np.testing.assert_allclose(decoded(plain['colors']),s.corner_rgb[1],atol=1e-7)


def test_legacy_defaults_remain_flat_and_corner_colors_are_opt_in():
    s=fixture_surface();flat=mesh_preview(s.mesh,face_rgb=np.full((3,3),.4))
    np.testing.assert_allclose(decoded(flat['normals']),np.repeat(s.mesh.face_normals,3,axis=0),atol=1e-7)
    np.testing.assert_allclose(decoded(flat['colors']),.4,atol=1e-7)
    smooth=mesh_preview(s.mesh,corner_rgb=s.corner_rgb,smooth_normals=True)
    np.testing.assert_allclose(decoded(smooth['normals']),s.mesh.vertex_normals[s.mesh.faces].reshape(-1,3),atol=1e-7)
    np.testing.assert_allclose(decoded(smooth['colors']),s.corner_rgb.reshape(-1,3),atol=1e-7)
    assert 'texture' not in flat
    assert flat['center']==s.mesh.centroid.tolist()


def test_rgba_texture_stays_lossless():
    s=fixture_surface();s.textures[0]=Image.new('RGBA',(2,2),(12,34,56,78))
    texture=surface_preview(s)['meshes'][0]['texture']
    image=Image.open(io.BytesIO(base64.b64decode(texture.split(',',1)[1])))
    assert image.mode=='RGBA' and image.getpixel((0,0))==(12,34,56,78)


@pytest.mark.parametrize('field,value',[('corner_uv',np.zeros((3,3,3))),('corner_rgb',np.full((3,3,3),np.nan)),('material_ids',np.array([0,-1,0]))])
def test_invalid_surface_arrays_rejected(field,value):
    s=fixture_surface();setattr(s,field,value)
    with pytest.raises(ValueError):surface_preview(s)


def test_conflicting_color_inputs_rejected():
    s=fixture_surface()
    with pytest.raises(ValueError):mesh_preview(s.mesh,face_rgb=np.ones((3,3)),corner_rgb=s.corner_rgb)
