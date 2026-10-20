"""Conservative Bambu native mixed-slot contract; no machine presets invented.

Ratios are optical sublayer recipes, not RGB interpolation or pigment mixing.
Only an existing native project's mixed slots are edited. Unknown settings and
physical filament profiles remain untouched. Validation is not print approval.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import zipfile

SETTINGS_PATH = 'Metadata/project_settings.config'
MODEL_SETTINGS_PATH = 'Metadata/model_settings.config'
ARRAYS = ('filament_is_mixed', 'filament_mixed_components',
          'filament_mixed_sublayer_ratios', 'filament_mixed_gradient',
          'filament_mixed_gradient_range', 'filament_mixed_gradient_curve',
          'filament_mixed_gradient_per_part')
MIN_COMPONENT_PERCENT = 10  # BambuStudio MixedFilamentDialog.cpp, 2026-10-16


class MixedFilamentError(ValueError):
    pass


@dataclass(frozen=True)
class MixRecipe:
    component_slots: tuple[int, int]
    first_percent: int

    def __post_init__(self):
        if (len(self.component_slots) != 2 or
                any(type(n) is not int or n < 1 for n in self.component_slots) or
                len(set(self.component_slots)) != 2):
            raise MixedFilamentError('Two distinct 1-based physical filament slots required')
        if type(self.first_percent) is not int or not 10 <= self.first_percent <= 90:
            raise MixedFilamentError('Bambu UI-compatible mixed ratios require 10–90%; use physical slots for pure colors')

    @property
    def ratios(self) -> str:
        return f'{self.first_percent / 100:.2f},{(100-self.first_percent) / 100:.2f}'

    def describe(self) -> dict:
        return {**asdict(self), 'percentages': [self.first_percent, 100-self.first_percent],
                'native_components': ','.join(map(str, self.component_slots)),
                'native_ratios': self.ratios,
                'color_prediction': 'uncalibrated; a printed swatch is required'}


def recipe_library(component_slots=(1, 2), step_percent=5) -> list[MixRecipe]:
    """17 UI-compatible recipes at 5% intervals. Pure colors use original slots."""
    if type(step_percent) is not int or step_percent < 1 or 80 % step_percent:
        raise MixedFilamentError('Step must divide the supported 10–90% interval')
    return [MixRecipe(tuple(component_slots), p) for p in range(10, 91, step_percent)]


def _flag(value):
    if value in ('1', True, 1):
        return True
    if value in ('0', False, 0):
        return False
    raise MixedFilamentError('Invalid Bambu boolean setting')


def validate_native_settings(settings: dict, *, nozzle_count=2) -> dict:
    """Reject references to virtual slots and profiles with unsupported ratios.

    nozzle_count is the product's chosen component limit, not a claim that AMS
    capacity equals nozzle count. H2D is limited here to two recipe components.
    """
    if type(nozzle_count) is not int or nozzle_count != 2:
        raise MixedFilamentError('Only the two-component H2D contract is currently verified')
    if 'extruder_nozzle_stats' in settings and settings['extruder_nozzle_stats']==[]:
        raise MixedFilamentError('Die native H2D-Vorlage enthaelt eine leere Duesen-Hardwareliste (extruder_nozzle_stats). In Bambu Studio die zwei installierten Duesen waehlen und die Vorlage neu speichern; reine Maschinen-/Filamentprofile reichen nicht fuer das Slicing.')
    flags = settings.get('filament_is_mixed')
    if not isinstance(flags, list) or not flags:
        raise MixedFilamentError('Native template has no filament_is_mixed slot array')
    count = len(flags)
    if count > 32:
        raise MixedFilamentError('More than 32 total filament slots is not supported by this contract')
    for key in ARRAYS:
        if not isinstance(settings.get(key), list) or len(settings[key]) != count:
            raise MixedFilamentError(f'Native slot array length mismatch: {key}')
    colors = settings.get('filament_colour')
    if not isinstance(colors, list) or len(colors) != count:
        raise MixedFilamentError('Native filament colors must cover all slots')
    mixed = [_flag(value) for value in flags]
    recipes = []
    for index, is_mixed in enumerate(mixed):
        if not is_mixed:
            continue
        if not _flag(settings.get('enable_mixed_color_sublayer', '0')):
            raise MixedFilamentError('Mixed color sublayers are disabled')
        try:
            slots = tuple(int(token) for token in settings['filament_mixed_components'][index].split(','))
            ratios = tuple(Decimal(token) for token in settings['filament_mixed_sublayer_ratios'][index].split(','))
        except (ValueError, InvalidOperation, AttributeError):
            raise MixedFilamentError('Invalid native mixed recipe encoding') from None
        if (len(slots) != 2 or len(set(slots)) != 2 or
                any(slot < 1 or slot > count or mixed[slot-1] for slot in slots)):
            raise MixedFilamentError('Mixed recipes must reference two existing physical slots')
        if (len(ratios) != 2 or any(not ratio.is_finite() or ratio < Decimal('.10') or ratio > Decimal('.90') for ratio in ratios)
                or sum(ratios) != 1):
            raise MixedFilamentError('Mixed ratios must be finite 10–90% values summing to 1')
        if _flag(settings['filament_mixed_gradient'][index]):
            raise MixedFilamentError('Z-direction gradient templates require separate validation; constant region recipes expected')
        recipes.append({'slot': index+1, 'component_slots': slots, 'ratios': tuple(str(r) for r in ratios)})
    return {'slot_count': count, 'physical_slots': [i+1 for i, flag in enumerate(mixed) if not flag],
            'mixed_slots': recipes, 'native_roundtrip_verified': False, 'slicing_verified': False}


def read_native_template(path: Path) -> tuple[dict, dict]:
    """Read only bounded native metadata; never extract arbitrary archive paths."""
    settings = _template_settings(path)
    return settings, validate_native_settings(settings)


def apply_recipes_to_template(settings: dict, assignments: dict[int, MixRecipe]) -> dict:
    """Return a copy; edit existing mixed slots only, preserving profiles/unknown keys."""
    report = validate_native_settings(settings)
    mixed_slots = {row['slot'] for row in report['mixed_slots']}
    result = deepcopy(settings)
    for slot, recipe in assignments.items():
        if type(slot) is not int or slot not in mixed_slots:
            raise MixedFilamentError('Recipe destination must be an existing native mixed slot')
        result['filament_mixed_components'][slot-1] = ','.join(map(str, recipe.component_slots))
        result['filament_mixed_sublayer_ratios'][slot-1] = recipe.ratios
    validate_native_settings(result)
    return result


def verify_native_roundtrip(expected: dict, actual: dict) -> dict:
    """Compare metadata from a genuine Bambu CLI/GUI save, not a Python ZIP copy."""
    validate_native_settings(expected)
    validate_native_settings(actual)
    keys = (*ARRAYS, 'enable_mixed_color_sublayer', 'filament_colour')
    mismatched = [key for key in keys if expected.get(key) != actual.get(key)]
    if mismatched:
        raise MixedFilamentError('Bambu roundtrip changed mixed slot settings: ' + ', '.join(mismatched))
    return {'mixed_settings_preserved': True, 'slicing_verified': False,
            'physical_color_verified': False,
            'scope': 'Metadata comparison only; printer profile, object assignment and sliced paths need independent checks'}


# Official Model.cpp CONST_FILAMENTS: full, unsplit triangle slot annotation.
_PAINT_CODES = ('', '4', '8', '0C', '1C', '2C', '3C', '4C', '5C', '6C',
                '7C', '8C', '9C', 'AC', 'BC', 'CC', 'DC', 'EC', '0FC',
                '1FC', '2FC', '3FC', '4FC', '5FC', '6FC', '7FC', '8FC',
                '9FC', 'AFC', 'BFC', 'CFC', 'DFC', 'EFC')


def attach_native_painting(source: Path, output: Path, settings: dict,
                           paintings: list[dict]) -> dict:
    """Write native slot settings and full-face painting to a NEW native 3MF.

    painting = {model_path: '3D/Objects/object_1.model', object_id: '1',
                expected_triangle_count: 1200, face_slots: {0: 3, 17: 4}}
    Face indices are 0-based in this exact object's triangle order. Slots are
    1-based native filament slots. Existing unselected painting is preserved.
    Source topology must be the reviewed plan's topology; no implicit nearest
    face transfer or remesh is performed here.
    """
    from xml.etree import ElementTree as ET
    ET.register_namespace('', 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02')
    source, output = Path(source), Path(output)
    if output.exists() or source.resolve() == output.resolve():
        raise MixedFilamentError('Output must be a new path; source is never overwritten')
    report = validate_native_settings(settings)
    replacements = {}
    selected = set()
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist()
        if len({i.filename for i in entries}) != len(entries):
            raise MixedFilamentError('Duplicate archive paths are not accepted')
        if sum(i.file_size for i in entries) > 512_000_000:
            raise MixedFilamentError('Native project exceeds bounded archive size')
        if MODEL_SETTINGS_PATH not in archive.namelist():
            raise MixedFilamentError('A native Bambu object-assignment template is required')
        for painting in paintings:
            name = painting['model_path']
            if not name.startswith('3D/') or not name.endswith('.model') or '..' in Path(name).parts:
                raise MixedFilamentError('Painting target must be a native model member')
            if (name, str(painting['object_id'])) in selected:
                raise MixedFilamentError('Duplicate painting target')
            selected.add((name, str(painting['object_id'])))
            root = ET.fromstring(replacements.get(name, archive.read(name)))
            ns = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
            obj = next((o for o in root.findall(f'{ns}resources/{ns}object')
                        if o.get('id') == str(painting['object_id'])), None)
            if obj is None:
                raise MixedFilamentError('Painting object id does not exist in model member')
            triangles = obj.findall(f'{ns}mesh/{ns}triangles/{ns}triangle')
            if len(triangles) != painting['expected_triangle_count']:
                raise MixedFilamentError('Painting topology changed: triangle count mismatch')
            for face_index, slot in painting['face_slots'].items():
                if type(face_index) is not int or not 0 <= face_index < len(triangles):
                    raise MixedFilamentError('Painting face index outside reviewed mesh')
                if type(slot) is not int or not 1 <= slot <= report['slot_count']:
                    raise MixedFilamentError('Painting references nonexistent filament slot')
                triangles[face_index].set('paint_color', _PAINT_CODES[slot])
            replacements[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)
        replacements[SETTINGS_PATH] = json.dumps(settings, ensure_ascii=False, indent=2).encode()
        output.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive create prevents accidental overwrite even with concurrent jobs.
        with output.open('xb') as target, zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as result:
            for item in entries:
                result.writestr(item, replacements.pop(item.filename, None) or archive.read(item))
            for name, data in replacements.items():
                result.writestr(name, data)
    return {'output': str(output), 'painted_objects': len(selected),
            'native_roundtrip_verified': False, 'slicing_verified': False}


def validate_part_filament_limits(settings: dict, part_slots: dict[str, list[int]],
                                  *, maximum_physical_filaments=2) -> dict:
    """Expand virtual recipes and limit EACH assembled part, not the whole figure."""
    report = validate_native_settings(settings)
    if maximum_physical_filaments != 2:
        raise MixedFilamentError('Only the requested two-base-filament part limit is supported')
    recipes = {row['slot']: set(row['component_slots']) for row in report['mixed_slots']}
    result = {}
    for part, slots in part_slots.items():
        physical = set()
        for slot in slots:
            if type(slot) is not int or not 1 <= slot <= report['slot_count']:
                raise MixedFilamentError('Part references an unknown native filament slot')
            physical.update(recipes.get(slot, {slot}))
        if len(physical) > maximum_physical_filaments:
            raise MixedFilamentError(f'Part {part} uses {len(physical)} physical filaments; split or reassign this part')
        result[part] = sorted(physical)
    return {'physical_slots_per_part': result, 'limit': maximum_physical_filaments,
            'whole_figure_color_limit': False}


def _checked_archive(path: Path):
    """Return bounded ZIP contents, rejecting traversal, links and encrypted entries."""
    from pathlib import PurePosixPath
    import stat
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if len(infos) > 4096 or len({i.filename for i in infos}) != len(infos):
            raise MixedFilamentError('Too many or duplicate native archive members')
        if sum(i.file_size for i in infos) > 512_000_000:
            raise MixedFilamentError('Native project exceeds 512 MB uncompressed limit')
        contents = {}
        for info in infos:
            name = info.filename
            if ('\\' in name or name.startswith('/') or ':' in name or
                    '..' in PurePosixPath(name).parts or
                    stat.S_ISLNK(info.external_attr >> 16) or info.flag_bits & 1):
                raise MixedFilamentError('Unsafe native archive member')
            limit = 8_000_000 if name.endswith(('.config', '.json')) else 256_000_000
            if info.file_size > limit:
                raise MixedFilamentError('Native archive member exceeds size limit')
            if not info.is_dir():
                contents[name] = archive.read(info)
        return contents


def inspect_template(path: Path, *, require_mixed: bool = False) -> dict:
    """Sanitized H2D-template preview. Never returns G-code, URLs or arbitrary config.

    Physical-only projects are valid for solid plans. ``require_mixed=True``
    additionally requires two base slots and an existing validated recipe.
    This does not certify the physical printer or GUI/slicer acceptance.
    """
    from xml.etree import ElementTree as ET
    settings = _template_settings(path)
    if not isinstance(settings, dict):
        raise MixedFilamentError('Native project settings must be a JSON object')
    if settings.get('printer_model') != 'Bambu Lab H2D':
        raise MixedFilamentError('Template must use the Bambu Lab H2D printer model')
    nozzles = settings.get('nozzle_diameter')
    try:
        correct_nozzles = (isinstance(nozzles, list) and len(nozzles) == 2 and
                           all(Decimal(str(n)).is_finite() and Decimal(str(n)) > 0 for n in nozzles))
    except InvalidOperation:
        correct_nozzles = False
    if not correct_nozzles:
        raise MixedFilamentError('H2D template must contain exactly two valid nozzle diameters')
    report = validate_native_settings(settings)
    if not report['physical_slots']:
        raise MixedFilamentError('Template needs at least one physical filament profile')
    if require_mixed and (len(report['physical_slots']) < 2 or not report['mixed_slots']):
        raise MixedFilamentError('Mixed template needs at least two physical and one existing mixed slot')
    # Allowlist deliberately excludes settings IDs, user names, G-code, paths,
    # network addresses, account metadata and arbitrary custom profile fields.
    keys = (*ARRAYS, 'filament_colour', 'enable_mixed_color_sublayer',
            'printer_model', 'nozzle_diameter', 'filament_type', 'filament_vendor')
    safe_config = {key: deepcopy(settings[key]) for key in keys if key in settings}
    basis = []
    for slot in report['physical_slots']:
        item = {'slot': slot, 'color': settings['filament_colour'][slot-1]}
        for key, target in [('filament_type','material'), ('filament_vendor','vendor')]:
            values = settings.get(key, [])
            if isinstance(values, list) and len(values) >= slot:
                # Treat profile strings as data, bounded for UI rendering.
                item[target] = str(values[slot-1])[:120]
        basis.append(item)
    models = _stream_model_counts(path)
    return {'printer_model': 'Bambu Lab H2D', 'nozzle_count': 2,
            'config': safe_config, 'basis_filaments': basis,
            'mixed_slots': report['mixed_slots'], 'models': models,
            'mixed_supported': bool(report['mixed_slots']), 'physical_only': not bool(report['mixed_slots']),
            'native_roundtrip_verified': False, 'slicing_verified': False}



_SUPPORT_KEYS = ('support_filament', 'support_interface_filament')


def _support_material_scope(settings, model_physical, default_slot, overrides=None):
    """AUTO resolves to the physical object default; explicit support may add one spool."""
    overrides=overrides or {};effective={};used=set(model_physical)
    mixed=validate_native_settings(settings)
    recipes={row['slot']:set(row['component_slots']) for row in mixed['mixed_slots']}
    for key in _SUPPORT_KEYS:
        raw=overrides.get(key,settings.get(key,'0'))
        if isinstance(raw,bool) or not str(raw).isdigit():
            raise MixedFilamentError(f'Invalid native support filament setting: {key}')
        slot=int(raw)
        if slot<0 or slot>mixed['slot_count']:
            raise MixedFilamentError(f'Support references nonexistent filament slot: {key}')
        physical=recipes.get(slot,{slot}) if slot else {default_slot}
        used.update(physical);effective[key]={'native_slot':slot,'physical_slots':sorted(physical)}
    if len(used)>2:
        raise MixedFilamentError('Part plus support/interface uses more than 2 physical filaments; reassign support or split the part')
    return {'support_routing':effective,'physical_slots_including_support':sorted(used)}


def _part_filament_defaults(parts, mappings, settings):
    """Area-weighted actual physical defaults; never leave converter's arbitrary slot 1."""
    report=validate_native_settings(settings)
    recipes={row['slot']:row for row in report['mixed_slots']};result={}
    for part in parts:
        weights={}
        for face,slot in mappings[part.id].items():
            area=float(part.mesh.area_faces[face])
            recipe=recipes.get(slot)
            components=zip(recipe['component_slots'],map(float,recipe['ratios'])) if recipe else [(slot,1.)]
            for physical,ratio in components:weights[physical]=weights.get(physical,0.)+area*ratio
        if not weights or any(not (value>=0 and value<float('inf')) for value in weights.values()):
            raise MixedFilamentError('Cannot determine a finite physical filament default')
        dominant=min(weights,key=lambda slot:(-weights[slot],slot))
        result[part.id]={'default_extruder':dominant,'physical_slots':sorted(weights),
                         'physical_surface_weights_mm2':weights,
                         **_support_material_scope(settings,set(weights),dominant)}
    return result


def _assign_object_filaments(contents, object_ids, defaults, settings):
    """Set object AND volume defaults; preserve support choices, gate their physical union."""
    from xml.etree import ElementTree as ET
    root=ET.fromstring(contents[MODEL_SETTINGS_PATH]);objects={obj.get('id'):obj for obj in root.findall('object')}
    report={}
    for part_id,object_id in object_ids.items():
        obj=objects.get(str(object_id))
        if obj is None:raise MixedFilamentError('Missing converted object metadata for filament default')
        parts=obj.findall('part')
        if len(parts)!=1:raise MixedFilamentError('Exactly one native volume per physical part required')
        values=defaults[part_id];overrides={}
        for element in [obj,*parts]:
            for item in element.findall('metadata'):
                if item.get('key') in _SUPPORT_KEYS:overrides[item.get('key')]=item.get('value')
        scope=_support_material_scope(settings,set(values['physical_slots']),values['default_extruder'],overrides)
        for element in [obj,*parts]:
            entries=[item for item in element.findall('metadata') if item.get('key')=='extruder']
            if len(entries)>1:raise MixedFilamentError('Duplicate native extruder metadata')
            entry=entries[0] if entries else ET.SubElement(element,'metadata',{'key':'extruder'})
            entry.set('value',str(values['default_extruder']))
        report[part_id]={**values,**scope}
    contents[MODEL_SETTINGS_PATH]=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    return report


def build_native_from_parts(template_path: Path, output: Path, parts: list,
                            placements: list[dict] | None, settings: dict,
                            face_slots: dict[str, list[int] | dict[int, int]],
                            *, executable='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio') -> dict:
    """Experimental native export via real Bambu conversion of new Core geometry.

    No mixed source is passed to CLI, no slicing or printer communication occurs.
    Final native settings/painting require an independent GUI acceptance check.
    Every source triangle is matched in-order within 0.001 mm after translation;
    changed/reordered topology aborts instead of guessing a face mapping.
    """
    import copy
    import subprocess
    import tempfile
    import numpy as np
    from xml.etree import ElementTree as ET
    from .export import write_3mf
    preview = inspect_template(template_path, require_mixed=False)
    settings = mark_explicit_process_overrides(settings, _template_settings(template_path))
    validate_native_settings(settings)
    if settings.get('printer_model') != 'Bambu Lab H2D' or settings.get('nozzle_diameter') != preview['config']['nozzle_diameter']:
        raise MixedFilamentError('Export hardware must match the inspected H2D template')
    output = Path(output)
    if output.exists():
        raise MixedFilamentError('Native output must be a new path')
    if not parts or len({p.id for p in parts}) != len(parts):
        raise MixedFilamentError('Nonempty, uniquely identified printable parts required')
    if set(face_slots) != {p.id for p in parts}:
        raise MixedFilamentError('Explicit face-slot assignment is required for every exported part')
    part_used_slots = {}
    mappings = {}
    for part in parts:
        raw = face_slots[part.id]
        mapping = dict(enumerate(raw)) if isinstance(raw, list) else dict(raw)
        if set(mapping) != set(range(len(part.mesh.faces))):
            raise MixedFilamentError('Every source triangle needs an explicit filament slot')
        mappings[part.id] = mapping
        part_used_slots[part.id] = list(set(mapping.values()))
    validate_part_filament_limits(settings, part_used_slots)
    filament_defaults = _part_filament_defaults(parts, mappings, settings)
    plate_validation = validate_plate_parts(parts, placements, settings)
    output.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='native-build-', dir=output.parent))
    core, native = work/'geometry-core.3mf', work/'geometry-native.3mf'
    named = []
    for part in parts:
        item = copy.copy(part); item.name = part.id; named.append(item)
    write_3mf(named, core, placements)
    try:
        result = subprocess.run([str(executable), '--export-3mf', str(native.resolve()),
                                 '--arrange', '0', '--orient', '0', str(core.resolve())],
                                capture_output=True, text=True, timeout=90, cwd=work)
    except subprocess.TimeoutExpired:
        raise MixedFilamentError('Local Bambu native geometry conversion exceeded 90 seconds') from None
    (work/'geometry-conversion.log').write_text(result.stdout+result.stderr)
    if result.returncode or not native.exists():
        raise MixedFilamentError(f'Local Bambu native geometry conversion failed (exit {result.returncode}); see derived conversion log')
    import trimesh
    from scipy.spatial import cKDTree
    source_scene = trimesh.load_scene(core)
    native_scene = trimesh.load_scene(native)
    def world_vertices(scene):
        points=[]
        for node in scene.graph.nodes_geometry:
            transform,key=scene.graph[node]
            points.append(trimesh.transform_points(scene.geometry[key].vertices,transform))
        return np.vstack(points)
    source_world,native_world=world_vertices(source_scene),world_vertices(native_scene)
    world_error=max(float(cKDTree(source_world).query(native_world)[0].max()),
                    float(cKDTree(native_world).query(source_world)[0].max()))
    if not np.isfinite(world_error) or world_error>.001:
        raise MixedFilamentError('Native conversion changed world placement or geometry')
    contents = _checked_archive(native)
    ns = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
    models = {name: ET.fromstring(data) for name,data in contents.items() if name.startswith('3D/') and name.endswith('.model')}
    root_path = '3D/3dmodel.model'
    meta = ET.fromstring(contents[MODEL_SETTINGS_PATH])
    by_name = {}
    for obj in meta.findall('object'):
        name = next((m.get('value') for m in obj.findall('metadata') if m.get('key') == 'name'), None)
        if name in by_name:
            raise MixedFilamentError('Ambiguous native object names after conversion')
        by_name[name] = obj.get('id')
    def mesh_object(path, object_id):
        root = models.get(path)
        if root is None: raise MixedFilamentError('Missing native geometry member')
        obj = next((o for o in root.findall(f'{ns}resources/{ns}object') if o.get('id') == object_id),None)
        if obj is None: raise MixedFilamentError('Missing converted native object id')
        if obj.find(f'{ns}mesh') is not None: return path,obj
        components = obj.findall(f'{ns}components/{ns}component')
        if len(components) != 1:
            raise MixedFilamentError('Expected one native geometry component per source part')
        comp = components[0]
        # The native Bambu converter uses a production-extension absolute path.
        child_path = next((v for k,v in comp.attrib.items() if k.endswith('}path') or k=='path'),path).lstrip('/')
        if child_path == path and comp.get('objectid') == object_id:
            raise MixedFilamentError('Cyclic native component reference')
        child_root=models.get(child_path)
        if child_root is None: raise MixedFilamentError('Missing native child model')
        child=next((o for o in child_root.findall(f'{ns}resources/{ns}object') if o.get('id')==comp.get('objectid')),None)
        if child is None or child.find(f'{ns}mesh') is None:
            raise MixedFilamentError('Unsupported nested native geometry mapping')
        return child_path,child
    paintings=[]; checks=[]
    for part in parts:
        if part.id not in by_name: raise MixedFilamentError('Converted part name lost')
        path,obj=mesh_object(root_path,by_name[part.id])
        mesh=obj.find(f'{ns}mesh')
        vertices=np.array([[float(v.get(c)) for c in ('x','y','z')] for v in mesh.findall(f'{ns}vertices/{ns}vertex')])
        triangles=np.array([[int(t.get(c)) for c in ('v1','v2','v3')] for t in mesh.findall(f'{ns}triangles/{ns}triangle')])
        original=np.asarray(part.mesh.vertices)[np.asarray(part.mesh.faces)]
        if triangles.shape != np.asarray(part.mesh.faces).shape:
            raise MixedFilamentError('Native conversion changed triangle count')
        actual=vertices[triangles]
        # The writer centers each part; translation changes are harmless for the
        # annotation but rotations/reordering are rejected, never inferred.
        original=original-(part.mesh.bounds.mean(axis=0))
        actual=actual-(vertices.min(axis=0)+vertices.max(axis=0))/2
        error=float(np.max(np.abs(original-actual)))
        if not np.isfinite(error) or error>.001:
            raise MixedFilamentError('Native conversion changed triangle order or geometry; painting aborted')
        paintings.append({'model_path':path,'object_id':obj.get('id'),
                          'expected_triangle_count':len(triangles),'face_slots':mappings[part.id]})
        checks.append({'part_id':part.id,'triangles':len(triangles),'ordered_vertex_error_mm':error})
    # New native geometry/model assignments come from Bambu's own conversion.
    # The complete existing project config brings actual H2D/material settings.
    contents[SETTINGS_PATH]=json.dumps(settings,ensure_ascii=False,indent=2).encode()
    material_routing = _assign_object_filaments(contents, {part.id:by_name[part.id] for part in parts}, filament_defaults, settings)
    _assign_printable_plate(contents, [by_name[part.id] for part in parts])
    merged=work/'native-before-painting.3mf'
    with zipfile.ZipFile(merged,'x',zipfile.ZIP_DEFLATED) as archive:
        for name,data in contents.items(): archive.writestr(name,data)
    result=attach_native_painting(merged,output,settings,paintings)
    return {**result,'geometry_conversion_verified':True,'geometry_checks':checks,
            'world_vertex_error_mm':world_error,
            'plate_validation':plate_validation,'printable_instances_assigned':len(parts),
            'physical_material_routing':material_routing,
            'profile_source':'existing H2D template project settings',
            'experimental':True,'gui_verification_required':True,
            'work_directory':str(work)}


def _template_catalog(archive):
    """Validate central-directory entries without opening auxiliary user files."""
    from pathlib import PurePosixPath
    import stat
    infos=archive.infolist()
    if len(infos)>4096 or len({i.filename for i in infos})!=len(infos):
        raise MixedFilamentError('Too many or duplicate native archive members')
    if sum(i.file_size for i in infos)>4_000_000_000:
        raise MixedFilamentError('Native template exceeds 4 GB uncompressed limit')
    for info in infos:
        name=info.filename
        if ('\\' in name or name.startswith('/') or ':' in name or '..' in PurePosixPath(name).parts
                or stat.S_ISLNK(info.external_attr>>16) or info.flag_bits&1):
            raise MixedFilamentError('Unsafe native archive member')
        if name.startswith('3D/') and name.endswith('.model') and info.file_size>2_000_000_000:
            raise MixedFilamentError('Native model exceeds 2 GB streaming limit')
        if name in (SETTINGS_PATH,MODEL_SETTINGS_PATH) and info.file_size>8_000_000:
            raise MixedFilamentError('Native settings exceed 8 MB limit')
    return {i.filename:i for i in infos}


def _template_settings(path):
    with zipfile.ZipFile(path) as archive:
        infos=_template_catalog(archive)
        if SETTINGS_PATH not in infos or MODEL_SETTINGS_PATH not in infos:
            raise MixedFilamentError('Native Bambu project settings and object assignments are required')
        settings=json.loads(archive.read(infos[SETTINGS_PATH]))
    if not isinstance(settings,dict):
        raise MixedFilamentError('Native project settings must be a JSON object')
    return settings


def _stream_model_counts(path):
    """Constant-memory XML statistics; private auxiliary assets are never read."""
    from xml.parsers import expat
    import time
    models=[];deadline=time.monotonic()+120
    with zipfile.ZipFile(path) as archive:
        infos=_template_catalog(archive)
        for name,info in infos.items():
            if not name.startswith('3D/') or not name.endswith('.model'):continue
            parser=expat.ParserCreate(namespace_separator='}')
            state={'object':None,'mesh':False,'count':0}
            def local(tag):return tag.rsplit('}',1)[-1]
            def start(tag,attrs):
                tag=local(tag)
                if tag=='object':state.update(object=attrs.get('id'),mesh=False,count=0)
                elif tag=='mesh':state['mesh']=True
                elif tag=='triangle' and state['mesh']:state['count']+=1
            def end(tag):
                if local(tag)=='object':
                    if state['mesh']:models.append({'model_path':name,'object_id':state['object'],'triangle_count':state['count']})
                    state.update(object=None,mesh=False,count=0)
            def forbidden(*args):raise MixedFilamentError('DTD/entity declarations are not accepted')
            parser.StartElementHandler=start;parser.EndElementHandler=end
            parser.StartDoctypeDeclHandler=forbidden;parser.EntityDeclHandler=forbidden
            with archive.open(info) as stream:
                while chunk:=stream.read(256*1024):
                    if time.monotonic()>deadline:raise MixedFilamentError('Native template XML inspection exceeded 120 seconds')
                    parser.Parse(chunk,False)
                parser.Parse(b'',True)
    return models


def make_profile_template(source: Path, output: Path) -> dict:
    """Create a small NEW profile-only template; copy no geometry or auxiliary images.

    Project settings may include operational printer/filament G-code. They stay
    local and are preserved for compatibility; the sanitized preview omits them.
    This helper creates no executable jobs and invokes no external application.
    """
    import hashlib
    source,output=Path(source),Path(output)
    settings=_template_settings(source)
    validate_native_settings(settings)
    if settings.get('printer_model')!='Bambu Lab H2D' or len(settings.get('nozzle_diameter',[]))!=2:
        raise MixedFilamentError('H2D two-nozzle template required')
    if output.exists() or output.resolve()==source.resolve():raise MixedFilamentError('Profile output must be a new file')
    model=b'<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources/><build/></model>'
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as file,zipfile.ZipFile(file,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(SETTINGS_PATH,json.dumps(settings,ensure_ascii=False))
        archive.writestr(MODEL_SETTINGS_PATH,'<?xml version="1.0"?><config/>')
        archive.writestr('3D/3dmodel.model',model)
        archive.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/></Types>')
        archive.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    return {'output':str(output),'profile_only':True,'geometry_copied':False,'auxiliary_assets_copied':False,'bytes':output.stat().st_size}


def validate_plate_parts(parts, placements, settings) -> dict:
    """Conservative actual H2D bed/exclusion/dual-nozzle world-space check.

    Mixed parts use both nozzles, so require the intersection of both nozzle
    envelopes. We use each part's convex XY footprint: a conservative refusal
    is preferable to marking out-of-volume geometry printable.
    """
    import numpy as np
    from shapely.geometry import Polygon, MultiPoint
    def polygon(raw,label):
        try:
            if isinstance(raw,str):raw=raw.split(',')
            points=[tuple(float(c) for c in token.split('x')) for token in raw]
            poly=Polygon(points)
            if any(len(p)!=2 for p in points) or not poly.is_valid or poly.area<=0:raise ValueError()
            return poly
        except (TypeError,ValueError):raise MixedFilamentError(f'Invalid {label} polygon') from None
    area=polygon(settings.get('printable_area'),'printable_area')
    envelopes=settings.get('extruder_printable_area')
    if not isinstance(envelopes,list) or len(envelopes)!=2:
        raise MixedFilamentError('Explicit two-nozzle printable envelopes required')
    for envelope in envelopes:area=area.intersection(polygon(envelope,'extruder_printable_area'))
    if area.is_empty:raise MixedFilamentError('Two-nozzle printable envelopes do not overlap')
    excluded=settings.get('bed_exclude_area',[])
    exclude=polygon(excluded,'bed_exclude_area') if excluded else None
    try:
        heights=[float(settings['printable_height'])]+[float(v) for v in settings.get('extruder_printable_height',[])]
        height=min(heights)
        if not np.isfinite(heights).all() or height<=0:raise ValueError()
    except (KeyError,TypeError,ValueError):raise MixedFilamentError('Valid printable height required') from None
    items=placements if placements is not None else [{'part_id':p.id,'transform':np.eye(4).tolist()} for p in parts]
    by_id={p.id:p for p in parts}
    if len(items)!=len(parts) or {i['part_id'] for i in items}!=set(by_id):
        raise MixedFilamentError('Exactly one placement per exported part required')
    checks=[]
    for item in items:
        tf=np.asarray(item['transform'],dtype=float)
        if tf.shape!=(4,4) or not np.isfinite(tf).all() or not np.allclose(tf[3],[0,0,0,1]):
            raise MixedFilamentError('Invalid print placement matrix')
        part=by_id[item['part_id']]
        world=np.asarray(part.mesh.vertices)@tf[:3,:3].T+tf[:3,3]
        footprint=MultiPoint(world[:,:2]).convex_hull
        if world[:,2].min() < -1e-5 or world[:,2].max()>height+1e-5:
            raise MixedFilamentError(f'Part {part.id} exceeds the actual dual-nozzle build height or lies below the bed')
        if not area.buffer(1e-5).covers(footprint):
            raise MixedFilamentError(f'Part {part.id} lies outside the actual dual-nozzle printable area')
        if exclude is not None and footprint.intersection(exclude).area>1e-8:
            raise MixedFilamentError(f'Part {part.id} intersects a bed exclusion region')
        checks.append({'part_id':part.id,'world_bounds_mm':[world.min(axis=0).tolist(),world.max(axis=0).tolist()]})
    return {'passed':True,'dual_nozzle_intersection_bounds_mm':list(area.bounds),
            'maximum_height_mm':height,'parts':checks,'conservative_convex_footprints':True}


def _assign_printable_plate(contents, object_ids):
    """Use the official bbs_3mf.cpp model_instance metadata schema after checks."""
    from xml.etree import ElementTree as ET
    ns='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
    root=ET.fromstring(contents['3D/3dmodel.model'])
    items=root.findall(f'{ns}build/{ns}item')
    if len(items)!=len(object_ids) or {i.get('objectid') for i in items}!=set(object_ids):
        raise MixedFilamentError('Native build items do not match checked printable parts')
    for item in items:item.set('printable','1')
    config=ET.fromstring(contents[MODEL_SETTINGS_PATH])
    plates=config.findall('plate')
    if len(plates)!=1:raise MixedFilamentError('Expected one native plate per exported file')
    plate=plates[0]
    for old in list(plate.findall('model_instance')):plate.remove(old)
    for sequence,object_id in enumerate(object_ids,1):
        instance=ET.SubElement(plate,'model_instance')
        for key,value in [('object_id',object_id),('instance_id','0'),('identify_id',str(sequence))]:
            ET.SubElement(instance,'metadata',{'key':key,'value':value})
    ET.register_namespace('',ns[1:-1])
    # Do not serialize the native root with ElementTree: it drops unused
    # xmlns:BambuStudio declarations that the GUI uses as native-file markers.
    import re
    original_root=contents['3D/3dmodel.model']
    patched_count=0
    def printable_tag(match):
        nonlocal patched_count
        tag=match.group(0)
        identifier=re.search(rb'\bobjectid="([^"]+)"',tag)
        if identifier is None or identifier.group(1).decode() not in object_ids:
            raise MixedFilamentError('Unexpected native build item while preserving root namespaces')
        patched_count+=1
        if re.search(rb'\bprintable="[^"]*"',tag):
            return re.sub(rb'\bprintable="[^"]*"',b'printable="1"',tag,count=1)
        return tag[:-2]+b' printable="1"/>' if tag.endswith(b'/>') else tag[:-1]+b' printable="1">'
    patched=re.sub(rb'<(?:[A-Za-z_][\w.-]*:)?item\b[^>]*>',printable_tag,original_root)
    if patched_count!=len(object_ids):raise MixedFilamentError('Printable build-item count mismatch')
    contents['3D/3dmodel.model']=patched
    contents[MODEL_SETTINGS_PATH]=ET.tostring(config,encoding='utf-8',xml_declaration=True)


def native_bed_bounds(settings: dict) -> dict:
    """Actual common H2D envelope for translating pack-frame placements.

    Bounds do not certify a nonrectangular polygon/exclusion-free footprint;
    validate_plate_parts performs that check on each translated part afterward.
    No scaling, implicit translation or machine-setting mutation occurs here.
    """
    import numpy as np
    from shapely.geometry import Polygon
    def polygon(raw):
        try:
            if isinstance(raw,str):raw=raw.split(',')
            points=[tuple(float(c) for c in point.split('x')) for point in raw]
            poly=Polygon(points)
            if not poly.is_valid or poly.area<=0:raise ValueError()
            return poly
        except (TypeError,ValueError):raise MixedFilamentError('Invalid native printable envelope') from None
    area=polygon(settings.get('printable_area'))
    nozzles=settings.get('extruder_printable_area')
    if not isinstance(nozzles,list) or len(nozzles)!=2:raise MixedFilamentError('Two nozzle envelopes required')
    for nozzle in nozzles:area=area.intersection(polygon(nozzle))
    try:
        heights=[float(settings['printable_height'])]+[float(v) for v in settings.get('extruder_printable_height',[])]
        height=min(heights)
        if not np.isfinite(heights).all() or height<=0:raise ValueError()
    except (KeyError,TypeError,ValueError):raise MixedFilamentError('Invalid native build height') from None
    if area.is_empty:raise MixedFilamentError('No common dual-nozzle printable area')
    x0,y0,x1,y1=map(float,area.bounds)
    return {'min':[x0,y0,0.0],'max':[x1,y1,height],
            'extents':[x1-x0,y1-y0,height],
            'rectangular':bool(area.equals(Polygon([(x0,y0),(x1,y0),(x1,y1),(x0,y1)]))),
            'per_part_validation_required':True}


_EXPLICIT_PROCESS_KEYS=frozenset({
    'layer_height','initial_layer_print_height','enable_support','support_type',
    'support_on_build_plate_only','support_threshold_angle','support_top_z_distance',
    'brim_type','brim_width','raft_layers','raft_contact_distance',
    'support_filament','support_interface_filament','enable_mixed_color_sublayer',
    'wipe_tower_x','wipe_tower_y','prime_tower_width',
})


def mark_explicit_process_overrides(settings: dict, source_settings: dict) -> dict:
    """Preserve intentional supported process edits against Bambu GUI inheritance.

    Official PresetBundle/Preset import restores non-diff keys from the system
    preset. CLI reads combined raw config directly, so CLI success alone does
    not prove these values survive GUI import. Only changed allowlisted process
    keys enter diff group 0. Filament/machine groups, thermal fields and G-code
    are never classified or copied into the process override group.
    """
    changed={key for key in _EXPLICIT_PROCESS_KEYS
             if key in settings and settings[key]!=source_settings.get(key)}
    result=deepcopy(settings)
    if not changed:return result
    flags=settings.get('filament_is_mixed')
    if not isinstance(flags,list) or not flags:
        raise MixedFilamentError('Explicit process overrides require native filament slots')
    count=len(flags)+2
    groups=result.get('different_settings_to_system')
    if groups is None:groups=['']*count
    if not isinstance(groups,list) or len(groups)!=count or any(not isinstance(v,str) for v in groups):
        raise MixedFilamentError('Native preset-difference groups must contain process, filament slots and machine groups')
    existing=set(groups[0].split(';'));existing.discard('')
    groups[0]=';'.join(sorted(existing|changed))
    result['different_settings_to_system']=groups
    return result
