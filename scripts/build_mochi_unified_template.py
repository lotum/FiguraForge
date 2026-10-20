"""Offline native CLI material-profile construction; source profiles remain untouched."""
from pathlib import Path
import json,zipfile,subprocess,hashlib,copy,sys,argparse,uuid
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-root',type=Path,default=ROOT/'benchmarks/mochi-single-body-native');parser.add_argument('--brown-id',type=int,choices=[28,29],default=29);parser.add_argument('--solid-only',action='store_true',help='Only Brown/Beige/Black physical profiles, no virtual mixtures');args=parser.parse_args();WORK=args.output_root.resolve()/('profiles-'+uuid.uuid4().hex);WORK.mkdir(parents=True)
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
material_specs=[('Generic PLA @BBL H2D','FiguraForge ELEGOO Matte EarthBrown 29 Generic PLA H2D UNCALIBRATED','#805947','29'),('Bambu PLA Basic @BBL H2D','FiguraForge Bambu PLA Basic Beige 31 H2D','#F7E6DE','31'),('Generic PLA @BBL H2D','FiguraForge eSUN ePLA Lite Black 30 Generic PLA H2D UNCALIBRATED','#272729','30')]
if args.brown_id==28:material_specs[0]=('Generic PLA @BBL H2D','FiguraForge ELEGOO PLA Plus Brown 28 Generic PLA H2D UNCALIBRATED','#9E6A4B','28')
if not args.solid_only:material_specs += [('Generic PLA @BBL H2D',f'FiguraForge Mixed virtual seed {i:02d} Generic PLA H2D','#BCAE9C',None) for i in range(18)]
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
for category,name in [('machine',settings['printer_settings_id']),('process','0.20mm Standard @BBL H2D')]:
    file=WORK/(category+'.json');file.write_text(json.dumps(flatten_preset(category,name),indent=2));setting_paths.append(str(file.resolve()))
output=WORK/f'physical-{len(material_specs)}slot-cli-profiles.3mf'
command=['/Applications/BambuStudio.app/Contents/MacOS/BambuStudio','--export-3mf',str(output.resolve()),'--load-settings',';'.join(setting_paths),'--load-filaments',';'.join(paths),'--arrange','0','--orient','0',str(inputfile.resolve())]
result=subprocess.run(command,capture_output=True,text=True,timeout=90,cwd=WORK);(WORK/'conversion.log').write_text(result.stdout+result.stderr)
if result.returncode or not output.exists():raise RuntimeError(f'CLI conversion exit {result.returncode}; see conversion.log')
# Intermediate CLI export contains no configured Mixed recipes yet.
with zipfile.ZipFile(output) as archive:converted=json.loads(archive.read(CONFIG))
assert len(converted['filament_colour'])==len(material_specs)
assert converted['filament_colour'][:3]==[s[2] for s in material_specs[:3]]
assert not any('Glow' in str(x) for x in converted['filament_settings_id'])
# The CLI constructs dimensional arrays. Restore only existing native mixed options;
# never resize or invent process/material/flush profile dimensions.
for key in ['filament_is_mixed','filament_mixed_components','filament_mixed_sublayer_ratios','filament_mixed_gradient','filament_mixed_gradient_per_part','filament_mixed_gradient_range','filament_mixed_gradient_curve']:
    # These seven known options are explicitly one value per native slot.
    # All thermals/flush/dimensioned arrays are freshly produced by the CLI.
    converted[key]=(['0' if key in ('filament_is_mixed','filament_mixed_gradient','filament_mixed_gradient_per_part') else '']*3 if args.solid_only else copy.deepcopy(settings[key])+[copy.deepcopy(settings[key][-1])])
converted['default_filament_colour']=copy.deepcopy(converted['filament_colour'])
converted['filament_map']=['1','2','2']+([] if args.solid_only else ['1']*18)
# Preserve actual two-nozzle hardware inventory from the verified H2D seed.
# Official machine presets alone leave these runtime hardware arrays empty.
for key in ['extruder_nozzle_stats','extruder_ams_count']:converted[key]=copy.deepcopy(settings[key])
converted['filament_nozzle_map']=['0']*len(material_specs)
converted['enable_mixed_color_sublayer']='0' if args.solid_only else '1'
process_source=copy.deepcopy(converted)
converted.update(sparse_infill_pattern='lightning',sparse_infill_density='5%',wall_loops='2',
    enable_support='1',support_type='tree(auto)',support_on_build_plate_only='1',
    support_threshold_angle='20',support_top_z_distance='0.2',layer_height='0.2',initial_layer_print_height='0.2')
converted=mark_explicit_process_overrides(converted,process_source)
# Known process keys only: preserve these edits on native GUI preset resolution.
groups=converted['different_settings_to_system'];groups[0]=';'.join(sorted(set(filter(None,groups[0].split(';')))|{'sparse_infill_pattern','sparse_infill_density','wall_loops'}))
RATIOS=[0,10,15,19,24,29,34,38,43,48,52,57,62,66,71,76,81,85,90,100]
allocated={'settings':converted,'report':{'mixed_slots':[]}} if args.solid_only else allocate_native_recipes(converted,[1,2],RATIOS);final=allocated['settings'];validate_native_settings(final)
stem='mochi-solid-3colors' if args.solid_only else 'mochi-single-body-20values'
full=WORK/(stem+'-native-cube.3mf')
with zipfile.ZipFile(output) as source,zipfile.ZipFile(full,'x',zipfile.ZIP_DEFLATED) as target:
    for name in source.namelist():target.writestr(name,json.dumps(final).encode() if name==CONFIG else source.read(name))
small=WORK/(stem+'-profile-only.3mf');inspection=make_profile_template(full,small)
report={'source_profile_sha256':provenance,'cli_command':command,'cli_exit':result.returncode,'profiles':[{'slot':i,'official_system_profile':row[0],'display_name':row[1],'hex':row[2],'inventory_id':row[3],'calibrated':False} for i,row in enumerate(material_specs,1)],'solid_only':args.solid_only,'required_color_value_count':2 if args.solid_only else 20,'pure_endpoint_count':2,'inner_recipe_count':0 if args.solid_only else 18,'first_component_percentages':[] if args.solid_only else RATIOS,'spacing_note':'No mixtures; two pure body colors plus separate black' if args.solid_only else '18 rounded near-uniform inner steps over legal 10..90 percent, plus pure endpoints; not uniform 0..100 spacing','black_on_separate_parts':True,'process_initial_proposal':{k:final[k] for k in ['sparse_infill_pattern','sparse_infill_density','wall_loops','enable_support','support_type','support_on_build_plate_only','support_threshold_angle','layer_height']},'allocation':allocated['report'],'native_inspection':inspection,'native_gui_verified':False,'physical_color_verified':False,'physical_calibration_verified':False,'template':str(small.relative_to(ROOT)),'settings_check':{k:converted.get(k) for k in ['filament_ids','filament_settings_id','filament_colour','nozzle_temperature','nozzle_temperature_initial_layer','filament_flow_ratio','filament_max_volumetric_speed','filament_map','filament_is_mixed','inherits_group']}}
(WORK/'profile-provenance.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'template':str(small),'cli_exit':result.returncode,'slots':len(final['filament_colour']),'mixed_slots':0 if args.solid_only else 18}))
