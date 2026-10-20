"""Native Buddy benchmark: read saved geometry, map actual inventory, slice locally.

Writes a fresh result directory. No project approvals or printer communication.
"""
from pathlib import Path
import argparse,json,sqlite3,copy,sys,base64,hashlib
import numpy as np
from figuraforge.config import Config
from figuraforge.db import uid
from figuraforge.geometry.types import load_part
from figuraforge.geometry.io import load_surface
from figuraforge.services.buddy_pipeline import configure_buddy_plate,build_buddy_parts_preview,pack_buddy_parts,MESH_HASH,SOURCE_SHA256
from figuraforge.services.plan_materials import prepare_native_materials
from figuraforge.services.mixed_filament import read_native_template,inspect_template,build_native_from_parts,native_bed_bounds
from slice_native_plates import slice_plate
from check_gcode_paths import check
CHECKER_SHA256=hashlib.sha256(Path(__file__).with_name('check_gcode_paths.py').read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('geometry',type=Path);p.add_argument('template',type=Path);p.add_argument('--limit',type=int);p.add_argument('--start',type=int,default=1);p.add_argument('--plan',type=Path);p.add_argument('--plate-ids',help='Comma-separated actual plate IDs; slice all selected plates before path checks');a=p.parse_args()
 root=Path('benchmarks/buddy-native')/('verification-'+uid());root.mkdir(parents=True)
 manifest=json.loads((a.geometry/'manifest.json').read_text());plan_path=a.plan or a.geometry/'material-proposal.json';plan=json.loads(plan_path.read_text());parts=[load_part(a.geometry/'parts',row) for row in manifest['parts']]
 config=Config()
 with sqlite3.connect(f'file:{config.data_dir/"forge.sqlite3"}?mode=ro',uri=True) as db:
  stock=[json.loads(r[0]) for r in db.execute('SELECT data FROM filaments')]
 source_path=config.data_dir/'projects/2c9a7959d13a438fbeb5b8340d8eefd4/runs/db7728785a564c3d8715c7388992129d/prepared-source.glb'
 if plan['mesh_hash']!=MESH_HASH or manifest.get('mesh_hash')!=MESH_HASH or hashlib.sha256(source_path.read_bytes()).hexdigest()!=SOURCE_SHA256:raise ValueError('Buddy native source/plan binding changed')
 source=load_surface(source_path,1000,'Y')
 settings,_=read_native_template(a.template);info=inspect_template(a.template,require_mixed=False)
 slots,mapping=prepare_native_materials(parts,source,plan,info,stock,native_settings=settings)
 (root/'material-mapping.json').write_text(json.dumps(mapping,indent=2))
 preview,_=build_buddy_parts_preview(parts,source,plan,stock,native_settings=settings)
 (root/'colored-parts-preview.json').write_text(json.dumps(preview,separators=(',',':')))
 from figuraforge.geometry.colors import hex_rgb
 palette=np.array([hex_rgb(value) for value in settings['filament_colour']])
 parity={}
 for item in preview['meshes']:
  color=np.frombuffer(base64.b64decode(item['colors']),dtype='<f4').reshape(-1,3,3)[:,0]
  native_color=palette[np.asarray(slots[item['id']])-1]
  parity[item['id']]=int((np.max(abs(color-native_color),axis=1)>1e-6).sum())
 (root/'preview-native-parity.json').write_text(json.dumps({'differing_faces':parity,'passed':not any(parity.values())},indent=2))
 if any(parity.values()):raise RuntimeError('Visible preview differs from actual native material slots')
 lookup={part.id:part for part in parts};report={'geometry':str(a.geometry),'plan':str(plan_path),'plan_file_sha256':hashlib.sha256(plan_path.read_bytes()).hexdigest(),'template':str(a.template),'parts':len(parts),'plates':[],'printer_communication':False,'physical_fit_verified':False,'checker_source_sha256':CHECKER_SHA256}
 inverse_slots={int(slot):ident for ident,slot in mapping['filament_slots'].items()}
 packed_report=copy.deepcopy(manifest)
 packed_report['part_filament_ids']={ident:sorted({inverse_slots[int(slot)] for slot in row['used_slots']}) for ident,row in mapping['parts'].items()}
 plates=pack_buddy_parts(parts,construction_report=packed_report);print(root,flush=True)
 requested=plates[a.start-1:][:a.limit]
 if a.plate_ids:
  selected={int(value) for value in a.plate_ids.split(',')}
  if not selected or not selected<={plate['id'] for plate in plates}:raise ValueError('Unknown Buddy plate ID')
  requested=[plate for plate in requested if plate['id'] in selected]
 report.update(total_planned_plate_count=len(plates),requested_plate_ids=[plate['id'] for plate in requested],phase='slicing_all_plates')
 (root/'packing.json').write_text(json.dumps(plates,indent=2))
 (root/'actual-part-filament-ids.json').write_text(json.dumps(packed_report['part_filament_ids'],indent=2))
 hash_bytes=lambda array:hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()
 inputs={'template_sha256':hashlib.sha256(a.template.read_bytes()).hexdigest(),'parts':{part.id:{'vertices_sha256':hash_bytes(part.mesh.vertices),'faces_sha256':hash_bytes(part.mesh.faces),'face_slots_sha256':hash_bytes(np.asarray(slots[part.id],dtype='<i4'))} for part in parts},'plates':[]}
 def checkpoint():
  report['completed_slice_count']=len(report['plates'])
  report['completed_path_count']=sum(row.get('paths') is not None for row in report['plates'])
  (root/'verification.json').write_text(json.dumps(report,indent=2))
 for plate in requested:
  plate=copy.deepcopy(plate)
  local_plate=copy.deepcopy(plate)
  local_plate['native_physical_slots']=sorted({mapping['filament_slots'][spool] for spool in plate['physical_filament_ids']})
  config=configure_buddy_plate(settings,local_plate)
  signature={'part_ids':[item['part_id'] for item in plate['placements']],'placements':plate['placements'],'settings':config,'template_sha256':inputs['template_sha256'],'parts':{item['part_id']:inputs['parts'][item['part_id']] for item in plate['placements']}}
  # Only actual printing inputs matter: plate indices and informational packing
  # rectangles/policies do not enter the model transform or the slicer profile.
  signature['placements']=[{'part_id':item['part_id'],'transform':item['transform']} for item in plate['placements']]
  inputs['plates'].append({'plate_id':plate['id'],'part_ids':signature['part_ids'],'input_sha256':hashlib.sha256(json.dumps(signature,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'signature':signature})
  (root/'native-inputs.json').write_text(json.dumps(inputs,indent=2))
  origin=native_bed_bounds(settings)['min']
  for item in plate['placements']:
   item['transform'][0][3]+=origin[0];item['transform'][1][3]+=origin[1]
   item['rect'][0]+=origin[0];item['rect'][1]+=origin[1]
  plate['native_physical_slots']=local_plate['native_physical_slots']
  chosen=[lookup[item['part_id']] for item in plate['placements']]
  path=root/f"plate-{plate['id']:02}.3mf"
  built=build_native_from_parts(a.template,path,chosen,plate['placements'],config,{part.id:slots[part.id] for part in chosen})
  sliced=slice_plate(path,root/f"slice-{plate['id']:02}",'/Applications/BambuStudio.app/Contents/MacOS/BambuStudio')
  row={'plate_id':plate['id'],'placements':plate['placements'],'physical_filament_ids':plate['physical_filament_ids'],'native_physical_slots':plate['native_physical_slots'],'native':built,'slice':sliced,'paths':None}
  report['plates'].append(row);checkpoint()
  print(f"Plate {plate['id']}: slice={sliced['passed']}, code={sliced['result'].get('return_code')}",flush=True)
 # Find every geometry/support boundary failure before spending time on large
 # arc-expanded footprint checks. Failed slices remain explicit blockers.
 report['phase']='full_footprints';checkpoint()
 for row in report['plates']:
  if not row['slice']['passed']:continue
  ident=row['plate_id']
  try:row['paths']=check(root/f"slice-{ident:02}/plate_1.gcode")
  except Exception as exc:row['paths']={'passed':False,'error':str(exc)}
  checkpoint();print(f"Plate {ident}: full_paths={row['paths']['passed']}",flush=True)
 report['requested_subset_passed']=all(row['slice']['passed'] and row.get('paths',{}).get('passed',False) for row in report['plates'])
 report['passed']=len(report['plates'])==len(plates) and report['requested_subset_passed']
 report['phase']='complete';checkpoint()
 if not report['requested_subset_passed']:raise RuntimeError('Buddy native slicing/path gates rejected one or more plates; inspect all collected results')

if __name__=='__main__':main()
