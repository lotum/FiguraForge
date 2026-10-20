"""Build a source release from an explicit allowlist; never archive runtime data."""
from pathlib import Path
import argparse,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]


def build(output:Path):
    names=['README.md','LICENSE','THIRD_PARTY_NOTICES.md','.env.example','.gitignore','.dockerignore',
           'pyproject.toml','requirements-tested.txt','start.sh','start.ps1','Dockerfile','compose.yaml',
           'examples/teddy-source.glb','examples/LICENSE.md']
    paths={ROOT/name for name in names}
    for folder,pattern in [('backend','*.py'),('tests','*.py'),('frontend','*.js'),('frontend','*.html'),('frontend','*.css'),
                           ('assets','*.json'),('docs','*.md'),('docs','*.json'),('docs','*.xml'),('screenshots','*.png'),('.github','*.yml')]:
        paths.update((ROOT/folder).rglob(pattern))
    for name in ('run.py','benchmark.py','benchmark_api.py','calibration.py','ui_capture.py','package_release.py'):
        paths.add(ROOT/'scripts'/name)
    files=sorted(p for p in paths if p.is_file() and '__pycache__' not in p.parts)
    forbidden={'vault.key','secrets.enc','.env'}
    if any(p.name in forbidden or any(x in p.relative_to(ROOT).parts for x in ('test-run-data','data','.venv')) for p in files):
        raise RuntimeError('Refusing to include runtime/private files')
    manifest={'project':'FiguraForge','version':'0.1.0','date':'2026-10-15',
              'license':'MIT for original code; see notices','files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in files: archive.write(path,'FiguraForge/'+str(path.relative_to(ROOT)))
        archive.writestr('FiguraForge/RELEASE_MANIFEST.json',json.dumps(manifest,indent=2))
    with zipfile.ZipFile(output) as archive:
        if archive.testzip(): raise RuntimeError('Source ZIP checksum failure')
        for name,expected in manifest['files'].items():
            if hashlib.sha256(archive.read('FiguraForge/'+name)).hexdigest()!=expected: raise RuntimeError('Manifest mismatch')
    print(json.dumps({'archive':str(output),'source_files':len(files),'bytes':output.stat().st_size,
                      'sha256':hashlib.sha256(output.read_bytes()).hexdigest()},indent=2))
    return manifest
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'dist'/'FiguraForge_0.1.0_Source.zip')
    args=parser.parse_args();build(args.output.resolve())
