"""Bound potentially pathological native clipping in a reusable child process.

This isolates only structural plane clipping, not every mesh parser/operation.
A failed or timed-out child is replaced before trying another cut candidate.
"""
from __future__ import annotations
import atexit
import multiprocessing as mp
import os
import threading
import numpy as np
import trimesh
from .types import GeometryError


def _worker(connection):
    from .split import _clip_half_impl
    while True:
        try: request=connection.recv()
        except EOFError: break
        if request is None: break
        vertices,faces,axis,position,positive=request
        try:
            mesh=trimesh.Trimesh(vertices,faces,process=False)
            out=_clip_half_impl(mesh,axis,position,positive)
            connection.send(('ok',np.asarray(out.vertices),np.asarray(out.faces)))
        except Exception as exc:
            connection.send(('error',str(exc)[:600]))
    connection.close()


class ClipWorker:
    def __init__(self):
        self.lock=threading.RLock(); self.process=None; self.pipe=None
    def close(self):
        with self.lock:
            if self.pipe is not None:
                self.pipe.close(); self.pipe=None
            if self.process is not None:
                if self.process.is_alive(): self.process.terminate()
                self.process.join(timeout=2)
                if self.process.is_alive(): self.process.kill(); self.process.join(timeout=2)
                self.process=None
    def _start(self):
        if self.process is not None and self.process.is_alive(): return
        self.close()
        context=mp.get_context('spawn'); parent,child=context.Pipe()
        process=context.Process(target=_worker,args=(child,),daemon=True,name='figuraforge-clip')
        process.start();child.close();self.pipe=parent;self.process=process
    def clip(self,mesh,axis,position,positive):
        with self.lock:
            self._start()
            timeout=max(3,min(float(os.getenv('FORGE_CLIP_TIMEOUT_SECONDS','10')),120))
            try:
                self.pipe.send((np.asarray(mesh.vertices),np.asarray(mesh.faces),axis,float(position),bool(positive)))
                if not self.pipe.poll(timeout):
                    self.close()
                    raise GeometryError('Structural clipping exceeded its time limit; use another cut position')
                response=self.pipe.recv()
            except (EOFError,BrokenPipeError,OSError) as exc:
                self.close();raise GeometryError('Structural clip worker exited; try another cut position') from exc
            if response[0]!='ok': raise GeometryError(response[1])
            return trimesh.Trimesh(response[1],response[2],process=False)


worker=ClipWorker()
atexit.register(worker.close)
