"""Editable five-material appearance proposal for the reviewed Buddy source.

It deliberately consolidates baked fur shadows and the brown iris, rather than
claiming that source texture colors are automatically five real spool colors.
No filament assignment, native profile or approval is invented.
"""
from __future__ import annotations
import copy
import hashlib
import numpy as np
from .buddy_collar import MESH_HASH,CENTER,AXIS,HMIN,HMAX,INNER_RADIUS
from .construct import face_components
from .topology import frame
from .compare import nearest
from .colors import hex_rgb,srgb_to_lab,delta_e_2000
from .types import GeometryError

PALETTE=[('#ECA24D','Fellgold','gold'),('#61360C','Rucksack und Gurte','brown'),
         ('#0C2842','Halsband Navy','navy'),('#292119','Nase dunkel','black'),
         ('#292119','Pupille und vereinheitlichte dunkle Iris','black'),
         ('#DCD4B7','Augencreme und Lichtpunkte','cream'),('#DCD4B7','Gerollte Karte Creme','cream'),
         ('#ECA24D','Halsbandgold fest','gold')]

REVIEWED_LEATHER_FACE_SHA256='e0757b163a2c4b3ee160b9f6a71b369e21376a7bf53879684a39fe26ddfc5ef2'
REVIEWED_EMBLEM_FACE_SHA256='1dd840d91b0f1cd4e761f191a90e5a6ed5db266dfa06df7fd433a0b49d63b444'


def clean_enclosed_leather_highlights(mesh,tags):
    """Copy material tags, filling only small gold islands enclosed by brown.

    A source-bound Buddy appearance rule, not general material recognition.
    The caller checks the exact reviewed face fingerprint before adoption.
    Large enclosed fur and any boundary touching a special material survive.
    """
    original=np.asarray(tags)
    if original.shape!=(len(mesh.faces),) or not np.issubdtype(original.dtype,np.integer):
        raise GeometryError('Buddy leather cleanup requires one integer material tag per face')
    result=original.copy();adj=np.asarray(mesh.face_adjacency);changed=[];areas=[]
    # An open mesh boundary is not a brown enclosing boundary.
    edge_counts=np.bincount(mesh.edges_unique_inverse,minlength=len(mesh.edges_unique))
    open_faces=np.any(edge_counts[mesh.faces_unique_edges]!=2,axis=1)
    for component in face_components(mesh,original==0):
        area=float(mesh.area_faces[component].sum())
        if not 0<area<5000 or open_faces[component].any():continue
        selected=np.zeros(len(original),dtype=bool);selected[component]=True
        crossing=adj[selected[adj].sum(axis=1)==1]
        if not len(crossing):continue
        outside=np.where(selected[crossing[:,0]],crossing[:,1],crossing[:,0])
        if not np.all(original[outside]==1):continue
        result[component]=1;changed.extend(map(int,component));areas.append(area)
    changed=np.asarray(sorted(changed),dtype='<i8')
    return result,{'method':'small gold components enclosed exclusively by leather brown',
        'component_count':len(areas),'changed_source_faces':len(changed),
        'changed_source_area_mm2':float(sum(areas)),
        'changed_source_face_ids_sha256':hashlib.sha256(changed.tobytes()).hexdigest(),
        'maximum_component_area_mm2_exclusive':5000,'only_material_transition':[0,1],
        'geometry_modified':False,'anatomical_masks_modified':False,
        'source_bound_visual_proposal':True}


def propose_materials(surface,original_plan,masks,parts):
    if original_plan.get('mesh_hash')!=MESH_HASH or len(surface.mesh.faces)!=150000:
        raise GeometryError('Buddy material proposal requires the reviewed working source')
    mesh=surface.mesh;original=np.asarray(original_plan['face_regions']);tags=np.zeros(len(mesh.faces),dtype=int)
    gear=max(face_components(mesh,original==1),key=lambda ids:mesh.area_faces[ids].sum())
    triangles=(mesh.triangles-CENTER)@frame(AXIS);radial=np.linalg.norm(triangles[:,:,:2],axis=2)
    touches_ring=(triangles[:,:,2].min(axis=1)<=HMAX+1)&(triangles[:,:,2].max(axis=1)>=HMIN-1)&(radial.max(axis=1)>=INNER_RADIUS-1)&(radial.min(axis=1)<=161)
    tags[gear]=1;tags[touches_ring&(tags==1)]=0;tags[original==3]=2
    samples=surface.sample();centers=mesh.triangles_center;lab=srgb_to_lab(samples)
    brows=(abs(centers[:,0])>25)&(abs(centers[:,0])<115)&(centers[:,1]<-350)&(centers[:,1]>-490)&(centers[:,2]>900)&(centers[:,2]<970)&(lab[:,0]<55)
    tags[brows]=1
    emblem=(centers[:,0]**2+(centers[:,2]-475)**2<35**2)&(centers[:,1]<-436)&(samples[:,0]>.88)&(samples[:,1]/np.maximum(samples[:,0],1e-9)>.8)&(samples[:,2]/np.maximum(samples[:,0],1e-9)>.4)
    emblem_ids=np.flatnonzero(emblem)
    if len(emblem_ids)!=5 or hashlib.sha256(emblem_ids.astype('<i8').tobytes()).hexdigest()!=REVIEWED_EMBLEM_FACE_SHA256:
        raise GeometryError('Buddy gold emblem differs from the reviewed five source faces; review the material proposal again')
    # One gold material: the real mesh ring/facets supply natural shading.
    tags[emblem]=0;tags[touches_ring&(tags==0)]=7
    for key in ['nose','left-eye','right-eye','rolled-map']:
        if key not in masks:raise GeometryError('Missing reviewed anatomical mask '+key)
        ids=np.asarray(masks[key])
        if ids.ndim!=1 or not np.issubdtype(ids.dtype,np.integer) or not len(ids) or ids.min()<0 or ids.max()>=len(tags):raise GeometryError('Invalid Buddy material mask '+key)
        if key=='nose':tags[ids]=3
        elif key=='rolled-map':tags[ids]=6
        else:tags[ids]=np.where(np.isin(original[ids],[1,4]),4,5)
    tags,leather_cleanup=clean_enclosed_leather_highlights(mesh,tags)
    if (leather_cleanup['component_count']!=61 or leather_cleanup['changed_source_faces']!=1053
            or leather_cleanup['changed_source_face_ids_sha256']!=REVIEWED_LEATHER_FACE_SHA256):
        raise GeometryError('Buddy leather cleanup differs from the reviewed 61-component source mask; review the material proposal again')
    document=copy.deepcopy(original_plan);document['filament_ids']=[];document['face_regions']=tags.tolist();document['regions']=[]
    rgb=np.array([hex_rgb(row[0]) for row in PALETTE]);source_rgb=surface.sample();error=delta_e_2000(srgb_to_lab(source_rgb),srgb_to_lab(rgb[tags]));summary=[]
    for i,(color,name,physical) in enumerate(PALETTE):
        selected=tags==i;area=float(mesh.area_faces[selected].sum())
        document['regions'].append({'id':i,'name':name,'strategy':'body' if i in (0,1) else 'part','color_mode':'solid','color':color,
            'filament_id':None,'part_group':{2:20,7:20,3:30,4:40,5:40,6:50}.get(i,0),'cut_type':'whole' if i not in (0,1) else 'inlay','reason':'Materialvorschlag auf bestehender anatomischer Konstruktion; reale Spule auswählen.',
            'face_count':int(selected.sum()),'area_mm2':round(area,2)})
        summary.append({'region_id':i,'physical_class':physical,'color':color,'source_area_mm2':area,
            'area_weighted_delta_e_2000':float(np.average(error[selected],weights=mesh.area_faces[selected])) if selected.any() else 0})
    mappings={};physical_mappings={};violations=[];unmatched=[];interior_fallbacks=[]
    for part in parts:
        distances,source_ids,_=nearest(surface,part.mesh.triangles_center)
        # Internal caps near an exterior seam must not import its material.
        exterior=(distances<=.03)&((part.mesh.face_normals*mesh.face_normals[source_ids]).sum(axis=1)>.95)
        if not exterior.any():
            if part.id.startswith('collar-neck-'):
                mappings[part.id]=[0];physical_mappings[part.id]=['gold'];interior_fallbacks.append(part.id);continue
            unmatched.append(part.id);continue
        region_ids=list(map(int,np.unique(tags[source_ids[exterior]])));classes=sorted({PALETTE[i][2] for i in region_ids})
        mappings[part.id]=region_ids;physical_mappings[part.id]=classes
        if len(classes)>2:violations.append({'part_id':part.id,'physical_classes':classes})
    report={'source_mesh_hash':MESH_HASH,'approved':False,'requires_real_filament_assignment':True,'native_profiles_verified':False,
        'palette':summary,'part_region_ids':mappings,'part_physical_classes':physical_mappings,'leather_highlight_cleanup':leather_cleanup,
        'gold_emblem':{'source_faces':5,'source_face_ids_sha256':REVIEWED_EMBLEM_FACE_SHA256,
            'source_area_mm2':float(mesh.area_faces[emblem_ids].sum()),'material_region':0,
            'geometry_modified':False,'natural_geometry_shading':True,'physical_color_verified':False},
        'two_materials_per_part_passed':not violations and not unmatched,'violations':violations,'unmatched_parts':unmatched,'interior_only_gold_fallbacks':interior_fallbacks,
        'decisions':['Fur gold/dark-gold/cream highlights and isolated dark sole/fur shadows become one gold material.',
          'Backpack/straps and both distinct eyebrows stay brown; the collar-intersecting gear fringe becomes gold.',
          'Pendant ring and facets use one gold material with natural mesh shading; baked albedo contrast and physical color are not guaranteed.',
          'The 61 reviewed enclosed leather-highlight islands become brown; large enclosed fur and all special-material boundaries remain unchanged.',
          'Eye brown iris becomes dark with pupil; rim/whites/highlights become cream. Exactly black+cream, no hidden third spool.',
          'Nose becomes dark, rolled map cream, collar navy+gold. The source texture remains available for comparison.'],
        'limitations':['Five proposed physical material classes are appearance targets, not selected spools or temperature presets.',
          'No Mixed Filament recipes are generated. No native 3MF or sliced material claim follows from this proposal.',
          'Document is a material-only proposal on the separate reviewed anatomical preset, not an instruction to recut generic color islands.']}
    return document,report,rgb[tags]
