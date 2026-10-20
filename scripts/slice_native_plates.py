"""Locally slice native Bambu plates with geometry/G-code checks enabled.

Disables only MakerWorld publication normative checks, which reject Mixed
Filament as experimental. Never use --no-check. No printer communication.
A known GUI-conflicting plate also returns CLI success: this script proves
G-code generation only; use the independent path checker and slicer preview.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import uuid


def slice_plate(source, output, executable, plate_index=1):
    if type(plate_index) is not int or plate_index<1:raise ValueError("Positive plate index required")
    source=source.resolve();output.mkdir(parents=True,exist_ok=False)
    command=[executable,'--normative-check=0','--slice',str(plate_index),'--arrange','0','--orient','0',
        '--outputdir',str(output.resolve()),'--export-3mf','sliced.3mf',str(source)]
    with (output/'slice.log').open('w') as log:
        run=subprocess.run(command,cwd=output,stdout=log,stderr=subprocess.STDOUT,timeout=900)
    result_path=output/'result.json'
    result=json.loads(result_path.read_text()) if result_path.exists() else {}
    gcode=output/f'plate_{plate_index}.gcode'
    passed=run.returncode==0 and result.get('return_code')==0 and gcode.exists() and gcode.stat().st_size>1000
    return {'source':str(source),'plate_index':plate_index,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'output':str(output.resolve()),'command':command,'exit_code':run.returncode,'passed':passed,
        'validity_checks_not_disabled':True,'gcode_path_validation_verified':False,'print_ready':False,
        'makerworld_normative_checks_enabled':False,
        'printer_communication':False,'physical_print_verified':False,'result':result,
        'gcode_sha256':hashlib.sha256(gcode.read_bytes()).hexdigest() if gcode.exists() else None}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plates',type=Path,nargs='+')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--bambu',default='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio')
    args=parser.parse_args();root=args.output.resolve()/('slice-'+uuid.uuid4().hex);root.mkdir(parents=True)
    print(root,flush=True);reports=[]
    for index,source in enumerate(args.plates,1):
        report=slice_plate(source,root/f'plate-{index:02}',args.bambu);reports.append(report)
        print(source.name,'PASS' if report['passed'] else 'FAIL',report['exit_code'],flush=True)
        (root/'verification.json').write_text(json.dumps({'plates':reports,'passed':all(r['passed'] for r in reports),
            'requested_plate_count':len(args.plates),'completed_plate_count':len(reports)},indent=2))
    return 0 if all(r['passed'] for r in reports) else 1


if __name__=='__main__':raise SystemExit(main())
