from pathlib import Path
import sys,json,uuid,copy,hashlib
import numpy as np
import trimesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'));sys.path.insert(0,str(ROOT/'scripts'))
from figuraforge.services.mixed_filament import read_native_template,build_native_from_parts,validate_native_settings
from figuraforge.services.native_recipe_library import allocate_native_recipes
from figuraforge.geometry.types import Part
from slice_native_plates import slice_plate
source=Path(sys.argv[1]);settings,_=read_native_template(source);ratios=[0,10,15,19,24,29,34,38,43,48,52,57,62,66,71,76,81,85,90,100];allocation=allocate_native_recipes(settings,[1,2],ratios);settings=allocation['settings']
# Keep purge tower safely separated from the actual 20 test articles.
settings.update(wipe_tower_x=['235','235'],wipe_tower_y=['250','250'],prime_tower_width='35')
out=ROOT/'benchmarks/mochi-single-body-native'/('verification-'+uuid.uuid4().hex);out.mkdir();parts=[];placements=[];slots={}
for i,percent in enumerate(ratios):
 ident=f'ratio-{percent:03d}';part=Part(ident,f'First component {percent} percent',trimesh.creation.box(extents=[3,12,2]),'#FFFFFF');parts.append(part);x=50+(i%10)*6;y=50+(i//10)*20;tf=np.eye(4);tf[:3,3]=[x+1.5,y+6,1]
 placements.append({'part_id':ident,'transform':tf.tolist(),'rect':[x,y,3,12],'height_mm':2});slots[ident]=[allocation['percent_to_slot'][percent]]*len(part.mesh.faces)
plate=out/'mochi-20-value-test-native.3mf';report=build_native_from_parts(source,plate,parts,placements,settings,slots);report.update(template=str(source),template_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),first_component_percentages=ratios,pure_endpoint_count=2,inner_recipe_count=18,native_config=validate_native_settings(settings),process={k:settings[k] for k in ['sparse_infill_pattern','sparse_infill_density','wall_loops','enable_support','support_type','layer_height']},print_started=False)
(out/'native-build-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(out,flush=True)
sliced=slice_plate(plate,out/'slice','/Applications/BambuStudio.app/Contents/MacOS/BambuStudio');(out/'slice-verification.json').write_text(json.dumps(sliced,indent=2)+'\n');print(json.dumps({'output':str(out),'slice_passed':sliced['passed'],'exit':sliced['exit_code']}),flush=True)
