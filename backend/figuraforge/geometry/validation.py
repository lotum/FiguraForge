from __future__ import annotations
import numpy as np
import trimesh
from .types import GeometryError


def to_vtk(mesh):
    import vtk
    from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
    p=vtk.vtkPoints(); p.SetData(numpy_to_vtk(np.asarray(mesh.vertices),deep=True))
    cells=vtk.vtkCellArray()
    offsets=np.arange(0,3*(len(mesh.faces)+1),3,dtype=np.int64)
    indices=np.asarray(mesh.faces,dtype=np.int64).ravel()
    cells.SetData(numpy_to_vtkIdTypeArray(offsets,deep=True),numpy_to_vtkIdTypeArray(indices,deep=True))
    poly=vtk.vtkPolyData(); poly.SetPoints(p); poly.SetPolys(cells)
    return poly


class DistanceQuery:
    def __init__(self,mesh):
        import vtk
        if not mesh.is_watertight or not mesh.is_winding_consistent:
            raise GeometryError('Inside/outside queries require a closed, consistently wound surface')
        components=trimesh.graph.connected_component_labels(mesh.face_adjacency,node_count=len(mesh.faces))
        if not len(components):raise GeometryError('Inside/outside queries require a nonempty surface')
        if components.max()!=0:
            # Ray parity across overlapping shells is not a solid union, and
            # blindly OR-ing shells would erase intentional internal cavities.
            shells=mesh.split(only_watertight=False)
            disjoint=all(shell.is_volume for shell in shells)
            for i,shell in enumerate(shells):
                for other in shells[i+1:]:
                    if not (np.any(shell.bounds[1]<=other.bounds[0]) or np.any(other.bounds[1]<=shell.bounds[0])):
                        disjoint=False
            if not disjoint:
                raise GeometryError('Inside/outside queries require one connected surface or disjoint positive solids. '
                                    'Separate disconnected solids or explicitly validate nested/overlapping shells first.')
        self.mesh=mesh; self.poly=to_vtk(mesh)
        self.function=vtk.vtkImplicitPolyDataDistance(); self.function.SetInput(self.poly)
        self.bounds=np.asarray(mesh.bounds)

    def values(self, points):
        import vtk
        from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
        points=np.asarray(points,float).reshape(-1,3)
        if not len(points):return np.empty(0,float)
        if not np.isfinite(points).all():raise GeometryError('Distance query contains non-finite points')
        p=vtk.vtkPoints(); p.SetData(numpy_to_vtk(points,deep=True))
        data=vtk.vtkPolyData(); data.SetPoints(p)
        f=vtk.vtkSampleImplicitFunctionFilter(); f.SetInputData(data)
        f.SetImplicitFunction(self.function); f.ComputeGradientsOff(); f.Update()
        # The nearest triangle's pseudonormal is not a reliable inside/outside
        # test around concave caps. Keep its distance magnitude, but obtain the
        # sign from closed-surface ray intersections instead.
        result=np.abs(vtk_to_numpy(f.GetOutput().GetPointData().GetArray('Implicit scalars'))).copy()
        candidates=np.flatnonzero(((points>=self.bounds[0])&(points<=self.bounds[1])).all(axis=1))
        if len(candidates):
            selected_points=vtk.vtkPoints();selected_points.SetData(numpy_to_vtk(points[candidates],deep=True))
            selected_data=vtk.vtkPolyData();selected_data.SetPoints(selected_points)
            enclosed=vtk.vtkSelectEnclosedPoints();enclosed.SetInputData(selected_data)
            enclosed.SetSurfaceData(self.poly);enclosed.SetTolerance(1e-9);enclosed.Update()
            inside=vtk_to_numpy(enclosed.GetOutput().GetPointData().GetArray('SelectedPoints')).astype(bool)
            result[candidates[inside]]*=-1
        return result


def validate_mesh(mesh, require_closed=True):
    boundary=int(np.sum(np.bincount(mesh.edges_unique_inverse)==1)) if len(mesh.faces) else 0
    edges=np.bincount(mesh.edges_unique_inverse) if len(mesh.faces) else np.array([])
    finite=bool(np.isfinite(mesh.vertices).all())
    return {
        'finite':finite, 'vertices':len(mesh.vertices),'triangles':len(mesh.faces),
        'watertight':bool(mesh.is_watertight),'winding_consistent':bool(mesh.is_winding_consistent),
        'boundary_edges':boundary,'nonmanifold_edges':int((edges>2).sum()),
        'volume_mm3':round(float(mesh.volume),5),
        'dimensions_mm':np.round(mesh.extents,4).tolist(),
        'components':len(mesh.split(only_watertight=False)),
        'valid':finite and (bool(mesh.is_volume) if require_closed else len(mesh.faces)>0),
        'self_intersections':'not exhaustively certified',
    }


def require_solid(mesh):
    r=validate_mesh(mesh)
    if not r['valid']:
        raise GeometryError('Input must be a closed, consistently wound solid. '
                            f"Boundary edges: {r['boundary_edges']}; nonmanifold: {r['nonmanifold_edges']}. "
                            'Repair and review the mesh before manufacturing; no destructive auto-remesh was applied.')


def sample_surface(mesh, count=2500):
    if len(mesh.vertices)<=count: return np.asarray(mesh.vertices)
    idx=np.linspace(0,len(mesh.vertices)-1,count,dtype=int)
    return np.asarray(mesh.vertices)[idx]


def check_insert_path(part, body, direction, travel_mm=15, samples=8, tolerance=.03):
    """Sampled straight-line extraction check, not a continuous collision proof."""
    d=np.asarray(direction,float); d/=np.linalg.norm(d)
    points=sample_surface(part,1800)
    q=DistanceQuery(body)
    worst=0.; blocked=[]
    for distance in np.linspace(.02,travel_mm,samples):
        inside=q.values(points+d*distance)
        penetration=max(0.,-float(inside.min()))
        worst=max(worst,penetration)
        if penetration>tolerance: blocked.append(round(float(distance),2))
    return {'method':'sampled straight extraction','samples':samples,
            'surface_points':len(points),'travel_mm':round(travel_mm,3),
            'max_penetration_mm':round(worst,4),'passed':not blocked,
            'blocked_distances_mm':blocked,
            'limitation':'Discrete surface/path sampling cannot certify absence of all collisions.'}


def basic_stability(mesh):
    low=mesh.vertices[:,2].min()
    feet=mesh.vertices[mesh.vertices[:,2]<low+max(.5,mesh.extents[2]*.003),:2]
    center=mesh.center_mass[:2]
    margin=None
    if len(feet)>=3:
        from shapely.geometry import MultiPoint, Point
        hull=MultiPoint(feet).convex_hull
        if hull.area>0:
            margin=float(hull.boundary.distance(Point(center)))
            if not hull.covers(Point(center)): margin=-margin
    return {'center_of_mass_mm':np.round(mesh.center_mass,3).tolist(),
            'projected_support_margin_mm':None if margin is None else round(margin,3),
            'assumption':'Uniform solid density; infill, hardware, tolerances and real loads not modelled.',
            'status':'advisory only'}
