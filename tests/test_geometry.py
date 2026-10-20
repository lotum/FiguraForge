import json,zipfile
from pathlib import Path
import numpy as np
import pytest
import trimesh
from figuraforge.geometry.types import GeometryError
from figuraforge.geometry.io import load_surface,validate_glb_bytes
from figuraforge.geometry.refine import split_marked_edges,refine_for_color
from figuraforge.geometry.construct import make_inlays
from figuraforge.geometry.validation import validate_mesh,require_solid,check_insert_path
from figuraforge.geometry.split import split_with_joint,tile_parts
from figuraforge.geometry.packing import pack_parts,validate_packing
from figuraforge.geometry.types import Part
from figuraforge.services.export import write_3mf,validate_3mf
from conftest import ROOT


def test_input_textures_preserved_and_height_scaled():
    s=load_surface(ROOT/'examples/teddy-source.glb',180,'Y')
    assert s.mesh.is_volume
    assert s.mesh.extents[2]==pytest.approx(180,abs=1e-6)
    assert np.ptp(s.sample(),axis=0).max()>.5
    assert len(s.corner_uv)==len(s.mesh.faces)

@pytest.mark.parametrize('fraction',[.01,.1,.4,1])
def test_conforming_refinement_never_creates_t_junction(painted_sphere,fraction):
    mask=np.random.default_rng(22).random(len(painted_sphere.mesh.faces))<fraction
    refined=split_marked_edges(painted_sphere,mask)
    assert refined.mesh.is_watertight and refined.mesh.is_winding_consistent
    assert refined.mesh.volume==pytest.approx(painted_sphere.mesh.volume,rel=1e-8)

def test_single_color_produces_unmodified_core(sphere):
    parts,r=make_inlays(sphere,np.zeros(len(sphere.faces),int),['#FFFFFF'])
    assert len(parts)==1 and parts[0].mesh.volume==pytest.approx(sphere.volume)

def test_two_adjacent_colors_share_organic_pocket(sphere):
    centers=sphere.triangles_center
    mask=(centers[:,1]<-12)&(np.abs(centers[:,0])<16)&(centers[:,2]>13)&(centers[:,2]<36)
    labels=np.zeros(len(sphere.faces),int);labels[mask]=1;labels[mask&(centers[:,0]>0)]=2
    parts,report=make_inlays(sphere,labels,['#895330','#E5C189','#EA7654'],depth_mm=2,pin_radius_mm=1.,pin_length_mm=2,validate_paths=True)
    assert len(report['pockets'])==1 and len(parts)==3
    assert all(p.mesh.is_volume for p in parts)
    assert all(t['passed'] for t in report['insertion_checks'])
    assert report['parts_volume_mm3']<=sphere.volume
    assert sum(len(p.connectors) for p in parts)>=2
    # Color region exterior is curved, not a plane fitted to the texture.
    insert=parts[1].mesh
    assert np.ptp(insert.vertices[:,1])>4

def test_wraparound_region_rejected(sphere):
    labels=(sphere.triangles_center[:,2]>25).astype(int)
    # Choosing an intentionally incompatible direction must fail safely.
    with pytest.raises(GeometryError):
        make_inlays(sphere,labels,['#FFFFFF','#FF0000'],direction_overrides={'0':[1,0,0]})

def test_too_deep_pocket_rejected(sphere):
    labels=(sphere.triangles_center[:,1]<-17).astype(int)
    with pytest.raises(GeometryError):make_inlays(sphere,labels,['#FFFFFF','#000000'],depth_mm=65)

def test_open_mesh_blocked(sphere):
    broken=sphere.copy();broken.update_faces(np.arange(len(broken.faces)-1))
    assert not validate_mesh(broken)['valid']
    with pytest.raises(GeometryError):require_solid(broken)

@pytest.mark.parametrize('axis',[0,1,2])
def test_large_part_split_has_matching_closed_keyed_pins(axis):
    m=trimesh.creation.box([70,60,80]);m.apply_translation([0,0,40])
    pos=m.centroid[axis]+.001
    a,b,connectors,d=split_with_joint(m,axis,pos,3,8,.2)
    assert a.is_volume and b.is_volume and connectors
    assert a.volume+b.volume<m.volume
    assert m.volume-(a.volume+b.volume)<1000

def test_packing_color_group_and_no_collision(sphere):
    parts=[Part('p'+str(i),'sphere',sphere.copy(),'#FF0000' if i<3 else '#00FF00') for i in range(6)]
    plates=pack_parts(parts,[140,140,120],margin=6,gap=5,max_colors=1)
    assert len(plates)>=2
    assert validate_packing(parts,plates)['passed']
    for plate in plates:
        assert len({next(p.color for p in parts if p.id==i['part_id']) for i in plate['placements']})<=1

def test_3mf_roundtrip_color_unit_transform(tmp_path,sphere):
    part=Part('sphere','Curved insert',sphere,'#E5C189')
    t=np.eye(4);t[:3,3]=[30,40,10]
    path=tmp_path/'sphere.3mf';write_3mf([part],path,[{'part_id':part.id,'transform':t.tolist()}])
    assert validate_3mf(path)['passed']
    with zipfile.ZipFile(path) as z:
        xml=z.read('3D/3dmodel.model').decode()
        assert '#E5C189' in xml and 'millimeter' in xml
    result=trimesh.load(path,force='scene').to_geometry()
    assert result.volume==pytest.approx(sphere.volume,rel=1e-5)
    assert np.allclose(result.bounds,sphere.bounds+[30,40,10],atol=.001)

def test_glb_external_resources_rejected():
    import struct
    obj={'asset':{'version':'2.0'},'images':[{'uri':'http://localhost/secret'}]}
    raw=json.dumps(obj).encode();raw+=b' ' *((-len(raw))%4)
    data=struct.pack('<4sII',b'glTF',2,len(raw)+20)+struct.pack('<I4s',len(raw),b'JSON')+raw
    with pytest.raises(GeometryError):validate_glb_bytes(data)

def test_3mf_preserves_distant_thin_geometry_in_float32_slicers(tmp_path):
    from xml.etree import ElementTree as ET
    # At 2000 mm, float32 cannot distinguish this thin feature's two sides.
    mesh=trimesh.creation.box(extents=[.00002,2,2])
    mesh.apply_translation([2000,1800,1600])
    part=Part('thin','Precision regression',mesh,'#E5C189')
    tf=trimesh.transformations.rotation_matrix(.7,[0,0,1])
    tf[:3,3]=[20,30,40]
    path=tmp_path/'thin.3mf'
    write_3mf([part],path,[{'part_id':part.id,'transform':tf.tolist()}])
    with zipfile.ZipFile(path) as z:
        doc=ET.fromstring(z.read('3D/3dmodel.model'))
    ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
    vertices=np.array([[float(v.get(c)) for c in ('x','y','z')]
        for v in doc.findall('.//m:vertex',ns)],dtype=np.float32)
    assert np.max(np.abs(vertices))<=1
    assert len(np.unique(vertices,axis=0))==8
    result=trimesh.load_scene(path).to_geometry()
    expected=mesh.copy();expected.apply_transform(tf)
    assert result.is_volume
    assert np.allclose(result.bounds,expected.bounds,atol=1e-6)

@pytest.mark.parametrize('shape',['hemisphere','circumferential-band','non-planar-wave'])
def test_whole_color_parts_follow_surface_boundaries(shape):
    from figuraforge.geometry.surface_parts import make_surface_parts
    m=trimesh.creation.icosphere(subdivisions=3,radius=35);m.apply_translation([0,0,35]);v=m.triangles_center
    labels=(v[:,2]>35).astype(int) if shape=='hemisphere' else ((v[:,2]>24)&(v[:,2]<46)).astype(int) if shape=='circumferential-band' else (v[:,2]>35+4*np.sin(v[:,0]/8)).astype(int)
    parts,report=make_surface_parts(m,labels,['#895330','#E5C189'],pin_radius_mm=2,pin_length_mm=5,validate_paths=True)
    assert len(parts)==(3 if shape=='circumferential-band' else 2)
    assert all(p.mesh.is_volume for p in parts)
    assert sum(len(p.connectors) for p in parts)>=2
    assert sum(p.mesh.volume for p in parts)<m.volume
    assert report['strategy']=='shared non-planar boundary caps'

@pytest.mark.parametrize('shape',['round','keyed'])
def test_calibration_actual_geometries(tmp_path,shape):
    import zipfile,json
    from figuraforge.services.calibration import create_calibration
    result=create_calibration(tmp_path,shape)
    assert result['parts']==10
    assert all(v['passed'] for v in result['validation'].values())
    with zipfile.ZipFile(tmp_path/result['bundle']) as z:
        assert 'PASSUNG.md' in z.namelist()
        manifest=json.loads(z.read('manifest.json'))
        assert [p['radial_clearance_mm'] for p in manifest['pairs']]==[.1,.15,.2,.25,.3]


def test_settings_no_nonfinite_build_volume():
    from figuraforge.models import Settings
    from pydantic import ValidationError
    with pytest.raises(ValidationError): Settings(build_volume_mm=[float('nan'),300,300])


def test_export_directory_reuse_has_no_stale_or_self_hash(tmp_path,sphere):
    import hashlib
    from figuraforge.services.export import export_bundle
    a=Part('a','part A',sphere,'#AABBCC')
    first=export_bundle([a],pack_parts([a]),tmp_path)
    (tmp_path/'private.txt').write_text('must not be exported')
    b=Part('b','part B',sphere,'#AABBCC')
    second=export_bundle([b],pack_parts([b]),tmp_path)
    with zipfile.ZipFile(tmp_path/second['bundle']) as z:
        assert 'a.3mf' not in z.namelist() and 'private.txt' not in z.namelist()
        sums=json.loads(z.read('SHA256.json'))
        assert 'SHA256.json' not in sums
        assert all(hashlib.sha256(z.read(name)).hexdigest()==sha for name,sha in sums.items())

@pytest.mark.parametrize('shape',['box','sphere','ring','torus'])
def test_constrained_plane_cut_preserves_volume_and_holes(shape):
    from figuraforge.geometry.plane_cut import clip_closed
    shapes={'box':lambda:trimesh.creation.box(extents=[60,70,80]),
            'sphere':lambda:trimesh.creation.icosphere(subdivisions=2,radius=25),
            'ring':lambda:trimesh.creation.annulus(r_min=12,r_max=25,height=50,sections=32),
            'torus':lambda:trimesh.creation.torus(major_radius=25,minor_radius=8)}
    m=shapes[shape]()
    for axis in range(3):
        lo,hi=m.bounds[:,axis];pos=lo+(hi-lo)*.417+.000137
        a=clip_closed(m,axis,pos,False);b=clip_closed(m,axis,pos,True)
        assert a.is_volume and b.is_volume
        assert abs(a.volume+b.volume-m.volume)<m.volume*1e-7


def test_small_cosmetic_insert_gets_explicitly_reported_smaller_pin(sphere):
    labels=((sphere.triangles_center[:,2]>49.3)).astype(int)
    if not labels.any(): pytest.fail('Fixture has no small cap')
    nominal,_=make_inlays(sphere,labels,['#AAAAAA','#111111'],pin_radius_mm=3,depth_mm=2,
                         min_region_area_mm2=0,validate_paths=False,adaptive_small_pins=False)
    adaptive,_=make_inlays(sphere,labels,['#AAAAAA','#111111'],pin_radius_mm=3,depth_mm=2,
                          min_region_area_mm2=0,validate_paths=False,adaptive_small_pins=True)
    assert all(p.mesh.is_volume for p in adaptive)
    assert not nominal[1].connectors
    assert adaptive[1].connectors and adaptive[1].connectors[0]['diameter_mm']==1.6
    assert any('reduced' in warning for warning in adaptive[1].warnings)


def test_mesh_import_keeps_a_bounded_face_limit(tmp_path,sphere,monkeypatch):
    from figuraforge.geometry import io as mesh_io
    from figuraforge.geometry.types import GeometryError
    path=tmp_path/'bounded.glb';path.write_bytes(sphere.export(file_type='glb'))
    assert mesh_io.MAX_FACES==1_000_000
    monkeypatch.setattr(mesh_io,'MAX_FACES',len(sphere.faces)-1)
    with pytest.raises(GeometryError,match='remesh below'):
        mesh_io.load_surface(path)


@pytest.mark.parametrize('fraction',[.01,.1,.4,1.])
def test_refinement_budget_prediction_is_exact(painted_sphere,fraction):
    from figuraforge.geometry.refine import projected_split_faces
    marked=np.random.default_rng(804).random(len(painted_sphere.mesh.faces))<fraction
    assert projected_split_faces(painted_sphere.mesh,marked)==len(split_marked_edges(painted_sphere,marked).mesh.faces)


def test_automatic_precision_is_scaled_and_reported(painted_sphere):
    from figuraforge.geometry.refine import refine_with_plan
    from figuraforge.models import Settings
    settings=Settings(height_mm=1000).model_dump()
    _,_,report=refine_with_plan(painted_sphere,['#404040'],settings)
    assert report['ready'] and report['effective_boundary_mm']==pytest.approx(.65*1000/180)
    assert report['triangles']<=settings['max_refined_faces']


def test_fixed_precision_is_never_silently_relaxed(painted_sphere):
    from figuraforge.geometry.refine import refine_with_plan
    from figuraforge.models import Settings
    settings=Settings(height_mm=1000,precision_mode='fixed').model_dump()
    _,_,report=refine_with_plan(painted_sphere,['#404040'],settings)
    assert report['effective_boundary_mm']==.65 and report['mode']=='fixed'


def test_direction_precheck_distinguishes_wrapping_region_from_insertable_patch():
    from figuraforge.geometry.construct import inspect_inlay_directions
    mesh=trimesh.creation.box()
    labels=(mesh.face_normals[:,2]>0.5).astype(int)
    good=inspect_inlay_directions(mesh,labels,min_area=0)
    assert good['passed'] and good['pockets']==1
    labels=(mesh.face_normals[:,2]>-0.5).astype(int)
    bad=inspect_inlay_directions(mesh,labels,min_area=0)
    assert not bad['passed'] and bad['blocked_directions']==1
    assert 'Weniger Faces' in bad['message']


def test_native_companion_is_included_with_checksum_and_clear_format_notes(tmp_path):
    import hashlib,json,zipfile
    from figuraforge.services.export import export_bundle
    part=Part('cube','Cube',trimesh.creation.box(),'#FFFFFF')
    (tmp_path/'plate-01-native.3mf').write_bytes(b'checked separately native file')
    result=export_bundle([part],pack_parts([part]),tmp_path,{'native_color_export':{'gui_verified':False}},
                         additional_files=['plate-01-native.3mf'])
    with zipfile.ZipFile(tmp_path/result['bundle']) as archive:
        assert archive.read('plate-01-native.3mf')==b'checked separately native file'
        checks=json.loads(archive.read('SHA256.json'))
        assert checks['plate-01-native.3mf']==hashlib.sha256(archive.read('plate-01-native.3mf')).hexdigest()
        assert 'experimental' in json.loads(archive.read('manifest.json'))['format_notes']['native']
        assert 'plate-XX-native.3mf' in archive.read('MONTAGE.md').decode()


def test_explicit_glue_inlay_does_not_grow_pins_when_clearance_is_tightened():
    mesh=trimesh.creation.box(extents=[20,20,20]);mesh.apply_translation([0,0,10])
    labels=(mesh.face_normals[:,2]>.9).astype(int)
    pinned,_=make_inlays(mesh,labels,['#AAAAAA','#111111'],depth_mm=2,seam_mm=0,
        pin_clearance_mm=.05,pin_radius_mm=1.5,pin_length_mm=1.5,validate_paths=False)
    assert any(p.connectors for p in pinned)
    glued,report=make_inlays(mesh,labels,['#AAAAAA','#111111'],depth_mm=2,seam_mm=0,
        pin_clearance_mm=.05,pin_radius_mm=1.5,pin_length_mm=1.5,connector_mode='glue')
    assert len(glued)==2 and all(not p.connectors for p in glued)
    assert [p.role for p in glued]==['body','glue-inlay']
    assert all(validate_mesh(p.mesh)['valid'] for p in glued)
    assert sum(p.mesh.volume for p in glued)==pytest.approx(mesh.volume)
    assert all(c['passed'] for c in report['insertion_checks'])

def test_native_bundle_preserves_pip_assembly_order_and_names_native_files_first(tmp_path):
    import json,zipfile
    from figuraforge.services.export import export_bundle
    from figuraforge.geometry.packing import pack_parts
    from figuraforge.geometry.types import Part
    part=Part('pip-head','Pip Kopf',trimesh.creation.box(), '#F7E6DE')
    instructions=[
        'Unterkiefer zuerst am oberen Kopf montieren, solange der Kopf noch vom Rumpf getrennt ist.',
        'Vormontierte Kopfgruppe senkrecht auf die beiden Halsstifte am vorderen Rumpf setzen.',
        'Beide Iris-/Augenrahmen am montierten Kopf einsetzen.',
        'Zuletzt die dunklen Pupillen mit ihren hellen Reflexen in die Irisrahmen stecken.',
    ]
    metadata={'native_color_export':{'gui_verified':False,'slicing_verified':False},
              'geometry_report':{'construction':{'construction_preset':'pip-anatomical-v1','assembly_instructions_de':instructions}}}
    # Payload identity/packaging only; this fixture is not a slicer/native-format test.
    native=tmp_path/'plate-01-native.3mf';native.write_bytes(b'native fixture preserved')
    result=export_bundle([part],pack_parts([part]),tmp_path,metadata,additional_files=[native.name])
    with zipfile.ZipFile(tmp_path/result['bundle']) as archive:
        guide=archive.read('MONTAGE.md').decode()
        positions=[guide.index(f'{i}. {step}') for i,step in enumerate(instructions,1)]
        assert positions==sorted(positions)
        assert '2. Je plate-XX-native.3mf als natives Projekt' in guide
        assert 'Core-Dateien und assembly.glb sind einfarbige Geometriebegleiter' in guide
        assert '5. Einsaetze entlang' not in guide
        assert 'noch nicht physisch geprueft' in guide
        assert archive.read(native.name)==b'native fixture preserved'
        manifest=json.loads(archive.read('manifest.json'))
        assert manifest['geometry_report']['construction']['assembly_instructions_de']==instructions
    assert metadata['geometry_report']['construction']['assembly_instructions_de']==instructions


def test_buddy_bundle_describes_tiled_connections_and_glue_without_false_zero_counts(tmp_path):
    import zipfile
    from figuraforge.services.export import export_bundle
    from figuraforge.geometry.packing import pack_parts
    from figuraforge.geometry.types import Part
    parts=[Part(ident,ident,trimesh.creation.box(),'#B19870') for ident in ('body-a','left-eye','collar-right')]
    connections={'total_keys':8,'total_keyed_interfaces':3,'structural_leaf_part_ids':['body-a'],'glue_part_ids':['left-eye']}
    metadata={'geometry_report':{'construction':{'construction_preset':'buddy-anatomical-v1',
        'assembly_connections':connections,'assembly_instructions_de':['Strukturkacheln zuerst entlang ihrer Schlüsselflächen verbinden.']}}}
    result=export_bundle(parts,pack_parts(parts),tmp_path,metadata)
    with zipfile.ZipFile(tmp_path/result['bundle']) as archive:
        guide=archive.read('MONTAGE.md').decode()
        assert '8 Schlüssel an 3 Steckanschlüssen' in guide
        assert 'body-a; #B19870; Strukturkachel mit Schlüsselflächen' in guide
        assert 'left-eye; #B19870; Klebeteil' in guide
        assert 'collar-right; #B19870; Buchsenteil' in guide
        assert '0 Verbinder' not in guide
    assert all(not p.connectors for p in parts)  # No fabricated connector planes.
