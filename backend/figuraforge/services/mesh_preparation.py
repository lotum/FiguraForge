"""Bound provider output before inspection; keep immutable originals."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import time
from ..geometry.io import validate_glb_bytes
from ..geometry.types import GeometryError
from ..geometry.compare import compare
from ..providers.meshy import mesh_target_for_budget


def glb_triangles(path):
    doc=validate_glb_bytes(Path(path).read_bytes());accessors=doc.get('accessors',[])
    per_mesh=[]
    for mesh in doc.get('meshes',[]):
        count=0
        for primitive in mesh.get('primitives',[]):
            if primitive.get('mode',4)!=4: raise GeometryError('Arbeitskopie braucht Dreiecksgeometrie.')
            accessor=primitive.get('indices',primitive.get('attributes',{}).get('POSITION'))
            if accessor is not None: count+=accessors[accessor]['count']//3
        per_mesh.append(count)
    nodes=[node['mesh'] for node in doc.get('nodes',[]) if 'mesh' in node]
    return sum(per_mesh[i] for i in nodes) if nodes else sum(per_mesh)


def prepare_source(path,out,settings,progress):
    path=Path(path);out=Path(out)
    if path.suffix.lower()!='.glb': return path,None
    count=glb_triangles(path)
    target=mesh_target_for_budget(settings['max_refined_faces'],settings.get('mesh_target_faces',150000))
    if count<=int(target*1.05): return path,None
    if count>4_000_000: raise GeometryError('Mehr als 4 Mio. Dreiecke: vor dem Import eine kleinere Arbeitskopie anfordern.')
    blender=os.getenv('FORGE_BLENDER_PATH') or shutil.which('blender')
    if not blender and Path('/Applications/Blender.app/Contents/MacOS/Blender').is_file():
        blender='/Applications/Blender.app/Contents/MacOS/Blender'
    if not blender: raise GeometryError('Modell ist zu dicht. Blender installieren oder eine kleinere GLB-Arbeitskopie importieren.')
    script=Path(__file__).resolve().parents[3]/'scripts/blender_prepare.py'
    # scripts is in the source checkout; no shell, no request headers, bounded threads.
    if not script.is_file(): raise GeometryError('Blender-Vorbereitungsskript fehlt in dieser Installation.')
    output=out/'prepared-source.glb';started=time.monotonic()
    progress(f'Arbeitskopie vorbereiten: {count:,} auf etwa {target:,} Dreiecke (Blender, 2 Threads)')
    with (out/'blender-preparation.log').open('w') as log:
        result=subprocess.run([blender,'--background','--factory-startup','--threads','2','--python',str(script),
            '--','--source',str(path.resolve()),'--output',str(output.resolve()),'--faces',str(target)],
            stdout=log,stderr=log,timeout=300,check=False)
    if result.returncode or not output.is_file(): raise GeometryError('Blender-Arbeitskopie fehlgeschlagen. Original erhalten; Vorbereitungsprotokoll pruefen.')
    progress('Arbeitskopie auf Form-, Farb- und Topologieerhalt pruefen')
    report=compare(path,output,settings['height_mm'],up_axis=settings['up_axis'])
    report.update(method='Blender UV seams welded + collapse',target_faces=target,preparation_seconds=round(time.monotonic()-started,3))
    (out/'preparation-quality.json').write_text(json.dumps(report,indent=2))
    allowed=max(.05,min(.5,settings['boundary_tolerance_mm']/2))
    if not report['working']['valid'] or report['working']['components']!=report['original']['components']:
        raise GeometryError('Reduzierte Arbeitskopie ist nicht geschlossen oder veraendert die Koerperzahl. Original erhalten; Reparatur pruefen.')
    if report['geometry_distance_mm']['max_sampled']>allowed or report['albedo_delta_e_2000']['p95']>5:
        raise GeometryError('Reduzierte Arbeitskopie verliert zu viel Form oder Farbe. Detailgrad erhoehen; Original erhalten.')
    return output,report
