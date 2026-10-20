from pathlib import Path
import tempfile
import pytest
import numpy as np
import trimesh
from fastapi.testclient import TestClient
from figuraforge.app import create_app
from figuraforge.config import Config
from figuraforge.geometry.types import Surface

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def client(tmp_path):
    app=create_app(Config(root=ROOT,data_dir=tmp_path/'store'))
    with TestClient(app) as c: yield c

@pytest.fixture
def sphere():
    mesh=trimesh.creation.icosphere(subdivisions=3,radius=25)
    mesh.apply_translation([0,0,25])
    return mesh

@pytest.fixture
def painted_sphere(sphere):
    rgb=np.ones((len(sphere.faces),3,3))*.25
    return Surface(sphere,np.zeros((len(sphere.faces),3,2)),rgb,np.zeros(len(sphere.faces),dtype=int))
