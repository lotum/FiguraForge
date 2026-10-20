"""Collect immutable actual Buddy slice/path references, retaining missing proof.

Does not slice, approve, mutate projects or submit printing. Final Main native
archives still require independent XML geometry/paint/settings parity.
"""
from pathlib import Path
import argparse,hashlib,json


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('selection',type=Path)
    parser.add_argument('--extra-check',type=Path,action='append',default=[])
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--main-parity',type=Path)
    args=parser.parse_args()
    if args.report.exists():raise ValueError('Use a fresh verification report path')
    selection=json.loads(args.selection.read_text())
    expected_checker=sha(Path(__file__).with_name('check_gcode_paths.py'))
    extra={};missing=[]
    for path in args.extra_check:
        if not path.exists():missing.append(str(path));continue
        data=json.loads(path.read_text())
        if data['checker_source_sha256']!=expected_checker:raise ValueError('Extra checker version differs')
        for row in data['plates']:extra[str(Path(row['native']).resolve())]=(row['paths'],str(path))
    report={'main_plan_hash':selection['main_plan_hash'],'reference_selection':str(args.selection),
            'checker_source_sha256':expected_checker,'plates':[],
            'scope':'Actual successful slice/GCode references; final Main geometry, face paint and complete settings parity still required.',
            'missing_extra_reports':missing,'main_native_parity_verified':False,'physical_fit_verified':False,'physical_strength_verified':False,'bambu_gui_verified':False,'printer_communication':False}
    for entry in selection['plates']:
        directory=Path(entry['reference_directory']);ident=entry['plate_id']
        data=json.loads((directory/'verification.json').read_text())
        row=next(item for item in data['plates'] if item['plate_id']==ident)
        if not row['slice']['passed'] or row['slice']['result']['return_code']!=0:raise ValueError('Selected reference slice failed')
        native=directory/f'plate-{ident:02}.3mf';gcode=directory/f'slice-{ident:02}/plate_1.gcode'
        paths,proof=extra.get(str(native.resolve()),(row.get('paths'),str(directory/'verification.json')))
        verified=bool(paths and paths.get('passed'))
        if verified:
            if data['checker_source_sha256']!=expected_checker:raise ValueError('Reference checker version differs')
            if paths['gcode_sha256']!=sha(gcode):raise ValueError('Actual GCode hash differs from its full footprint proof')
        sliced=row['slice']['result'];plate=sliced['sliced_plates'][0]
        report['plates'].append({'plate_id':ident,'part_ids':[p['part_id'] for p in row['placements']],
            'native':str(native),'native_sha256':sha(native),'gcode':str(gcode),'full_path_proof':proof,
            'full_paths_passed':verified,'slice_passed':True,'physical_filament_ids':row['physical_filament_ids'],
            'seconds':plate['total_predication'],'grams':sum(f['total_used_g'] for f in plate['filaments']),
            'wall_loops':sliced['wall_loops'],'infill_percent':sliced['sparse_infill_density'],
            'gcode_sha256':paths['gcode_sha256'] if verified else None})
    report['slice_count']=len(report['plates']);report['full_path_count']=sum(r['full_paths_passed'] for r in report['plates'])
    report['reference_gates_passed']=report['slice_count']==34 and report['full_path_count']==34 and all(len(r['physical_filament_ids'])<=2 for r in report['plates'])
    report['total_hours']=sum(r['seconds'] for r in report['plates'])/3600
    report['total_kg']=sum(r['grams'] for r in report['plates'])/1000
    if args.main_parity:
        main=json.loads(args.main_parity.read_text())
        if not main.get('passed') or len(main.get('plates',[]))!=34:raise ValueError('Actual Main native parity incomplete')
        if main['main_plan_hash']!=report['main_plan_hash']:raise ValueError('Main plan binding changed')
        if {row['reference_sha256'] for row in main['plates']}!={row['native_sha256'] for row in report['plates']}:raise ValueError('Actual Main parity refers to different native references')
        package=Path(main['main_export'])/'print-package.zip'
        if sha(package)!=main['package_sha256']:raise ValueError('Actual Main ZIP changed after parity check')
        report.update(main_native_parity_verified=True,main_native_parity_report=str(args.main_parity),main_native_parity_report_sha256=sha(args.main_parity),main_package_sha256=main['package_sha256'])
    report['digital_cli_and_xml_gates_passed']=report['reference_gates_passed'] and report['main_native_parity_verified']
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ['slice_count','full_path_count','reference_gates_passed','total_hours','total_kg']}))

if __name__=='__main__':main()
