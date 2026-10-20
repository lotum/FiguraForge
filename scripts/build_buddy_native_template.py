"""Offline native CLI material-profile construction; source profiles remain untouched."""
from pathlib import Path
import json,zipfile,subprocess,hashlib,copy,sys,argparse,uuid
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-root',type=Path,default=ROOT/'benchmarks/buddy-native-template');args=parser.parse_args();WORK=args.output_root.resolve()/('profiles-'+uuid.uuid4().hex);WORK.mkdir(parents=True)
sys.path.insert(0,str(ROOT/'backend'))
from figuraforge.services.mixed_filament import read_native_template,validate_native_settings,make_profile_template,mark_explicit_process_overrides
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
settings,_=read_native_template(SOURCE)
material_specs=[('Generic PLA @BBL H2D','FiguraForge ELEGOO Matte EarthBrown 29 Generic PLA H2D UNCALIBRATED','#805947','29'),
('Generic PLA @BBL H2D','FiguraForge ELEGOO PLA Plus Wood 33 Generic PLA H2D UNCALIBRATED','#B19870','33'),
('Generic PLA @BBL H2D','FiguraForge ELEGOO Matte NavyBlue 60 Generic PLA H2D UNCALIBRATED','#2D3F6F','60'),
('Generic PLA @BBL H2D','FiguraForge eSUN ePLA Lite Black 30 Generic PLA H2D UNCALIBRATED','#272729','30'),
('Bambu PLA Basic @BBL H2D','FiguraForge Bambu PLA Basic Beige 31 H2D','#F7E6DE','31')]
paths=[]
for slot,(system,name,color,stock) in enumerate(material_specs,1):
    config=flatten(system);config.update(name=name,inherits=system,from_='user',instantiation='true',filament_colour=[color],filament_settings_id=[name]);config['from']=config.pop('from_')
    file=WORK/f'filament-{slot:02d}.json';file.write_text(json.dumps(config,indent=2)+'\n');paths.append(str(file.resolve()))
# Fresh STL + official presets: let the native CLI allocate all N/N² vectors.
# Do not resize inherited N/N² vectors by hand.
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
output=WORK/'physical-five-slot-cli-profiles.3mf'
command=['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--export-3mf',str(output.resolve()),'--load-settings',';'.join(setting_paths),'--load-filaments',';'.join(paths),'--arrange','0','--orient','0',str(inputfile.resolve())]
with (WORK/'conversion.log').open('w') as log:
    result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=120,cwd=WORK)
if result.returncode or not output.exists():raise RuntimeError(f'CLI conversion exit {result.returncode}; see conversion.log')
with zipfile.ZipFile(output) as archive:converted=json.loads(archive.read(CONFIG))
assert len(converted['filament_colour'])==5
assert converted['filament_colour']==[row[2] for row in material_specs]
converted['enable_mixed_color_sublayer']='0'
for key in ['filament_is_mixed','filament_mixed_gradient','filament_mixed_gradient_per_part']:converted[key]=['0']*5
for key in ['filament_mixed_components','filament_mixed_sublayer_ratios','filament_mixed_gradient_range','filament_mixed_gradient_curve']:converted[key]=['']*5
for key in ['extruder_nozzle_stats','extruder_ams_count']:
    converted[key]=copy.deepcopy(settings[key])
converted['filament_nozzle_map']=['0']*5
converted['filament_map']=['1','2','1','1','2']
converted['default_filament_colour']=copy.deepcopy(converted['filament_colour'])
validate_native_settings(converted)
full=WORK/'buddy-real-five-materials-native-cube.3mf'
with zipfile.ZipFile(output) as source,zipfile.ZipFile(full,'x',zipfile.ZIP_DEFLATED) as target:
    for name in source.namelist():target.writestr(name,json.dumps(converted).encode() if name==CONFIG else source.read(name))
small=WORK/'buddy-real-materials-profile-only.3mf';inspection=make_profile_template(full,small)
report={'source_profile_sha256':provenance,'cli_command':command,'cli_exit':result.returncode,'profiles':[{'slot':i,'official_system_profile':row[0],'display_name':row[1],'hex':row[2],'inventory_id':'richard-inventory-202609-'+row[3],'calibrated':False} for i,row in enumerate(material_specs,1)],'native_inspection':inspection,'native_gui_verified':False,'physical_color_verified':False,'physical_calibration_verified':False,'template':str(small.relative_to(ROOT)),'generic_fallback':'No installed exact ELEGOO/ePLA-Lite profile: official H2D Generic PLA thermal settings inherited unchanged; not calibrated.'}
(WORK/'profile-provenance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'template':str(small),'cli_exit':result.returncode,'slots':5,'mixed_slots':0}))
