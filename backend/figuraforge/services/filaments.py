from __future__ import annotations
import hashlib
import numpy as np
from ..geometry.colors import hex_rgb,srgb_to_lab,delta_e_2000


def normalize_spoolmandb(data):
    """Normalize the compiled SpoolmanDB list; preserve provenance/uncertainty."""
    if not isinstance(data,list): raise ValueError('SpoolmanDB must return a list')
    result=[]
    for row in data:
        if not isinstance(row,dict): continue
        color=str(row.get('color_hex',row.get('hex',''))).lstrip('#')[:6]
        if len(color)!=6: continue
        try: hex_rgb(color)
        except ValueError: continue
        manufacturer=row.get('manufacturer','Unknown')
        brand=manufacturer.get('name','Unknown') if isinstance(manufacturer,dict) else str(manufacturer)
        key=str(row.get('id') or hashlib.sha256(str(row).encode()).hexdigest()[:16])
        result.append({'id':'spoolmandb-'+key,'brand':brand,'name':str(row.get('name','Unnamed')),
            'material':str(row.get('material','PLA')),'hex':'#'+color.upper(),'owned':False,'allowed':True,
            'measured':False,'finish':row.get('finish','unknown'),'source':'SpoolmanDB community catalog',
            'source_url':'https://donkie.github.io/SpoolmanDB/filaments.json',
            'diameter_mm':row.get('diameter',1.75),'density_g_cm3':row.get('density'),
            'price_eur':None,'availability':'not checked','url':row.get('url')})
    return result


def normalize_spoolman(data):
    if not isinstance(data,list): raise ValueError('Spoolman must return a list of spools')
    out=[]
    for spool in data:
        f=spool.get('filament',{}); vendor=f.get('vendor') or {}
        color=str(f.get('color_hex','')).lstrip('#')[:6]
        if len(color)!=6: continue
        try: hex_rgb(color)
        except ValueError: continue
        out.append({'id':f"spoolman-{spool['id']}",'brand':vendor.get('name','Unknown'),'name':f.get('name','Spool'),
            'material':f.get('material','PLA'),'hex':'#'+color.upper(),'owned':True,'allowed':not spool.get('archived',False),
            'measured':False,'finish':'unknown','source':'user Spoolman inventory','remaining_weight_g':spool.get('remaining_weight')})
    return out


def rank_filaments(target,filaments,owned_only=False,materials=None,brands=None,limit=8,preferred_brands=None):
    target_lab=srgb_to_lab(hex_rgb(target)); rows=[]
    for f in filaments:
        if not f.get('allowed',True) or (owned_only and not f.get('owned')): continue
        if materials and f.get('material') not in materials: continue
        if brands and f.get('brand') not in brands: continue
        try:
            measured=f.get('lab_d65')
            lab=np.array(measured) if measured is not None else srgb_to_lab(hex_rgb(f['hex']))
            de=float(delta_e_2000(target_lab,lab))
        except (ValueError,KeyError): continue
        # Color distance is never altered to disguise a brand preference.
        preferences=preferred_brands if preferred_brands is not None else ['elegoo','bambu lab','bambulab']
        preferred=f.get('brand','').lower() in [x.lower() for x in preferences]
        rows.append({**f,'delta_e_2000':round(de,3),
                     'color_score':round(max(0,100-3*de),1),
                     'score_note':'Heuristic ranking, not a physical appearance guarantee.',
                     'color_source':'measured Lab D65' if measured is not None else 'unmeasured sRGB/catalog color',
                     'preferred_brand':preferred})
    rows.sort(key=lambda r:(r['delta_e_2000']//1.0,not r['preferred_brand'],r['delta_e_2000'],not r.get('owned',False)))
    return rows[:limit]
