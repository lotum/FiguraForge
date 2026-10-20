import json
import os
from pathlib import Path
import subprocess
import sys
import time
import pytest
from figuraforge.geometry.types import GeometryError
from figuraforge.services.native_jobs import monitor_process, run_native


def launch(tmp_path,code):
    log=tmp_path/'worker.log';log.write_text('')
    p=subprocess.Popen([sys.executable,'-c',code],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=os.name=='posix')
    return p,log,tmp_path/'worker-result.json'


def test_deadline_terminates_native_worker(tmp_path):
    p,log,result=launch(tmp_path,'import time; time.sleep(30)')
    start=time.monotonic()
    with pytest.raises(GeometryError,match='time limit'):
        monitor_process(p,log,result,lambda _:None,.1)
    assert p.poll() is not None and time.monotonic()-start<8


def test_cancellation_terminates_native_worker(tmp_path):
    class Cancel(Exception): pass
    p,log,result=launch(tmp_path,'import time; time.sleep(30)')
    def cancel(message): raise Cancel('cancelled')
    with pytest.raises(Cancel): monitor_process(p,log,result,cancel,60)
    assert p.poll() is not None


def test_crash_does_not_return_success(tmp_path):
    p,log,result=launch(tmp_path,'import os; os._exit(13)')
    with pytest.raises(GeometryError,match='without a result'):
        monitor_process(p,log,result,lambda _:None,10)
    assert p.poll()==13


def test_worker_error_is_propagated(tmp_path):
    with pytest.raises(GeometryError,match='Unsupported disposable'):
        run_native({'operation':'unknown'},tmp_path/'task',lambda _:None,15)
    assert not (tmp_path/'task'/'export').exists()
