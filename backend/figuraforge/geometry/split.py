from __future__ import annotations
import numpy as np
import trimesh
from .types import Part, GeometryError
from .topology import frame, projected_outline, mesh_from_triangles, orient_local
from .connectors import pick_connectors, root_with_connectors
from .validation import to_vtk, require_solid, DistanceQuery


def _clip_half_impl(mesh, axis:int, position:float, positive:bool):
    from .plane_cut import clip_closed
    try:
        return clip_closed(mesh,axis,position,positive)
    except GeometryError:
        return _vtk_clip_half(mesh,axis,position,positive)


def _vtk_clip_half(mesh, axis:int, position:float, positive:bool):
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy
    plane=vtk.vtkPlane(); n=np.zeros(3); n[axis]=1 if positive else -1
    origin=np.zeros(3); origin[axis]=position
    plane.SetNormal(n); plane.SetOrigin(origin)
    planes=vtk.vtkPlaneCollection(); planes.AddItem(plane)
    clip=vtk.vtkClipClosedSurface(); clip.SetInputData(to_vtk(mesh)); clip.SetClippingPlanes(planes)
    clip.SetTolerance(1e-7); clip.GenerateFacesOn(); clip.Update()
    tri=vtk.vtkTriangleFilter(); tri.SetInputConnection(clip.GetOutputPort()); tri.Update()
    out=tri.GetOutput()
    if out.GetNumberOfCells()==0: raise GeometryError('Cut produced an empty half')
    vertices=vtk_to_numpy(out.GetPoints().GetData())
    faces=vtk_to_numpy(out.GetPolys().GetConnectivityArray()).reshape(-1,3)
    return mesh_from_triangles(vertices[faces])


def clip_half(mesh, axis:int, position:float, positive:bool):
    # A pathological native cap triangulation must not freeze an overnight run.
    from .clip_worker import worker
    return worker.clip(mesh,axis,position,positive)


def split_with_joint(mesh, axis:int, position:float, radius:float=3.,length:float=8.,clearance:float=.2,shape:str='keyed',count:int=3):
    low=clip_half(mesh,axis,position,False); high=clip_half(mesh,axis,position,True)
    return joint_between_halves(low,high,axis,position,radius,length,clearance,shape,count)


def joint_between_halves(low,high,axis:int,position:float,radius:float=3.,length:float=8.,
                        clearance:float=.2,shape:str='keyed',count:int=3):
    """Add a matched joint to already validated, complementary planar halves."""
    require_solid(low); require_solid(high)
    low_cap=(np.abs(low.triangles[:,:,axis]-position)<1e-5).all(axis=1)
    high_cap=(np.abs(high.triangles[:,:,axis]-position)<1e-5).all(axis=1)
    if not low_cap.any() or not high_cap.any(): raise GeometryError('Cut caps could not be identified')
    direction=-np.eye(3)[axis]; basis=frame(direction)
    root=low.submesh([np.flatnonzero(low_cap)],append=True,repair=False)
    local=root.triangles@basis
    root=mesh_from_triangles(orient_local(local,True)@basis.T,check=False)
    outline=projected_outline(root,basis)
    connectors=pick_connectors(outline,root,basis,0,radius=radius,length=length,clearance=clearance,count=count,shape=shape)
    q=DistanceQuery(high)
    connectors=[c for c in connectors if q.values(np.array([[c.x,c.y,c.tip_z-.4]])@basis.T)[0]<-(c.radius+.6)]
    male=root_with_connectors(root,basis,connectors,False)
    female=root_with_connectors(root,basis,connectors,True)
    a=mesh_from_triangles(np.concatenate([low.triangles[~low_cap],male]))
    b=mesh_from_triangles(np.concatenate([high.triangles[~high_cap],female]))
    require_solid(a); require_solid(b)
    return a,b,[c.summary(basis) for c in connectors],direction


def fits_some_orientation(extents,volume,margin):
    from itertools import permutations
    return any(np.all(np.asarray(p)+2*margin<=volume) for p in permutations(extents))


def tile_parts(parts:list[Part],volume=(300.,320.,325.),margin=6.,max_parts=80,progress=None,clearance=.2,shape='keyed'):
    """Retain organic color splits; add structural cuts only for oversize pieces."""
    volume=np.asarray(volume,float); pending=list(parts); result=[]; report=[]; cut_no=0
    while pending:
        part=pending.pop(0)
        if fits_some_orientation(part.mesh.extents,volume,margin):
            result.append(part); continue
        if len(pending)+len(result)>=max_parts: raise GeometryError('Too many build-volume subdivisions')
        if progress: progress(f'Splitting oversize part: {part.name}')
        axis=int(np.argmax(part.mesh.extents))
        lo,hi=part.mesh.bounds[:,axis]
        # Prefer a narrow nearby section, but guarantee meaningful subdivision.
        candidates=np.linspace(lo+(hi-lo)*.38,lo+(hi-lo)*.62,7)
        candidates+=.000137  # avoid perfectly coincident source vertices
        areas=[]
        for pos in candidates:
            try:
                half=clip_half(part.mesh,axis,float(pos),False)
                cap=(np.abs(half.triangles[:,:,axis]-pos)<1e-5).all(axis=1)
                areas.append(float(half.area_faces[cap].sum()))
            except GeometryError as exc:
                if progress: progress('Skipping structural candidate: '+str(exc)[:120])
                areas.append(float('inf'))
        if not np.isfinite(areas).any(): raise GeometryError('No reliable structural cut found')
        transverse=np.delete(part.mesh.extents,axis)
        radius=float(np.clip(transverse.min()*.05,1.2,6.))
        length=float(np.clip(radius*2.5,3,16))
        errors=[]; success=False
        for candidate in np.argsort(areas):
            if not np.isfinite(areas[candidate]): continue
            pos=float(candidates[candidate])
            try:
                a,b,connectors,d=split_with_joint(part.mesh,axis,pos,radius,length,clearance,shape)
                success=True; break
            except GeometryError as exc:
                errors.append(str(exc))
        if not success: raise GeometryError('No valid structural joint found: '+('; '.join(errors[:2]) or 'invalid caps'))
        cut_no+=1
        for suffix,m in [('a',a),('b',b)]:
            warnings=part.warnings.copy()
            warnings.append('Structural subdivision requires assembly review; existing connector metadata refers to the parent assembly.')
            if not connectors: warnings.append('Cross-section too thin for an additional structural joint. The piece needs separate retention on the core.')
            pending.append(Part(f'{part.id}-{suffix}',f'{part.name} / {suffix.upper()}',m,part.color,
                part.color_index,part.role,d.tolist(),part.connectors+connectors,warnings,part.filament_id))
        report.append({'parent':part.id,'axis':'XYZ'[axis],'position_mm':pos,'connectors':connectors,
                       'reason':'part exceeds printer envelope; extra structural seam, not a replacement for the organic color boundary'})
    return result,report
