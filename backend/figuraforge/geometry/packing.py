from __future__ import annotations
from itertools import permutations, product
import numpy as np
from .types import Part, GeometryError


def rotations():
    out=[]
    for perm in permutations(range(3)):
        for signs in product((-1,1),repeat=3):
            r=np.eye(3)[list(perm)]*np.array(signs)[:,None]
            if np.linalg.det(r)>.5: out.append(r)
    return out


def orientations(part,volume,margin):
    candidates=[]
    mesh=part.mesh
    matrices=rotations()
    # Inlays often print best with their hidden root roughly horizontal.
    if part.assembly_direction:
        from .topology import frame
        matrices.extend([frame(np.array(part.assembly_direction)).T,
                         np.diag([1,-1,-1])@frame(np.array(part.assembly_direction)).T])
    for r in matrices:
        v=mesh.vertices@r.T; lo=v.min(axis=0); extent=np.ptp(v,axis=0)
        if (extent[:2]+2*margin>volume[:2]+1e-6).any() or extent[2]>volume[2]: continue
        normal=mesh.face_normals@r.T
        overhang=mesh.area_faces[(normal[:,2]<-.707) & ((mesh.triangles@r.T)[:,:,2].min(axis=1)>lo[2]+.3)].sum()
        contact=mesh.area_faces[((mesh.triangles@r.T)[:,:,2].max(axis=1)<lo[2]+.22)].sum()
        # A heuristic, deliberately not labelled a sliced print-time estimate.
        score=overhang/(mesh.area+1e-9)*100 + extent[2]/max(volume[2],1)*20 - min(contact,500)*.015
        tf=np.eye(4); tf[:3,:3]=r; tf[:3,3]=-lo
        candidates.append({'transform':tf,'size':extent,'score':float(score),'overhang_area_mm2':float(overhang),'contact_area_mm2':float(contact)})
    if not candidates: raise GeometryError(f'{part.name} cannot fit the configured build envelope')
    return sorted(candidates,key=lambda o:o['score'])


def pack_parts(parts:list[Part],volume=(300.,320.,325.),margin=6.,gap=5.,max_colors=1):
    """Deterministic rectangular skyline placement, color-aware and non-overlapping."""
    volume=np.asarray(volume,float); plates=[]
    order=sorted(parts,key=lambda p: (p.color,-np.sort(p.mesh.extents)[-2:].prod()))
    for p in order:
        choices=orientations(p,volume,margin)
        winner=None
        for pi,plate in enumerate(plates):
            if p.color not in plate['colors'] and len(plate['colors'])>=max_colors: continue
            anchors=[(margin,margin)]
            for item in plate['placements']:
                x,y,w,h=item['rect']
                anchors.extend([(x+w+gap,y),(x,y+h+gap)])
            for orient in choices:
                w,h,_=orient['size']
                for x,y in anchors:
                    if x+w+margin>volume[0]+1e-6 or y+h+margin>volume[1]+1e-6: continue
                    if any(not (x+w+gap<=xx+1e-6 or xx+ww+gap<=x+1e-6 or y+h+gap<=yy+1e-6 or yy+hh+gap<=y+1e-6)
                           for xx,yy,ww,hh in [i['rect'] for i in plate['placements']]): continue
                    score=pi*100000+orient['score']+y*.015+x*.005
                    if winner is None or score<winner[0]: winner=(score,pi,x,y,orient)
        if winner is None:
            plate={'id':len(plates)+1,'colors':[],'placements':[],'volume_mm':volume.tolist()}
            plates.append(plate)
            orient=choices[0]; winner=(0,len(plates)-1,margin,margin,orient)
        _,pi,x,y,o=winner; plate=plates[pi]
        tf=o['transform'].copy(); tf[0,3]+=x; tf[1,3]+=y
        w,h,z=o['size']
        plate['placements'].append({'part_id':p.id,'transform':np.round(tf,9).tolist(),
            'rect':[float(x),float(y),float(w),float(h)],'height_mm':float(z),'color':p.color,
            'orientation_score':round(o['score'],3),'overhang_area_mm2':round(o['overhang_area_mm2'],3),
            'contact_area_mm2':round(o['contact_area_mm2'],3),'support_status':'slicer review required'})
        if p.color not in plate['colors']: plate['colors'].append(p.color)
    for plate in plates:
        plate['utilization_percent']=round(sum(p['rect'][2]*p['rect'][3] for p in plate['placements'])/(volume[0]*volume[1])*100,1)
    return plates


def validate_packing(parts,plates,tolerance=1e-5):
    lookup={p.id:p for p in parts}; seen=[]; problems=[]
    for plate in plates:
        volume=np.array(plate['volume_mm'])
        for i,p in enumerate(plate['placements']):
            seen.append(p['part_id']); part=lookup[p['part_id']]; t=np.array(p['transform'])
            v=part.mesh.vertices@t[:3,:3].T+t[:3,3]
            if (v.min(axis=0)<-tolerance).any() or (v.max(axis=0)>volume+tolerance).any():
                problems.append(f"{p['part_id']} outside plate {plate['id']}")
            x,y,w,h=p['rect']
            for q in plate['placements'][i+1:]:
                xx,yy,ww,hh=q['rect']
                if min(x+w,xx+ww)>max(x,xx)+tolerance and min(y+h,yy+hh)>max(y,yy)+tolerance:
                    problems.append(f"Overlapping placement: {p['part_id']} and {q['part_id']}")
    if sorted(seen)!=sorted(lookup): problems.append('Parts missing or duplicated')
    return {'passed':not problems,'problems':problems,'method':'transformed bounds and conservative XY rectangles'}
