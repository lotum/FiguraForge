from __future__ import annotations
import numpy as np
import trimesh
from .types import Surface, GeometryError
from .colors import classify


class RefinementBudgetError(GeometryError): pass


def projected_split_faces(mesh,marked):
    """Exact conforming split count, including affected unmarked neighbors."""
    f=np.asarray(mesh.faces)
    edges=np.sort(np.stack([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]],axis=1),axis=2)
    unique,inv=np.unique(edges.reshape(-1,2),axis=0,return_inverse=True)
    inv=inv.reshape(-1,3)
    selected=np.zeros(len(unique),bool);selected[inv[marked].reshape(-1)]=True
    return len(f)+int(selected[inv].sum())


def split_marked_edges(s: Surface, marked: np.ndarray) -> Surface:
    """Conforming edge subdivision. No T-junctions, including across UV seams."""
    mesh=s.mesh; f=np.asarray(mesh.faces); v=np.asarray(mesh.vertices)
    edges=np.sort(np.stack([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]],axis=1),axis=2)
    unique,inv=np.unique(edges.reshape(-1,2),axis=0,return_inverse=True)
    inv=inv.reshape(-1,3)
    selected=np.zeros(len(unique),bool); selected[inv[marked].reshape(-1)]=True
    mids=np.full(len(unique),-1,int)
    mids[selected]=np.arange(selected.sum())+len(v)
    vv=np.vstack([v,(v[unique[selected,0]]+v[unique[selected,1]])/2])
    local_mid=mids[inv]
    ff=[]; uu=[]; cc=[]; mat=[]; tags=[]
    # Explicit 0/1/2/3 edge cases preserve positive orientation.
    patterns={
      0:[[0,1,2]], 1:[[0,3,2],[3,1,2]], 2:[[1,4,0],[4,2,0]],
      4:[[2,5,1],[5,0,1]], 3:[[1,4,3],[0,3,2],[3,4,2]],
      6:[[2,5,4],[1,4,0],[4,5,0]], 5:[[0,3,5],[2,5,1],[5,3,1]],
      7:[[0,3,5],[3,1,4],[5,4,2],[3,4,5]]}
    mask=(local_mid[:,0]>=0).astype(int)+2*(local_mid[:,1]>=0)+4*(local_mid[:,2]>=0)
    for code,pat in patterns.items():
        rows=np.flatnonzero(mask==code)
        if not len(rows): continue
        ix=np.column_stack([f[rows],local_mid[rows]])
        uv=s.corner_uv[rows]; rgb=s.corner_rgb[rows]
        uv6=np.concatenate([uv,(uv[:,[0,1,2]]+uv[:,[1,2,0]])/2],axis=1)
        rgb6=np.concatenate([rgb,(rgb[:,[0,1,2]]+rgb[:,[1,2,0]])/2],axis=1)
        for tri in pat:
            ff.append(ix[:,tri]); uu.append(uv6[:,tri]); cc.append(rgb6[:,tri]); mat.append(s.material_ids[rows])
            if s.face_tags is not None: tags.append(s.face_tags[rows])
    m=trimesh.Trimesh(vv,np.concatenate(ff),process=False)
    return Surface(m,np.concatenate(uu),np.concatenate(cc),np.concatenate(mat),s.textures,s.factors,s.warnings.copy(),None if s.face_tags is None else np.concatenate(tags))


def refine_for_color(s: Surface, palette: list[str], tolerance_mm: float=.65,
                     coarse_mm: float=5, max_faces: int=350000, progress=None) -> tuple[Surface,np.ndarray,dict]:
    if tolerance_mm<.05: raise GeometryError('Boundary tolerance must be at least 0.05 mm')
    if len(s.mesh.faces)>max_faces:
        raise RefinementBudgetError('Input mesh already exceeds the configured triangle budget; prepare a smaller working copy.')
    for step in range(64):
        mesh=s.mesh
        triangles=mesh.triangles
        longest=np.linalg.norm(triangles-triangles[:,[1,2,0]],axis=2).max(axis=1)
        sample_labels=np.stack([classify(s.sample(b),palette) for b in
            ([1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3)],axis=1)
        boundary=(sample_labels!=sample_labels[:,0,None]).any(axis=1)
        mark=(longest>coarse_mm) | (boundary & (longest>tolerance_mm))
        if not mark.any(): break
        # Conservatively stop, rather than silently degrade requested precision.
        projected=projected_split_faces(mesh,mark)
        if projected>max_faces:
            raise RefinementBudgetError(f'Color-boundary refinement needs {projected:,} triangles in the next step '
                                f'(current {len(mesh.faces):,}, configured limit {max_faces:,}). '
                                'Prepare a mesh/precision plan before construction; input reduction alone does not bound refinement.')
        if progress: progress(f'Refining color boundary: {len(mesh.faces):,} triangles')
        s=split_marked_edges(s,mark)
    else: raise GeometryError('Boundary refinement did not converge after 64 passes; reduce texture noise or use coarser sampling')
    labels=classify(s.sample(),palette)
    adj=s.mesh.face_adjacency
    boundary_pairs=adj[labels[adj[:,0]]!=labels[adj[:,1]]]
    info={'triangles':len(s.mesh.faces),'boundary_pairs':len(boundary_pairs),
          'requested_tolerance_mm':tolerance_mm,'coarse_sampling_mm':coarse_mm,
          'precision_note':'Boundary follows the sampled albedo at mesh resolution; small features below the coarse sampling can be missed. This is not a mathematical raster-to-curve error bound.'}
    return s,labels,info


def refine_with_plan(surface,palette,settings,progress=None):
    """Plan in physical units before part construction; never exceed face budget."""
    import time
    started=time.monotonic()
    auto=settings.get('precision_mode','auto')=='auto'
    scale=max(1.,settings['height_mm']/180.) if auto else 1.
    tolerance=settings['boundary_tolerance_mm']*scale
    coarse=settings['coarse_sampling_mm']*scale
    maximum=max(tolerance,settings['height_mm']*.0055) if auto else tolerance
    attempts=[]
    while True:
        try:
            result,labels,report=refine_for_color(surface,palette,tolerance,coarse,
                                                settings['max_refined_faces'],progress)
            report.update(ready=True,mode='auto' if auto else 'fixed',
                          effective_boundary_mm=tolerance,effective_coarse_mm=coarse,
                          input_triangles=len(surface.mesh.faces),face_budget=settings['max_refined_faces'],
                          seconds=round(time.monotonic()-started,3),planning_attempts=attempts)
            return result,labels,report
        except RefinementBudgetError as exc:
            attempts.append({'boundary_mm':tolerance,'reason':str(exc)})
            if not auto or tolerance>=maximum-1e-9:
                raise GeometryError('Farbteile noch nicht vorbereitet: Die gewaehlte Groesse, Palette und '
                    'Farbgrenzen-Praezision passen nicht in das Dreiecksbudget. '
                    'Im Mesh-Schritt Arbeitskopie vorbereiten oder unter Praezision automatisch waehlen; '
                    'bei fester Praezision ein groesseres Rechenbudget planen. '+str(exc)) from exc
            tolerance=min(maximum,tolerance*1.4)
            if progress: progress(f'Farbgrenzen planen: {tolerance:.2f} mm bei festem Dreiecksbudget')
