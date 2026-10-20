from __future__ import annotations
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image


def make_demo(path:Path, pitch=2.0):
    """Original procedural teddy fixture. No third-party character or input photo."""
    from skimage.measure import marching_cubes
    x=np.arange(-72,72+pitch,pitch); y=np.arange(-48,48+pitch,pitch); z=np.arange(-4,190+pitch,pitch)
    X,Y,Z=np.meshgrid(x,y,z,indexing='ij'); points=np.stack([X,Y,Z],axis=-1)
    field=np.full(X.shape,1e4)
    ellipsoids=[((0,0,74),(40,29,53)),((0,-1,137),(38,30,35)),
                ((-28,0,165),(17,15,19)),((28,0,165),(17,15,19)),
                ((-40,0,88),(18,19,32)),((40,0,88),(18,19,32)),
                ((-21,-4,25),(19,24,29)),((21,-4,25),(19,24,29))]
    for center,radii in ellipsoids:
        d=(np.linalg.norm((points-center)/radii,axis=-1)-1)*min(radii)
        k=4.; h=np.maximum(k-np.abs(field-d),0)/k
        field=np.minimum(field,d)-h*h*k*.25
    field=np.maximum(field,2-Z)
    verts,faces,_,_=marching_cubes(field,0,spacing=(pitch,)*3,allow_degenerate=False)
    verts+=np.array([x[0],y[0],z[0]])
    mesh=trimesh.Trimesh(verts,faces,process=True)
    mesh.merge_vertices(digits_vertex=6)
    mesh.update_faces(mesh.nondegenerate_faces() & mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    trimesh.repair.fix_normals(mesh)
    if mesh.volume<0: mesh.invert()
    mesh.apply_translation([0,0,-mesh.bounds[0,2]])
    height=mesh.extents[2]
    triangles=mesh.triangles
    uv=np.stack([(np.arctan2(triangles[:,:,1],triangles[:,:,0])+np.pi)/(2*np.pi),triangles[:,:,2]/height],axis=-1)
    # Unwrap each seam-crossing triangle locally before duplicate-vertex GLB export.
    seam=np.ptp(uv[:,:,0],axis=1)>.5
    uv[seam,:,0]=np.where(uv[seam,:,0]<.5,uv[seam,:,0]+1,uv[seam,:,0])
    image=np.zeros((1024,1024,3),dtype=np.uint8); image[:]=[137,83,48]
    u=np.linspace(0,1,1024)[None,:]; v=np.linspace(1,0,1024)[:,None]
    belly=((u-.25)/.078)**2+((v-.39)/.177)**2
    angle=np.arctan2((v-.39)/.177,(u-.25)/.078)
    mask=belly < (1+.09*np.sin(5*angle))**2
    muzzle=((u-.25)/.056)**2+((v-.748)/.064)**2 < 1
    image[mask|muzzle]=[229,193,137]
    eyes=(((u-.216)/.010)**2+((v-.838)/.020)**2<1)|(((u-.284)/.010)**2+((v-.838)/.020)**2<1)
    nose=((u-.25)/.012)**2+((v-.765)/.013)**2<1
    image[eyes|nose]=[33,29,26]
    duplicate=trimesh.Trimesh(triangles.reshape(-1,3),np.arange(len(faces)*3).reshape(-1,3),process=False)
    # GLB convention Y-up: the app restores Z-up on import.
    vertices=duplicate.vertices.copy(); duplicate.vertices=vertices[:,[0,2,1]]; duplicate.vertices[:,2]*=-1
    mat=trimesh.visual.material.PBRMaterial(baseColorTexture=Image.fromarray(image),metallicFactor=0,roughnessFactor=.85)
    duplicate.visual=trimesh.visual.TextureVisuals(uv=uv.reshape(-1,2),material=mat)
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(duplicate.export(file_type='glb'))
    return {'path':str(path),'height_mm':height,'triangles':len(mesh.faces),'license':'CC0, generated procedurally for this project'}
