"""Source/version binding and accepted-fit gates for the independent V2 draft."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
import pytest
from figuraforge.geometry.types import GeometryError
from figuraforge.services.mochi_detail_pipeline import detail_clearance,construct_mochi_detail


@pytest.mark.parametrize('value',[.04,.049,.1,.15,.2,0,-.05,float('nan'),'invalid'])
def test_v2_never_silently_changes_the_accepted_point05_fit(value):
    with pytest.raises(GeometryError,match='0,05'):
        detail_clearance({'pin_clearance_mm':value})


def test_v2_accepted_fit_is_exact():
    assert detail_clearance({'pin_clearance_mm':.05})==.05


@pytest.fixture(scope='module')
def local_review_source():
    from figuraforge.geometry.io import load_surface
    work=Path(__file__).resolve().parents[1]/'benchmarks/mochi-eye-detail-20261016'
    if not (work/'weighted-eyes-150k.glb').exists():
        pytest.skip('Optional local geometry QA asset; fit/version unit gates run without it')
    return load_surface(work/'weighted-eyes-150k.glb',180,'Y'),json.loads((work/'v2-reference-plan.json').read_text()),work


def test_local_v2_source_preserves_v1_rejection_and_checks_new_class_hash(local_review_source):
    from figuraforge.geometry.mochi_masks import mochi_masks
    from figuraforge.geometry.mochi_detail_masks import mochi_detail_masks
    surface,reference,_=local_review_source
    with pytest.raises(GeometryError,match='verified 180 mm'):
        mochi_masks(surface,reference)
    changed=deepcopy(reference);changed['face_regions'][0]=(changed['face_regions'][0]+1)%4
    with pytest.raises(GeometryError,match='mask hash'):
        mochi_detail_masks(surface,changed)


def test_local_v2_semantic_brush_edit_cannot_be_ignored(local_review_source):
    surface,reference,work=local_review_source
    plan=json.loads((work/'v2-draft-6ea76642ad7f4d0491554dded3fbc1b5/plan.json').read_text())
    saved=deepcopy(reference);plan['face_regions'][0]=(plan['face_regions'][0]+1)%9
    with pytest.raises(GeometryError,match='Anatomiemasken'):
        construct_mochi_detail(surface,plan,{'height_mm':180,'up_axis':'Y','pin_clearance_mm':.05},reference_plan=reference)
    assert reference==saved
