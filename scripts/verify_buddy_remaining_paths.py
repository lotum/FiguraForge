"""Resume selected saved Buddy GCodes without reslicing or modifying old proof."""
from pathlib import Path
import argparse,json,hashlib
from figuraforge.db import uid
from check_gcode_paths import check


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('verification',type=Path)
    parser.add_argument('--plate-ids',required=True)
    args=parser.parse_args()
    wanted={int(value) for value in args.plate_ids.split(',')}
    original=json.loads((args.verification/'verification.json').read_text())
    rows={row['plate_id']:row for row in original['plates']}
    if not wanted or not wanted<=rows.keys():raise ValueError('Unknown saved plate')
    if not all(rows[i]['slice']['passed'] for i in wanted):raise ValueError('Failed slices cannot become valid through a path-only check')
    out=Path('benchmarks/buddy-native')/('remaining-paths-'+uid());out.mkdir()
    result={'reference_directory':str(args.verification),'checker_source_sha256':hashlib.sha256(Path(__file__).with_name('check_gcode_paths.py').read_bytes()).hexdigest(),
            'requested_plate_ids':sorted(wanted),'scope':'Existing actual GCodes only; no reslice, source or previous proof change. Match final native inputs separately.','plates':[]}
    print(out,flush=True)
    for ident in sorted(wanted):
        row=rows[ident];gcode=args.verification/f'slice-{ident:02}/plate_1.gcode'
        paths=check(gcode)
        result['plates'].append({'plate_id':ident,'part_ids':[p['part_id'] for p in row['placements']],'native':str(args.verification/f'plate-{ident:02}.3mf'),'paths':paths})
        result['passed']=len(result['plates'])==len(wanted) and all(p['paths']['passed'] for p in result['plates'])
        (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
        print(f'Plate {ident}: full_paths={paths["passed"]}',flush=True)
    if not result['passed']:raise RuntimeError('One or more actual saved GCodes failed footprint checks')

if __name__=='__main__':main()
