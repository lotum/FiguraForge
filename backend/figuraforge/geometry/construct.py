from __future__ import annotations
import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from .types import Part, GeometryError
from .topology import (frame, projected_outline, clip_surface, side_triangles,
                       mesh_from_triangles, boundary_loops)
from .connectors import pick_connectors, root_with_connectors
from .validation import require_solid, DistanceQuery, sample_surface, check_insert_path, validate_mesh


def face_components(mesh, mask):
    chosen=np.flatnonzero(mask)
    if not len(chosen): return []
    inverse=np.full(len(mesh.faces),-1,int); inverse[chosen]=np.arange(len(chosen))
    adj=mesh.face_adjacency
    adj=adj[mask[adj].all(axis=1)]
    if not len(adj): return [np.array([i]) for i in chosen]
    edges=inverse[adj]
    graph=coo_matrix((np.ones(len(edges)*2),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(chosen),len(chosen)))
    _,groups=connected_components(graph,directed=False)
    return [chosen[groups==i] for i in np.unique(groups)]


def patch_from_faces(mesh, indexes):
    return mesh.submesh([indexes],append=True,repair=False)


def clean_small_islands(mesh, labels, min_area=3.0):
    labels=labels.copy(); notes=[]
    adj=mesh.face_adjacency
    for color in np.unique(labels):
        for group in face_components(mesh,labels==color):
            if mesh.area_faces[group].sum()>=min_area: continue
            inside=np.zeros(len(labels),bool); inside[group]=True
            edge=adj[inside[adj[:,0]] ^ inside[adj[:,1]]]
            neighbors=edge[~inside[edge]]
            if len(neighbors):
                new=int(np.bincount(labels[neighbors]).argmax()); labels[group]=new
                notes.append({'faces':len(group),'old_color':int(color),'new_color':new,'reason':'island below minimum printable area'})
    return labels,notes


def choose_direction(patch, override=None):
    if override is not None:
        normal=np.asarray(override,float)
    else:
        normal=(patch.face_normals*patch.area_faces[:,None]).sum(axis=0)
    length=np.linalg.norm(normal)
    if length>=1e-8:normal/=length
    alignment=patch.face_normals@normal
    if override is None and (length<1e-8 or alignment.min()<.06):
        # A weighted mean is not a feasibility proof: a large oblique face can
        # dominate the average even though another direction clears every face.
        # Search a common normal cone; keep the exact same acceptance margin.
        from scipy.optimize import linprog
        normals=np.asarray(patch.face_normals)
        result=linprog([0,0,0,-1],A_ub=np.column_stack([-normals,np.ones(len(normals))]),
                       b_ub=np.zeros(len(normals)),bounds=[(-1,1)]*3+[(-1,1)],method='highs')
        if result.success and np.linalg.norm(result.x[:3])>1e-8:
            candidate=result.x[:3]/np.linalg.norm(result.x[:3])
            if (normals@candidate).min()>=.06:normal=candidate;alignment=normals@normal;length=1.
    if length<1e-8:
        raise GeometryError('This color region wraps around the model. Split it into insertion-direction regions or use a solid-cut workflow.')
    if alignment.min()<.06:
        raise GeometryError('Color region contains an undercut along its proposed assembly axis. Reassign a boundary or split the region before export.')
    return normal


def inspect_inlay_directions(mesh, labels, base_color=0, min_area=3., overrides=None):
    """Cheap necessary assembly checks, not a collision/printability certificate."""
    labels,_=clean_small_islands(mesh,np.asarray(labels),min_area)
    pockets=face_components(mesh,labels!=base_color)
    blocked=[]
    for index,faces in enumerate(pockets):
        try: choose_direction(patch_from_faces(mesh,faces),(overrides or {}).get(str(index)))
        except GeometryError:
            blocked.append(index)
    return {'pockets':len(pockets),'blocked_directions':len(blocked),'blocked_examples':blocked[:10],
            'passed':not blocked,'scope':'Necessary direction test only; depth, connectors and collisions are checked during construction.',
            'message':(f'{len(blocked)} von {len(pockets)} Farbtaschen haben keine zulaessige Steckrichtung. '
                       'Farbregionen muessen weiter unterteilt werden. Weniger Faces beheben diese Hinterschneidungen nicht.') if blocked else
                      'Steckrichtungen vorgeprueft; Taschentiefe, Stifte und Kollisionen werden erst beim Bau geprueft.'}


def make_inlays(mesh:trimesh.Trimesh, labels:np.ndarray, palette:list[str],
                 base_color:int=0, depth_mm:float=3.2, seam_mm:float=.15,
                 pin_radius_mm:float=1.5,pin_length_mm:float=4.,pin_clearance_mm:float=.2,
                 min_region_area_mm2:float=3,connector_shape:str='round',
                 validate_paths:bool=True,progress=None,direction_overrides=None,adaptive_small_pins:bool=True,
                 connector_mode:str='pins'):
    """Carve organic pockets, preserve the visible source triangles, add connectors.

    Adjacent non-base colors share a single pocket. This avoids zero-thickness
    back-to-back pocket walls between neighboring color inlays.
    """
    if connector_mode not in ('pins','glue'):raise GeometryError('Unknown inlay connection mode')
    require_solid(mesh)
    labels,merged=clean_small_islands(mesh,np.asarray(labels),min_region_area_mm2)
    q=DistanceQuery(mesh)
    pockets=face_components(mesh,labels!=base_color)
    keep=np.ones(len(mesh.faces),bool); replacements=[]; parts=[]; notes=[]
    if not pockets:
        return [Part('body','Grundkoerper',mesh.copy(),palette[base_color],base_color,'body')],{'pockets':0,'merged_islands':merged,'insertion_checks':[]}
    part_number=1
    for pocket_id,indexes in enumerate(pockets):
        if progress: progress(f'Constructing organic pocket {pocket_id+1}/{len(pockets)}')
        top=patch_from_faces(mesh,indexes)
        normal=choose_direction(top,(direction_overrides or {}).get(str(pocket_id)))
        basis=frame(normal)
        outline=projected_outline(top,basis)
        root=top.copy(); root.apply_translation(-normal*depth_mm)
        # Reject over-deep shells instead of clipping them into an unrelated wall.
        probe=sample_surface(root,3000)
        if q.values(probe).max()>.02:
            raise GeometryError(f'Pocket {pocket_id+1} exceeds the local material thickness. Reduce inlay depth or split the region.')
        socket_connectors=[]; pocket_parts=[]
        for color in np.unique(labels[indexes]):
            restricted=np.zeros(len(labels),bool); restricted[indexes]=labels[indexes]==color
            for component in face_components(mesh,restricted):
                region=patch_from_faces(mesh,component)
                region_outline=projected_outline(region,basis)
                inner=region_outline.buffer(-seam_mm,join_style='round') if seam_mm else region_outline
                if inner.is_empty: raise GeometryError('A color feature is narrower than twice the seam allowance')
                top_tri=clip_surface(region,basis,keep=inner)
                insert_top=mesh_from_triangles(top_tri,check=False)
                connectors=[] if connector_mode=='glue' else pick_connectors(inner,insert_top,basis,depth_mm,
                    radius=pin_radius_mm,length=pin_length_mm,clearance=pin_clearance_mm,shape=connector_shape)
                reduced=False
                if connector_mode=='pins' and not connectors and adaptive_small_pins and pin_radius_mm>.8:
                    # Small cosmetic inserts may accept a smaller, non-structural pin.
                    # Never go below 1.6 mm diameter; report the deviation explicitly.
                    connectors=pick_connectors(inner,insert_top,basis,depth_mm,
                        radius=.8,length=min(pin_length_mm,3.2),clearance=pin_clearance_mm,
                        count=1,shape=connector_shape,wall=.65)
                    reduced=bool(connectors)
                allowed=[]
                for c in connectors:
                    tip=np.array([[c.x,c.y,c.tip_z-.35]])@basis.T
                    if q.values(tip)[0]<-(c.radius+.7): allowed.append(c)
                connectors=allowed
                insert_root=insert_top.copy(); insert_root.apply_translation(-normal*depth_mm)
                bottom=root_with_connectors(insert_root,basis,connectors,socket=False)
                walls=side_triangles(insert_top,-normal*depth_mm)
                whole=mesh_from_triangles(np.concatenate([insert_top.triangles,bottom,walls]))
                require_solid(whole)
                if len(whole.split(only_watertight=False))!=1:
                    raise GeometryError('Seam erosion disconnected an inlay; reduce seam or separate the islands')
                warnings=[]
                if reduced and connectors: warnings.append('Small cosmetic insert uses a reduced 1.6 mm pin and 0.65 mm nominal edge allowance. Calibrate this pin diameter separately; not a structural joint.')
                if connector_mode=='glue':warnings.append('Intentional glue insert without pins. Adhesive fit and retention require a physical test.')
                elif not connectors: warnings.append('No safe pin fits this region. Retention is not guaranteed; adjust size, clearance or connection method.')
                p=Part(f'part-{part_number:03d}',f'Farbeinsatz {part_number:02d}',whole,palette[int(color)],int(color),'glue-inlay' if connector_mode=='glue' else 'inlay',normal.tolist(),
                       [c.summary(basis) for c in connectors],warnings)
                part_number+=1; pocket_parts.append(p); socket_connectors.extend(connectors)
        pocket_bottom=root_with_connectors(root,basis,socket_connectors,socket=True)
        pocket_walls=side_triangles(top,-normal*depth_mm)[:,::-1]
        replacements.extend([pocket_bottom,pocket_walls])
        keep[indexes]=False; parts.extend(pocket_parts)
        notes.append({'pocket':pocket_id,'area_mm2':round(top.area,3),
                      'direction':np.round(normal,5).tolist(),'depth_mm':depth_mm,'inlays':len(pocket_parts)})
    body=mesh_from_triangles(np.concatenate([mesh.triangles[keep],*replacements]))
    require_solid(body)
    if len(body.split(only_watertight=False))!=1:
        raise GeometryError('Pocket construction disconnected the core. Reduce depth or revise the part boundaries.')
    body_part=Part('body','Grundkoerper',body,palette[base_color],base_color,'body')
    checks=[]
    if validate_paths:
        for p in parts:
            if progress: progress(f'Checking straight assembly path: {p.name}')
            test=check_insert_path(p.mesh,body,p.assembly_direction,travel_mm=depth_mm+pin_length_mm+3)
            test['part_id']=p.id; checks.append(test)
            if not test['passed']:
                raise GeometryError(f'{p.name}: insertion path collides with core (sampled penetration {test["max_penetration_mm"]} mm). Revise the direction, seam or pocket geometry.')
    total=sum(p.mesh.volume for p in parts)+body.volume
    loss=float(mesh.volume-total)
    if loss < -max(1.,mesh.volume*1e-5):
        raise GeometryError('Part volume exceeds the source volume. Possible overlapping pockets/connectors; export blocked.')
    return [body_part,*parts],{'pockets':notes,'merged_islands':merged,'insertion_checks':checks,
                             'source_volume_mm3':float(mesh.volume),'parts_volume_mm3':float(total),
                             'clearance_void_mm3':max(0,loss),
                             'construction':'surface-preserving curved pockets; not planar slicing',
                             'semantic_limit':'Albedo color regions, not automatic semantic body-part recognition.'}
