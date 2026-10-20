"""Run installed Bambu Studio locally; compare imported/exported plate geometry.

No slicing, profile changes, network requests or printer communication. Outputs
are prefixed verified-; input plate-XX.3mf files are never changed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone

import numpy as np
from scipy.spatial import cKDTree
import trimesh


def meshes(path):
    scene = trimesh.load_scene(path)
    result = []
    for node in scene.graph.nodes_geometry:
        transform, key = scene.graph[node]
        mesh = scene.geometry[key].copy()
        mesh.apply_transform(transform)
        result.append(mesh)
    return sorted(result, key=lambda mesh: (len(mesh.faces), float(mesh.volume)))


def verify(source, executable):
    target = source.with_name('verified-' + source.name)
    run = subprocess.run(
        [executable, '--export-3mf', str(target), '--arrange', '0', '--orient', '0', str(source)],
        capture_output=True, text=True, cwd=source.parent, timeout=120,
    )
    source.with_suffix('.log').write_text(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError(f'Bambu Studio exited {run.returncode}: {run.stdout + run.stderr}')
    originals, imported = meshes(source), meshes(target)
    if len(originals) != len(imported):
        raise RuntimeError('Object count changed')
    checks = []
    for original, actual in zip(originals, imported):
        bounds_error = float(np.abs(original.bounds - actual.bounds).max())
        volume_error = abs(original.volume - actual.volume) / original.volume
        vertex_error = max(float(cKDTree(original.vertices).query(actual.vertices)[0].max()),
                           float(cKDTree(actual.vertices).query(original.vertices)[0].max()))
        zero_area = int((actual.area_faces == 0).sum())
        if not (original.is_volume and actual.is_volume and
                len(original.faces) == len(actual.faces) and bounds_error < .001 and
                vertex_error < .001 and volume_error < 1e-5 and zero_area == 0):
            raise RuntimeError(f'Geometry changed/collapsed: bounds={bounds_error}, '
                               f'vertices={vertex_error}, zero-area triangles={zero_area}')
        checks.append({'triangles': len(actual.faces), 'bounds_error_mm': bounds_error,
                       'relative_volume_error': volume_error, 'watertight': bool(actual.is_watertight),
                       'max_vertex_error_mm': vertex_error, 'zero_area_triangles': zero_area})
    return {'plate': source.name, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'passed': True, 'objects': len(originals), 'checks': checks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path, help='Directory with plate-XX.3mf files')
    parser.add_argument('--bambu', default='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    sources = sorted(directory.glob('plate-*.3mf'))
    if not sources:
        parser.error('No plate-XX.3mf files found')
    version_run = subprocess.run([args.bambu, '--help'], capture_output=True, text=True,
                                 cwd=directory, timeout=30)
    version = re.search(r'BambuStudio-([^:]+)', version_run.stdout)
    reports = []
    for source in sources:
        try:
            reports.append(verify(source, args.bambu))
        except Exception as exc:
            reports.append({'plate': source.name, 'passed': False, 'error': str(exc)})
    report = {'tested_at_utc': datetime.now(timezone.utc).isoformat(),
              'bambu_version': version.group(1) if version else 'unknown',
              'method': 'Bambu Studio CLI import and native 3MF export; independent trimesh comparison in world coordinates',
              'plates': reports, 'passed': all(item['passed'] for item in reports),
              'slicing_tested': False, 'physical_fit_tested': False, 'filament_assignment_verified': False}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
