"""Bind final Mochi neck geometry, native painting, reloads and actual G-code."""
from pathlib import Path
import json,hashlib,sys
from collections import Counter
from xml.etree import ElementTree as E
import zipfile
import numpy as np
import trimesh
from shapely.geometry import Polygon
from figuraforge.geometry.mochi_neck import field,clipped_shell,cap_and_socket
from figuraforge.geometry.validation import DistanceQuery,basic_stability
from figuraforge.services.native_plates import N,MODEL
sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_native_parity import records


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())


def verify(root,joint):
    construction=read(root/'construction-verification.json');height=construction['height_mm'];factor=height/180;project=Path(construction['project']);native,config=records(project)
    assert len(native)==8 and not any(v!='0' for v in config['filament_is_mixed'])
    report={'project':str(project),'project_sha256':sha(project),'height_mm':height,'construction':construction,'parts':{},'plates':[],'native_save_reload':{}}
    with zipfile.ZipFile(project) as z:
        ids=[o.get('id') for n in z.namelist() if n.startswith('3D/') and n.endswith('.model') for o in E.fromstring(z.read(n)).findall(N+'resources/'+N+'object')];assert len(ids)==len(set(ids));assert len(E.fromstring(z.read(MODEL)).findall('plate'))==3
    placements={r['part_id']:(i,np.asarray(r['transform'])) for i,plate in enumerate(construction['plate_placements']) for r in plate}
    for name,rows in native.items():
        a=np.load(root/'parts'/f'{name}.npz');mesh=trimesh.Trimesh(a['vertices'],a['faces'],process=False);i,tf=placements[name];expected=mesh.triangles@tf[:3,:3].T+tf[:3,3];offset=np.array([[0,0,0],[420,0,0],[0,-384,0]][i]);v,f,p=rows[0];actual=v[f]-offset;err=float(np.max(abs(expected-actual)));assert err<.001;assert p==read(root/f'{name}-paint.json')
        report['parts'][name]={'triangles':len(f),'native_ordered_triangle_error_mm':err,'native_paint_exact':True,'watertight':mesh.is_volume}
    for i in (1,2):
        actual,_=records(root/f'native-save-reload-{i}.3mf');assert actual.keys()==native.keys();checks={}
        for name in native:
            v,f,p=native[name][0];w,g,q=actual[name][0];err=float(np.max(abs(v-w)));assert np.array_equal(f,g) and p==q and err<1e-5;checks[name]={'triangles':len(f),'paint_identical':True,'max_world_error_mm':err}
        report['native_save_reload'][str(i)]={'passed':True,'parts':checks}
    for i in (1,2,3):
        sliced=read(root/f'slice-{i}.json');paths=read(root/f'paths-{i}.json')['checks'][0];assert sliced['passed'] and paths['passed'];assert sliced['source_sha256']==report['project_sha256'];assert sliced['gcode_sha256']==paths['gcode_sha256']
        for bounds in paths['owner_extrusion_xy_bounds_mm'].values():assert bounds[0]>=25 and bounds[1]>=0 and bounds[2]<=325 and bounds[3]<=320
        report['plates'].append({'plate':i,'slice':sliced,'footprints':paths})
    socket=read(joint/'construction.json');a=np.load(joint/'source-body.npz');mesh=trimesh.Trimesh(a['vertices'],a['faces'],process=False);paint=read(joint/'source-paint.json')
    user,_=records(Path(construction['source_user_file']));uv,uf,up=user['body'][0];uv=uv.copy();uv[:,:2]-=(uv[:,:2].min(0)+uv[:,:2].max(0))/2
    assert np.array_equal(uf,mesh.faces) and np.max(abs(uv-mesh.vertices))<1e-8 and up==paint,'Cached body must match the real immutable user file'
    values=mesh.vertices[:,2]-field(mesh.vertices[:,:2],socket['interface']['source_valley_quadratic']);low,lp,_=clipped_shell(mesh,paint,values,False);head,hp,_=clipped_shell(mesh,paint,values,True)
    assert Counter(p for p in paint if p not in ('4','8'))==Counter(p for p in lp+hp if p not in ('4','8'));assert abs(mesh.area-low.area-head.area)<1e-5
    meshes={}
    for name in ('torso','head'):
        a=np.load(joint/f'{name}-source.npz');meshes[name]=trimesh.Trimesh(a['vertices'],a['faces'],process=False)
    area=Polygon(socket['body_socket']['socket_outline_source_xy']).area;expected=area*((18.6*2+socket['head_socket']['head_self_supporting_roof_mm']/3)/factor);actual=mesh.volume-sum(m.volume for m in meshes.values());assert abs(expected-actual)<1e-4
    report['conservation']={'source_exterior_area_source_mm2':mesh.area,'preserved_exterior_area_source_mm2':low.area+head.area,'complex_painted_faces_original':sum(p not in ('4','8') for p in paint),'complex_painted_faces_preserved':sum(p not in ('4','8') for p in lp+hp),'expected_socket_removed_source_mm3':expected,'actual_socket_removed_source_mm3':actual,'volume_error_mm3':actual-expected,'passed':True}
    source=mesh.copy();source.vertices*=factor;q=DistanceQuery(source);boundary=np.array(socket['interface']['boundary_source']);outline=Polygon(boundary[:,:2]);report['internal_containment']={}
    for head_bool,name in [(False,'torso'),(True,'head')]:
        t,_=cap_and_socket(outline,boundary,center=(0,-27),coefficients=socket['interface']['source_valley_quadratic'],scale_factor=factor,head=head_bool);points=np.concatenate([t.reshape(-1,3),t.mean(1)])*factor;dist=q.values(points);assert dist.max()<.005;report['internal_containment'][name]={'points':len(points),'max_outside_mm':float(dist.max()),'passed':True}
    m=meshes['head'].copy();m.vertices*=factor;m.apply_transform(construction['plate_placements'][1][0]['transform']);report['head_print_stability_advisory']=basic_stability(m)
    stats=[p['slice']['result']['sliced_plates'][0] for p in report['plates']];report['estimated_seconds']=sum(s['total_predication'] for s in stats);report['estimated_g']=sum(sum(f['total_used_g'] for f in s['filaments']) for s in stats);report['extrusion_segments']=sum(p['footprints']['extrusion_segments'] for p in report['plates'])
    with zipfile.ZipFile(root/'slice-plate-3/sliced.3mf') as z:
        meta=E.fromstring(z.read(MODEL));key=next(o for o in meta.findall('object') if o.find("metadata[@key='name']").get('value')=='neck-key');kv={m.get('key'):m.get('value') for m in key.findall('metadata') if m.get('key')};assert kv['sparse_infill_density']=='100%' and kv['wall_loops']=='4' and kv['enable_support']=='0' and kv['raft_layers']=='0';report['solid_key_sliced_overrides']=kv
    assert construction['head_extraction']['passed'] and all(p['passed'] for p in construction['key_extraction'].values())
    report.update(passed=True,physical_fit_verified=False,manual_gui_verified=False,full_nozzle_dynamics_verified=False,paid_api_calls=0,printer_communication=False)
    return report


if __name__=='__main__':
    base=Path('benchmarks/mochi-neck-split-20261018');result={}
    for height,folder,joint in [(470,'production-470-final','joint-final'),(500,'production-500','joint-500')]:
        result[str(height)]=verify(base/folder,base/joint);print(height,'PASS',result[str(height)]['estimated_seconds'],result[str(height)]['estimated_g'],flush=True)
    original=Path('benchmarks/mochi-solid-production/Mochi-Braun-Beige-H2D-2-Platten.3mf');assert sha(original)=='4197d3b9bbd3dff88fe65bacc47bc0448c0d76530c56b66d221760318df73508'
    result['user_original']={'path':str(original),'sha256':sha(original),'unchanged':True}
    probe=read(base/'production-470-final/fit-probe-two-plates/slice-verification.json');assert all(p['slice']['passed'] and p['paths']['passed'] for p in probe);result['fit_probe']={'plates':probe,'scope':'Exact key, sockets, materials and layer heights; not the full organic exterior seam.'}
    suite=E.parse('docs/test-results-mochi-neck-split.xml').getroot().find('testsuite');result['tests']={k:suite.get(k) for k in ('tests','failures','errors','time')}
    Path('docs/mochi-neck-split-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
