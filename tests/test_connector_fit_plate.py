import importlib.util
from pathlib import Path
import numpy as np
import pytest
spec=importlib.util.spec_from_file_location('connector_fit_plate',Path(__file__).resolve().parents[1]/'scripts/prepare_connector_fit_plate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

@pytest.mark.parametrize('letter,name,radius,length,shape',m.SPECS)
def test_optional_calibration_preserves_real_profile_and_open_support_free_socket(letter,name,radius,length,shape):
    for female in (False,True):
        mesh,qa=m.coupon(letter,radius,length,shape,female)
        assert qa['quality']['valid'] and qa['quality']['components']==1
        assert qa['above_bed_downward_area_mm2']==0
        assert abs(qa['volume_error_mm3'])<1e-4
        profile=m.Connector(0,4,radius,length,-length,shape,.05,.35).profile(socket=female)
        target=np.c_[np.asarray(profile.exterior.coords)[:-1],np.full(len(profile.exterior.coords)-1,2+length+.35 if female else 2)]
        assert np.linalg.norm(mesh.vertices[:,None]-target,axis=2).min(0).max()<1e-6
