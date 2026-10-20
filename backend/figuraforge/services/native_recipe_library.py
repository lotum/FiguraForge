"""Exact preview-ratio allocation into EXISTING Bambu virtual recipe slots.

No physical filament/profile, temperature, nozzle vector or purge matrix is
created. If the template cannot represent every requested ratio simultaneously,
export is rejected explicitly instead of silently reducing the color palette.
"""
from __future__ import annotations
from copy import deepcopy
from decimal import Decimal
import numpy as np
from ..geometry.colors import hex_rgb, rgb_hex
from .mixed_filament import MixedFilamentError, validate_native_settings


class NativeRecipeCapacityError(MixedFilamentError):
    pass


def _percent(recipe):
    value=recipe.get('first_percent') if isinstance(recipe,dict) else recipe
    if type(value) is not int or value not in (0,100) and not 10<=value<=90:
        raise MixedFilamentError('Native Rezeptanteile brauchen ganze Prozentwerte 10–90 oder reine Basisfarben 0/100')
    return value


def _optical_color(first,second,percent):
    colors=np.array([hex_rgb(first),hex_rgb(second)])
    linear=np.where(colors<=.04045,colors/12.92,((colors+.055)/1.055)**2.4)
    value=linear[0]*(percent/100)+linear[1]*(1-percent/100)
    rgb=np.where(value<=.0031308,value*12.92,1.055*np.maximum(value,0)**(1/2.4)-.055)
    return rgb_hex(rgb)


def allocate_native_recipes(settings: dict, basis_slots, required_recipes) -> dict:
    """Allocate ALL requested exact preview percentages, or fail atomically.

    required_recipes: preview recipe dictionaries OR integer first-component
    percentages. basis_slots: two existing physical slot indices in the same
    order as preview physical_filament_ids. Pure 100/0 uses the first slot;
    0/100 uses the second. Unused recipes are left as original template data.

    Existing exact slots are preferred, remaining requested ratios reuse only
    unclaimed virtual slots belonging to this exact physical pair. This does
    not append arrays or reinterpret unknown N×2/N²×2/N+2 native structures.
    """
    report=validate_native_settings(settings)
    if (len(basis_slots)!=2 or len(set(basis_slots))!=2 or
            any(type(slot) is not int or slot not in report['physical_slots'] for slot in basis_slots)):
        raise MixedFilamentError('Das Basispaar muss zwei vorhandene physische native Slots verwenden')
    first,second=map(int,basis_slots)
    requested=sorted({_percent(recipe) for recipe in required_recipes})
    mixed=[p for p in requested if p not in (0,100)]
    candidates=[r for r in report['mixed_slots'] if set(r['component_slots'])=={first,second}]
    if len(mixed)>len(candidates):
        raise NativeRecipeCapacityError(
            f'Native Vorlage hat {len(candidates)} vorhandene Mischslots fuer dieses Basispaar, '
            f'die Vorschau benoetigt {len(mixed)} verschiedene Mischrezepte. '
            'Export blockiert: fehlende Mischslots in Bambu Studio anlegen und Vorlage erneut speichern. '
            'Es werden keine Vorschaufarben stillschweigend zusammengelegt.')
    percent_to_slot={}
    if 100 in requested:percent_to_slot[100]=first
    if 0 in requested:percent_to_slot[0]=second
    # Preserve exact matching recipes first, including reverse component order.
    for percent in mixed:
        for row in candidates:
            if row['slot'] in percent_to_slot.values():continue
            ratio=Decimal(row['ratios'][0 if row['component_slots'][0]==first else 1])*100
            if ratio==percent:
                percent_to_slot[percent]=row['slot'];break
    remaining=[row['slot'] for row in candidates if row['slot'] not in percent_to_slot.values()]
    for percent in mixed:
        if percent not in percent_to_slot:percent_to_slot[percent]=remaining.pop(0)
    result=deepcopy(settings);changes=[]
    for percent in mixed:
        slot=percent_to_slot[percent];index=slot-1
        components=f'{first},{second}';ratios=f'{percent/100:.2f},{(100-percent)/100:.2f}'
        color=_optical_color(settings['filament_colour'][first-1],settings['filament_colour'][second-1],percent)
        before={'components':result['filament_mixed_components'][index],
                'ratios':result['filament_mixed_sublayer_ratios'][index],
                'color':result['filament_colour'][index]}
        result['filament_mixed_components'][index]=components
        result['filament_mixed_sublayer_ratios'][index]=ratios
        result['filament_colour'][index]=color
        if 'default_filament_colour' in result:
            if not isinstance(result['default_filament_colour'],list) or len(result['default_filament_colour'])!=report['slot_count']:
                raise MixedFilamentError('Vorlagen-Standardfarben haben eine unbekannte Slotdimension')
            result['default_filament_colour'][index]=color
        if 'filament_settings_id' in result:
            if not isinstance(result['filament_settings_id'],list) or len(result['filament_settings_id'])!=report['slot_count']:
                raise MixedFilamentError('Vorlagen-Filamentnamen haben eine unbekannte Slotdimension')
            result['filament_settings_id'][index]=f'FiguraForge Mischung {percent}/{100-percent}'
        changes.append({'slot':slot,'first_percent':percent,'before':before,
                        'after':{'components':components,'ratios':ratios,'color':color}})
    validate_native_settings(result)
    allowed={'filament_mixed_components','filament_mixed_sublayer_ratios','filament_colour',
             'default_filament_colour','filament_settings_id'}
    if any(result[key]!=value for key,value in settings.items() if key not in allowed):
        raise MixedFilamentError('Unerwartete Aenderung eines physischen Profils oder nativen Dimensionsfeldes')
    return {'settings':result,'percent_to_slot':percent_to_slot,
            'report':{'status':'exact_existing_virtual_slots','requested_percentages':requested,
                      'required_mixed_recipe_count':len(mixed),'available_matching_virtual_slots':len(candidates),
                      'allocated_virtual_slots':sorted(percent_to_slot[p] for p in mixed),
                      'slot_count_before':report['slot_count'],'slot_count_after':report['slot_count'],
                      'physical_slots_before':report['physical_slots'],'physical_slots_after':report['physical_slots'],
                      'new_physical_profiles_created':False,'new_virtual_slots_created':False,
                      'slot_array_sizes_unchanged':True,'purge_matrix_unchanged':True,
                      'preview_palette_coarsened':False,'changes':changes,
                      'color_model':'uncalibrated linear-light optical estimate',
                      'native_gui_verified':False,'slicing_verified':False,
                      'warnings':['Bestehende thermische Profile und Spuelmatrix bleiben erhalten. Neue Rezeptverhaeltnisse brauchen eine native Slice-/Farbpruefung.']}}
