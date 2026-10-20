import numpy as np
import pytest
from figuraforge.geometry.colors import delta_e_2000,srgb_to_lab,hex_rgb,choose_palette
from figuraforge.services.filaments import rank_filaments,normalize_spoolmandb,normalize_spoolman

@pytest.mark.parametrize('a,b,expected',[
 ([50,2.6772,-79.7751],[50,0,-82.7485],2.0425),
 ([50,3.1571,-77.2803],[50,0,-82.7485],2.8615),
 ([50,2.8361,-74.0200],[50,0,-82.7485],3.4412),
 ([50,-1.3802,-84.2814],[50,0,-82.7485],1.0000),
 ([50,0,0],[50,0,0],0),
])
def test_ciede2000_reference_pairs(a,b,expected):
    assert float(delta_e_2000(np.array(a),np.array(b)))==pytest.approx(expected,abs=5e-5)

def test_lab_white_black():
    assert srgb_to_lab(np.ones(3))[0]==pytest.approx(100,abs=.01)
    assert np.allclose(srgb_to_lab(np.zeros(3)),0)

def test_palette_deterministic_and_not_average_boundary():
    colors=np.array([[1,0,0]]*100+[[0,0,1]]*30)
    assert choose_palette(colors,2)==choose_palette(colors,2)
    assert set(choose_palette(colors,2))=={'#FF0000','#0000FF'}

def test_real_color_distance_preserved_with_preference():
    fs=[dict(id='a',brand='Elegoo',hex='#FF0000',owned=True),dict(id='b',brand='Other',hex='#0000FF',owned=True)]
    r=rank_filaments('#FF0000',fs)
    assert r[0]['id']=='a' and r[0]['delta_e_2000']==0

def test_filament_filters():
    fs=[dict(id='a',brand='Elegoo',hex='#FF0000',owned=False),dict(id='b',brand='Other',hex='#FE0000',owned=True),dict(id='c',brand='Other',hex='#FF0000',owned=True,allowed=False)]
    assert [r['id'] for r in rank_filaments('#FF0000',fs,owned_only=True)]==['b']

def test_catalog_normalization():
    rows=normalize_spoolmandb([{'id':1,'manufacturer':'Elegoo','name':'Red','material':'PLA','color_hex':'FF0000'}])
    assert rows[0]['brand']=='Elegoo' and not rows[0]['owned'] and not rows[0]['measured']
    assert normalize_spoolmandb([{'color_hex':'invalid'}])==[]
    sp=normalize_spoolman([{'id':2,'remaining_weight':480,'filament':{'color_hex':'ff0000','vendor':{'name':'Bambu Lab'}}}])
    assert sp[0]['owned'] and sp[0]['remaining_weight_g']==480
