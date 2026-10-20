import importlib.util
from pathlib import Path
import numpy as np
import pytest
spec=importlib.util.spec_from_file_location('gcode_paths',Path(__file__).resolve().parents[1]/'scripts/check_gcode_paths.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_modal_parser_owner_does_not_follow_early_object_id():
    source='''G90
M83
G1 X0 Y0 Z.2
; start printing object, unique label id: 1
; FEATURE: Support
; LINE_WIDTH: .5
G1 X1 E.2
; OBJECT_ID: 2
G1 X2 E.2
; stop printing object, unique label id: 1
G1 X3 E.2
; start printing object, unique label id: 2
M82
G92 E0
G1 X4 E1
G1 X5 E.5
G91
M83
G1 X1 E.2
'''.splitlines()
    rows=list(m.parse(source));assert [r[6] for r in rows]==[1,1,2,2];assert rows[-1][1:5]==(5.,0.,6.,0.)

def test_cross_object_support_model_and_prime_are_checked_same_owner_not():
    rows=np.array([(.2,0,0,2,0,.4,1,1,1,.2),(.2,1,-1,1,1,.4,2,0,2,.2),(.2,1,-1,1,1,.4,1,0,3,.2),(.2,1,-1,1,1,.4,-2,2,4,.2)],dtype=m.FIELDS)
    counts,hits=m.screen_records(rows);assert counts['support-model']==1 and counts['prime-model']==2;assert not any(h['owners']==[1,1] for h in hits)

def test_separated_paths_have_no_conflicts(tmp_path):
    path=tmp_path/'safe.gcode';path.write_text('''G90
M83
G1 X0 Y0 Z.2
; start printing object, unique label id: 1
; FEATURE: Support
G1 X2 E.2
; stop printing object, unique label id: 1
G1 X0 Y2
; start printing object, unique label id: 2
; FEATURE: Outer wall
G1 X2 E.2
''');assert m.check(path)['passed']

def test_cli_persists_real_json_report(tmp_path):
    import subprocess,sys,json
    source=tmp_path/'one.gcode';output=tmp_path/'report.json'
    source.write_text('G90\nM83\nG1 X0 Y0 Z.2\n; start printing object, unique label id: 1\n; FEATURE: Outer wall\nG1 X1 E.1\n')
    result=subprocess.run([sys.executable,str(Path(m.__file__)),str(source),'--output',str(output)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert json.loads(output.read_text())['checks'][0]['passed']
    assert json.loads(result.stdout)['extrusion_segments']==1

def test_unlabeled_model_extrusion_requires_single_object_evidence(tmp_path):
    import json,pytest
    source=tmp_path/'one.gcode';source.write_text('G90\nM83\nG1 X0 Y0 Z.2\n; FEATURE: Outer wall\nG1 X1 E.1\n')
    with pytest.raises(ValueError,match='Unassigned'):m.check(source)
    (tmp_path/'result.json').write_text(json.dumps({'sliced_plates':[{'objects':[{'id':5,'name':'single'}]}]}))
    result=m.check(source);assert result['passed'] and result['extrusion_segments']==1
    assert result['single_object_owner_evidence']['object_id']==5
    (tmp_path/'result.json').write_text(json.dumps({'sliced_plates':[{'objects':[{'id':5},{'id':6}]}]}))
    with pytest.raises(ValueError,match='Unassigned'):m.check(source)

def test_unsupported_arc_or_nonplanar_extrusion_is_not_silent_pass(tmp_path):
    import pytest
    path=tmp_path/'unsupported.gcode'
    pre='G90\nM83\nG1 X0 Y0 Z.2\n; start printing object, unique label id: 1\n; FEATURE: Outer wall\n'
    path.write_text(pre+'G2 X1 Y1 R1 E.2\n')
    with pytest.raises(ValueError,match='R-encoded'):m.check(path)
    path.write_text(pre+'G1 X1 Z.3 E.2\n')
    with pytest.raises(ValueError,match='Nonplanar'):m.check(path)

def test_mixed_sublayers_need_actual_bead_height_not_equal_top_z():
    rows=np.array([(.2,0,0,2,0,.4,1,1,1,.2),(.12,1,-1,1,1,.4,2,0,2,.01)],dtype=m.FIELDS)
    counts,hits=m.screen_records(rows,current_z=.2)
    assert counts=={'support-model':1} and hits[0]['other_z_mm']==.12
    rows[1]['z']=.21
    assert m.screen_records(rows,current_z=.21)[0]=={}

def test_arc_clockwise_counterclockwise_winding_endpoint_and_sagitta():
    import math
    for clockwise,sweep in [(False,math.pi/2),(True,-3*math.pi/2)]:
        points,bound,mismatch=m.arc_points([1,0],[0,1],[-1,0],clockwise)
        np.testing.assert_array_equal(points[0],[1,0]);np.testing.assert_array_equal(points[-1],[0,1])
        assert np.sign((points[:-1,0]*points[1:,1]-points[:-1,1]*points[1:,0]).sum())==np.sign(sweep)
        midpoint=(points[:-1]+points[1:])/2
        assert (1-np.linalg.norm(midpoint,axis=1)).max()<=m.ARC_CHORD_ERROR_MM
        assert bound<=m.ARC_CHORD_ERROR_MM and mismatch==0
        assert abs(np.linalg.norm(np.diff(points,axis=0),axis=1).sum()-abs(sweep))<.02


def test_full_circle_without_xy_endpoint_is_actual_extrusion_not_discarded():
    source='''G17
G90
M83
G92 X1 Y0 Z.2 E0
; start printing object, unique label id: 1
; FEATURE: Outer wall
G2 I-1 J0 E1
'''.splitlines();stats={};rows=list(m.parse(source,stats=stats))
    assert len(rows)>4 and stats['extrusion_arcs']==1
    assert rows[0][1:3]==(1.,0.) and rows[-1][3:5]==(1.,0.)
    assert min(r[2] for r in rows)<-.99 and max(r[2] for r in rows)>.99


def test_arc_relative_absolute_and_g92_keep_actual_endpoint_and_ownership():
    source='''G17
G90
M83
G92 X1 Y0 Z.2 E0
; start printing object, unique label id: 7
; FEATURE: Support
G3 X0 Y1 I-1 J0 E1
G91
G2 X1 Y-1 I0 J-1 E1
G90
G92 X2 Y0 E0
M82
G3 X0 Y2 I-2 J0 E1
'''.splitlines();rows=list(m.parse(source))
    assert rows[-1][3:5]==(0.,2.) and all(r[6]==7 and r[7]==1 for r in rows)
    assert all(r[5]>=.4 for r in rows)


def test_arc_owner_intersection_is_detected_at_curve_not_straight_endpoint_chord(tmp_path):
    source=tmp_path/'arc.gcode';source.write_text('''G17
G90
M83
G92 X1 Y0 Z.2 E0
; start printing object, unique label id: 1
; FEATURE: Support
; LINE_WIDTH: .1
G3 X-1 Y0 I-1 J0 E1
; stop printing object, unique label id: 1
G1 X0 Y.8
; start printing object, unique label id: 2
; FEATURE: Outer wall
G1 Y1.2 E.2
''')
    result=m.check(source);assert not result['passed'] and result['conflict_counts']['support-model']>0
    assert result['maximum_arc_chord_error_bound_mm']<=.005


def test_rounded_arc_endpoint_consumes_error_budget_and_stays_exact():
    points,bound,mismatch=m.arc_points([1,0],[0,1.001],[-1,0],False)
    np.testing.assert_array_equal(points[-1],[0,1.001]);assert .00099<mismatch<.00101 and bound<=.005
    import pytest
    with pytest.raises(ValueError,match='radius mismatch'):m.arc_points([1,0],[0,1.01],[-1,0],False)
    with pytest.raises(ValueError,match='center'):m.arc_points([0,0],[1,0],[0,0],False)


@pytest.mark.parametrize('code,match',[
    ('G18\nG2 X0 Y1 I-1 J0 E1','plane'),
    ('G19\nG2 X0 Y1 I-1 J0 E1','plane'),
    ('G2 X0 Y1 R1 E1','R-encoded'),
    ('G3 X0 Y1 I-1 J0 Z.3 E1','Helical'),
    ('G90.1\nG3 X0 Y1 I-1 J0 E1','Absolute'),
    ('G3 X0 Y1 E1','relative I/J'),
    ('G3 X0 Y1 I-1 J0 P2 E1','K/P'),
])
def test_unsupported_arc_encoding_is_explicit_failure(code,match):
    pre='G17\nG90\nM83\nG92 X1 Y0 Z.2\n; start printing object, unique label id: 1\n; FEATURE: Outer wall\n'
    with pytest.raises(ValueError,match=match):list(m.parse((pre+code).splitlines()))

def test_nonprinting_vendor_startup_helix_updates_position_without_claiming_extrusion():
    source='''G17
G91
M83
G3 Z.4 I1.217 J0 P1 F60000
G90
G1 X0 Y0 Z.6
; start printing object, unique label id: 1
; FEATURE: Outer wall
G1 X1 E.1
'''.splitlines();stats={};rows=list(m.parse(source,stats=stats))
    assert len(rows)==1 and rows[0][0]==.6
    assert stats['ignored_nonprinting_arc_commands']==1 and stats.get('extrusion_arcs',0)==0

def original_all_owner_tree_screen(rows,tolerance_mm=.02,*,current_z=None):
    """Frozen pre-optimization candidate policy, for exact outcome comparison."""
    from shapely.geometry import LineString,box
    from shapely.strtree import STRtree
    lines=[LineString([(r['x1'],r['y1']),(r['x2'],r['y2'])]) for r in rows]
    tree=STRtree(lines);maxwidth=max(rows['width'],default=0);hits=[];counts={}
    for i,(a,line) in enumerate(zip(rows,lines)):
        if current_z is not None and a['z']!=current_z:continue
        radius=(float(a['width'])+maxwidth)/2-tolerance_mm
        if radius<=0:continue
        for j in tree.query(box(*(np.array(line.bounds)+[-radius,-radius,radius,radius]))):
            j=int(j)
            if current_z is None and j<=i:continue
            if current_z is not None and rows[j]['z']==current_z and j<=i:continue
            b=rows[j];kind=m.candidate_kind(a,b)
            if min(a['z'],b['z'])-max(a['z']-a['height'],b['z']-b['height'])<=1e-6:continue
            if not kind:continue
            distance=line.distance(lines[j]);limit=(float(a['width'])+float(b['width']))/2-tolerance_mm
            if distance>=limit:continue
            counts[kind]=counts.get(kind,0)+1;hits.append((int(a['line']),int(b['line']),kind,distance))
    return counts,sorted(hits)


@pytest.mark.parametrize('current_z',[None,.12,.2,.4])
def test_separate_owner_trees_preserve_full_original_collision_policy(current_z):
    rng=np.random.default_rng(16);rows=[]
    for i in range(240):
        owner=int(rng.choice([1,2,3,-2]));kind=2 if owner==-2 else int(rng.choice([0,1]));x,y=rng.uniform(-2,2,2);dx,dy=rng.uniform(-1,1,2);z=float(rng.choice([.12,.2,.4]));height=float(rng.choice([.01,.12,.2]));width=float(rng.choice([.2,.4,.6]))
        rows.append((z,x,y,x+dx,y+dy,width,owner,kind,i+1,height))
    records=np.array(rows,dtype=m.FIELDS);expected_counts,expected_hits=original_all_owner_tree_screen(records,current_z=current_z)
    counts,hits=m.screen_records(records,current_z=current_z,max_examples=100000)
    actual=sorted((h['lines'][0],h['lines'][1],h['type'],h['centerline_distance_mm']) for h in hits)
    assert counts==expected_counts and actual==expected_hits

def test_numpy_owner_bbox_filter_preserves_indices_and_all_actual_pairs():
    rows=np.array([
        (.2,0,0,1,0,.4,1,0,101,.2),
        (.2,500,500,501,500,.4,1,0,102,.2),
        (.2,.5,-1,.5,1,.4,2,1,103,.2),
        (.2,-500,-500,-499,-500,.4,2,0,104,.2),
        (.2,.5,.3,.5,1,.4,-2,2,105,.2),
    ],dtype=m.FIELDS)
    mask=m.cross_owner_bbox_mask(rows)
    assert len(mask)==len(rows) and mask[0] and mask[2] and mask[4]
    assert not mask[1] and not mask[3]
    expected_counts,expected_hits=original_all_owner_tree_screen(rows)
    counts,hits=m.screen_records(rows,max_examples=1000)
    actual=sorted((h['lines'][0],h['lines'][1],h['type'],h['centerline_distance_mm']) for h in hits)
    assert counts==expected_counts and actual==expected_hits
    assert np.array_equal(rows['line'],[101,102,103,104,105])
