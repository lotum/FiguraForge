"""Source-projected conforming head detail; no source/project mutation."""
from pathlib import Path
import json,hashlib,time,uuid
import numpy as np
import trimesh
from figuraforge.geometry.io import load_surface
from figuraforge.geometry.types import Surface
from figuraforge.geometry.refine import projected_split_faces,split_marked_edges
from figuraforge.geometry.compare import nearest,colors_at
from figuraforge.geometry.validation import validate_mesh

ROOT=Path(__file__).resolve().parents[1]
V2=ROOT/'benchmarks/mochi-eye-detail-20261016/weighted-eyes-150k.glb'
ORIGINAL=ROOT/'data/projects/1b0e2fdd463d4f15ac64f1c7b3e8acc7/inputs/original-source.glb'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def load_refined_surface(directory):
    """Canonical face order/ancestry loader; coordinates already180mm/Z-up."""
    from PIL import Image
    directory=Path(directory);meta=json.loads((directory/'surface.json').read_text())
    with np.load(directory/'surface.npz',allow_pickle=False) as a:
        mesh=trimesh.Trimesh(a['vertices'],a['faces'],process=False)
        return Surface(mesh,a['corner_uv'],a['corner_rgb'],a['material_ids'],
            [None if name is None else Image.open(directory/name).copy() for name in meta['textures']],
            [np.asarray(v) for v in meta['factors']],meta['warnings'],a['face_ancestry'])


def metric(values):
    return {key:float(np.quantile(values,q)) for key,q in [('median',.5),('p95',.95),('p99',.99),('max',1.)]}


def area_samples(mesh,count,seed,mask):
    rng=np.random.default_rng(seed);ids=np.flatnonzero(mask);weights=mesh.area_faces[ids];ids=rng.choice(ids,count,p=weights/weights.sum());ab=rng.random((count,2));ab[ab.sum(axis=1)>1]=1-ab[ab.sum(axis=1)>1];bary=np.c_[1-ab.sum(axis=1),ab]
    return np.einsum('nvc,nv->nc',mesh.triangles[ids],bary),ids,bary


def main():
    started=time.monotonic();out=ROOT/'benchmarks/mochi-unified-head'/('head-'+uuid.uuid4().hex);out.mkdir()
    if sha(V2)!='bdb9e145f308d7c9a1a6a49ba2111f1bbea658f1bfdf00f9ead2b353e50f29e7' or sha(ORIGINAL)!='bdd4b23a89588c47ea18e9e731f5d1e0c9f1b82ea6b921ff1edc484339377dfd':raise ValueError('Reviewed source changed')
    v2=load_surface(V2,180,'Y');original=load_surface(ORIGINAL,180,'Y',max_faces=4_000_000)
    v2.face_tags=np.arange(len(v2.mesh.faces));tri=v2.mesh.triangles
    longest=np.linalg.norm(tri-tri[:,[1,2,0]],axis=2).max(axis=1);eligible=tri[:,:,2].min(axis=1)>111.
    lo,hi=0.,2.
    for _ in range(24):
        mid=(lo+hi)/2;count=projected_split_faces(v2.mesh,eligible&(longest>mid))
        if count>300000:lo=mid
        else:hi=mid
    marked=eligible&(longest>hi);s=split_marked_edges(v2,marked);before=s.mesh.vertices.copy();old_count=len(v2.mesh.vertices)
    # Only new edge points with no incident face crossing the immutable body
    # boundary can move. Old V2 vertices, including eye details, remain exact.
    protected_faces=s.mesh.triangles[:,:,2].min(axis=1)<=110.
    safe=np.ones(len(before),bool);safe[s.mesh.faces[protected_faces].reshape(-1)]=False
    candidate=np.flatnonzero((np.arange(len(before))>=old_count)&safe)
    print(out,'faces',len(s.mesh.faces),'projecting',len(candidate),flush=True)
    dist,original_ids,bary=nearest(original,before[candidate]);target=np.einsum('nvc,nv->nc',original.mesh.triangles[original_ids],bary)
    vertices=before.copy();vertices[candidate]=target
    baseline=trimesh.triangles.normals(before[s.mesh.faces])[0]
    rejected=np.zeros(len(vertices),bool)
    # Reject complete unsafe vertex moves instead of retaining reversed faces.
    for iteration in range(20):
        tri_new=vertices[s.mesh.faces];cross=np.cross(tri_new[:,1]-tri_new[:,0],tri_new[:,2]-tri_new[:,0]);dot=np.einsum('ij,ij->i',cross,baseline)
        bad=(dot<=1e-12)|(~np.isfinite(cross).all(axis=1))
        if not bad.any():break
        ids=np.unique(s.mesh.faces[bad]);ids=ids[(ids>=old_count)&(~rejected[ids])]
        if not len(ids):raise ValueError('Unresolved face reversal')
        vertices[ids]=before[ids];rejected[ids]=True
    else:raise ValueError('Projection rejection did not converge')
    s.mesh.vertices=vertices
    accepted=candidate[~rejected[candidate]]
    # Texture coordinates are sampled on original geometric triangle for EVERY
    # projected corner, so atlas seams remain face-local rather than averaged.
    head=s.mesh.triangles[:,:,2].min(axis=1)>110.
    uv_original_dist,uv_original_ids,uv_bary=nearest(original,s.mesh.triangles[head].reshape(-1,3))
    uv=np.einsum('nvc,nv->nc',original.corner_uv[uv_original_ids],uv_bary).reshape(-1,3,2)
    rgb=np.einsum('nvc,nv->nc',original.corner_rgb[uv_original_ids],uv_bary).reshape(-1,3,3)
    mats=original.material_ids[uv_original_ids].reshape(-1,3)
    if not np.all(mats==mats[:,0,None]):raise ValueError('Original multi-material crossing needs explicit splitting')
    expected_uv=s.corner_uv[head].copy()
    bad_uv=np.linalg.norm(uv-expected_uv,axis=2)>.02
    corrected=0;fallback=0
    if bad_uv.any():
        from scipy.spatial import cKDTree
        corner_points=s.mesh.triangles[head].reshape(-1,3)
        bad_rows=np.flatnonzero(bad_uv.reshape(-1));tree=cKDTree(original.mesh.vertices)
        vertex_faces=original.mesh.vertex_faces
        flat_uv=uv.reshape(-1,2);flat_rgb=rgb.reshape(-1,3);expected=expected_uv.reshape(-1,2)
        for start in range(0,len(bad_rows),256):
            rows=bad_rows[start:start+256];points=corner_points[rows]
            _,neighbors=tree.query(points,k=8,workers=2)
            candidates=vertex_faces[neighbors].reshape(len(rows),-1);valid=candidates>=0;candidates=np.maximum(candidates,0);width=candidates.shape[1]
            triangles=original.mesh.triangles[candidates.reshape(-1)]
            repeated=np.repeat(points,width,axis=0)
            closest=trimesh.triangles.closest_point(triangles,repeated)
            weights=trimesh.triangles.points_to_barycentric(triangles,closest)
            candidate_uv=np.einsum('nvc,nv->nc',original.corner_uv[candidates.reshape(-1)],weights).reshape(len(rows),width,2)
            delta=np.linalg.norm(candidate_uv-expected[rows,None,:],axis=2)
            geometry_error=np.linalg.norm(closest-repeated,axis=1).reshape(len(rows),width)
            score=np.where(valid&(delta<.02),geometry_error+.01*delta,np.inf)
            chosen=score.argmin(axis=1);ok=np.isfinite(score[np.arange(len(rows)),chosen])
            chosen_flat=np.arange(len(rows))*width+chosen
            flat_uv[rows[ok]]=candidate_uv[np.arange(len(rows))[ok],chosen[ok]]
            selected_weights=weights[chosen_flat[ok]];selected_ids=candidates[np.arange(len(rows))[ok],chosen[ok]]
            flat_rgb[rows[ok]]=np.einsum('nvc,nv->nc',original.corner_rgb[selected_ids],selected_weights)
            flat_uv[rows[~ok]]=expected[rows[~ok]]
            corrected+=int(ok.sum());fallback+=int((~ok).sum())
    uv_span=np.ptp(uv,axis=1).max(axis=1)
    if (uv_span>.2).any():raise ValueError('New cross-atlas UV triangle')
    uv_change=np.linalg.norm(uv-expected_uv,axis=2)
    s.corner_uv[head]=uv;s.corner_rgb[head]=rgb;s.material_ids[head]=mats[:,0]
    s.textures=original.textures;s.factors=original.factors
    # Immutable lower faces retain their linear V2 interpolation exactly.
    non_head=~head;ancestry=np.asarray(s.face_tags)
    unchanged_lower=np.max(abs(s.mesh.triangles[non_head]-before[s.mesh.faces[non_head]]),initial=0.)
    if unchanged_lower!=0:raise ValueError('Body boundary changed')
    quality=validate_mesh(s.mesh)
    if not s.mesh.is_watertight or not s.mesh.is_winding_consistent or len(s.mesh.split(only_watertight=False))!=1:raise ValueError('Closed single component required')
    rng_mask=original.mesh.triangles_center[:,2]>112
    points,_,_=area_samples(original.mesh,24000,904,rng_mask);old_error,_,_=nearest(v2,points);new_error,_,_=nearest(s,points)
    reverse,_,_=area_samples(s.mesh,12000,905,s.mesh.triangles_center[:,2]>112);reverse_error,_,_=nearest(original,reverse)
    improvements={'original_to_v2_head_mm':metric(old_error),'original_to_new_head_mm':metric(new_error),'new_to_original_head_mm':metric(reverse_error),'paired_improved_fraction':float((new_error<old_error-1e-7).mean()),'paired_worsened_over_0_01mm_fraction':float((new_error>old_error+.01).mean())}
    report={'v2_source':str(V2),'v2_sha256':sha(V2),'original':str(ORIGINAL),'original_sha256':sha(ORIGINAL),'faces':len(s.mesh.faces),'vertices':len(vertices),'marked_v2_faces':int(marked.sum()),'longest_edge_threshold_mm':hi,'projection_vertices':len(candidate),'accepted_projection_vertices':len(accepted),'rejected_projection_vertices':int(rejected.sum()),'projection_movement_mm':metric(dist),'body_under110_max_geometry_change_mm':unchanged_lower,'old_v2_vertices_exact':bool(np.array_equal(vertices[:old_count],v2.mesh.vertices)),'quality':quality,'uv_chart_corrected_corners':corrected,'uv_v2_fallback_corners':fallback,'uv_delta_vs_v2':metric(uv_change.reshape(-1)),'new_cross_atlas_triangles':int((uv_span>.2).sum()),'face_ancestry_count':len(ancestry),'shape_comparison':improvements,'seconds':time.monotonic()-started,'limitation':'Finite24k+12k area samples, no exhaustive self-intersection/Hausdorff certification. Rejected moves retain exact planar V2 midpoint. All old V2 vertices and lower-boundary triangles remain unchanged.'}
    np.savez_compressed(out/'surface.npz',vertices=vertices,faces=s.mesh.faces,corner_uv=s.corner_uv,corner_rgb=s.corner_rgb,material_ids=s.material_ids,face_ancestry=ancestry)
    tex=[]
    for i,image in enumerate(s.textures):
        name=None if image is None else f'texture-{i}.png';tex.append(name)
        if image is not None:image.save(out/name)
    (out/'surface.json').write_text(json.dumps({'textures':tex,'factors':[x.tolist() for x in s.factors],'warnings':s.warnings,'height_mm':180,'up_axis':'Z','face_ancestry':'V2canonicalface index'},indent=2)+'\n')
    # GLB is a visual exchange copy; NPZ remains canonical ordered topology.
    geometry=[]
    for mid in np.unique(s.material_ids):
        rows=np.flatnonzero(s.material_ids==mid);mesh=trimesh.Trimesh(s.mesh.triangles[rows].reshape(-1,3),np.arange(3*len(rows)).reshape(-1,3),process=False)
        material=trimesh.visual.material.PBRMaterial(baseColorTexture=s.textures[mid],baseColorFactor=s.factors[mid],metallicFactor=0,roughnessFactor=1)
        mesh.visual=trimesh.visual.TextureVisuals(uv=s.corner_uv[rows].reshape(-1,2),material=material)
        mesh.apply_transform(np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],float))
        rotation=np.array([[1,0,0],[0,0,1],[0,-1,0]])
        mesh.vertex_normals=s.mesh.vertex_normals[s.mesh.faces[rows]].reshape(-1,3)@rotation.T
        geometry.append(mesh)
    (out/'head-detail.glb').write_bytes(trimesh.Scene(geometry).export(file_type='glb'))
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
