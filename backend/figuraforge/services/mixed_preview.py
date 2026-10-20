"""Local, per-face two-spool optical recipe preview.

Linear-light interpolation is an UNCALIBRATED appearance estimate. It is neither
pigment mixing nor a claim about real Bambu sublayer color/printability. Region
strategy is independent from the output color: mixed faces retain local source
albedo variation through virtual recipes, without inventing additional spools.
"""
from __future__ import annotations
import base64
from decimal import Decimal
import numpy as np
from ..geometry.colors import hex_rgb, rgb_hex, srgb_to_lab, delta_e_2000
from ..geometry.preview import mesh_preview
from ..geometry.types import GeometryError
from .mixed_filament import recipe_library, validate_native_settings
from .color_plan import is_mixed


class MixedPreviewError(GeometryError):
    pass


def _filament_color(filament):
    value=filament.get('hex') or filament.get('color_hex') or filament.get('color')
    try:
        if not isinstance(value,str):raise ValueError()
        rgb=hex_rgb(value)
    except (TypeError,ValueError):
        raise MixedPreviewError('Ein ausgewaehltes Basisfilament hat keine gueltige HEX-Farbe; bitte den Bestand korrigieren.') from None
    return rgb, rgb_hex(rgb)


def _linear(rgb):
    rgb=np.asarray(rgb,float)
    return np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)


def _srgb(linear):
    value=np.asarray(linear,float)
    return np.where(value<=.0031308,12.92*value,1.055*np.maximum(value,0)**(1/2.4)-.055)


def _coverage(palette, bases, native_settings):
    if native_settings is None:
        return {'status':'not_checked','available_native_mixed_slots':0,
                'reason':'Keine native Rezeptvorlage fuer diese Vorschau geprueft.',
                'all_used_recipes_available':False}
    report=validate_native_settings(native_settings)
    colors=[rgb_hex(hex_rgb(c)) for c in native_settings['filament_colour']]
    slots={}
    for physical in report['physical_slots']:
        for index,base in enumerate(bases):
            if colors[physical-1]==base['color']:
                slots.setdefault(100 if index==0 else 0,[]).append(physical)
    for mixed in report['mixed_slots']:
        a,b=mixed['component_slots']; pair=[colors[a-1],colors[b-1]]
        ratios=[Decimal(r) for r in mixed['ratios']]
        if pair==[bases[0]['color'],bases[1]['color']]:first=ratios[0]*100
        elif pair==[bases[1]['color'],bases[0]['color']]:first=ratios[1]*100
        else:continue
        if first==first.to_integral_value():slots.setdefault(int(first),[]).append(mixed['slot'])
    for recipe in palette:recipe['native_slots']=slots.get(recipe['first_percent'],[])
    return {'status':'checked_metadata_only','available_native_mixed_slots':len(report['mixed_slots']),
            'matching_mixed_recipe_count':sum(bool(r['native_slots']) for r in palette if r['kind']=='mixed'),
            'basis_color_match_required':True,'native_gui_verified':False,'slicing_verified':False}


def build_mixed_preview(surface, plan, filaments, layer_height_mm=.2, *, native_settings=None, reference_plan=None, include_geometry=True, recipe_percentages=None):
    """Return face-order-preserving preview, recipe assignments and export coverage.

    ``plan.filament_ids`` is the one fixed two-filament pair for mixed regions.
    ``filaments`` are ordinary inventory rows (id, hex, material, allowed).
    Optional native_settings is full existing Bambu project settings, used only
    to report exact matching recipe metadata, never to silently replace a pair.
    ``reference_plan`` must remain the immutable initial color plan. Region
    edits apply an absolute Lab delta to each original sample; passing the last
    edited plan as a fresh baseline would erase earlier intended corrections.
    ``face_recipe_indices`` uses -1 for non-mixed faces; all other values index
    recipe_palette. The consumer must bind these indices to the mesh hash.
    """
    try:height=float(layer_height_mm)
    except (TypeError,ValueError):raise MixedPreviewError('Gueltige Schichthoehe erforderlich.') from None
    if not np.isfinite(height) or height<=0:raise MixedPreviewError('Schichthoehe muss positiv und endlich sein.')
    count=len(surface.mesh.faces)
    labels=np.asarray(plan.get('face_regions',[]))
    if labels.shape!=(count,) or not np.issubdtype(labels.dtype,np.integer):
        raise MixedPreviewError('Farbplan und Mesh-Dreiecke stimmen nicht ueberein.')
    if plan.get('face_count',count)!=count:raise MixedPreviewError('Farbplan hat eine andere Dreieckszahl.')
    regions=plan.get('regions',[])
    references={}
    if reference_plan is not None:
        if reference_plan.get('face_count',count)!=count:
            raise MixedPreviewError('Referenz-Farbplan gehoert zu einer anderen Geometrie.')
        if reference_plan.get('mesh_hash')!=plan.get('mesh_hash'):
            raise MixedPreviewError('Referenz-Farbplan hat eine andere Meshversion.')
        references={r['id']:r for r in reference_plan.get('regions',[])}
    by_region={row['id']:row for row in regions}
    if len(by_region)!=len(regions) or set(labels)-set(by_region):raise MixedPreviewError('Ungueltige Farbregionen im Plan.')
    mixed=np.array([is_mixed(by_region[int(label)]) for label in labels])
    selected=plan.get('filament_ids',[])
    inventory={row['id']:row for row in filaments}
    if mixed.any() and (len(selected)!=2 or len(set(selected))!=2):
        raise MixedPreviewError('Fuer Verlaeufe bitte genau zwei verschiedene Basisfilamente waehlen.')
    if not mixed.any() and len(selected)!=2:
        colors=np.array([hex_rgb(by_region[int(label)]['color']) for label in labels])
        preview=mesh_preview(surface.mesh,face_rgb=colors,name='Zielfarben',smooth_normals=True)
        return {'preview':{'format':'figuraforge-mesh-v1','unit':'millimeter','up_axis':'Z','meshes':[preview]},
                'recipe_palette':[],'face_recipe_indices':[-1]*count,'per_region':[],
                'layer_height_mm':height,
                'export_coverage':{'status':'not_applicable','all_used_recipes_available':True},'warnings':[]}
    bases=[]
    for ident in selected:
        filament=inventory.get(ident)
        if filament is None or not filament.get('allowed',True):
            raise MixedPreviewError('Ein Basisfilament fehlt oder ist fuer die Verwendung gesperrt.')
        rgb,color=_filament_color(filament)
        bases.append({'id':ident,'color':color,'rgb':rgb,'material':str(filament.get('material','')).casefold()})
    if not bases[0]['material'] or bases[0]['material']!=bases[1]['material']:
        raise MixedPreviewError('Die zwei Basisfilamente muessen dieselbe Materialart haben.')
    if bases[0]['color']==bases[1]['color']:
        raise MixedPreviewError('Die zwei Basisfilamente haben dieselbe hinterlegte Farbe; damit ist kein Farbverlauf schaetzbar.')
    step=plan.get('ratio_step_percent',5)
    if step not in (5,10,20):raise MixedPreviewError('Rezeptabstand muss 5, 10 oder 20 Prozent betragen.')
    percentages=[0,*[r.first_percent for r in recipe_library((1,2),step)],100]
    if recipe_percentages is not None:
        percentages=list(recipe_percentages)
        if (len(percentages)<2
                or any(isinstance(p,bool) or not isinstance(p,(int,np.integer)) for p in percentages)
                or percentages!=sorted(set(percentages))
                or percentages[0]!=0 or percentages[-1]!=100
                or any(not 10<=p<=90 for p in percentages[1:-1])):
            raise MixedPreviewError('Explizite Mischwerte brauchen eindeutige aufsteigende Ganzzahlprozente, reine Endpunkte 0/100 und innere Werte von 10 bis 90.')
        percentages=[int(p) for p in percentages]
    first=np.array(percentages,float)/100
    palette_rgb=_srgb(first[:,None]*_linear(bases[0]['rgb'])+(1-first[:,None])*_linear(bases[1]['rgb']))
    palette=[]
    for index,percent in enumerate(percentages):
        palette.append({'id':f'mix-{percent:03d}','index':index,'kind':'pure' if percent in (0,100) else 'mixed',
                        'first_percent':percent,'percentages':[percent,100-percent],
                        'physical_filament_ids':[bases[0]['id'],bases[1]['id']],
                        'color':rgb_hex(palette_rgb[index]),
                        'sublayer_thickness_mm':[round(height*percent/100,6),round(height*(100-percent)/100,6)],
                        'thickness_note':'Nominale Aufteilung der Schichthoehe, keine Slicer-/Duese-Freigabe.',
                        'native_slots':[],'calibrated':False})
    coverage=_coverage(palette,bases,native_settings)
    source=np.asarray(surface.sample(),float)
    if source.shape!=(count,3) or not np.isfinite(source).all() or (source<0).any() or (source>1).any():
        raise MixedPreviewError('Original-Albedofarben sind ungueltig.')
    colors=np.empty((count,3),float)
    for region in regions:
        try:
            assigned=inventory.get(region.get('filament_id'))
            rgb=_filament_color(assigned)[0] if assigned else hex_rgb(region['color'])
        except (ValueError,TypeError):raise MixedPreviewError('Ein Bereich hat keine gueltige Zielfarbe.') from None
        colors[labels==region['id']]=rgb
    assignments=np.full(count,-1,dtype=int)
    distances=np.zeros(count,float)
    selected_faces=np.flatnonzero(mixed);palette_lab=srgb_to_lab(palette_rgb)
    region_deltas={}
    for region in regions:
        if not is_mixed(region) or region['id'] not in references:continue
        try:
            region_deltas[region['id']]=srgb_to_lab(hex_rgb(region['color']))-srgb_to_lab(hex_rgb(references[region['id']]['color']))
        except (ValueError,KeyError,TypeError):raise MixedPreviewError('Ungueltige Farbkorrektur in Referenz oder aktuellem Plan.') from None
    for offset in range(0,len(selected_faces),8192):
        indices=selected_faces[offset:offset+8192]
        targets=srgb_to_lab(source[indices])
        for region_id,delta in region_deltas.items():targets[labels[indices]==region_id]+=delta
        differences=delta_e_2000(targets[:,None,:],palette_lab[None,:,:])
        best=differences.argmin(axis=1)
        assignments[indices]=best;colors[indices]=palette_rgb[best]
        distances[indices]=differences[np.arange(len(indices)),best]
    preview=mesh_preview(surface.mesh,face_rgb=colors,name='Zielfarben aus Mischrezepten',smooth_normals=True) if include_geometry else None
    if preview is not None:preview['face_region_ids']=base64.b64encode(labels.astype('<u4').tobytes()).decode()
    per_region=[]
    for region in regions:
        mask=labels==region['id'];used=[]
        for index in np.unique(assignments[mask]):
            if index<0:continue
            recipe_faces=mask&(assignments==index)
            used.append({'recipe_index':int(index),'recipe_id':palette[index]['id'],
                         'face_count':int(recipe_faces.sum()),
                         'area_mm2':round(float(surface.mesh.area_faces[recipe_faces].sum()),6)})
        per_region.append({'region_id':region['id'],'strategy':region['strategy'],'color_mode':'mixed' if is_mixed(region) else 'solid',
                           'face_count':int(mask.sum()),'used_recipe_count':len(used),'used_recipes':used})
    used_indices=sorted(set(assignments[mixed].tolist()))
    coverage['used_recipe_count']=len(used_indices)
    coverage['used_missing_recipes']=[palette[i]['id'] for i in used_indices if not palette[i]['native_slots']]
    coverage['all_used_recipes_available']=(native_settings is not None and not coverage['used_missing_recipes'])
    warnings=['Unkalibrierte optische Schaetzung durch Interpolation in linearem Licht. Reale Layerfarben brauchen gedruckte Farbmuster.',
              'Pro Dreieck wird die Original-Albedo abgetastet; Licht/Schatten in der Textur sind nicht automatisch vom Material getrennt.',
              'Nominale Unterlagenstaerken bestaetigen keine druckbare Mindestschichthoehe.']
    if reference_plan is None and mixed.any():
        warnings.append('Ohne unveraenderten Referenzplan werden lokale Originalfarben verwendet; nachtraegliche Bereichs-Farbkorrekturen sind nicht eingerechnet.')
    if reference_plan is not None and any(is_mixed(r) and r['id'] not in references for r in regions):
        warnings.append('Neue Bereiche ohne Referenz verwenden Originalfarben ohne Bereichs-Farbkorrektur.')
    if not coverage['all_used_recipes_available']:
        warnings.append('Nicht alle Vorschau-Rezepte sind in der nativen Vorlage nachgewiesen; Vorschau ist keine Exportfreigabe.')
    return {'preview':{'format':'figuraforge-mesh-v1','unit':'millimeter','up_axis':'Z','meshes':[preview]} if preview is not None else None,
            'recipe_palette':palette,'face_recipe_indices':assignments.tolist(),'per_region':per_region,
            'basis_filaments':[{k:v for k,v in b.items() if k!='rgb'} for b in bases],
            'recipe_count':len(palette),'predicted_color_count':len({row['color'] for row in palette}),
            'minimum_mixed_component_percent':10,'maximum_mixed_component_percent':90,
            'physical_filament_count':2,'ratio_step_percent':step,
            'explicit_recipe_percentages':percentages if recipe_percentages is not None else None,
            'nominal_layer_height_mm':height,'layer_height_mm':height,
            'region_color_adjustments_applied':bool(region_deltas),
            'reference_color_model':'Original-Lab plus delta current-region Lab minus immutable-reference-region Lab' if reference_plan is not None else None,
            'color_model':'uncalibrated linear-light optical estimate',
            'source_sampling':'original albedo at triangle barycenter; flat recipe per triangle',
            'matching_metric':'CIEDE2000','mixed_face_count':int(mixed.sum()),
            'matching_error_delta_e':{'median':round(float(np.median(distances[mixed])),4) if mixed.any() else 0,
                                     'p95':round(float(np.percentile(distances[mixed],95)),4) if mixed.any() else 0},
            'export_coverage':coverage,'warnings':warnings}
