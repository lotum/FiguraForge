"""Offline, source-bound Buddy construction and material proposal.

No DB mutation, approval, cloud or printer submission. Explicit workdir stores
killable local Blender jobs and diagnostics. This is a reviewed 1000-mm source
preset, not general character anatomy recognition.
"""
from __future__ import annotations
from pathlib import Path
import json,hashlib,time,copy
from functools import partial
from types import SimpleNamespace
from itertools import permutations
import numpy as np
from scipy.spatial import cKDTree
from figuraforge.geometry.anatomical import anatomical_seed_cut,seed_geodesic_faces
from figuraforge.geometry.construct import face_components,patch_from_faces,make_inlays
from figuraforge.geometry.surface_parts import interior_cap
from figuraforge.geometry.connectors import pick_connectors,root_with_connectors
from figuraforge.geometry.topology import mesh_from_triangles,boundary_loops,frame,projected_outline
from figuraforge.geometry.plane_cut import clip_primary_component
from figuraforge.geometry.split import joint_between_halves,fits_some_orientation
from figuraforge.geometry.validation import DistanceQuery,sample_surface,validate_mesh,require_solid,check_insert_path
from figuraforge.geometry.compare import nearest
from figuraforge.geometry.packing import pack_parts,validate_packing
from figuraforge.geometry.preview import surface_preview,parts_preview
from figuraforge.geometry.types import Part,GeometryError,Surface
from figuraforge.geometry.planned_parts import _combined_checks

from figuraforge.db import uid,digest
from figuraforge.geometry.colors import classify,hex_rgb,srgb_to_lab,delta_e_2000
from figuraforge.geometry.buddy_materials import propose_materials,PALETTE
PRESET='buddy-anatomical-v1'
MESH_HASH='5d60b394adfbf92e46b0b6d3a70fbbeb2b02d3284557297a48aba5cad14f43af'
SOURCE_SHA256='1fbf9afb006d912cb612702232d7eb0e194e35407ad0e293b6550b4337bce61c'
SOURCE_SHA=SOURCE_SHA256
SOURCE_SIGNATURE='8d0817e834a9cfe92d46c8bab87e7d7aef1e6ab9747000f7844036f4c188a6dd'
REFERENCE_PALETTE=['#ECA24D','#61360C','#CF8433','#0C2842','#292119','#E2B16D']


def _asdict(value):
    return value.model_dump() if hasattr(value,'model_dump') else dict(value)


def _source(surface,settings,mesh_hash,reference_plan):
    settings=_asdict(settings)
    signature=hashlib.sha256(np.asarray(surface.mesh.vertices,dtype='<f8').round(6).tobytes()+np.asarray(surface.mesh.faces,dtype='<i8').tobytes()).hexdigest()
    if mesh_hash!=MESH_HASH or signature!=SOURCE_SIGNATURE or len(surface.mesh.faces)!=150000:
        raise GeometryError('Buddy-Anatomiepreset benötigt die unveränderte verifizierte 150k-Quelle.')
    if abs(float(settings.get('height_mm',0))-1000)>1e-6 or settings.get('up_axis')!='Y':
        raise GeometryError('Buddy-Anatomiepreset ist nur für 1000 mm und Y-up verifiziert.')
    if reference_plan is not None and _asdict(reference_plan).get('mesh_hash')!=MESH_HASH:
        raise GeometryError('Buddy-Referenzplan gehört zu einer anderen Meshversion.')
    labels=classify(surface.sample(),REFERENCE_PALETTE)
    reference={'version':1,'mesh_hash':MESH_HASH,'face_count':len(labels),'face_regions':labels.tolist(),
        'regions':[{'id':i,'color':color} for i,color in enumerate(REFERENCE_PALETTE)],
        'filament_ids':[],'nozzle_count':2,'ratio_step_percent':5}
    return settings,labels,reference


def anatomical_masks(surface,labels):
    mesh=surface.mesh;centers=mesh.triangles_center;masks={};analysis={}
    for name,color,grow in [('nose',4,12),('rolled-map',5,20)]:
        seed=max(face_components(mesh,labels==color),key=lambda ids:mesh.area_faces[ids].sum())
        domain=seed_geodesic_faces(mesh,seed,grow)
        masks[name],analysis[name]=anatomical_seed_cut(mesh,seed,np.setdiff1d(np.arange(len(mesh.faces)),domain),smoothing_iterations=30,concavity_scale=.06)
    for side,sign in [('left',-1),('right',1)]:
        seed=np.flatnonzero((sign*centers[:,0]>40)&(sign*centers[:,0]<115)&(centers[:,1]<-440)&(centers[:,1]>-510)&(centers[:,2]>815)&(centers[:,2]<895)&np.isin(labels,[4,5]))
        domain=seed_geodesic_faces(mesh,seed,8)
        ids,analysis[side+'-eye']=anatomical_seed_cut(mesh,seed,np.setdiff1d(np.arange(len(mesh.faces)),domain),smoothing_iterations=30,concavity_scale=.06)
        mask=np.isin(np.arange(len(mesh.faces)),ids)
        for hole in face_components(mesh,~mask):
            if mesh.area_faces[hole].sum()<5000:mask[hole]=True
        masks[side+'-eye']=np.flatnonzero(mask)
    ears=sorted(face_components(mesh,labels==2),key=lambda ids:-mesh.area_faces[ids].sum())[:2]
    for index,name,grow in [(0,'right-ear',2),(1,'left-ear',5)]:
        core=np.flatnonzero((abs(centers[:,0])<100)|(centers[:,2]<680)|(centers[:,1]<-445));seed=np.setdiff1d(ears[index],core)
        ids,analysis[name]=anatomical_seed_cut(mesh,seed,core,smoothing_iterations=30,concavity_scale=.06)
        masks[name]=seed_geodesic_faces(mesh,ids,grow)
    return masks,analysis


def suggest_buddy_plan(surface,reference_plan,settings,mesh_hash,filaments,*,current_plan=None):
    settings,labels,reference=_source(surface,settings,mesh_hash,reference_plan)
    masks,analysis=anatomical_masks(surface,labels)
    document,material_report,_=propose_materials(surface,reference,masks,[])
    rows=list(filaments.values()) if isinstance(filaments,dict) else list(filaments)
    stock={row['id']:row for row in rows if row.get('id') and row.get('hex') and row.get('allowed',True) and (not settings.get('owned_filaments_only') or row.get('owned'))}
    if not stock:raise GeometryError('Buddy braucht erlaubte reale Bestandsspulen für den editierbaren Materialvorschlag.')
    previous=_asdict(current_plan) if current_plan is not None else {}
    previous_regions={r['id']:r for r in previous.get('regions',[])} if previous.get('construction_preset')==PRESET and previous.get('face_regions')==document['face_regions'] else {}
    preferred={key:row for key,row in stock.items() if row.get('owned')} or stock
    anchor=previous_regions.get(0,{}).get('filament_id')
    if anchor not in stock:anchor=min(preferred,key=lambda key:float(delta_e_2000(srgb_to_lab(hex_rgb('#ECA24D')),srgb_to_lab(hex_rgb(preferred[key]['hex'])))))
    material=str(stock[anchor].get('material','')).casefold()
    eligible={key:row for key,row in stock.items() if material and str(row.get('material','')).casefold()==material}
    if not eligible:raise GeometryError('Buddy braucht eine bekannte kompatible Materialart, keine erfundenen Profile.')
    preferred_eligible={key:row for key,row in eligible.items() if row.get('owned')} or eligible
    chosen={};choices=[]
    for i,region in enumerate(document['regions']):
        physical=PALETTE[i][2];desired=region['color']
        if physical not in chosen:
            pool=preferred_eligible
            # Imported swatches are unmeasured. Prefer an explicitly named Navy
            # over a green-labelled spool with a deceptively navy HEX.
            if physical=='navy':
                named={key:row for key,row in pool.items() if any(word in str(row.get('name','')).casefold() for word in ['navy','dunkelblau'])}
                if named:pool=named
            chosen[physical]=min(pool,key=lambda key:float(delta_e_2000(srgb_to_lab(hex_rgb(desired)),srgb_to_lab(hex_rgb(pool[key]['hex'])))))
        explicit=previous_regions.get(i,{}).get('filament_id')
        spool=eligible[explicit if explicit in eligible else chosen[physical]]
        region['filament_id']=spool['id'];region['color']=spool['hex']
        choices.append({'region_id':i,'physical_class':physical,'filament_id':spool['id'],'name':spool.get('name'),'brand':spool.get('brand'),'material':spool.get('material'),'owned':spool.get('owned',False),'target_color':desired,'stock_color':spool['hex'],
            'delta_e_2000':float(delta_e_2000(srgb_to_lab(hex_rgb(desired)),srgb_to_lab(hex_rgb(spool['hex']))))})
    document['construction_preset']=PRESET;document['note']='Modellgebundener Buddy-Entwurf: Halsband-Montagefolge, Steckteile und zwei Klebeaugen. Farben/Spulen editierbar; Originalkonturen bleiben gebunden. Keine physische Farb- oder Belastungsfreigabe.'
    return document,{'construction_preset':PRESET,'source_sha256_required':SOURCE_SHA256,'source_signature':SOURCE_SIGNATURE,
        'mesh_hash':MESH_HASH,'reference_plan_hash':digest(_asdict(reference_plan)) if reference_plan is not None else None,
        'selected_materials':choices,'anatomical_analysis':analysis,'material_decisions':material_report['decisions'],
        'suggested_settings':{'pin_clearance_mm':.05,'build_volume_mm':[300,320,320],'plate_margin_mm':10,'part_gap_mm':20},
        'anatomical_face_masks_editable':False,'colors_and_spools_editable':True,'mixed_supported':False,'automatic_approval':False,
        'requires_constructed_material_limit_check':True,'requires_native_profiles':True,'physical_fit_verified':False,'warnings':['Bestands-HEX sind ungemessen; Spulenname und reale Farbe vor dem nativen Druck prüfen. Navy bevorzugt ausdrücklich als Navy/Dunkelblau bezeichnete Spulen, um widersprüchliche Grün-HEX nicht blind zu übernehmen.']}


def fit_cap(points,inward,anchor_offset=0.,*,minimum_refinements=0,dense_check=False,query):
 cap=interior_cap(points);boundary=cKDTree(points)
 def pushed(values):
  values=np.asarray(values).copy();isboundary=boundary.query(values)[0]<1e-7
  values[~isboundary]+=inward*anchor_offset
  unresolved=~isboundary & (query.values(values)>-.03)
  for depth in [.05,.1,.25,.5,1,2,4,8,16,32]:
   selected=np.flatnonzero(unresolved)
   if not len(selected):break
   candidate=values[selected]+inward*depth;valid=query.values(candidate)<-.04
   values[selected[valid]]=candidate[valid];unresolved[selected[valid]]=False
  if unresolved.any():raise ValueError('No source-inside cap point found along inward direction')
  return values
 v=pushed(cap.vertices);cap=mesh_from_triangles(v[cap.faces],check=False)
 for iteration in range(3):
  checkpoints=np.concatenate([cap.vertices,cap.triangles_center,cap.vertices[cap.edges_unique].mean(axis=1)]) if dense_check else sample_surface(cap,1500)
  maxdist=float(query.values(checkpoints).max())
  if maxdist<=(.005 if dense_check else .035) and iteration>=minimum_refinements:return cap
  # Refine internal edges only; original visible boundary vertices/edges stay exact.
  edges=np.sort(cap.edges,axis=1);unique,count=np.unique(edges,axis=0,return_counts=True)
  inner={tuple(e) for e in unique[count==2]};edge_list=sorted(inner);midpoints=pushed(cap.vertices[np.asarray(edge_list)].mean(axis=1));mid=dict(zip(edge_list,midpoints))
  triangles=[]
  centers=pushed(cap.triangles_center)
  for face_index,ids in enumerate(cap.faces):
   ring=[]
   for j in range(3):
    a=int(ids[j]);b=int(ids[(j+1)%3]);ring.append(cap.vertices[a]);edge=tuple(sorted((a,b)))
    if edge in mid:ring.append(mid[edge])
   center=centers[face_index];ring=np.array(ring)
   triangles.extend(np.stack([ring,np.roll(ring,-1,axis=0),np.repeat(center[None],len(ring),axis=0)],axis=1))
  cap=mesh_from_triangles(np.array(triangles),check=False)
 raise ValueError('Cap still exits source after bounded local fitting')


def common_axis(source,indexes,direction,radius=6,length=10,cap_anchor_offset=0.,*,minimum_cap_refinements=0,dense_cap_check=False,query):
 direction=np.asarray(direction,float);direction/=np.linalg.norm(direction);basis=frame(direction)
 patch=patch_from_faces(source,indexes);keep=np.ones(len(source.faces),bool);keep[indexes]=False
 caps=[fit_cap(patch.vertices[loop],-direction,cap_anchor_offset,minimum_refinements=minimum_cap_refinements,dense_check=dense_cap_check,query=query) for loop in boundary_loops(patch)]
 target0=mesh_from_triangles(np.concatenate([patch.triangles,*[cap.triangles for cap in caps]]));rest0=mesh_from_triangles(np.concatenate([source.triangles[keep],*[cap.triangles[:,::-1] for cap in caps]]))
 require_solid(target0);require_solid(rest0);q=DistanceQuery(rest0)
 target=[patch.triangles];rest=[source.triangles[keep]];summaries=[]
 for cap in caps:
  root=cap.copy();root.invert();outline=projected_outline(root,basis)
  pins=pick_connectors(outline,root,basis,0,radius=radius,length=length,clearance=.05,count=2,shape='keyed')
  pins=[pin for pin in pins if q.values(np.array([[pin.x,pin.y,pin.tip_z-.35]])@basis.T)[0]<-(radius+.5)]
  target.append(root_with_connectors(root,basis,pins,socket=False));rest.append(root_with_connectors(root,basis,pins,socket=True));summaries.extend([pin.summary(basis) for pin in pins])
 target=mesh_from_triangles(np.concatenate(target));rest=mesh_from_triangles(np.concatenate(rest));require_solid(target);require_solid(rest)
 check=check_insert_path(target,rest,direction,travel_mm=40)
 if not check['passed']:raise ValueError(str(check))
 return [Part('body','Body',rest,'#ECA24D',role='body'),Part('appendage','Appendage',target,'#CF8433',assembly_direction=direction.tolist(),connectors=summaries)],check


def source_mask(surface,current,source_ids):
    distance,index,_=nearest(surface,current.triangles_center)
    return np.flatnonzero((distance<=.03)&np.isin(index,source_ids))


def single_solid(mesh):
    quality=validate_mesh(mesh)
    if not quality['valid'] or quality['components']!=1:raise GeometryError('Each physical part must be one closed connected solid')
    return quality


def fits_h2d(extents):
    return any(p[0]+16<=300 and p[1]+16<=320 and p[2]<=320 for p in permutations(extents))


def tile_connected(parts,out):
    """Peel one connected component per structural split; never bundle loose legs."""
    pending=list(parts);done=[];splits=[]
    while pending:
        part=pending.pop(0)
        if fits_h2d(part.mesh.extents):done.append(part);continue
        if len(done)+len(pending)>100:raise GeometryError('More than 100 physical parts; review scale and assembly')
        errors=[];winner=None
        for axis in np.argsort(part.mesh.extents)[::-1]:
            axis=int(axis);lo,hi=part.mesh.bounds[:,axis]
            for fraction in [.50,.45,.55,.40,.60]:
                pos=lo+(hi-lo)*fraction+.000137
                for positive in [True,False]:
                    try:
                        primary,remainder,retention=clip_primary_component(part.mesh,axis,pos,positive)
                        low,high=(remainder,primary) if positive else (primary,remainder)
                        a,b,pins,direction=joint_between_halves(low,high,axis,pos,radius=6,length=16,clearance=.05,shape='keyed',count=2)
                        single_solid(a);single_solid(b)
                        if not pins:raise GeometryError('No safe structural key fits')
                        target,obstacle=(b,a) if positive else (a,b)
                        motion=-direction if positive else direction
                        check=check_insert_path(target,obstacle,motion,travel_mm=40)
                        if not check['passed']:raise GeometryError('Structural sibling extraction path blocked')
                        winner=(axis,pos,a,b,pins,direction,check,retention,positive);break
                    except GeometryError as error:errors.append(str(error))
                if winner:break
            if winner:break
        if not winner:
            from figuraforge.geometry.buddy_collar import boolean_structural_split
            for axis in np.argsort(part.mesh.extents)[::-1]:
                axis=int(axis);lo,hi=part.mesh.bounds[:,axis]
                for fraction in [.50,.45,.55]:
                    pos=lo+(hi-lo)*fraction+.000137
                    for positive in [True,False]:
                        try:
                            work=out/'boolean-structural'/(part.id+'-'+uid())
                            a,b,pins,direction,retention=boolean_structural_split(part.mesh,axis,pos,positive,work)
                            target,obstacle=(b,a) if positive else (a,b)
                            check=check_insert_path(target,obstacle,-direction if positive else direction,travel_mm=40)
                            if not check['passed']:raise GeometryError('Boolean sibling extraction path blocked')
                            retention['algorithm']='local closed Blender Boolean; source fragments retained, no remesh'
                            winner=(axis,float(np.float32(pos)),a,b,pins,direction,check,retention,positive);break
                        except GeometryError as error:errors.append('Boolean: '+str(error))
                    if winner:break
                if winner:break
        if not winner:
            part.save(out/'blocked-parts')
            (out/'blocked-structural.json').write_text(json.dumps({'part':part.summary(),'errors':errors},indent=2))
            raise GeometryError('No reliable connected structural cut: '+'; '.join(errors[:4]))
        axis,pos,a,b,pins,direction,check,retention,positive=winner
        split_id=f'joint-{len(splits)+1:03d}';row={'id':split_id,'parent':part.id,'axis':axis,'position_mm':pos,
            'pins':pins,'path_check':check,'primary_positive':positive,'retention':retention,'discarded_candidates':errors}
        children=[]
        for suffix,mesh in [('a',a),('b',b)]:
            child=Part(part.id+'-'+suffix,part.name+' / '+suffix.upper(),mesh,part.color,part.color_index,part.role,
                       None,[],part.warnings.copy())
            child.warnings.append(f'Structural interface {split_id}: see assembly tree, not an independently certified global motion')
            children.append(child);pending.append(child)
        row['children']=[child.id for child in children];splits.append(row)
        (out/'structural-progress.json').write_text(json.dumps(splits,indent=2)+'\n')
        print(f'{split_id}: {part.id}, {len(pins)} keys; pending {len(pending)}, fitted {len(done)}',flush=True)
    return done,splits


def assign_buddy_materials(parts,surface,plan,settings,*,reference_plan=None):
    mesh=surface.mesh
    plan=_asdict(plan);settings,labels,reference=_source(surface,settings,plan.get('mesh_hash'),reference_plan)
    masks,_=anatomical_masks(surface,labels);canonical,_,_=propose_materials(surface,reference,masks,[])
    if plan.get('face_regions')!=canonical['face_regions']:raise GeometryError('Buddy-Materialmasken gehören nicht zum geprüften Anatomieentwurf.')
    if any(r.get('color_mode')=='mixed' or r.get('strategy')=='mixed' for r in plan['regions']):raise GeometryError('Buddy-v1 braucht zunächst die geprüften festen Materialzuordnungen.')
    report={}
    _,material_report,_=propose_materials(surface,reference,masks,parts)
    if not material_report['two_materials_per_part_passed']:raise GeometryError('Buddy-Zweimaterialvorschlag nicht vollständig: '+str(material_report['violations']))
    report['part_region_ids']=material_report['part_region_ids'];report['material_decisions']=material_report['decisions'];report['part_filament_ids']={}
    region_map={r['id']:r for r in plan['regions']}
    for part in parts:
        region_ids=report['part_region_ids'][part.id];ids=sorted({region_map[i].get('filament_id') for i in region_ids if region_map[i].get('filament_id')})
        if len(ids)>plan.get('nozzle_count',2):raise GeometryError('Buddy-Teil '+part.id+' verwendet mehr physische Spulen als Düsen.')
        report['part_filament_ids'][part.id]=ids or material_report['part_physical_classes'][part.id]
        distances,index,_=nearest(surface,part.mesh.triangles_center);exterior=(distances<=.03)&((part.mesh.face_normals*mesh.face_normals[index]).sum(axis=1)>.95)
        source_regions=np.asarray(plan['face_regions'])[index];areas={i:float(part.mesh.area_faces[exterior&(source_regions==i)].sum()) for i in region_ids}
        dominant=max(region_ids,key=lambda i:areas[i]);part.color_index=dominant;part.color=region_map[dominant]['color'];part.filament_id=ids[0] if len(ids)==1 else None
    return report


def construct_buddy(surface,plan,settings,*,reference_plan,workdir):
    plan=_asdict(plan);settings,labels,reference=_source(surface,settings,plan.get('mesh_hash'),reference_plan)
    if abs(float(settings.get('pin_clearance_mm',.05))-.05)>1e-8:
        raise GeometryError('Buddy-Preset verwendet die physisch verglichene 0,05-mm-Radialpassung. Bitte Einstellung auf 0,05 mm setzen; keine unbemerkte Überschreibung.')
    if any(r.get('color_mode')=='mixed' or r.get('strategy')=='mixed' for r in plan['regions']):
        raise GeometryError('Buddy-v1 ist zunächst mit festen Bestandsspulen verifiziert. Mixed für Fell erst mit getrenntem festen Halsbandgold und nativer Vorlage erneut prüfen.')
    masks,analysis=anatomical_masks(surface,labels)
    canonical,_,_=propose_materials(surface,reference,masks,[])
    if plan.get('face_regions')!=canonical['face_regions']:
        raise GeometryError('Buddy-Anatomie-/Materialmasken wurden geändert. Modellgebundene Konstruktion neu prüfen; Maskenänderungen werden nicht ignoriert.')
    expected={r['id']:(r['strategy'],r['part_group'],r['cut_type']) for r in canonical['regions']}
    if {r['id']:(r['strategy'],r['part_group'],r['cut_type']) for r in plan['regions']}!=expected:
        raise GeometryError('Buddy-Preset hat feste anatomische Teilgruppen; Schnittänderungen separat prüfen.')
    out=Path(workdir)/('buddy-'+uid());out.mkdir(parents=True,exist_ok=False)
    mesh=surface.mesh;centers=mesh.triangles_center;query=DistanceQuery(mesh);build_axis=partial(common_axis,query=query);args=SimpleNamespace(include_collar=True)
    report={'construction_preset':PRESET,'source_sha256_required':SOURCE_SHA256,'source_signature':SOURCE_SIGNATURE,'mesh_hash':MESH_HASH,
        'plan_hash':digest(plan),'source_original_preserved':True,'source_volume_mm3':float(mesh.volume),'anatomical_attempts':[],
        'warnings':['Modellgebundener Buddy-Entwurf, keine physische Belastungs-/Farbfreigabe.','Augen sind geschlossene Klebeteile ohne sichere Stifte; Klebespiel physisch prüfen.'],
        'physical_fit_verified':False,'physical_color_verified':False,'local_diagnostics_directory':str(out)}
    ears=sorted(face_components(mesh,labels==2),key=lambda ids:-mesh.area_faces[ids].sum())[:2]
    remaining=mesh.copy();parts=[]
    dark=sorted(face_components(mesh,labels==4),key=lambda ids:-mesh.area_faces[ids].sum())
    nose_seed=dark[0];domain=seed_geodesic_faces(mesh,nose_seed,12)
    nose_ids,nose_cut=anatomical_seed_cut(mesh,nose_seed,np.setdiff1d(np.arange(len(mesh.faces)),domain),smoothing_iterations=30,concavity_scale=.06)
    built,nose_check=build_axis(remaining,nose_ids,[0,-1,0],radius=6,length=10,cap_anchor_offset=2.)
    for part in built:single_solid(part.mesh)
    nose=built[1];nose.id='nose';nose.name='Buddy Nase – vollständige dunkle Region';nose.color='#292119';nose.role='color-body'
    parts.append(nose);remaining=built[0].mesh;np.save(out/'nose-source-face-ids.npy',nose_ids)
    report['anatomical_attempts'].append({'part_id':'nose','cut':nose_cut,'cap_anchor_offset_mm':2.,'path_check':nose_check,'parts':[nose.summary()]})
    print('nose built with '+str(len(nose.connectors))+' keys',flush=True)
    for side,sign in [('left',-1),('right',1)]:
        seed=np.flatnonzero((sign*centers[:,0]>40)&(sign*centers[:,0]<115)&(centers[:,1]<-440)&(centers[:,1]>-510)&(centers[:,2]>815)&(centers[:,2]<895)&np.isin(labels,[4,5]))
        domain=seed_geodesic_faces(mesh,seed,8)
        eye_ids,eye_cut=anatomical_seed_cut(mesh,seed,np.setdiff1d(np.arange(len(mesh.faces)),domain),smoothing_iterations=30,concavity_scale=.06)
        eye_mask=np.isin(np.arange(len(mesh.faces)),eye_ids)
        for hole in face_components(mesh,~eye_mask):
            if mesh.area_faces[hole].sum()<5000:eye_mask[hole]=True
        eye_ids=np.flatnonzero(eye_mask)
        built,eye_check=build_axis(remaining,source_mask(surface,remaining,eye_ids),[sign*.2,-1,0],radius=1.5,length=3,cap_anchor_offset=20.,minimum_cap_refinements=1,dense_cap_check=True)
        for part in built:single_solid(part.mesh)
        eye=built[1];eye.id=side+'-eye';eye.name='Buddy '+side+' Auge – Creme und Pupille';eye.color='#E2B16D';eye.role='color-body'
        if not eye.connectors:eye.warnings.append('Geschlossenes Klebeteil: keine sichere Steckverbindung mit den geprüften Parametern. Keine Press-/Steckpassung behauptet; Klebespalt und reale Montage noch prüfen.')
        parts.append(eye);remaining=built[0].mesh;np.save(out/(side+'-eye-source-face-ids.npy'),eye_ids)
        report['anatomical_attempts'].append({'part_id':eye.id,'cut':eye_cut,'cap_anchor_offset_mm':20.,'minimum_cap_refinements':1,'dense_cap_check':True,'path_check':eye_check,'parts':[eye.summary()]})
        print(side+' eye built with '+str(len(eye.connectors))+' keys (zero explicitly means glue-on)',flush=True)
    cream=sorted(face_components(mesh,labels==5),key=lambda ids:-mesh.area_faces[ids].sum())[0]
    paper_domain=seed_geodesic_faces(mesh,cream,20)
    paper_ids,paper_cut=anatomical_seed_cut(mesh,cream,np.setdiff1d(np.arange(len(mesh.faces)),paper_domain),smoothing_iterations=30,concavity_scale=.06)
    built,paper_check=build_axis(remaining,source_mask(surface,remaining,paper_ids),[.2,.15,1],radius=3,length=6,cap_anchor_offset=2.)
    for part in built:single_solid(part.mesh)
    paper=built[1];paper.id='rolled-map';paper.name='Buddy gerollte Karte';paper.color='#E2B16D';paper.role='color-body'
    parts.append(paper);remaining=built[0].mesh;np.save(out/'rolled-map-source-face-ids.npy',paper_ids)
    report['anatomical_attempts'].append({'part_id':'rolled-map','cut':paper_cut,'cap_anchor_offset_mm':2.,'path_check':paper_check,'parts':[paper.summary()]})
    print('rolled map built with '+str(len(paper.connectors))+' keys',flush=True)
    for index,name,direction,grow in [(0,'right-ear',[1,0,0],2),(1,'left-ear',[-1,0,0],5)]:
        core=np.flatnonzero((np.abs(centers[:,0])<100)|(centers[:,2]<680)|(centers[:,1]<-445));seed=np.setdiff1d(ears[index],core)
        ids,cut=anatomical_seed_cut(mesh,seed,core,smoothing_iterations=30,concavity_scale=.06)
        ids=seed_geodesic_faces(mesh,ids,grow);np.save(out/(name+'-source-face-ids.npy'),ids)
        built,check=build_axis(remaining,source_mask(surface,remaining,ids),direction,cap_anchor_offset=1.)
        for part in built:single_solid(part.mesh)
        part=built[1];part.id=name;part.name='Buddy '+name+' – organische Wurzel';part.role='color-body'
        part.color='#CF8433';parts.append(part);remaining=built[0].mesh
        report['anatomical_attempts'].append({'part_id':name,'cut':cut,'boundary_growth_mm':grow,'cap_anchor_offset_mm':1.,'path_check':check,'parts':[part.summary()]})
        print(name+' built with '+str(len(part.connectors))+' keys',flush=True)
    # Ear construction does not change the tail neighborhood. Prefer the proximal
    # root even though a farther cut would make the tail fit one plate sooner.
    pos=275.000137;high,low,retention=clip_primary_component(remaining,1,pos,True)
    a,b,pins,direction=joint_between_halves(low,high,1,pos,radius=6,length=16,clearance=.05,shape='keyed',count=2)
    check=check_insert_path(b,a,-direction,travel_mm=40)
    if not check['passed'] or len(pins)!=2:raise GeometryError('Tail root assembly rejected')
    single_solid(a);single_solid(b);remaining=a
    parts.append(Part('tail','Buddy Schwanz – proximale Wurzel',b,'#ECA24D',role='color-body',assembly_direction=(-direction).tolist(),connectors=pins))
    report['anatomical_attempts'].append({'part_id':'tail','position_mm':pos,'retention':retention,'path_check':check,'pins':pins})
    parts.insert(0,Part('body','Buddy Körper mit Ausrüstung',remaining,'#ECA24D',role='body'))
    if args.include_collar:
        from figuraforge.geometry.buddy_collar import build_collar
        collar_parts,collar_report=build_collar(parts[0].mesh,out/'collar-kernel',source_binding={'source_sha256':SOURCE_SHA,'mesh_hash':MESH_HASH,'height_mm':1000})
        parts=collar_parts+parts[1:];report['collar_assembly']=collar_report
        report['warnings'].append('Collar assembly follows its explicitly checked sequence before nose/eyes/ears/map/tail attachment; no simultaneous global collar extraction is claimed.')
    report['anatomical_combined_checks']=_combined_checks(parts,40)
    parts,splits=tile_connected(parts,out);report['structural_splits']=splits
    report.update(assign_buddy_materials(parts,surface,plan,settings,reference_plan=reference_plan))
    report['quality']={p.id:single_solid(p.mesh) for p in parts};report['parts_volume_mm3']=sum(float(p.mesh.volume) for p in parts)
    report['clearance_void_mm3']=report['source_volume_mm3']-report['parts_volume_mm3']
    if report['clearance_void_mm3']<-.1:raise GeometryError('Buddy-Teile überschreiten das Quellvolumen.')
    report['parameter_policy']='1000mm/Y-up, .05 radial; anatomy-specific Ø12/L10 ears/nose, Ø6/L6 map, Ø12/L16 structure, Ø4/L6 collar seam. Generic pin sizes superseded visibly by preset.'
    report['global_final_motion_verified']=False;report['automatic_approval']=False
    report['assembly_instructions_de']=assembly_instructions(report)
    report['assembly_connections']=connection_summary(report)
    (out/'construction-check.json').write_text(json.dumps(report,indent=2)+'\n')
    return parts,report


def validate_buddy_pack_settings(volume,margin,gap):
    """Reject unsupported printer/spacing inputs before expensive construction."""
    if tuple(volume)!=(300,320,320) or margin<10:raise GeometryError('Buddy braucht den geprüften H2D-Gemeinschaftsraum 300×320×320 mm mit mindestens10 mm XY-Rand für Stützen.')
    if gap<20:raise GeometryError('Buddy braucht mindestens20 mm Abstand zwischen Bauteilen für reale Tree-Stützen; Druckplanung neu berechnen.')


def pack_buddy_parts(parts,*,construction_report,volume=(300,320,320),margin=10,gap=20):
    validate_buddy_pack_settings(volume,margin,gap)
    mapping=construction_report.get('part_filament_ids',{})
    if set(mapping)!=set(p.id for p in parts):raise GeometryError('Buddy-Druckplanung braucht die Materialunion jedes tatsächlichen Teils.')
    batches=[]
    special={part.id:part for part in parts if part.id in {'nose','left-eye','right-eye','rolled-map'} and part.assembly_direction}
    for part in sorted(parts,key=lambda p:(-len(mapping[p.id]),-abs(p.mesh.volume),p.id)):
        if part.id in special:continue
        physical=set(mapping[part.id])
        if not 1<=len(physical)<=2:raise GeometryError('Buddy-Teil hat keine gültige Zweispulen-Zuordnung.')
        target=next((batch for batch in batches if len(batch['physical']|physical)<=2),None)
        if target is None:target={'physical':set(),'parts':[]};batches.append(target)
        target['physical']|=physical;target['parts'].append(part)
    plates=[]
    for batch in batches:
        packed=pack_parts(batch['parts'],volume=volume,margin=max(margin,10),gap=gap,max_colors=len(batch['parts']))
        for plate in packed:
            # This reviewed tall torso tile grows a tree foot 24.8 mm left of
            # its model bbox. The actual support envelope fits the bed; center
            # only X, keeping the reserved tower's free Y band unchanged.
            if len(plate['placements'])==1 and plate['placements'][0]['part_id'] in {'collar-body-a-b-a-a','collar-body-b-a-a-a'}:
                item=plate['placements'][0];delta=(volume[0]-item['rect'][2])/2-item['rect'][0]
                if item['part_id']=='collar-body-a-b-a-a' and len(mapping[item['part_id']])==1:
                    # Mono-material slicing grows a different tree foot: its
                    # centerline X=25.181 still crosses X25 by half linewidth.
                    delta+=1.0
                item['rect'][0]+=delta;item['transform'][0][3]+=delta
                item['support_placement_policy']='X centered after actual support envelope exceeded shared-bed X min; Y unchanged for tower'
                item['support_lateral_shift_mm']=delta
            plate['id']=len(plates)+1;actual={spool for item in plate['placements'] for spool in mapping[item['part_id']]};plate['physical_filament_ids']=sorted(actual);plate['physical_spool_count']=len(actual);plate['material_batch']=' / '.join(sorted(actual));plates.append(plate)
    # Reserve a conservative 55×85-mm prime-tower footprint for two-spool
    # plates. Split occupied multi-part plates instead of silently overlapping.
    reserved=[]
    for plate in plates:
        if plate['physical_spool_count']>1 and _buddy_tower(plate) is None:
            if len(plate['placements'])<2:raise GeometryError('Buddy-Platte hat keinen freien Prime-Tower-Bereich.')
            for item in plate['placements']:
                own=copy.deepcopy(plate);own['placements']=[item];physical=set(mapping[item['part_id']])
                own['physical_filament_ids']=sorted(physical);own['physical_spool_count']=len(physical)
                if len(physical)>1 and _buddy_tower(own) is None:raise GeometryError('Buddy-Einzelteil lässt keinen sicheren Tower-Bereich frei.')
                reserved.append(own)
        else:reserved.append(plate)
    plates=reserved
    for plate in plates:
        # The right ring's sliced support envelope is 308×133 mm: too
        # wide for shared X, but fits shared Y. Rotate in XY only, keeping
        # gravity/support contacts unchanged, then center that measured
        # support envelope (not merely the narrower model bbox).
        if len(plate['placements'])==1 and plate['placements'][0]['part_id']=='collar-right':
            item=plate['placements'][0];x,y,w,h=item['rect']
            rotation=np.array([[0.,-1.,0.,376.617],[1.,0.,0.,10.238],[0.,0.,1.,0.],[0.,0.,0.,1.]])
            item['transform']=np.round(rotation@np.asarray(item['transform']),9).tolist()
            item['rect']=[376.617-y-h,10.238+x,h,w]
            item['support_placement_policy']='XY quarter turn; actual 308×133 mm support envelope centered in 300×320 shared bed, Z unchanged'

    for index,plate in enumerate(plates,1):plate['id']=index;plate['prime_tower_reserve']=_buddy_tower(plate) if plate['physical_spool_count']>1 else None
    for ident in ['rolled-map','left-eye','right-eye','nose']:
        if ident not in special:continue
        part=special[ident]
        rotation=frame(np.asarray(part.assembly_direction)*(-1 if ident=='nose' else 1)).T
        vertices=part.mesh.vertices@rotation.T;lower=vertices.min(axis=0);extent=np.ptp(vertices,axis=0)
        if (extent[:2]+2*margin>np.asarray(volume[:2])).any() or extent[2]>volume[2]:raise GeometryError('Buddy-Anbauteil passt mit seiner vorgeschriebenen Druckorientierung nicht in den Bauraum.')
        xy=(np.asarray(volume[:2])-extent[:2])/2
        transform=np.eye(4);transform[:3,:3]=rotation;transform[:3,3]=-lower+[xy[0],xy[1],0]
        policy='nose keys vertical +Z; rounded visible base needs support/raft' if ident=='nose' else ('map visible side +Z, keys -Z; support hidden root and use raft' if ident=='rolled-map' else 'eye visible side +Z; support hidden fitted back and use raft')
        item={'part_id':ident,'transform':np.round(transform,9).tolist(),'rect':[float(xy[0]),float(xy[1]),float(extent[0]),float(extent[1])],
              'height_mm':float(extent[2]),'color':part.color,'orientation_policy':policy,
              'support_status':'tree support and raft required; inspect support contacts, nose visible-surface marks possible'}
        physical=sorted(mapping[ident]);plate={'id':len(plates)+1,'colors':[part.color],'placements':[item],'volume_mm':list(volume),
            'physical_filament_ids':physical,'physical_spool_count':len(physical),'material_batch':' / '.join(physical)}
        plate['prime_tower_reserve']=_buddy_tower(plate) if len(physical)>1 else None
        if len(physical)>1 and plate['prime_tower_reserve'] is None:raise GeometryError('Buddy-Anbauteil lässt keinen freien Towerbereich.')
        plates.append(plate)
    if not validate_packing(parts,plates)['passed']:raise GeometryError('Buddy-Plattenvorschlag ist geometrisch ungültig.')
    return plates


def build_buddy_parts_preview(parts,surface,plan,filaments,reference_plan=None,native_settings=None):
    from figuraforge.geometry.preview import mesh_preview,_encode
    plan=_asdict(plan);stock=filaments if isinstance(filaments,dict) else {f['id']:f for f in filaments};regions={r['id']:r for r in plan['regions']};tags=np.asarray(plan['face_regions']);meshes=[]
    rgb={}
    for i,region in regions.items():
        if region.get('color_mode')=='mixed':raise GeometryError('Buddy-Mixed-Vorschau braucht zuerst eine separat geprüfte native Rezeptvorlage.')
        spool=stock.get(region.get('filament_id'))
        if not spool or not spool.get('hex'):raise GeometryError('Buddy-Vorschau benötigt die konkret ausgewählte Bestandsspule.')
        rgb[i]=hex_rgb(spool['hex'])
    for part in parts:
        distance,index,_=nearest(surface,part.mesh.triangles_center);exterior=(distance<=.03)&((part.mesh.face_normals*surface.mesh.face_normals[index]).sum(axis=1)>.95);labels=tags[index]
        weights={}
        for i,region in regions.items():
            spool=region['filament_id'];weights[spool]=weights.get(spool,0.)+float(part.mesh.area_faces[exterior&(labels==i)].sum())
        dominant=max(weights,key=weights.get) if any(weights.values()) else part.filament_id
        fallback=hex_rgb(stock[dominant]['hex']) if dominant in stock else hex_rgb(part.color)
        colors=np.repeat(np.asarray(fallback)[None],len(part.mesh.faces),axis=0)
        for i,color in rgb.items():colors[exterior&(labels==i)]=color
        record=mesh_preview(part.mesh,part.color,ident=part.id,name=part.name,role=part.role,direction=part.assembly_direction,corner_rgb=np.repeat(colors[:,None,:],3,axis=1))
        record['normals']=_encode(_buddy_corner_normals(part.mesh,surface,exterior,index));meshes.append(record)
    return {'format':'figuraforge-mesh-v1','up_axis':'Z','unit':'millimeter','meshes':meshes},['Bestands-HEX ist eine unkalibrierte Farbannäherung; keine geslicte Druckvorschau.']


def _buddy_corner_normals(mesh,surface,exterior,source_ids):
    """Source shading outside, explicit flat construction surfaces inside."""
    import trimesh
    normals=np.repeat(mesh.face_normals[:,None,:],3,axis=1)
    if exterior.any():
        ids=source_ids[exterior]
        original=np.repeat(surface.mesh.triangles[ids],3,axis=0)
        bary=trimesh.triangles.points_to_barycentric(original,mesh.triangles[exterior].reshape(-1,3)).reshape(-1,3,3)
        bary=np.maximum(bary,0);bary/=np.maximum(bary.sum(axis=2,keepdims=True),1e-12)
        corner=surface.mesh.vertex_normals[surface.mesh.faces[ids]]
        interpolated=np.einsum('ncs,nsv->ncv',bary,corner)
        interpolated/=np.maximum(np.linalg.norm(interpolated,axis=2,keepdims=True),1e-12)
        normals[exterior]=interpolated
    return normals


def _buddy_tower(plate):
    # Pack-frame coordinates; actual H2D hardware origin is added at export.
    # Actual 35-mm tower includes the official 8-mm ribs: measured width
    # 50.2 mm. Grow the reserved box around existing anchors so previously
    # checked native placements remain valid whenever the broader box fits.
    width,depth=55.,85.
    for anchor_y in [232.,152.,72.,8.]:
        for anchor_x in [247.,197.,147.,97.,47.,8.]:
            x,y=anchor_x-4,anchor_y-5
            if all(x+width+5<=xx or xx+ww+5<=x or y+depth+5<=yy or yy+hh+5<=y
                   for xx,yy,ww,hh in [item['rect'] for item in plate['placements']]):
                return {'rect':[x,y,width,depth],'prime_tower_width_mm':35.,'physical_xy':[anchor_x+30,anchor_y+5],
                        'scope':'includes official tower ribs; actual sliced extrusion paths remain mandatory'}
    return None


def configure_buddy_plate(config,plate):
    """Explicit local support routing; no material temperatures are invented."""
    from figuraforge.services.mixed_filament import validate_native_settings,mark_explicit_process_overrides
    native=validate_native_settings(config)
    slots=sorted(set(plate.get('native_physical_slots',[])))
    if not 1<=len(slots)<=2 or not set(slots)<=set(native['physical_slots']):
        raise GeometryError('Buddy-Stützen benötigen die ein bis zwei tatsächlich belegten physischen Plattenspulen.')
    source=copy.deepcopy(config);settings=copy.deepcopy(config)
    if len(slots)>1:
        tower=plate.get('prime_tower_reserve') or _buddy_tower(plate)
        if tower is None:raise GeometryError('Buddy-Platte braucht eine freie Prime-Tower-Reserve; Druckplanung neu berechnen.')
        settings.update(prime_tower_width='35',wipe_tower_x=[str(tower['physical_xy'][0])],wipe_tower_y=[str(tower['physical_xy'][1])])
    settings.update(layer_height='0.2',initial_layer_print_height='0.2',
        enable_support='1',support_type='tree(auto)',support_on_build_plate_only='0',
        support_threshold_angle='20',support_top_z_distance='0.2',
        brim_type='auto_brim',brim_width='5',raft_layers='0',
        support_filament=str(slots[0]) if len(slots)==1 else '0',support_interface_filament=str(slots[0]) if len(slots)==1 else '0')
    if any(item['part_id'] in {'nose','left-eye','right-eye','rolled-map'} for item in plate['placements']):
        settings.update(raft_layers='3',brim_type='outer_only')
    # Native H2D physical filament routing is 1-based extruder selection.
    # Each plate's two used slots get different nozzles, irrespective of slot id.
    routing=list(settings.get('filament_map',['1']*native['slot_count']))
    if len(routing)!=native['slot_count']:raise GeometryError('Ungültige native H2D-Filamentzuordnung.')
    for extruder,slot in enumerate(slots,1):routing[slot-1]=str(extruder)
    settings['filament_map']=routing
    return mark_explicit_process_overrides(settings,source)


def assembly_instructions(report):
    """Human-readable order reconstructed from the checked construction tree."""
    if report.get('construction'):report=report['construction']
    collar=report.get('collar_assembly',{})
    if report.get('construction_preset')!=PRESET or not collar.get('ordered_part_ids'):
        raise GeometryError('Buddy-Montageanleitung braucht den tatsächlichen anatomischen Konstruktionsbericht.')
    steps=[
        'Vorbereitung: alle Teile an ihrer Datei-/Teil-ID zuordnen. Stützen und Brim entfernen, Steckflächen reinigen. Erst trocken stecken. 0,05 mm radiales Spiel stammt aus der kleinen Passungsprobe; große Verbindungen, Kleber und Tragfähigkeit sind nicht physisch bestätigt.',
        'Zuerst getrennte Baugruppen aus den Strukturkacheln aufbauen. Die folgenden Schnittpaare werden in umgekehrter Schnittreihenfolge zusammengesteckt; der Elternname bezeichnet jeweils die so entstehende Baugruppe, keine zusätzliche Druckdatei. Noch keine Ohren, Nase, Augen, Karte oder Schwanz am Körper befestigen.'
    ]
    for split in reversed(report.get('structural_splits',[])):
        if not split.get('path_check',{}).get('passed') or len(split.get('children',[]))!=2:
            raise GeometryError('Buddy-Montagebaum enthält eine ungeprüfte Strukturverbindung.')
        a,b=split['children'];axis='XYZ'[split['axis']]
        steps.append(f"Struktur {split['id']}: {a} und {b} an ihren passenden Schlüsselflächen entlang der {axis}-Achse zur Baugruppe {split['parent']} verbinden. {len(split['pins'])} Schlüssel; digitaler Geschwister-Auszug 40 mm geprüft. Nicht verkanten oder mit Gewalt pressen.")
    sequence=collar['ordered_part_ids']
    for index,ident in enumerate(sequence):
        if ident=='collar-body':text='Den aus seinen Strukturkacheln aufgebauten Unterkörper collar-body bereitstellen und standsicher abstützen.'
        elif ident=='collar-left':text='Die linke Halsbandhälfte collar-left am noch kopflosen Halsunterteil einsetzen. Kopf und innere Halskomponenten bleiben zunächst abgenommen.'
        elif ident=='collar-right':text='Die rechte Halsbandhälfte collar-right schließen und mit den Schlüsseln der linken Hälfte verbinden.'
        elif ident=='collar-neck-0':text='Das innere Halsstück collar-neck-0 mit seinen drei Schlüsseln in das geschlossene Halsband/Unterteil einführen.'
        elif ident=='collar-neck-1':text='Die kleine erhaltene Halskontur collar-neck-1 an ihrer Originalposition einsetzen. Sie hat keine eigenen Stifte: bewusst gefangenes/Klebeteil; nicht als eigenständige Steckverbindung behandeln. Kleber/Spalt real prüfen.'
        elif ident=='collar-head':text='Erst jetzt die aus Strukturkacheln aufgebaute Kopfgruppe collar-head auf den Hals montieren. Ein bereits komplett montierter Hund ist kein gültiger Ausgangszustand zum nachträglichen Einsetzen des geschlossenen Halsbands.'
        else:raise GeometryError('Unbekannte Buddy-Halsbandstufe; Montageanleitung neu prüfen.')
        steps.append(f'Halsmontage {index+1}: '+text)
    steps.extend([
        'Den zuvor aus tail-a und tail-b aufgebauten Schwanz an seiner proximalen Wurzel einsetzen; beide Ohren, vollständige Nase und gerollte Karte an den jeweils anatomisch passenden Schlüsselflächen montieren. Ihre digitalen Auszugspfade beziehen sich auf den zusammengesetzten Körper; die Orientierung im Montageviewer beachten.',
        'left-eye und right-eye sind zwei geschlossene Klebeaugen ohne Steckstifte. Links/rechts anhand der Form prüfen, trocken anhalten und erst nach realer Spalt-/Kleberprobe befestigen. Zusammen mit collar-neck-1 sind dies drei ausdrücklich stiftlose Klebe-/gefangene Teile.',
        'Prüfgrenze: Halsmontage wurde in dieser Reihenfolge gegen bereits montierte Teile über 80 mm geprüft, Strukturpaare über 40 mm. Diskrete Geometrieprüfungen sind kein Nachweis aller Kollisionen, realer Klebefestigkeit, Statik oder Kippstabilität. Den 1-m-Aufbau bis zur realen Belastungsprüfung abstützen.'
    ])
    return steps


def connection_summary(report):
    """Count constructed interfaces before tiling without inventing child pins.

    Parent/group IDs describe the assembly tree; they are not claims about the
    local connector geometry of any final structural child.
    """
    report=report.get('construction',report)
    if report.get('construction_preset')!=PRESET:
        raise GeometryError('Buddy-Verbindungsübersicht braucht den tatsächlichen Konstruktionsbericht.')
    interfaces=[]
    for attempt in report.get('anatomical_attempts',[]):
        ident=attempt['part_id']
        pins=attempt.get('pins')
        if pins is None:
            pins=[pin for part in attempt.get('parts',[]) if part.get('id')==ident for pin in part.get('connectors',[])]
        if pins:
            interfaces.append({'id':'anatomy-'+ident,'system':'anatomical','keys':len(pins),
                               'part_or_group_ids':[ident,'assembled-body']})
    collar={part['id']:part for part in report.get('collar_assembly',{}).get('parts',[])}
    for ident,other,label in [('collar-body','collar-neck-0','lower-neck'),
                             ('collar-neck-0','collar-head','upper-neck'),
                             ('collar-left','collar-right','ring-seam')]:
        count=len(collar.get(ident,{}).get('connectors',[]))
        if count:
            interfaces.append({'id':'collar-'+label,'system':'collar','keys':count,
                               'part_or_group_ids':[ident,other]})
    parents=set();children=set()
    for split in report.get('structural_splits',[]):
        pair=split.get('children',[])
        if len(pair)!=2 or not split.get('path_check',{}).get('passed'):
            raise GeometryError('Buddy-Verbindungsübersicht enthält eine ungeprüfte Strukturverbindung.')
        parents.add(split['parent']);children.update(pair)
        interfaces.append({'id':split['id'],'system':'structural','keys':len(split.get('pins',[])),
                           'part_or_group_ids':list(pair),'parent':split['parent'],'children':list(pair)})
    leaves=children-parents
    final=set(report.get('part_region_ids',{})) or set(report.get('quality',{}))
    if final and not leaves<=final:
        raise GeometryError('Buddy-Strukturbaum stimmt nicht mit den tatsächlichen Endteilen überein.')
    glue=[ident for ident in ('left-eye','right-eye','collar-neck-1') if ident in final]
    result={'total_keys':sum(row['keys'] for row in interfaces),'total_keyed_interfaces':len(interfaces),
            'structural_leaf_part_ids':sorted(leaves),'glue_part_ids':glue,'interfaces':interfaces,
            'assembly_connections_metadata_safe':True,
            'limitation':'Counts describe constructed key/socket pairs and assembly-tree interfaces; final child meshes receive no fabricated connector annotations. Physical strength and fit remain unverified.'}
    for system in ('anatomical','collar','structural'):
        rows=[row for row in interfaces if row['system']==system]
        result[system+'_keys']=sum(row['keys'] for row in rows)
        result[system+'_interfaces']=len(rows)
    return result
