from pathlib import Path
import numpy as np
import pytest
import trimesh
from figuraforge.geometry.buddy_collar import build_collar,_axial_joint
from figuraforge.geometry.types import GeometryError
from figuraforge.geometry.validation import check_insert_path,validate_mesh


def test_collar_rejects_unreviewed_source_before_writing(tmp_path):
    target=tmp_path/'unexpected'
    with pytest.raises(GeometryError,match='bound to the reviewed'):
        build_collar(trimesh.creation.box(),target,source_binding={'height_mm':1000})
    assert not target.exists()


def test_central_neck_joint_keeps_closed_halves_and_real_fit_clearance():
    low=trimesh.creation.cylinder(radius=89.85,height=40,sections=64)
    high=low.copy();low.apply_translation([0,0,-20]);high.apply_translation([0,0,20])
    a,b,pins=_axial_joint(low,high,0.)
    assert len(pins)>=2
    assert all(p['radial_clearance_mm']==.05 for p in pins)
    assert all(validate_mesh(m)['valid'] for m in [a,b])
    assert a.volume+b.volume < low.volume+high.volume
    assert check_insert_path(b,a,np.array([0.,0.,1.]),travel_mm=40)['passed']
    # Source cylindrical exterior dimensions survive; no replacement/remesh.
    assert np.array_equal(a.bounds[:,:2],low.bounds[:,:2])
    assert np.array_equal(b.bounds[:,:2],high.bounds[:,:2])


def test_boolean_connector_reaches_nominal_radius_at_real_root():
    from figuraforge.geometry.buddy_collar import _primitive
    from figuraforge.geometry.connectors import Connector
    for radius,length in [(6,10),(2,6)]:
        pin=Connector(0,0,radius,length,-length,shape='keyed',clearance=.05)
        male=_primitive(pin,np.eye(3),False);socket=_primitive(pin,np.eye(3),True)
        assert validate_mesh(male)['valid'] and validate_mesh(socket)['valid']
        for z in [0.,1.,2.]:
            for mesh,expected in [(male,radius),(socket,radius+.05)]:
                points=mesh.vertices[np.isclose(mesh.vertices[:,2],z)]
                if z==1.:points=mesh.section([0,0,1],[0,0,z]).vertices
                assert np.max(abs(points[:,:2]))==pytest.approx(expected)
        root_male=male.vertices[np.isclose(male.vertices[:,2],0)]
        root_socket=socket.vertices[np.isclose(socket.vertices[:,2],0)]
        assert np.max(abs(root_socket[:,:2]))-np.max(abs(root_male[:,:2]))==pytest.approx(.05)


def test_collar_sliding_bore_has_real_radial_clearance_without_changing_core():
    from figuraforge.geometry.buddy_collar import _annular_cutters,INNER_RADIUS
    core,ring=_annular_cutters(np.eye(4))
    cr=np.linalg.norm(core.vertices[:,:2],axis=1);rr=np.linalg.norm(ring.vertices[:,:2],axis=1)
    assert min(cr)==pytest.approx(INNER_RADIUS)
    assert min(rr)-min(cr)==pytest.approx(.05)
    assert max(rr)==pytest.approx(max(cr))
    assert np.array_equal(core.bounds[:,2],ring.bounds[:,2])
    assert validate_mesh(core)['valid'] and validate_mesh(ring)['valid']
