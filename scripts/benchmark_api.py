"""Exercise the actual app, disposable workers, approvals and export without API keys."""
from pathlib import Path
import argparse,json,sys,time,zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from fastapi.testclient import TestClient
from figuraforge.app import create_app
from figuraforge.config import Config
from figuraforge.models import Settings


def run(height,output):
    output=output.resolve();output.mkdir(parents=True,exist_ok=True)
    settings=Settings(height_mm=height)
    if height>=500:
        settings=settings.model_copy(update={'boundary_tolerance_mm':2,'coarse_sampling_mm':8,
            'max_refined_faces':500000,'inlay_depth_mm':5,'pin_radius_mm':2.5,'pin_length_mm':7})
    start=time.monotonic();timings={}
    def record(name):timings[name]=round(time.monotonic()-start,3)
    with TestClient(create_app(Config(root=ROOT,data_dir=output/'workspace'))) as client:
        def post(path,body=None):
            response=client.post(path,json=body)
            response.raise_for_status();return response.json()
        def wait(job):
            deadline=time.monotonic()+1900;last=None
            while time.monotonic()<deadline:
                state=client.get('/api/jobs/'+job['id']).json()
                if state['message']!=last:
                    last=state['message'];print(state['operation'],last,flush=True)
                if state['status'] not in ('queued','running'):
                    if state['status']!='succeeded': raise RuntimeError(state.get('error') or state)
                    return state
                time.sleep(.2)
            raise TimeoutError('Benchmark job exceeded deadline')
        p=post('/api/projects',{'title':f'API Benchmark {height:g} mm','settings':settings.model_dump()});base='/api/projects/'+p['id']
        wait(post(base+'/demo'));record('inspect')
        p=client.get(base).json()
        post(base+'/approve',{'stage':'mesh','artifact_hash':p['artifacts']['mesh']['hash'],'warnings_acknowledged':True})
        wait(post(base+'/jobs',{'operation':'segment'}));record('segment')
        p=client.get(base).json();seg=p['artifacts']['segments'];colors=p['artifacts']['colors']
        post(base+'/approve',{'stage':'colors','artifact_hash':colors['hash'],'warnings_acknowledged':True})
        wait(post(base+'/jobs',{'operation':'export'}));record('export')
        p=client.get(base).json();ex=p['artifacts']['export']
        response=client.get(base+'/files/'+ex['bundle']);response.raise_for_status()
        archive=output/'print-package.zip';archive.write_bytes(response.content)
        with zipfile.ZipFile(archive) as z:export_checks=json.loads(z.read('validation.json'))
        report={'height_mm':height,'parts':len(seg['parts']),'plates':len(colors['plates']),
            'all_parts_valid':all(v['valid'] for v in seg['geometry_report']['quality'].values()),
            'all_parts_single_component':all(v['components']==1 for v in seg['geometry_report']['quality'].values()),
            'packing':seg['geometry_report']['packing'],'all_3mf_checks_passed':all(v['passed'] for v in export_checks.values()),
            'timings_cumulative_seconds':timings,'cloud_calls':0,'physical_print_test':False,'bambu_studio_test':False,
            'settings':settings.model_dump(),'parts_summary':seg['parts'],'geometry_report':seg['geometry_report']}
        (output/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False))
        print(json.dumps({k:report[k] for k in ('height_mm','parts','plates','all_parts_valid','all_3mf_checks_passed','timings_cumulative_seconds')},indent=2),flush=True)
        return report
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--height',type=float,default=180);parser.add_argument('--output',type=Path)
    args=parser.parse_args();run(args.height,args.output or ROOT/'benchmarks'/f'api-{int(args.height)}')
