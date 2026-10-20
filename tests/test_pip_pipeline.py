from copy import deepcopy
import numpy as np
import pytest
import trimesh
from figuraforge.geometry.types import Surface,Part,GeometryError
from figuraforge.services import pip_pipeline as pip


def surface():
    mesh=trimesh.creation.box();count=len(mesh.faces)
    return Surface(mesh,np.zeros((count,3,2)),np.ones((count,3,3)),np.zeros(count,int))


def settings(**changes):
    return {'height_mm':180,'up_axis':'Y','printer_id':'h2d-dual','validate_paths':True,**changes}


def test_pip_preset_rejects_unrelated_source_without_mutating_reference():
    source=surface();reference={'mesh_hash':pip.MESH_HASH};before=deepcopy(reference)
    with pytest.raises(GeometryError,match='Quellgeometrie'):
        pip.suggest_pip_plan(source,reference,settings(),pip.MESH_HASH,[])
    assert reference==before


@pytest.mark.parametrize('override',[{'height_mm':181},{'up_axis':'Z'},{'printer_id':'other'}])
def test_pip_bound_scale_axis_and_printer(override):
    with pytest.raises(GeometryError,match='180 mm'):
        pip._guard(surface(),settings(**override),pip.MESH_HASH)


def test_pip_mesh_version_cannot_be_reused_for_new_import():
    with pytest.raises(GeometryError,match='Meshversion'):
        pip._guard(surface(),settings(),'a'*64)


def test_exterior_mapping_rejects_centroid_normal_coincidence_without_corner_provenance():
    source=surface();original=source.mesh.triangles[0];center=original.mean(axis=0)
    # Oversized coplanar cap: exactly the same centroid and normal, corners outside source.
    triangles=center+(original-center)*1.5
    cap=trimesh.Trimesh(triangles,[[0,1,2]],process=False)
    mask,_,_=pip.exterior_face_mapping(source,Part('cap','cap',cap,'#FFFFFF'))
    assert not mask.any()
    # A true subdivision entirely within the same source triangle remains exterior.
    sub=trimesh.Trimesh([original[0],original[1],center],[[0,1,2]],process=False)
    mask,_,_=pip.exterior_face_mapping(source,Part('sub','sub',sub,'#FFFFFF'))
    assert mask.tolist()==[True]


def test_internal_near_surface_wall_is_never_printed_as_external_color():
    source=surface();tri=source.mesh.triangles[0].copy();tri-=source.mesh.face_normals[0]*.0001
    inner=trimesh.Trimesh(tri,[[0,1,2]],process=False)
    assert not pip.exterior_face_mapping(source,Part('inner','inner',inner,'#FFFFFF'))[0].any()


def test_semantic_cream_is_not_reassigned_to_pale_green_by_nearest_inventory_hex(monkeypatch):
    source=surface();count=len(source.mesh.faces)
    source.corner_rgb[:]=np.array([.57,.67,.16]);source.corner_rgb[0]=np.array([.875,.788,.45])
    owner=np.arange(count)%len(pip.PART_KEYS);monkeypatch.setattr(pip,'source_ownership',lambda *_:(owner,{}))
    parts=[Part(k,k,source.mesh,'#FFFFFF') for k in pip.PART_KEYS]
    stock={ident:{'hex':color,'name':ident} for ident,color in [(pip.GREEN,'#C2E189'),(pip.BROWN,'#805947'),(pip.BEIGE,'#F7E6DE'),(pip.BLACK,'#272729')]}
    plan,mapping,_=pip._semantic_plan(source,parts,pip.MESH_HASH,stock,[pip.GREEN,pip.BROWN])
    region=next(r for r in plan['regions'] if r['id']==plan['face_regions'][0])
    assert region['filament_id']==pip.BEIGE
    assert region['part_group']==1 and region['id'] in mapping['body-front']


def test_isolated_plate_orientation_keeps_both_front_pin_axes_up_and_preserves_geometry():
    parts=[]
    for name in pip.PART_KEYS:
        mesh=trimesh.creation.box(extents=[5,6,7]);direction=[0,-.894427,-.447214]
        parts.append(Part(name,name,mesh,'#FFFFFF',assembly_direction=direction,connectors=[{}] if name not in ['body-rear','head-upper'] else []))
    vertices=[p.mesh.vertices.copy() for p in parts];plates=pip.pack_pip_parts(parts)
    assert len(plates)==10 and all(len(p['placements'])==1 for p in plates)
    rotation=np.array(plates[0]['placements'][0]['transform'])[:3,:3]
    for pin_axis in [np.array([0,1,.5])/np.linalg.norm([0,1,.5]),np.array([0,0,1])]:
        assert (rotation@pin_axis)[2]>.8
    for part,before in zip(parts,vertices):np.testing.assert_array_equal(part.mesh.vertices,before)


def test_support_settings_remain_explicit_and_auto_uses_actual_object_material():
    old={'layer_height':'0.16','enable_support':'0','support_filament':'1','filament_is_mixed':['0','0']};before=deepcopy(old)
    result=pip.configure_pip_plate(old,{'placements':[{'part_id':'left-iris'}]})
    assert old==before
    assert result['support_filament']=='0' and result['raft_layers']=='3'
    assert result['support_on_build_plate_only']=='1' and result['layer_height']=='0.2'
    with pytest.raises(GeometryError,match='isolierte'):
        pip.configure_pip_plate(old,{'placements':[{'part_id':'left-iris'},{'part_id':'jaw'}]})


def test_existing_edge_subdivision_closes_tjunction_without_inventing_hole_cap():
    from figuraforge.geometry.topology import mesh_from_triangles
    mesh=trimesh.creation.box();a,b,c=mesh.triangles[0];mid=(a+b)/2
    broken=mesh_from_triangles(np.concatenate([[[a,mid,c],[mid,b,c]],mesh.triangles[1:]]),check=False)
    assert not broken.is_watertight
    fixed,report=pip.split_existing_tjunctions(broken)
    assert fixed.is_volume and fixed.volume==pytest.approx(mesh.volume)
    assert report and all(row['new_hole_caps']==0 for row in report)
    np.testing.assert_allclose(fixed.bounds,mesh.bounds)


def test_existing_edge_subdivision_refuses_actual_missing_face():
    broken=trimesh.creation.box();broken.update_faces(np.arange(1,len(broken.faces)))
    with pytest.raises(GeometryError,match='Remaining open'):
        pip.split_existing_tjunctions(broken)


def test_deeper_eye_cap_preserves_all_original_anatomical_boundary_points():
    from scipy.spatial import cKDTree
    boundary=np.array([[0.,0.,0.],[2.,0.,0.],[2.,2.,0.],[0.,2.,0.]])
    before=boundary.copy();cap=pip.pip_eye_interior_cap(boundary)
    assert (cKDTree(cap.vertices).query(boundary)[0]<1e-9).all()
    assert np.max(np.abs(cap.vertices[:,2]))==pytest.approx(.15)
    np.testing.assert_array_equal(boundary,before)


def test_microscopic_near_cut_fragment_requires_full_source_corner_identity(monkeypatch):
    source=surface();triangle=source.mesh.triangles[0];center=triangle.mean(axis=0)
    monkeypatch.setattr(pip,'PLANES',[(np.array([0.,0.,1.]),float(center[2]))])
    fragment=center+(triangle-center)*.0001
    tiny=trimesh.Trimesh(fragment,[[0,1,2]],process=False)
    assert not pip.exterior_face_mapping(source,Part('sliver','sliver',tiny,'#FFFFFF'))[0].any()
    # The source triangle itself is unaffected: only the numerical boundary band is special.
    original=trimesh.Trimesh(triangle,[[0,1,2]],process=False)
    assert pip.exterior_face_mapping(source,Part('skin','skin',original,'#FFFFFF'))[0].tolist()==[True]


def test_upper_head_is_an_explicit_socket_receiver_not_a_missing_pin_part():
    mesh=trimesh.creation.box();before=mesh.vertices.copy();head=pip.make_head_receiver(mesh)
    assert head.id=='head-upper' and head.role=='socket-body'
    assert head.summary()['role']=='socket-body' and head.connectors==[]
    assert 'zwei Kieferstifte' in head.warnings[0] and 'Halsbuchsen im Kiefer' in head.warnings[0]
    np.testing.assert_array_equal(mesh.vertices,before)


@pytest.mark.parametrize('part_id',['jaw','body-front'])
def test_body_highlight_cleanup_keeps_main_cream_and_never_changes_eye_glints_or_geometry(part_id):
    main=trimesh.creation.box(extents=[4,4,4]);island=trimesh.creation.box();island.apply_translation([8,0,0]);eye=trimesh.creation.box();eye.apply_translation([12,0,0])
    mesh=trimesh.util.concatenate([main,island,eye]);n=len(mesh.faces)
    source=Surface(mesh,np.zeros((n,3,2)),np.full((n,3,3),.8),np.zeros(n,int))
    owner=np.repeat([0,0,1],12);classes=np.ones(n,int);before=classes.copy();vertices=mesh.vertices.copy();faces=mesh.faces.copy()
    parts=[Part(part_id,part_id,mesh,'#FFFFFF'),Part('left-pupil','eye',mesh,'#FFFFFF')]
    result,report=pip.clean_body_light_components(source,owner,classes,parts)
    assert np.all(result[:12]==1) and np.all(result[12:24]==0) and np.all(result[24:]==1)
    assert report[part_id]['removed_islands']==1 and report[part_id]['reassigned_area_mm2']==pytest.approx(6)
    np.testing.assert_array_equal(classes,before);np.testing.assert_array_equal(mesh.vertices,vertices);np.testing.assert_array_equal(mesh.faces,faces)


def test_seam_completion_never_overwrites_an_authentic_source_face_owner(monkeypatch):
    from types import SimpleNamespace
    # Edge 0->1 fills a missing microscopic seam; stale edge 1->2 must
    # subsequently preserve face 2's authentic ownership by the other part.
    mesh=SimpleNamespace(faces=np.zeros((3,3),int),area_faces=np.array([1.,.00001,1.]),face_adjacency=np.array([[0,1],[1,2]]))
    source=SimpleNamespace(mesh=mesh)
    parts=[SimpleNamespace(id=i,mesh=SimpleNamespace(area_faces=np.array([1.]))) for i in [0,1]]
    monkeypatch.setattr(pip,'exterior_face_mapping',lambda s,p:(np.array([True]),np.array([p.id*2]),None))
    owner,report=pip.source_ownership(source,parts)
    assert owner.tolist()==[0,0,1]
    assert report['unmapped_seam_source_faces']==1


def test_stale_seam_edge_preserves_two_different_original_owners(monkeypatch):
    from types import SimpleNamespace
    mesh=SimpleNamespace(faces=np.zeros((3,3),int),area_faces=np.array([.00001,1.,1.]),face_adjacency=np.array([[0,2],[0,1]]))
    source=SimpleNamespace(mesh=mesh);parts=[SimpleNamespace(id=i,mesh=SimpleNamespace(area_faces=np.array([1.]))) for i in [1,2]]
    monkeypatch.setattr(pip,'exterior_face_mapping',lambda s,p:(np.array([True]),np.array([p.id]),None))
    owner,_=pip.source_ownership(source,parts)
    assert owner.tolist()==[1,0,1]

@pytest.mark.parametrize('missing_count,missing_area',[(21,1e-7),(3,.0004)])
def test_seam_fill_rejects_original_face_or_area_budget_excess(monkeypatch,missing_count,missing_area):
    from types import SimpleNamespace
    n=1+missing_count
    mesh=SimpleNamespace(faces=np.zeros((n,3),int),area_faces=np.r_[1.,np.full(missing_count,missing_area)],face_adjacency=np.column_stack([np.zeros(missing_count,int),np.arange(1,n)]))
    source=SimpleNamespace(mesh=mesh);part=SimpleNamespace(id='body',mesh=SimpleNamespace(area_faces=np.array([1.])))
    monkeypatch.setattr(pip,'exterior_face_mapping',lambda *_:(np.array([True]),np.array([0]),None))
    with pytest.raises(GeometryError,match='unvollstaendig'):pip.source_ownership(source,[part])


def test_tiny_unowned_disconnected_component_cannot_inherit_unrelated_part(monkeypatch):
    from types import SimpleNamespace
    mesh=SimpleNamespace(faces=np.zeros((2,3),int),area_faces=np.array([1.,.00001]),face_adjacency=np.empty((0,2),int))
    source=SimpleNamespace(mesh=mesh);part=SimpleNamespace(id='body',mesh=SimpleNamespace(area_faces=np.array([1.])))
    monkeypatch.setattr(pip,'exterior_face_mapping',lambda *_:(np.array([True]),np.array([0]),None))
    with pytest.raises(GeometryError,match='keine Bauteilzuordnung'):pip.source_ownership(source,[part])


def test_source_face_authentically_owned_by_two_parts_is_not_hidden_by_seam_completion(monkeypatch):
    from types import SimpleNamespace
    mesh=SimpleNamespace(faces=np.zeros((1,3),int),area_faces=np.array([1.]),face_adjacency=np.empty((0,2),int))
    source=SimpleNamespace(mesh=mesh);parts=[SimpleNamespace(id=i,mesh=SimpleNamespace(area_faces=np.array([.5]))) for i in range(2)]
    monkeypatch.setattr(pip,'exterior_face_mapping',lambda *_:(np.array([True]),np.array([0]),None))
    with pytest.raises(GeometryError,match='mehreren mechanischen'):pip.source_ownership(source,parts)
