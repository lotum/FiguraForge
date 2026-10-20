"""Run native geometry outside the web process with a killable deadline."""
from __future__ import annotations
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from ..geometry.types import GeometryError
from .workflow import write_json


def stop_tree(process):
    """Terminate only the owned worker process group, including VTK clip children."""
    if os.name=='posix':
        try: os.killpg(process.pid,signal.SIGTERM)
        except ProcessLookupError: pass
        try: process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try: os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            process.wait(timeout=2)
    elif process.poll() is None:
        # Every argument is server-controlled; never invoke a shell or user command.
        subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True,timeout=5,check=False)
        try: process.wait(timeout=2)
        except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=2)


def monitor_process(process,progress_path,result_path,progress,timeout):
    """Poll files rather than blocking on a native worker's stdout/pipe."""
    started=time.monotonic();message='Geometrie-Worker gestartet';offset=0;pending=''
    try:
        while True:
            if progress_path.exists():
                with progress_path.open('r',encoding='utf-8',errors='replace') as log:
                    log.seek(offset);pending+=log.read(65536);offset=log.tell()
                lines=pending.split('\n');pending=lines.pop()
                for line in lines:
                    try:
                        item=json.loads(line)
                        if isinstance(item,dict) and 'progress' in item: message=str(item['progress'])[:500]
                    except (ValueError,TypeError): pass
                if len(pending)>10000: pending=pending[-10000:]
            # This callback also checks the project's cancellation flag.
            progress(message)
            if process.poll() is not None: break
            if time.monotonic()-started>timeout:
                raise GeometryError('Geometry worker exceeded its time limit. Previous approved artifacts are unchanged; reduce complexity or adjust FORGE_GEOMETRY_TIMEOUT_SECONDS.')
            time.sleep(.2)
        if not result_path.exists():
            raise GeometryError(f'Native geometry worker exited without a result (exit {process.returncode}). The web process remains available; inspect the mesh and retry.')
        result=json.loads(result_path.read_text())
        if not result.get('ok'): raise GeometryError(result.get('error','Geometry operation failed'))
        if process.returncode!=0: raise GeometryError('Geometry worker returned an unexpected exit code')
        return result['result']
    finally:
        stop_tree(process)


def run_native(request,out:Path,progress,timeout=None):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    request={**request,'out':str(out)}
    request_path=out/'worker-request.json';result_path=out/'worker-result.json';log_path=out/'worker.log'
    result_path.unlink(missing_ok=True)
    write_json(request_path,request)
    env=dict(os.environ)
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):
        env[name]='2'
    for name in ('OPENAI_API_KEY','GEMINI_API_KEY','MESHY_API_KEY','TRIPO_API_KEY','LOCAL_API_KEY','FORGE_VAULT_KEY','FORGE_API_TOKEN'):
        env.pop(name,None)
    package_root=Path(__file__).resolve().parents[2]
    env['PYTHONPATH']=str(package_root)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    duration=float(os.getenv('FORGE_GEOMETRY_TIMEOUT_SECONDS','1800')) if timeout is None else float(timeout)
    if not math.isfinite(duration) or duration<=0: raise GeometryError('Geometry timeout must be positive')
    with log_path.open('w',encoding='utf-8') as log:
        process=subprocess.Popen([sys.executable,'-m','figuraforge.services.geometry_task',str(request_path)],
            stdout=log,stderr=log,env=env,start_new_session=os.name=='posix',close_fds=True)
        return monitor_process(process,log_path,result_path,progress,duration)
