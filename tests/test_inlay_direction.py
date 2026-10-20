from types import SimpleNamespace
import numpy as np
import pytest
from figuraforge.geometry.construct import choose_direction
from figuraforge.geometry.types import GeometryError


def patch(normals,areas):
    return SimpleNamespace(face_normals=np.asarray(normals,float),area_faces=np.asarray(areas,float))


def test_oblique_patch_uses_feasible_cone_instead_of_rejecting_biased_mean():
    p=patch([[1,0,0],[-.8,.6,0]],[100,1])
    mean=np.average(p.face_normals,weights=p.area_faces,axis=0);mean/=np.linalg.norm(mean)
    assert (p.face_normals@mean).min()<0
    direction=choose_direction(p)
    assert np.isclose(np.linalg.norm(direction),1)
    assert (p.face_normals@direction).min()>=.06


def test_opposing_faces_still_reject_an_impossible_straight_insertion():
    with pytest.raises(GeometryError):choose_direction(patch([[1,0,0],[-1,0,0]],[100,1]))


def test_explicit_unsafe_override_is_not_silently_replaced():
    with pytest.raises(GeometryError):choose_direction(patch([[1,0,0],[-.8,.6,0]],[100,1]),[1,0,0])


def test_existing_good_average_remains_unchanged():
    p=patch([[1,0,0],[.8,.6,0]],[2,1]);expected=np.average(p.face_normals,weights=p.area_faces,axis=0);expected/=np.linalg.norm(expected)
    np.testing.assert_allclose(choose_direction(p),expected)
