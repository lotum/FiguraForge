"""Compare every actual packaged Main native plate with its sliced reference."""
from pathlib import Path
import argparse,hashlib,json,re,zipfile
from xml.etree import ElementTree as ET
from verify_native_parity import records,compare,NS


def routing(path):
    with zipfile.ZipFile(path) as archive:
        root=ET.fromstring(archive.read('Metadata/model_settings.config'))
        result={}
        for obj in root.findall('object'):
            metadata={m.get('key'):m.get('value') for m in obj.findall('metadata')}
            result[metadata.get('name')]= {'object_extruder':metadata.get('extruder'),
                'part_extruders':[next((m.get('value') for m in part.findall('metadata') if m.get('key')=='extruder'),None) for part in obj.findall('part')]}
        model=ET.fromstring(archive.read('3D/3dmodel.model'))
        if not all(item.get('printable')=='1' for item in model.findall(NS+'build/'+NS+'item')):
            raise ValueError('Native printable instance missing')
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export',type=Path);parser.add_argument('selection',type=Path)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():raise ValueError('Use a fresh verification report path')
    selection=json.loads(args.selection.read_text());expected={tuple(sorted(row['part_ids'])):row for row in selection['plates']}
    if len(expected)!=34:raise ValueError('Expected34unique final reference part sets')
    package=args.export/'print-package.zip';result={'main_export':str(args.export),'package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
        'reference_selection':str(args.selection),'main_plan_hash':selection['main_plan_hash'],'plates':[],
        'scope':'Actual complete native XML vertices/faces/world transforms/per-face paint/all project settings/object+part extrusion defaults and packaged bytes; actual sliced reference GCode/full footprint proof remains separate.',
        'physical_print_verified':False,'physical_strength_verified':False,'printer_communication':False}
    seen=set()
    with zipfile.ZipFile(package) as archive:
        names=[name for name in archive.namelist() if re.fullmatch(r'plate-\d+-native\.3mf',name)]
        if len(names)!=34:raise ValueError('Actual ZIP does not contain34native plates')
        for name in sorted(names):
            actual=args.export/name
            if archive.read(name)!=actual.read_bytes():raise ValueError('Packaged bytes differ from actual export')
            actual_records,_=records(actual);key=tuple(sorted(actual_records))
            if key not in expected or key in seen:raise ValueError('Final actual native part set differs or duplicated')
            seen.add(key);reference=Path(expected[key]['native']);proof=compare(reference,actual)
            if routing(reference)!=routing(actual):raise ValueError('Actual object/part filament defaults differ')
            result['plates'].append({'actual_native':str(actual),'reference_native':str(reference),'part_ids':list(key),
                'packaged_bytes_exact':True,'extruder_defaults_exact':True,**proof})
    result['passed']=seen==set(expected) and all(row['passed'] for row in result['plates'])
    args.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'plates':len(result['plates']),'package_sha256':result['package_sha256']}))

if __name__=='__main__':main()
