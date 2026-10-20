import numpy as np
import pytest
import trimesh
from figuraforge.geometry.validation import DistanceQuery
from figuraforge.geometry.types import GeometryError


def test_closed_surface_sign_distinguishes_hole_from_material():
    mesh=trimesh.creation.annulus(r_min=2,r_max=4,height=3,sections=40)
    query=DistanceQuery(mesh)
    values=query.values([[0,0,0],[3,0,0],[0,0,4],[5,0,0]])
    assert values[0]>1.9  # Empty hole is inside bounds, outside material.
    assert values[1]<-.9
    assert values[2]>0 and values[3]>0


def test_sign_is_independent_of_nearest_face_pseudonormal(monkeypatch):
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy
    mesh=trimesh.creation.annulus(r_min=2,r_max=4,height=3,sections=40)
    query=DistanceQuery(mesh)
    original=vtk.vtkSampleImplicitFunctionFilter
    class ReversedPseudoNormal:
        def __init__(self):self.filter=original()
        def __getattr__(self,name):return getattr(self.filter,name)
        def Update(self):
            self.filter.Update()
            array=vtk_to_numpy(self.filter.GetOutput().GetPointData().GetArray('Implicit scalars'))
            array[:]=-array
    monkeypatch.setattr(vtk,'vtkSampleImplicitFunctionFilter',ReversedPseudoNormal)
    values=query.values([[0,0,0],[3,0,0],[5,0,0]])
    assert values[0]>0 and values[1]<0 and values[2]>0


def test_open_surfaces_and_nonfinite_query_points_are_rejected():
    mesh=trimesh.creation.box()
    with pytest.raises(GeometryError):DistanceQuery(mesh.submesh([np.arange(10)],append=True))
    query=DistanceQuery(mesh)
    with pytest.raises(GeometryError):query.values([[np.nan,0,0]])
    assert query.values([]).shape==(0,)


def test_overlapping_closed_shells_cannot_hide_real_material_by_ray_parity():
    first=trimesh.creation.box(extents=[4,4,4]);second=first.copy()
    second.apply_translation([1,0,0])
    overlapping=trimesh.util.concatenate([first,second])
    assert overlapping.is_watertight and overlapping.is_winding_consistent and overlapping.is_volume
    with pytest.raises(GeometryError,match='one connected surface'):
        DistanceQuery(overlapping)


def test_nested_closed_shells_require_explicit_cavity_validation():
    outer=trimesh.creation.box(extents=[6,6,6]);inner=trimesh.creation.box(extents=[2,2,2]);inner.invert()
    cavity=trimesh.util.concatenate([outer,inner])
    assert cavity.is_volume
    with pytest.raises(GeometryError,match='nested/overlapping'):
        DistanceQuery(cavity)


def test_certified_disjoint_positive_solids_retain_union_sign():
    first=trimesh.creation.box(extents=[2,2,2]);second=first.copy();second.apply_translation([4,0,0])
    query=DistanceQuery(trimesh.util.concatenate([first,second]))
    values=query.values([[0,0,0],[4,0,0],[2,0,0],[0,3,0]])
    assert values[0]<0 and values[1]<0 and values[2]>0 and values[3]>0
