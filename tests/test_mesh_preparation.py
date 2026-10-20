import numpy as np
import pytest
from figuraforge.services.mesh_preparation import glb_triangles
from figuraforge.geometry.compare import compare


def test_glb_count_includes_triangles(tmp_path,sphere):
    path=tmp_path/'source.glb';path.write_bytes(sphere.export(file_type='glb'))
    assert glb_triangles(path)==len(sphere.faces)


def test_independent_quality_comparison_detects_no_change(tmp_path,sphere):
    path=tmp_path/'source.glb';path.write_bytes(sphere.export(file_type='glb'))
    report=compare(path,path,height=180,count=200)
    assert report['working']['valid']
    assert report['geometry_distance_mm']['max_sampled']<1e-8
    assert report['albedo_delta_e_2000']['p95']<1e-8
