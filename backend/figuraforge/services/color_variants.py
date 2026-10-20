"""Nine editable local color hypotheses, never a claim of recovered albedo.

Columns suppress progressively fewer similar-hue shade regions. Rows change
proposed target lightness, not geometry, real illumination, or spool profiles.
"""
from copy import deepcopy
import colorsys
import numpy as np
from ..models import ColorPlanDocument
from .color_plan import is_mixed
from ..geometry.colors import hex_rgb,rgb_hex,srgb_to_lab,delta_e_2000


def _similar_shade(a,b,threshold):
    lab=srgb_to_lab([hex_rgb(a),hex_rgb(b)])
    # Protect very dark facial details and high-contrast light markings.
    if min(lab[:,0])<22:return False
    chroma=np.linalg.norm(lab[:,1:],axis=1)
    if abs(chroma[0]-chroma[1])>18:return False
    if min(chroma)<12 and max(chroma)>20:return False
    if min(chroma)>10:
        hue=np.degrees(np.arctan2(lab[:,2],lab[:,1]))
        if abs((hue[0]-hue[1]+180)%360-180)>22:return False
    return float(delta_e_2000(*lab))<threshold


def generate_variants(document):
    original=ColorPlanDocument.model_validate(document).model_dump()
    used=set(original['face_regions']);regions=[r for r in original['regions'] if r['id'] in used]
    anchors=sorted(regions,key=lambda r:-r['area_mm2'])
    result=[]
    for row,(lightness,light_title) in enumerate(((.06,'Heller'),(0,'Originalhelligkeit'),(-.06,'Dunkler'))):
        for column,(threshold,detail_title) in enumerate(((28,'Grundfarben'),(18,'Ausgewogen'),(8,'Mehr Farbdetails'))):
            plan=deepcopy(original);byid={r['id']:r for r in plan['regions']};merged=[]
            # Keep explicitly painted regions untouched by
            # shade merging; changes concern suggested color islands only.
            for source in anchors:
                if source.get('reason','').startswith('Manuell'):continue
                target=next((r for r in anchors if r['area_mm2']>source['area_mm2'] and not is_mixed(r)
                    and _similar_shade(source['color'],r['color'],threshold)),None)
                if target:
                    r=byid[source['id']];t=byid[target['id']]
                    for key in ('color','strategy','color_mode','part_group','cut_type','filament_id'):r[key]=t[key]
                    # Same physical group even for legacy ungrouped regions.
                    if r['strategy']=='part':r['part_group']=t['part_group'] or t['id']+1
                    r['reason']='Aehnlicher Farbton vereinheitlicht; Schatten-Hypothese, manuell pruefen.'
                    merged.append(source['id'])
            changed=[]
            for region in plan['regions']:
                saturation_shift=(-.08,0,.08)[column]
                if not lightness and not saturation_shift:continue
                rgb=hex_rgb(region['color']);h,l,s=colorsys.rgb_to_hls(*rgb)
                # Black pupils/nose remain black rather than drifting to gray.
                if srgb_to_lab(rgb)[0]<22:continue
                color=rgb_hex(colorsys.hls_to_rgb(h,max(0,min(1,l+lightness)),max(0,min(1,s+saturation_shift))))
                if color!=region['color']:
                    region['color']=color;region['filament_id']=None;changed.append(region['id'])
            plan['note']='Lokale Farbvariante: Schatten-Unterdrueckung ist eine Hypothese, keine physikalische Entlichtung. Reale Filamente vor Export zuordnen.'
            result.append({'id':f'{row}-{column}','row':row,'column':column,'title':f'{light_title} · {detail_title}',
                'description':f'{len(merged)} aehnliche Farbbereiche vereinheitlicht. Schwarze Details und manuell markierte Bereiche bleiben geschuetzt.',
                'merged_regions':merged,'requires_filament_mapping':bool(changed),'document':plan})
    return result
