"""Camera briefing regression: opposing views, not mirrored anatomy."""
import pytest
from figuraforge.providers.images import pose_prompt


def test_side_cameras_have_opposite_anatomical_and_screen_direction():
    left=pose_prompt('Sitzend','Gecko mit einem Schwanz','left',has_front=True)
    right=pose_prompt('Sitzend','Gecko mit einem Schwanz','right',has_front=True)
    assert 'anatomical LEFT side' in left
    assert "character's own left side" in left and 'LEFT edge of the image' in left
    assert 'anatomical RIGHT side' in right
    assert "character's own right side" in right and 'RIGHT edge of the image' in right
    assert 'RIGHT edge of the image' not in left
    assert 'LEFT edge of the image' not in right


@pytest.mark.parametrize('view',['front','left','back','right'])
def test_turnaround_keeps_asymmetry_and_reference_limb_count(view):
    prompt=pose_prompt('Freundlich','Ein Gecko mit vier Gliedmassen und einem Schwanz',view)
    assert 'never mirror a reference' in prompt
    assert 'asymmetrical markings and accessories on their original anatomical side' in prompt
    assert 'exact limb count and attachment points' in prompt
    assert 'four feet' not in prompt and 'four legs' not in prompt


@pytest.mark.parametrize('model_type',['figurine','bust','relief','custom'])
def test_camera_briefing_does_not_impose_quadruped_anatomy_on_other_models(model_type):
    prompt=pose_prompt('Aufrecht','Zweibeiniger Roboter mit einem Arm',view='left',model_type=model_type)
    assert 'Zweibeiniger Roboter mit einem Arm' in prompt
    assert 'exact limb count' in prompt
    assert 'front legs' not in prompt and 'hind legs' not in prompt
    assert 'both feet' not in prompt
    assert 'four legs' not in prompt
