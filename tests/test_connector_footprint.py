import numpy as np
import trimesh
from shapely.geometry import Point,box
from figuraforge.geometry.connectors import pick_connectors


def flat_patch():
    return trimesh.Trimesh(vertices=[[-10,-10,0],[10,-10,0],[10,10,0],[-10,10,0]],
        faces=[[0,1,2],[0,2,3]],process=False)


def test_keyed_corners_cannot_consume_the_required_wall():
    outline=Point(0,0).buffer(3.4,quad_segs=64)
    kwargs=dict(radius=2,length=2,clearance=.1,count=1,wall=1)
    assert pick_connectors(outline,flat_patch(),np.eye(3),1,shape='round',**kwargs)
    assert not pick_connectors(outline,flat_patch(),np.eye(3),1,shape='keyed',**kwargs)


def test_exact_keyed_footprint_accepts_a_square_without_using_circumscribed_circle():
    outline=box(-3.2,-3.2,3.2,3.2)
    pins=pick_connectors(outline,flat_patch(),np.eye(3),1,radius=2,length=2,
        clearance=.1,count=1,shape='keyed',wall=1)
    assert pins
    assert all(outline.buffer(-1).covers(p.profile(socket=True)) for p in pins)
