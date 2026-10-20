"""Geometry regression for Buddy's bounded internal-cap refinement."""
import importlib.util
from pathlib import Path
import numpy as np
from figuraforge.geometry.surface_parts import interior_cap
from figuraforge.geometry.topology import boundary_loops


def test_refined_cap_preserves_source_boundary_and_winding():
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'verify_buddy_construction.py'
    spec = importlib.util.spec_from_file_location('buddy_cap_regression', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class InteriorQuery:
        def values(self, points):
            return np.full(len(points), -.2)

    module.query = InteriorQuery()
    angle = np.linspace(0, 2*np.pi, 12, endpoint=False)
    boundary = np.column_stack([np.cos(angle), np.sin(angle), np.zeros(12)])
    original = interior_cap(boundary)
    refined = module.fit_cap(boundary, np.array([0., 0., -.1]), .1,
                             minimum_refinements=1, dense_check=True)
    normal = np.average(original.face_normals, axis=0, weights=original.area_faces)
    assert (refined.face_normals @ normal > 0).all()
    assert refined.is_winding_consistent
    assert len(refined.faces) > len(original.faces)
    loops = boundary_loops(refined)
    assert len(loops) == 1
    actual = refined.vertices[loops[0]]
    assert len(actual) == len(boundary)
    assert np.array_equal(np.sort(actual, axis=0), np.sort(boundary, axis=0))
