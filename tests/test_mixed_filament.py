from copy import deepcopy
import pytest
from figuraforge.services.mixed_filament import (
    MixedFilamentError, MixRecipe, recipe_library, validate_native_settings,
    apply_recipes_to_template, verify_native_roundtrip,
)


def template():
    return {'enable_mixed_color_sublayer': '1',
            'filament_colour': ['#112233', '#FFEECC', '#888888'],
            'filament_is_mixed': ['0', '0', '1'],
            'filament_mixed_components': ['', '', '1,2'],
            'filament_mixed_sublayer_ratios': ['', '', '0.50,0.50'],
            'filament_mixed_gradient': ['0']*3,
            'filament_mixed_gradient_range': ['']*3,
            'filament_mixed_gradient_curve': ['']*3,
            'filament_mixed_gradient_per_part': ['0']*3,
            'machine_start_gcode': 'preserve me'}


def test_safe_five_percent_library():
    recipes = recipe_library()
    assert len(recipes) == 17
    assert recipes[0].ratios == '0.10,0.90'
    assert recipes[-1].ratios == '0.90,0.10'
    with pytest.raises(MixedFilamentError): MixRecipe((1, 2), 5)
    with pytest.raises(MixedFilamentError): MixRecipe((1, 1), 50)


def test_edit_existing_slot_preserves_input_and_profiles():
    source = template()
    original = deepcopy(source)
    result = apply_recipes_to_template(source, {3: MixRecipe((1, 2), 35)})
    assert result['filament_mixed_sublayer_ratios'][2] == '0.35,0.65'
    assert result['machine_start_gcode'] == source['machine_start_gcode']
    assert source == original
    with pytest.raises(MixedFilamentError): apply_recipes_to_template(source, {4: MixRecipe((1, 2), 50)})


@pytest.mark.parametrize(('key','value'), [
    ('filament_mixed_components', ['', '', '1,3']),
    ('filament_mixed_components', ['', '', '0,2']),
    ('filament_mixed_components', ['', '', '1,1']),
    ('filament_mixed_sublayer_ratios', ['', '', 'nan,0.5']),
    ('filament_mixed_sublayer_ratios', ['', '', '0.3,0.3']),
    ('filament_mixed_sublayer_ratios', ['', '', '0.05,0.95']),
    ('filament_is_mixed', ['0']),
    ('enable_mixed_color_sublayer', '0'),
    ('filament_mixed_gradient', ['0','0','1']),
])
def test_rejects_unusable_native_settings(key, value):
    source = template(); source[key] = value
    with pytest.raises(MixedFilamentError): validate_native_settings(source)


def test_roundtrip_requires_recipe_preservation():
    source = template()
    assert verify_native_roundtrip(source, deepcopy(source))['mixed_settings_preserved']
    actual = deepcopy(source); actual['filament_mixed_sublayer_ratios'][2] = '0.4,0.6'
    with pytest.raises(MixedFilamentError): verify_native_roundtrip(source, actual)


def test_real_triangle_annotation_and_non_overwrite(tmp_path):
    import json, zipfile
    from xml.etree import ElementTree as ET
    from figuraforge.services.mixed_filament import attach_native_painting
    source=tmp_path/'template.3mf'; output=tmp_path/'painted.3mf'
    model=b'<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources><object id="7"><mesh><triangles><triangle v1="0" v2="1" v3="2"/></triangles></mesh></object></resources></model>'
    with zipfile.ZipFile(source,'w') as z:
        z.writestr('3D/Objects/object_7.model',model)
        z.writestr('Metadata/model_settings.config',b'<config/>')
        z.writestr('Metadata/project_settings.config',json.dumps(template()))
    painting={'model_path':'3D/Objects/object_7.model','object_id':'7',
              'expected_triangle_count':1,'face_slots':{0:3}}
    assert not attach_native_painting(source,output,template(),[painting])['native_roundtrip_verified']
    with zipfile.ZipFile(output) as z:
        triangle=next(n for n in ET.fromstring(z.read('3D/Objects/object_7.model')).iter() if n.tag.endswith('triangle'))
        assert triangle.get('paint_color')=='0C'
    with zipfile.ZipFile(source) as z: assert z.read('3D/Objects/object_7.model')==model
    with pytest.raises(MixedFilamentError): attach_native_painting(source,output,template(),[painting])
    painting['expected_triangle_count']=2
    with pytest.raises(MixedFilamentError): attach_native_painting(source,tmp_path/'bad.3mf',template(),[painting])
    assert not (tmp_path/'bad.3mf').exists()


def test_two_filaments_per_part_not_whole_figure():
    from figuraforge.services.mixed_filament import validate_part_filament_limits
    source=template()
    for key,value in source.items():
        if isinstance(value,list):value.append(value[0])
    source['filament_colour'][3]='#000000'
    result=validate_part_filament_limits(source,{'ear':[1,2,3],'nose':[4]})
    assert result['physical_slots_per_part']=={'ear':[1,2],'nose':[4]}
    with pytest.raises(MixedFilamentError):validate_part_filament_limits(source,{'ear':[1,3,4]})


def _template_archive(path, settings, extra=None):
    import json, zipfile
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('Metadata/project_settings.config',json.dumps(settings))
        z.writestr('Metadata/model_settings.config','<config/>')
        z.writestr('3D/3dmodel.model','<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources><object id="2"><mesh><triangles><triangle v1="0" v2="1" v3="2"/></triangles></mesh></object></resources></model>')
        for name,value in (extra or {}).items():z.writestr(name,value)


def test_inspect_h2d_template_is_sanitized(tmp_path):
    from figuraforge.services.mixed_filament import inspect_template
    source=template();source.update(printer_model='Bambu Lab H2D',nozzle_diameter=['0.4','0.4'],filament_type=['PLA']*3,filament_vendor=['Bambu Lab']*3,private_api_key='secret')
    path=tmp_path/'h2d.3mf';_template_archive(path,source)
    result=inspect_template(path)
    assert result['nozzle_count']==2
    assert result['models'][0]['triangle_count']==1
    assert result['basis_filaments'][0]['material']=='PLA'
    assert 'private_api_key' not in result['config']
    assert 'machine_start_gcode' not in result['config']


@pytest.mark.parametrize('update',[
    {'printer_model':'Bambu Lab A1'}, {'nozzle_diameter':['0.4']},
    {'nozzle_diameter':['NaN','0.4']}, {'nozzle_diameter':['-1','0.4']},
    {'filament_is_mixed':['0','0','0']},
])
def test_inspector_rejects_wrong_hardware_or_explicitly_required_missing_mix(tmp_path,update):
    from figuraforge.services.mixed_filament import inspect_template
    source=template();source.update(printer_model='Bambu Lab H2D',nozzle_diameter=['0.4','0.4']);source.update(update)
    path=tmp_path/'bad.3mf';_template_archive(path,source)
    with pytest.raises(MixedFilamentError):inspect_template(path,require_mixed=True)


@pytest.mark.parametrize('name',['../escape','/absolute','3D/../escape','C:/escape','3D\\escape'])
def test_inspector_rejects_unsafe_zip_paths(tmp_path,name):
    from figuraforge.services.mixed_filament import inspect_template
    source=template();source.update(printer_model='Bambu Lab H2D',nozzle_diameter=['0.4','0.4'])
    path=tmp_path/'bad.3mf';_template_archive(path,source,{name:'unsafe'})
    with pytest.raises(MixedFilamentError):inspect_template(path)


def test_builder_rejects_incomplete_or_three_color_part_before_cli(tmp_path):
    import trimesh
    from figuraforge.geometry.types import Part
    from figuraforge.services.mixed_filament import build_native_from_parts
    source=template();source.update(printer_model='Bambu Lab H2D',nozzle_diameter=['0.4','0.4'])
    path=tmp_path/'h2d.3mf';_template_archive(path,source)
    part=Part('ear','Ear',trimesh.creation.box(),'#888888')
    with pytest.raises(MixedFilamentError,match='every exported part'):
        build_native_from_parts(path,tmp_path/'out.3mf',[part],None,source,{})
    with pytest.raises(MixedFilamentError,match='Every source triangle'):
        build_native_from_parts(path,tmp_path/'out.3mf',[part],None,source,{'ear':[3]})
    assert not (tmp_path/'out.3mf').exists()


def test_profile_import_never_opens_auxiliary_images(tmp_path,monkeypatch):
    import zipfile
    from figuraforge.services.mixed_filament import inspect_template,make_profile_template,read_native_template
    source=template();source.update(printer_model='Bambu Lab H2D',nozzle_diameter=['0.4','0.4'])
    original=tmp_path/'original.3mf';_template_archive(original,source,{'Auxiliaries/private-photo.png':b'private image'})
    real_open=zipfile.ZipFile.open
    def guarded_open(self,name,*args,**kwargs):
        filename=getattr(name,'filename',name)
        assert not str(filename).startswith('Auxiliaries/')
        return real_open(self,name,*args,**kwargs)
    monkeypatch.setattr(zipfile.ZipFile,'open',guarded_open)
    assert inspect_template(original)['models'][0]['triangle_count']==1
    small=tmp_path/'profiles-only.3mf';make_profile_template(original,small)
    assert read_native_template(small)[0]==source
    with zipfile.ZipFile(small) as z:
        assert all(not n.startswith('Auxiliaries/') for n in z.namelist())
    assert inspect_template(small)['models']==[]


def test_streaming_model_rejects_entities(tmp_path):
    import zipfile,json
    from figuraforge.services.mixed_filament import inspect_template
    source=template();source.update(printer_model='Bambu Lab H2D',nozzle_diameter=['0.4','0.4'])
    path=tmp_path/'entity.3mf'
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('Metadata/project_settings.config',json.dumps(source))
        z.writestr('Metadata/model_settings.config','<config/>')
        z.writestr('3D/3dmodel.model','<!DOCTYPE model [<!ENTITY a "unsafe">]><model/>')
    with pytest.raises(MixedFilamentError,match='DTD/entity'):inspect_template(path)


def _h2d_bed():
    return {'printable_area':['0x0','350x0','350x320','0x320'],
            'extruder_printable_area':['0x0,325x0,325x320,0x320','25x0,350x0,350x320,25x320'],
            'printable_height':'325','extruder_printable_height':['320','325'],'bed_exclude_area':[]}


def test_actual_dual_nozzle_plate_limits():
    import trimesh
    from figuraforge.geometry.types import Part
    from figuraforge.services.mixed_filament import validate_plate_parts
    mesh=trimesh.creation.box(extents=[12,12,12]);mesh.apply_translation([50,50,6])
    part=Part('cube','Cube',mesh,'#000000')
    result=validate_plate_parts([part],None,_h2d_bed())
    assert result['dual_nozzle_intersection_bounds_mm']==[25,0,325,320]
    assert result['maximum_height_mm']==320
    part.mesh.apply_translation([-20,0,0]) # min X24 fits whole bed but not right nozzle
    with pytest.raises(MixedFilamentError,match='dual-nozzle printable area'):
        validate_plate_parts([part],None,_h2d_bed())


@pytest.mark.parametrize('translation',[[400,0,0],[0,400,0],[0,0,-1],[0,0,321]])
def test_plate_rejects_world_bounds(translation):
    import trimesh,numpy as np
    from figuraforge.geometry.types import Part
    from figuraforge.services.mixed_filament import validate_plate_parts
    mesh=trimesh.creation.box(extents=[10,10,10]);mesh.apply_translation([50,50,5])
    part=Part('cube','Cube',mesh,'#000000');tf=np.eye(4);tf[:3,3]=translation
    with pytest.raises(MixedFilamentError):validate_plate_parts([part],[{'part_id':'cube','transform':tf.tolist()}],_h2d_bed())


def test_plate_exclusions_and_printable_instance_schema():
    import trimesh
    from xml.etree import ElementTree as ET
    from figuraforge.geometry.types import Part
    from figuraforge.services.mixed_filament import validate_plate_parts,_assign_printable_plate
    mesh=trimesh.creation.box(extents=[10,10,10]);mesh.apply_translation([50,50,5]);part=Part('cube','Cube',mesh,'#000000')
    settings=_h2d_bed();settings['bed_exclude_area']=['44x44','56x44','56x56','44x56']
    with pytest.raises(MixedFilamentError,match='exclusion'):validate_plate_parts([part],None,settings)
    contents={'3D/3dmodel.model':b'<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><build><item objectid="2" printable="0"/></build></model>',
              'Metadata/model_settings.config':b'<config><plate/></config>'}
    _assign_printable_plate(contents,['2'])
    assert b'printable="1"' in contents['3D/3dmodel.model']
    node=ET.fromstring(contents['Metadata/model_settings.config']).find('plate/model_instance')
    assert {m.get('key'):m.get('value') for m in node}=={'object_id':'2','instance_id':'0','identify_id':'1'}


def test_native_root_preserves_unused_bambu_namespace():
    from figuraforge.services.mixed_filament import _assign_printable_plate,native_bed_bounds
    raw=b'<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021"><build><item objectid="2" printable="0"/></build></model>'
    contents={'3D/3dmodel.model':raw,'Metadata/model_settings.config':b'<config><plate/></config>'}
    _assign_printable_plate(contents,['2'])
    assert contents['3D/3dmodel.model']==raw.replace(b'printable="0"',b'printable="1"')
    bounds=native_bed_bounds(_h2d_bed())
    assert bounds['min']==[25,0,0]
    assert bounds['max']==[325,320,320]
    assert bounds['extents']==[300,320,320]


def _routing_part():
    import trimesh
    from figuraforge.geometry.types import Part
    return Part('nose','Nose',trimesh.creation.box(),'#FFEECC')


def test_native_object_and_volume_default_follow_actual_beige_faces():
    from xml.etree import ElementTree as ET
    from figuraforge.services.mixed_filament import _part_filament_defaults,_assign_object_filaments,MODEL_SETTINGS_PATH
    settings=template();settings.update(support_filament='0',support_interface_filament='0')
    part=_routing_part();mapping={part.id:dict(enumerate([2]*len(part.mesh.faces)))}
    defaults=_part_filament_defaults([part],mapping,settings)
    contents={MODEL_SETTINGS_PATH:b'<config><object id="2"><metadata key="extruder" value="1"/><part id="1"><metadata key="extruder" value="1"/></part></object></config>'}
    result=_assign_object_filaments(contents,{'nose':'2'},defaults,settings)
    obj=ET.fromstring(contents[MODEL_SETTINGS_PATH]).find('object')
    assert [item.get('value') for item in obj.findall(".//metadata[@key='extruder']")]==['2','2']
    assert result['nose']['physical_slots_including_support']==[2]
    assert settings['support_filament']=='0' # AUTO routing preserved, no invented support preset
    assert settings['machine_start_gcode']=='preserve me'


def test_mixed_default_resolves_recipe_to_dominant_physical_not_virtual_slot():
    from figuraforge.services.mixed_filament import _part_filament_defaults
    settings=template();settings['filament_mixed_sublayer_ratios'][2]='0.25,0.75'
    part=_routing_part();mapping={part.id:dict(enumerate([3]*len(part.mesh.faces)))}
    result=_part_filament_defaults([part],mapping,settings)['nose']
    assert result['default_extruder']==2
    assert result['physical_slots_including_support']==[1,2]
    assert result['physical_surface_weights_mm2'][2]==pytest.approx(3*result['physical_surface_weights_mm2'][1])


def _four_slot_template():
    settings=template()
    for value in settings.values():
        if isinstance(value,list):value.append(value[0])
    settings['filament_colour'][3]='#008800'
    return settings


def test_one_model_material_plus_different_support_is_legitimate():
    from figuraforge.services.mixed_filament import _part_filament_defaults
    settings=_four_slot_template();settings.update(support_filament='4',support_interface_filament='4')
    part=_routing_part();mapping={part.id:dict(enumerate([2]*len(part.mesh.faces)))}
    result=_part_filament_defaults([part],mapping,settings)['nose']
    assert result['default_extruder']==2
    assert result['physical_slots_including_support']==[2,4]
    assert settings['support_filament']=='4'


def test_mixed_two_bases_plus_third_support_blocks_before_conversion(tmp_path):
    from figuraforge.services.mixed_filament import build_native_from_parts
    settings=_four_slot_template();settings.update(printer_model='Bambu Lab H2D',nozzle_diameter=['0.4','0.4'],support_filament='4')
    path=tmp_path/'template.3mf';_template_archive(path,settings)
    part=_routing_part();output=tmp_path/'blocked.3mf'
    with pytest.raises(MixedFilamentError,match='plus support/interface'):
        build_native_from_parts(path,output,[part],None,settings,{'nose':[3]*len(part.mesh.faces)},executable='/nonexistent/must-not-run')
    assert not output.exists()


def test_native_object_support_override_cannot_add_third_spool():
    from figuraforge.services.mixed_filament import _part_filament_defaults,_assign_object_filaments,MODEL_SETTINGS_PATH
    settings=_four_slot_template();part=_routing_part()
    defaults=_part_filament_defaults([part],{'nose':dict(enumerate([3]*len(part.mesh.faces)))},settings)
    contents={MODEL_SETTINGS_PATH:b'<config><object id="2"><metadata key="support_interface_filament" value="4"/><part id="1"/></object></config>'}
    before=contents.copy()
    with pytest.raises(MixedFilamentError,match='plus support/interface'):
        _assign_object_filaments(contents,{'nose':'2'},defaults,settings)
    assert contents==before


def test_physical_default_weights_surface_area_instead_of_face_count():
    import numpy as np
    import trimesh
    from figuraforge.services.mixed_filament import _part_filament_defaults
    part=_routing_part();part.mesh=trimesh.creation.box(extents=[10,1,1])
    large=np.argsort(part.mesh.area_faces)[-5:]
    mapping={index:2 if index in large else 1 for index in range(len(part.mesh.faces))}
    assert list(mapping.values()).count(2)<list(mapping.values()).count(1)
    result=_part_filament_defaults([part],{'nose':mapping},template())['nose']
    assert result['default_extruder']==2


def test_gui_process_inheritance_tracks_only_intentional_allowlisted_edits():
    from copy import deepcopy
    from figuraforge.services.mixed_filament import mark_explicit_process_overrides
    source=template()
    source.update(raft_layers='0',brim_type='auto_brim',support_filament='0',support_interface_filament='0',
                  layer_height='0.2',different_settings_to_system=['enable_support','physical-a','physical-b','mixed-c','machine'])
    changed=deepcopy(source)
    changed.update(raft_layers='3',brim_type='outer_only',support_filament='2',support_interface_filament='2',
                   layer_height='0.12',machine_start_gcode='do not classify',nozzle_temperature=['123','234','345'])
    before=deepcopy(changed)
    result=mark_explicit_process_overrides(changed,source)
    process=set(result['different_settings_to_system'][0].split(';'))
    assert {'enable_support','raft_layers','brim_type','support_filament','support_interface_filament','layer_height'}<=process
    assert 'machine_start_gcode' not in process and 'nozzle_temperature' not in process
    assert result['different_settings_to_system'][1:]==source['different_settings_to_system'][1:]
    assert changed==before
    assert mark_explicit_process_overrides(source,source)==source


def test_process_diff_groups_reject_unknown_dimensions():
    from figuraforge.services.mixed_filament import mark_explicit_process_overrides
    source=template();source['raft_layers']='0'
    changed={**source,'raft_layers':'3','different_settings_to_system':['too short']}
    with pytest.raises(MixedFilamentError,match='difference groups'):
        mark_explicit_process_overrides(changed,source)


def test_explicit_empty_h2d_nozzle_inventory_is_rejected_before_export():
    config=template();config.update(printer_model='Bambu Lab H2D',nozzle_diameter=['0.4','0.4'],extruder_nozzle_stats=[])
    before=deepcopy(config)
    with pytest.raises(MixedFilamentError,match='leere Duesen-Hardwareliste'):
        validate_native_settings(config)
    assert config==before


def test_absent_hardware_inventory_does_not_invent_defaults_for_minimal_schema():
    config=template();before=deepcopy(config)
    assert validate_native_settings(config)['slot_count']==3
    assert config==before and 'extruder_nozzle_stats' not in config
    config['extruder_nozzle_stats']=['Standard#1','Standard#1']
    assert validate_native_settings(config)['physical_slots']==[1,2]

def test_inspector_accepts_physical_only_profile_without_inventing_virtual_slots(tmp_path):
    from figuraforge.services.mixed_filament import inspect_template
    source=template();source.update(printer_model='Bambu Lab H2D',nozzle_diameter=['0.4','0.4'],enable_mixed_color_sublayer='0',filament_is_mixed=['0']*3,filament_mixed_components=['']*3,filament_mixed_sublayer_ratios=['']*3,filament_type=['PLA']*3)
    path=tmp_path/'physical-only.3mf';_template_archive(path,source)
    result=inspect_template(path)
    assert result['physical_only'] and not result['mixed_supported'] and result['mixed_slots']==[]
    assert [x['slot'] for x in result['basis_filaments']]==[1,2,3]
    assert result['config']['filament_is_mixed']==['0']*3
    with pytest.raises(MixedFilamentError,match='Mixed template needs'):inspect_template(path,require_mixed=True)


def test_native_builder_physical_only_profile_reaches_actual_conversion_without_fake_mix(tmp_path,monkeypatch):
    import subprocess,trimesh
    from figuraforge.geometry.types import Part
    from figuraforge.services.mixed_filament import build_native_from_parts
    source=template();source.update(printer_model='Bambu Lab H2D',nozzle_diameter=['0.4','0.4'],enable_mixed_color_sublayer='0',filament_is_mixed=['0']*3,filament_mixed_components=['']*3,filament_mixed_sublayer_ratios=['']*3,printable_area=['0x0','100x0','100x100','0x100'],extruder_printable_area=[['0x0','100x0','100x100','0x100']]*2,printable_height='100')
    path=tmp_path/'physical-only.3mf';_template_archive(path,source)
    mesh=trimesh.creation.box();mesh.apply_translation([10,10,.5]);part=Part('piece','Piece',mesh,'#FFEECC')
    class ConversionReached(Exception):pass
    def stop(*args,**kwargs):raise ConversionReached()
    monkeypatch.setattr(subprocess,'run',stop)
    with pytest.raises(ConversionReached):build_native_from_parts(path,tmp_path/'new.3mf',[part],None,source,{'piece':[2]*len(mesh.faces)})
    assert source['filament_is_mixed']==['0']*3

def test_explicit_prime_tower_width_survives_without_thermal_or_gcode_override():
    from figuraforge.services.mixed_filament import mark_explicit_process_overrides
    source=template();source.update(prime_tower_width='60',wipe_tower_x=['100'],wipe_tower_y=['100'],nozzle_temperature=['220','220'],different_settings_to_system=['']*5)
    changed=deepcopy(source);changed.update(prime_tower_width='35',wipe_tower_x=['320'],wipe_tower_y=['240'])
    before=deepcopy(changed);result=mark_explicit_process_overrides(changed,source)
    keys=set(result['different_settings_to_system'][0].split(';'))
    assert {'prime_tower_width','wipe_tower_x','wipe_tower_y'}<=keys
    assert 'nozzle_temperature' not in keys and 'machine_start_gcode' not in keys
    assert result['nozzle_temperature']==source['nozzle_temperature']
    assert result['machine_start_gcode']==source['machine_start_gcode'] and changed==before
