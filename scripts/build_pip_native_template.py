"""Offline native CLI material-profile construction; source profiles remain untouched."""
from pathlib import Path
import json,zipfile,subprocess,hashlib,copy,sys,argparse,uuid
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-root',type=Path,default=ROOT/'benchmarks/pip-native-template');parser.add_argument('--brown-id',type=int,choices=[28,29],default=29);args=parser.parse_args();WORK=args.output_root.resolve()/('profiles-'+uuid.uuid4().hex);WORK.mkdir(parents=True)
sys.path.insert(0,str(ROOT/'backend'))
from figuraforge.services.mixed_filament import read_native_template,validate_native_settings,make_profile_template,mark_explicit_process_overrides
from figuraforge.services.native_recipe_library import allocate_native_recipes
PROFILE=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL/filament')
SOURCE=ROOT/'benchmarks/mixed-filament-native/h2d-17-mixed-recipes.3mf'
CONFIG='Metadata/project_settings.config'
provenance={}
def flatten(name,stack=()):
    if name in stack:raise ValueError('Profile inheritance cycle')
    path=PROFILE/(name+'.json');raw=json.loads(path.read_text());provenance[name]=hashlib.sha256(path.read_bytes()).hexdigest();result={}
    if raw.get('inherits'):result.update(flatten(raw['inherits'],(*stack,name)))
    for include in raw.get('include',[]):result.update(flatten(include,(*stack,name)))
    result.update(raw);result.pop('include',None)
    return result
settings,_=read_native_template(SOURCE);base=copy.deepcopy(settings);n=len(settings['filament_colour'])
base['enable_mixed_color_sublayer']='0'
for key in ['filament_is_mixed','filament_mixed_gradient','filament_mixed_gradient_per_part']:base[key]=['0']*n
for key in ['filament_mixed_components','filament_mixed_sublayer_ratios','filament_mixed_gradient_range','filament_mixed_gradient_curve']:base[key]=['']*n
material_specs=[('Bambu PLA Matte @BBL H2D','FiguraForge Bambu PLA Matte Apple Green 52 H2D','#C2E189','52'),('Generic PLA @BBL H2D','FiguraForge ELEGOO Matte EarthBrown 29 Generic PLA H2D UNCALIBRATED','#805947','29'),('Bambu PLA Basic @BBL H2D','FiguraForge Bambu PLA Basic Beige 31 H2D','#F7E6DE','31'),('Generic PLA @BBL H2D','FiguraForge eSUN ePLA Lite Black 30 Generic PLA H2D UNCALIBRATED','#272729','30')]
if args.brown_id==28:material_specs[1]=('Generic PLA @BBL H2D','FiguraForge ELEGOO PLA Plus Brown 28 Generic PLA H2D UNCALIBRATED','#9E6A4B','28')
material_specs += [('Generic PLA @BBL H2D',f'FiguraForge Mixed virtual seed {i:02d} Generic PLA H2D','#BCAE9C',None) for i in range(17)]
paths=[]
for slot,(system,name,color,stock) in enumerate(material_specs,1):
    config=flatten(system);config.update(name=name,inherits=system,from_='user',instantiation='true',filament_colour=[color],filament_settings_id=[name]);config['from']=config.pop('from_')
    file=WORK/f'filament-{slot:02d}.json';file.write_text(json.dumps(config,indent=2)+'\n');paths.append(str(file.resolve()))
# Fresh STL + official presets: let the native CLI allocate all N/N² vectors.
# Loading 21 profiles into an old 20-slot project is rejected by this CLI.
import trimesh
inputfile=WORK/'cube.stl';trimesh.creation.box(extents=[8,8,8]).export(inputfile)
def flatten_preset(category,name,stack=()):
    if name in stack:raise ValueError('Preset inheritance cycle')
    path=PROFILE.parent/category/(name+'.json');raw=json.loads(path.read_text());provenance[str(path.relative_to(PROFILE.parent))]=hashlib.sha256(path.read_bytes()).hexdigest();result={}
    if raw.get('inherits'):result.update(flatten_preset(category,raw['inherits'],(*stack,name)))
    for include in raw.get('include',[]):result.update(flatten_preset(category,include,(*stack,name)))
    result.update(raw);result.pop('include',None);return result
setting_paths=[]
for category,name in [('machine',settings['printer_settings_id']),('process',settings['print_settings_id'])]:
    file=WORK/(category+'.json');file.write_text(json.dumps(flatten_preset(category,name),indent=2));setting_paths.append(str(file.resolve()))
output=WORK/'physical-21slot-cli-profiles.3mf'
command=['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--export-3mf',str(output.resolve()),'--load-settings',';'.join(setting_paths),'--load-filaments',';'.join(paths),'--arrange','0','--orient','0',str(inputfile.resolve())]
result=subprocess.run(command,capture_output=True,text=True,timeout=90,cwd=WORK);(WORK/'conversion.log').write_text(result.stdout+result.stderr)
if result.returncode or not output.exists():raise RuntimeError(f'CLI conversion exit {result.returncode}; see conversion.log')
# Intermediate CLI export contains no configured Mixed recipes yet.
with zipfile.ZipFile(output) as archive:converted=json.loads(archive.read(CONFIG))
assert len(converted['filament_colour'])==21
assert converted['filament_colour'][:4]==[s[2] for s in material_specs[:4]]
assert not any('Glow' in str(x) for x in converted['filament_settings_id'])
# The CLI constructs dimensional arrays. Restore only existing native mixed options;
# never resize or invent process/material/flush profile dimensions.
for key in ['filament_is_mixed','filament_mixed_components','filament_mixed_sublayer_ratios','filament_mixed_gradient','filament_mixed_gradient_per_part','filament_mixed_gradient_range','filament_mixed_gradient_curve']:converted[key]=copy.deepcopy(settings[key][:3])+[('0' if key in ('filament_is_mixed','filament_mixed_gradient','filament_mixed_gradient_per_part') else '')]+copy.deepcopy(settings[key][3:])
converted['default_filament_colour']=copy.deepcopy(converted['filament_colour'])
converted['filament_map']=['1','2','2','2']+['1']*17
# Preserve actual two-nozzle hardware inventory from the verified H2D seed.
# Official machine presets alone leave these runtime hardware arrays empty.
for key in ['extruder_nozzle_stats','extruder_ams_count']:converted[key]=copy.deepcopy(settings[key])
converted['filament_nozzle_map']=['0']*len(material_specs)
converted['enable_mixed_color_sublayer']='1'
converted=mark_explicit_process_overrides(converted,settings)
allocated=allocate_native_recipes(converted,[1,2],[0,*range(10,91,5),100]);final=allocated['settings'];validate_native_settings(final)
full=WORK/'pip-real-materials-19recipes-native-cube.3mf'
with zipfile.ZipFile(output) as source,zipfile.ZipFile(full,'x',zipfile.ZIP_DEFLATED) as target:
    for name in source.namelist():target.writestr(name,json.dumps(final).encode() if name==CONFIG else source.read(name))
small=WORK/'pip-real-materials-profile-only.3mf';inspection=make_profile_template(full,small)
report={'source_profile_sha256':provenance,'cli_command':command,'cli_exit':result.returncode,'profiles':[{'slot':i,'official_system_profile':row[0],'display_name':row[1],'hex':row[2],'inventory_id':row[3],'calibrated':False} for i,row in enumerate(material_specs,1)],'allocation':allocated['report'],'native_inspection':inspection,'native_gui_verified':False,'physical_color_verified':False,'physical_calibration_verified':False,'template':str(small.relative_to(ROOT)),'settings_check':{k:converted.get(k) for k in ['filament_ids','filament_settings_id','filament_colour','nozzle_temperature','nozzle_temperature_initial_layer','filament_flow_ratio','filament_max_volumetric_speed','filament_map','filament_is_mixed','inherits_group']}}
(WORK/'profile-provenance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'template':str(small),'cli_exit':result.returncode,'slots':len(final['filament_colour']),'mixed_slots':17}))
