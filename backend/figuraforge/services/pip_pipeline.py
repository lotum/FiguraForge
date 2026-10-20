"""Source-bound local Pip anatomical construction; no approval, database or cloud side effects.

Only the explicitly inspected 180-mm partitioned surface is accepted. Original
visible triangles are retained, except tiny numerical plane snapping documented
in the report. Checks are finite samples, not a physical fit/strength proof.
"""
from itertools import product,combinations
import hashlib
import numpy as np
from shapely.geometry import Point
from figuraforge.geometry.io import load_surface
from figuraforge.geometry.topology import frame,mesh_from_triangles,projected_outline
from figuraforge.geometry.plane_cut import clip_closed,clip_primary_component
from figuraforge.geometry.split import joint_between_halves
from figuraforge.geometry.connectors import Connector,pick_connectors,root_with_connectors
from figuraforge.geometry.construct import face_components,patch_from_faces,choose_direction,make_inlays
from figuraforge.geometry.anatomical import anatomical_seed_cut
from figuraforge.geometry.patch_masks import _branches
from figuraforge.geometry.compare import nearest,colors_at
from figuraforge.geometry.colors import classify
from figuraforge.geometry.types import Part,GeometryError
from figuraforge.geometry.validation import validate_mesh,DistanceQuery,check_insert_path,sample_surface

PRESET='pip-anatomical-v1'
MESH_HASH='6b50653c44351800405a94665290e745a712664a400e933106409fe44c6ce644'
SOURCE_SHA256='b5486af116bf337a3ea905ce2be19a0495020094833b637a67ed20309eb6ea1c'
REFERENCE_SIGNATURE='c49a4101886bc0cbe1b578a04c902c392f32df8a9fd504800a54c98ecbece2dd'
PALETTE=['#92AB2A','#DFC973','#865B11','#F5E5C9','#0B0502']
Z=116.000137
PLANES=[(np.array([0.,0.,1.]),Z),(np.array([0.,1.,.5]),-11.),(np.array([-.2,.4,1.]),100.),(np.array([.2,.4,1.]),100.)]

def signature(mesh):
 return hashlib.sha256(np.asarray(mesh.vertices,dtype='<f8').round(6).tobytes()+np.asarray(mesh.faces,dtype='<i8').tobytes()).hexdigest()

def valid(mesh):
 q=validate_mesh(mesh)
 if not q['valid'] or q['components']!=1:raise GeometryError('Pip requires one closed connected body per part: '+str(q))
 return q

def snap_source(mesh):
 m=mesh.copy();v=m.vertices.copy();normals=np.stack([n for n,_ in PLANES]);constants=np.array([c for _,c in PLANES]);near=np.abs(v@normals.T-constants)<3e-5
 for selected in np.unique(near,axis=0):
  if not selected.any():continue
  rows=np.all(near==selected,axis=1);A=normals[selected];b=constants[selected];v[rows]-=(v[rows]@A.T-b)@np.linalg.pinv(A).T
 displacement=float(np.linalg.norm(v-m.vertices,axis=1).max());m.vertices=v;valid(m);return m,displacement

def plane_clip(mesh,n,c,positive):
 length=np.linalg.norm(n);B=frame(n.copy());m=mesh.copy();m.vertices=m.vertices@B;m=clip_closed(m,2,c/length,positive);m.vertices=m.vertices@B.T;return m

def neck_joint(mesh,clearance):
 low=clip_closed(mesh,2,Z,False);high=clip_closed(mesh,2,Z,True);lc=np.all(np.abs(low.triangles[:,:,2]-Z)<1e-5,axis=1);hc=np.all(np.abs(high.triangles[:,:,2]-Z)<1e-5,axis=1);root=low.submesh([np.flatnonzero(lc)],append=True,repair=False);root.invert();B=frame(np.array([0.,0.,-1.]));outline=projected_outline(root,B);pins=[];q=DistanceQuery(high)
 for x,y in [(-5.,-72.),(5.,-72.)]:
  p=np.array([x,y,Z])@B;c=Connector(p[0],p[1],1.5,3.,p[2]-3.,'round',clearance)
  if not outline.buffer(-1.).covers(c.profile(socket=True)):raise GeometryError('Pip neck socket footprint lacks required wall')
  if q.values(np.array([[c.x,c.y,c.tip_z-.35]])@B.T)[0]>=-2.2:raise GeometryError('Pip neck socket too close to exterior')
  pins.append(c)
 low=mesh_from_triangles(np.concatenate([low.triangles[~lc],root_with_connectors(root,B,pins,False)]));high=mesh_from_triangles(np.concatenate([high.triangles[~hc],root_with_connectors(root,B,pins,True)]));valid(low);valid(high);return low,high,[p.summary(B) for p in pins]

def split_existing_tjunctions(mesh,tolerance=2e-6):
 import trimesh
 m=mesh;reports=[]
 for stage in range(3):
  if m.is_watertight:return m,reports
  counts=np.bincount(m.edges_unique_inverse);edges=m.edges_unique[counts==1];vertices=np.unique(edges);points=m.vertices[vertices];splits={};max_distance=0.
  for a,b in edges:
   A,B=m.vertices[[a,b]];delta=B-A;length=float(np.linalg.norm(delta));ts=(points-A)@delta/(delta@delta);distance=np.linalg.norm(points-(A+ts[:,None]*delta),axis=1);candidate=(distance<min(tolerance,length*.001))&(ts>1e-7)&(ts<1-1e-7)
   if candidate.any():
    order=np.argsort(ts[candidate]);found=vertices[candidate][order];splits[tuple(sorted((int(a),int(b))))]=list(map(int,found if a<b else found[::-1]));max_distance=max(max_distance,float(distance[candidate].max()))
  if not splits:break
  if len(splits)>256:raise GeometryError('T-junction subdivision exceeds bounded source-specific repair')
  verts=m.vertices.tolist();faces=[];changed_count=0
  for face in m.faces:
   ring=[];changed=False
   for a,b in zip(face,np.roll(face,-1)):
    ring.append(int(a));key=tuple(sorted((int(a),int(b))))
    if key in splits:ring.extend(splits[key] if a<b else splits[key][::-1]);changed=True
   if changed:
    center=len(verts);verts.append(m.vertices[face].mean(axis=0).tolist());faces.extend([[a,b,center] for a,b in zip(ring,ring[1:]+ring[:1])]);changed_count+=1
   else:faces.append(face.tolist())
  before=float(m.volume);m=trimesh.Trimesh(verts,faces,process=False);m.merge_vertices(digits_vertex=6);m.update_faces(m.nondegenerate_faces(height=1e-8));m.remove_unreferenced_vertices();reports.append({'split_existing_edges':len(splits),'split_triangles':changed_count,'maximum_insert_distance_mm':max_distance,'volume_change_mm3':float(m.volume-before),'new_hole_caps':0})
 if not m.is_watertight:raise GeometryError('Remaining open edges after exact existing-edge subdivision')
 return m,reports

def primary_component_numeric(mesh,axis,position,positive):
 # Cap identity follows the actual 1e-6 vertex weld precision; normals protect exterior faces.
 def cap_mask(part):return np.all(np.abs(part.triangles[:,:,axis]-position)<2e-6,axis=1)&(np.abs(part.face_normals[:,axis])>1-1e-8)
 if cap_mask(mesh).any():raise GeometryError('Source contains a preexisting face on the mechanical cut plane')
 selected=clip_closed(mesh,axis,position,positive);opposite=clip_closed(mesh,axis,position,not positive)
 components=sorted(selected.split(only_watertight=False),key=lambda m:-abs(m.volume));primary=components[0];minor=components[1:]
 if minor:
  exterior=[opposite.triangles[~cap_mask(opposite)]]+[m.triangles[~cap_mask(m)] for m in minor]
  remainder=mesh_from_triangles(np.concatenate([*exterior,primary.triangles[cap_mask(primary)][:,::-1]]),check=False)
  remainder,tjunction_report=split_existing_tjunctions(remainder)
 else:remainder=opposite
 valid(primary);valid(remainder)
 volume_error=abs(float(primary.volume+remainder.volume-mesh.volume));area=float(primary.area_faces[~cap_mask(primary)].sum()+remainder.area_faces[~cap_mask(remainder)].sum());area_error=abs(area-mesh.area)
 if volume_error>max(.01,abs(mesh.volume)*1e-7) or area_error>max(.01,mesh.area*1e-7):raise GeometryError('Primary component numerical cap repair failed source volume/exterior conservation')
 return primary,remainder,{'returned_fragments':len(minor),'fragment_volumes_mm3':[float(m.volume) for m in minor],'volume_error_mm3':volume_error,'exterior_area_error_mm2':area_error,'cap_position_tolerance_mm':2e-6,'cap_normal_alignment':1-1e-8,'exterior_components_deleted':0,'tjunctions':tjunction_report if minor else []}

def joint_numeric(low,high,axis,position,radius,length,clearance,shape,count):
 from figuraforge.geometry.topology import orient_local
 def cap_mask(part):return np.all(np.abs(part.triangles[:,:,axis]-position)<1e-5,axis=1)&(np.abs(part.face_normals[:,axis])>1-1e-7)
 low_cap=cap_mask(low);high_cap=cap_mask(high)
 if not low_cap.any() or not high_cap.any():raise GeometryError('Shared structural caps missing')
 direction=-np.eye(3)[axis];B=frame(direction.copy());root=low.submesh([np.flatnonzero(low_cap)],append=True,repair=False);root=mesh_from_triangles(orient_local(root.triangles@B,True)@B.T,check=False);outline=projected_outline(root,B);pins=pick_connectors(outline,root,B,0,radius=radius,length=length,clearance=clearance,count=count,shape=shape);q=DistanceQuery(high);pins=[p for p in pins if q.values(np.array([[p.x,p.y,p.tip_z-.4]])@B.T)[0]<-(p.radius+.6)]
 a=mesh_from_triangles(np.concatenate([low.triangles[~low_cap],root_with_connectors(root,B,pins,False)]),check=False);b=mesh_from_triangles(np.concatenate([high.triangles[~high_cap],root_with_connectors(root,B,pins,True)]),check=False);a,ar=split_existing_tjunctions(a);b,br=split_existing_tjunctions(b);valid(a);valid(b)
 return a,b,[p.summary(B) for p in pins],direction,{'male_tjunctions':ar,'female_tjunctions':br}

def body_joint(mesh,clearance):
 n=np.array([0.,1.,.5]);position=-11/np.linalg.norm(n);B=frame(n.copy());m=mesh.copy();m.vertices=m.vertices@B;low,high,component_report=primary_component_numeric(m,2,position,False);a,b,pins,d,joint_report=joint_numeric(low,high,2,position,radius=1.5,length=3,clearance=clearance,shape='round',count=2);a.vertices=a.vertices@B.T;b.vertices=b.vertices@B.T;d=np.asarray(d)@B.T
 for pin in pins:pin['position_mm']=(np.asarray(pin['position_mm'])@B.T).tolist()
 valid(a);valid(b)
 if len(pins)!=2:raise GeometryError('Pip body expects two safe pins')
 check=check_insert_path(a,b,d,travel_mm=15)
 if not check['passed']:raise GeometryError('Pip front torso cannot be assembled: '+str(check))
 return a,b,pins,d,{'component_reassignment':component_report,'joint':joint_report,'path':check}

def jaw_joint(head,clearance):
 normals=[np.array([sign*.2,.4,1.]) for sign in [-1,1]]
 def cap_mask(mesh):return np.any([np.all(np.abs(mesh.triangles@n-100)<2e-5,axis=1) for n in normals],axis=0)
 outside=[];high=None
 for signs in product([False,True],repeat=2):
  m=head.copy()
  for n,positive in zip(normals,signs):m=plane_clip(m,n,100.,positive)
  if signs==(True,True):high=m
  else:outside.append(m.triangles[~cap_mask(m)])
 mask=cap_mask(high);cap=high.submesh([np.flatnonzero(mask)],append=True,repair=False);d=np.array([0.,-.4,-1.]);d/=np.linalg.norm(d);B=frame(d.copy());outline=projected_outline(cap,B);pins=pick_connectors(outline,cap,B,0,radius=1.5,length=3,clearance=clearance,count=2,shape='round');q=DistanceQuery(high);pins=[p for p in pins if q.values(np.array([[p.x,p.y,p.tip_z-.35]])@B.T)[0]<-(p.radius+.7)]
 jaw=mesh_from_triangles(np.concatenate([*outside,root_with_connectors(cap,B,pins,False)]),check=False);high=mesh_from_triangles(np.concatenate([high.triangles[~mask],root_with_connectors(cap,B,pins,True)]),check=False);jaw,jr=split_existing_tjunctions(jaw);high,hr=split_existing_tjunctions(high);valid(jaw);valid(high)
 if len(pins)!=2:raise GeometryError('Pip jaw expects two safe pins')
 check=check_insert_path(jaw,high,d,travel_mm=15)
 if not check['passed']:raise GeometryError('Pip jaw blocked: '+str(check))
 return jaw,high,[p.summary(B) for p in pins],d,{'path':check,'male_tjunctions':jr,'female_tjunctions':hr}

def repair_whole_mask(mesh,mask,max_added=150):
 mask=mask.copy();added=[]
 for iteration in range(max_added):
  bad=_branches(mesh,mask)
  if not bad:return mask,added
  winner=None
  for vertex in sorted(bad):
   candidates=[int(i) for i in mesh.vertex_faces[vertex] if i>=0 and not mask[i]]
   for count in range(1,min(3,len(candidates))+1):
    for group in combinations(candidates,count):
     trial=mask.copy();trial[list(group)]=True;remaining=len(_branches(mesh,trial))
     if remaining<len(bad):
      score=(remaining,float(mesh.area_faces[list(group)].sum()),count)
      if winner is None or score<winner[0]:winner=(score,group)
   if winner:break
  if winner is None:raise GeometryError('No bounded local mask repair')
  mask[list(winner[1])]=True;added.extend(winner[1])
 raise GeometryError('Mask repair budget exceeded')

def eye_masks(surface):
 c=surface.mesh.triangles_center;result={};reports={}
 for key,center,r1,r2,y1,y2 in [('left-eye',[-30,-84,154],12,25,-82,-65),('right-eye',[30,-84,154],12,25,-82,-65),('left-pupil',[-29,-86,154],6.4,10.7,-85,-81),('right-pupil',[29,-86,154],6.4,10.7,-85,-81)]:
  d=np.linalg.norm(c-np.asarray(center),axis=1);result[key],reports[key]=anatomical_seed_cut(surface.mesh,np.flatnonzero((d<r1)&(c[:,1]<y1)),np.flatnonzero((d>r2)|(c[:,1]>y2)),smoothing_iterations=25,concavity_scale=.07)
 return result,reports

def cut_eye(surface,current,source_ids,name,radius,length,clearance):
 cut_region=cut_eye_region
 distance,ids,_=nearest(surface,current.triangles_center);initial=(distance<1e-4)&np.isin(ids,source_ids);adj=current.face_adjacency;trials=[]
 for ring in range(13):
  mask=initial.copy()
  for _ in range(ring):edge=adj[mask[adj[:,0]]!=mask[adj[:,1]]];mask[edge.ravel()]=False
  if not mask.any():break
  biggest=max(face_components(current,mask),key=lambda a:current.area_faces[a].sum());mask[:]=False;mask[biggest]=True
  try:
   mask,added=repair_whole_mask(current,mask);mask,projection_repair=repair_projected_mask(current,mask);target,remainder,_,pins,interfaces=cut_region(current,np.zeros(len(current.faces),int),np.flatnonzero(mask),radius=radius,length=length,clearance=clearance,shape='round',count=1 if 'pupil' in name else 2);valid(target);valid(remainder)
   if len(interfaces)!=1 or len(pins)!=(1 if 'pupil' in name else 2):raise GeometryError('Unexpected eye interfaces/pin count')
   direction=interfaces[0]['direction'];check=check_insert_path(target,remainder,direction,travel_mm=8 if 'pupil' in name else 15)
   if not check['passed']:raise GeometryError('Eye extraction blocked')
   return target,remainder,pins,direction,{'erosion_rings':ring,'added_current_faces':added,'projection_repair':projection_repair,'cap_inner_anchor_depth_mm':.15,'path':check,'trials':trials}
  except GeometryError as exc:trials.append({'erosion_rings':ring,'error':str(exc)})
 raise GeometryError(name+' has no validated contour: '+str(trials))

def cream_inlay(surface,current,kind,clearance):
 from figuraforge.geometry.patch_masks import repair_patch_boundary
 c=current.triangles_center;distance,ids,bary=nearest(surface,c);l=classify(colors_at(surface,ids,bary),PALETTE);exterior=distance<1e-4
 if kind=='tail':mask=exterior&(l==1)&(c[:,1]>20);normal=None
 else:mask=exterior&(l==1)&(c[:,2]<4)&(c[:,1]>-15)&(c[:,1]<12)&(np.abs(c[:,0])<16);normal=np.array([0.,0.,-1.]);mask&=current.face_normals@normal>.12
 indexes=max(face_components(current,mask),key=lambda a:current.area_faces[a].sum())
 if normal is None:normal=choose_direction(patch_from_faces(current,indexes))
 indexes,repair=repair_patch_boundary(current,indexes,normal,max_added=150,allowed_faces=exterior);labels=np.zeros(len(current.faces),int);labels[indexes]=1
 built,report=make_inlays(current,labels,[PALETTE[0],PALETTE[1]],depth_mm=1.2,seam_mm=.08,pin_radius_mm=1.2,pin_length_mm=2.5,pin_clearance_mm=clearance,min_region_area_mm2=0,validate_paths=True,direction_overrides={'0':normal.tolist()});cores=[p for p in built if p.role=='body'];inserts=[p for p in built if p.role!='body']
 if len(cores)!=1 or len(inserts)!=1 or len(inserts[0].connectors)!=2:raise GeometryError('Cream inlay needs one body and one two-pin insert')
 for p in built:valid(p.mesh)
 p=inserts[0];p.id=kind+'-cream';p.name='Pip '+kind+' underside';return p,cores[0].mesh,{'mask_repair':repair,'construction':report}

def build_draft(surface,clearance=.05,progress=None):
 if signature(surface.mesh)!=REFERENCE_SIGNATURE:raise GeometryError('Pip source signature mismatch; no generic anatomy inferred')
 if abs(float(clearance)-.05)>1e-8:raise GeometryError('This current Pip draft is tested only at .05 radial clearance')
 report={'source_sha256':SOURCE_SHA256,'source_signature':REFERENCE_SIGNATURE,'automatic_approval':False,'physical_fit_verified':False,'construction':{},'stage':'starting'};parts=[]
 def note(stage):
  report['stage']=stage
  if progress:progress(stage)
 m,snap=snap_source(surface.mesh);report['maximum_numeric_plane_snap_mm']=snap
 note('neck');low,head,neckpins=neck_joint(m,clearance);report['construction']['neck']={'pins':neckpins}
 note('body');front,rear,pins,direction,body_report=body_joint(low,clearance);parts.append(Part('body-front','Pip front torso',front,PALETTE[0],role='color-body',assembly_direction=direction.tolist(),connectors=pins+neckpins));report['construction']['body']=body_report
 note('jaw');jaw,head,pins,direction,jaw_report=jaw_joint(head,clearance);parts.append(Part('jaw','Pip entire chin',jaw,PALETTE[1],role='color-body',assembly_direction=direction.tolist(),connectors=pins));report['construction']['jaw']=jaw_report
 note('floor');p,rear,r=cream_inlay(surface,rear,'floor',clearance);parts.append(p);report['construction']['floor']=r
 note('tail');p,rear,r=cream_inlay(surface,rear,'tail',clearance);parts.append(p);report['construction']['tail']=r
 note('eye masks');masks,analysis=eye_masks(surface);report['construction']['anatomical_analysis']=analysis
 for side in ['left','right']:
  note(side+' eye');eye,head,pins,axis,r=cut_eye(surface,head,masks[side+'-eye'],side+'-eye',1.2,2.5,clearance);report['construction'][side+'-eye']=r
  pupil,iris,ppins,paxis,r=cut_eye(surface,eye,masks[side+'-pupil'],side+'-pupil',.9,1.5,clearance);report['construction'][side+'-pupil']=r
  parts.append(Part(side+'-iris','Pip '+side+' iris and rim',iris,PALETTE[3],role='color-body',assembly_direction=axis,connectors=pins));parts.append(Part(side+'-pupil','Pip '+side+' pupil and highlight',pupil,PALETTE[4],role='color-body',assembly_direction=paxis,connectors=ppins))
 parts.extend([Part('body-rear','Pip rear torso and tail',rear,PALETTE[0],role='body'),make_head_receiver(head)]);report['quality']={p.id:valid(p.mesh) for p in parts};report['source_volume_mm3']=float(surface.mesh.volume);report['parts_volume_mm3']=sum(float(p.mesh.volume) for p in parts)
 if report['parts_volume_mm3']>report['source_volume_mm3']+.01:raise GeometryError('Parts exceed original source volume')
 report['combined_checks']=check_combined_assembly(parts);report['stage']='geometry and sampled assembly verified';report['complete']=True;return parts,report


from figuraforge.geometry.surface_parts import boundary_loops,interior_cap,require_solid
from scipy.spatial import cKDTree

def cut_eye_region(mesh,labels,indexes,base_color=0,radius=2,length=5,clearance=.2,shape='keyed',count=2):
    patch=patch_from_faces(mesh,indexes); loops=boundary_loops(patch)
    if not loops: raise GeometryError('This color region encloses an entire component; separate that component first')
    caps=[pip_eye_interior_cap(np.asarray(patch.vertices)[loop]) for loop in loops]
    query=DistanceQuery(mesh)
    for cap in caps:
        if query.values(np.concatenate([sample_surface(cap,1500),cap.triangles_center])).max()>.002:
            raise GeometryError('Interior color-boundary cap exits the source solid. Use inlay mode or subdivide the region.')
    # Nested coplanar caps indicate an annular inlay, not a separable whole body part.
    for i,a in enumerate(caps):
        na=np.average(a.face_normals,axis=0,weights=a.area_faces);na/=np.linalg.norm(na)
        for b in caps[i+1:]:
            if np.abs((b.vertices-a.centroid)@na).max()<.05:
                basis=frame(na)
                pa=projected_outline(a,basis);pb=projected_outline(b,basis)
                if pa.intersection(pb).area>.05:
                    raise GeometryError('Nested color boundaries require a shared inlay pocket, not independent body-part caps')
    keep=np.ones(len(mesh.faces),bool);keep[indexes]=False
    target0=closed_eye_triangles(np.concatenate([patch.triangles,*[c.triangles for c in caps]]))
    rest0=closed_eye_triangles(np.concatenate([mesh.triangles[keep],*[c.triangles[:,::-1] for c in caps]]))
    require_solid(target0);require_solid(rest0)
    rest_query=DistanceQuery(rest0)
    target_tri=[patch.triangles];rest_tri=[mesh.triangles[keep]];connections=[];directions=[];interfaces=[]
    for cap_index,cap in enumerate(caps):
        root=cap.copy();root.invert()
        n=np.average(root.face_normals,axis=0,weights=root.area_faces);n/=np.linalg.norm(n)
        basis=frame(n);outline=projected_outline(root,basis)
        connectors=pick_connectors(outline,root,basis,0,radius=radius,length=length,clearance=clearance,count=count,shape=shape)
        safe=[]
        for connector in connectors:
            tip=np.array([[connector.x,connector.y,connector.tip_z-.35]])@basis.T
            if rest_query.values(tip)[0]<-(radius+.5):safe.append(connector)
        target_tri.append(root_with_connectors(root,basis,safe,socket=False))
        rest_tri.append(root_with_connectors(root,basis,safe,socket=True))
        for connector in safe:
            item=connector.summary(basis);item['interface']=cap_index;connections.append(item)
        directions.append(n.tolist());interfaces.append({'index':cap_index,'direction':n.tolist(),'area_mm2':float(cap.area),'connectors':len(safe)})
    target=closed_eye_triangles(np.concatenate(target_tri));remainder=closed_eye_triangles(np.concatenate(rest_tri))
    require_solid(target);require_solid(remainder)
    if abs((target0.volume+rest0.volume)-mesh.volume)>max(.01,mesh.volume*1e-7):
        raise GeometryError('Color partition failed volume conservation')
    if target.volume+remainder.volume>mesh.volume+max(.01,mesh.volume*1e-6):
        raise GeometryError('Connected parts exceed original volume; possible cap overlap')
    # Preserve original exterior color IDs, label new hidden interfaces as core.
    before=np.concatenate(rest_tri)
    before_labels=np.r_[labels[keep],np.full(sum(len(t) for t in rest_tri[1:]),base_color,int)]
    dist,mapping=cKDTree(before.mean(axis=1)).query(remainder.triangles_center)
    if dist.max()>1e-5:raise GeometryError('Failed to transfer exterior labels after partition')
    return target,remainder,before_labels[mapping],connections,interfaces


PART_KEYS=('body-front','jaw','floor-cream','tail-cream','left-iris','left-pupil','right-iris','right-pupil','body-rear','head-upper')
GREEN='richard-inventory-202609-52'
BROWN='richard-inventory-202609-29'
BEIGE='richard-inventory-202609-31'
BLACK='richard-inventory-202609-30'


def _guard(surface,settings,mesh_hash):
 if mesh_hash!=MESH_HASH:raise GeometryError('Pip-Anatomievorschlag braucht exakt die gepruefte Meshversion.')
 if float(settings.get('height_mm',0))!=180 or settings.get('up_axis')!='Y' or settings.get('printer_id')!='h2d-dual':raise GeometryError('Pip-Preset ist ausschliesslich fuer 180 mm, Y-up und den H2D geprueft.')
 if signature(surface.mesh)!=REFERENCE_SIGNATURE:raise GeometryError('Pip-Anatomievorschlag braucht die unveraenderte partitionierte Quellgeometrie.')
 if not settings.get('validate_paths',True):raise GeometryError('Pip-Preset braucht aktivierte Montagepfadpruefung.')


def check_combined_assembly(parts):
 """Pairwise overlaps and actual partial-assembly sequence, finite samples."""
 lookup={p.id:p for p in parts}
 if tuple(lookup)!=PART_KEYS:raise GeometryError('Pip braucht genau die zehn vorgesehenen Bauteile.')
 query={k:DistanceQuery(p.mesh) for k,p in lookup.items()};samples={k:sample_surface(p.mesh,2400) for k,p in lookup.items()};overlaps=[]
 for a,b in combinations(lookup,2):
  ma,mb=lookup[a].mesh,lookup[b].mesh
  if np.any(ma.bounds[1]<mb.bounds[0]) or np.any(mb.bounds[1]<ma.bounds[0]):continue
  depth=float(max(0.,-query[b].values(samples[a]).min(),-query[a].values(samples[b]).min()));overlaps.append({'a':a,'b':b,'max_penetration_mm':depth,'passed':depth<=.03})
 if not all(q['passed'] for q in overlaps):raise GeometryError('Pip-Bauteile ueberlappen: '+str([q for q in overlaps if not q['passed']]))
 steps=[(['body-front'],['body-rear']),(['floor-cream'],['body-rear','body-front']),(['tail-cream'],['body-rear','body-front','floor-cream']),(['jaw'],['head-upper']),(['jaw','head-upper'],['body-rear','body-front','floor-cream','tail-cream']),(['left-iris'],['body-rear','body-front','floor-cream','tail-cream','head-upper','jaw']),(['right-iris'],['body-rear','body-front','floor-cream','tail-cream','head-upper','jaw','left-iris']),(['left-pupil'],[k for k in lookup if k not in ['left-pupil','right-pupil']]),(['right-pupil'],[k for k in lookup if k!='right-pupil'])];checks=[]
 for moving,stationary in steps:
  direction=[0,0,1] if len(moving)>1 else lookup[moving[0]].assembly_direction;results=[]
  for a,b in product(moving,stationary):results.append({'moving':a,'stationary':b,**check_insert_path(lookup[a].mesh,lookup[b].mesh,direction,travel_mm=15)})
  if not all(q['passed'] for q in results):raise GeometryError('Pip-Montagefolge blockiert: '+str(moving))
  checks.append({'moving_group':moving,'stationary':stationary,'direction':direction,'passed':True,'checks':results})
 return {'passed':True,'pairwise_overlaps':overlaps,'assembly_sequence':checks,'limitation':'Diskrete Stichproben, kein kontinuierlicher Kollisionsbeweis oder physischer Drucknachweis.'}


def exterior_face_mapping(surface,part):
 """Same strictly near-coplanar source mapping for preview AND native export."""
 distance,ids,bary=nearest(surface,part.mesh.triangles_center)
 exterior=(distance<3e-5)&(np.einsum('ij,ij->i',surface.mesh.face_normals[ids],part.mesh.face_normals)>.999)
 # Every exterior corner must lie within that actual source triangle's footprint,
 # including true coplanar subdivisions. A cap's matching centroid is insufficient.
 from trimesh.triangles import closest_point
 selected=np.flatnonzero(exterior)
 for start in range(0,len(selected),8192):
  indexes=selected[start:start+8192];triangles=surface.mesh.triangles[ids[indexes]];corners=part.mesh.triangles[indexes];normal=surface.mesh.face_normals[ids[indexes]]
  plane=np.abs(np.einsum('fvc,fc->fv',corners-triangles[:,0,None,:],normal));closest=closest_point(np.repeat(triangles,3,axis=0),corners.reshape(-1,3)).reshape(-1,3,3)
  exterior[indexes]&=(plane<=3e-5).all(axis=1)&(np.linalg.norm(corners-closest,axis=2)<=3e-5).all(axis=1)
 # Explicit engineering-plane identity wins over accidental source coincidence.
 # Numerical clipping can produce microscopic coplanar cap triangles at a seam.
 # They are never exterior texture, even if all corners happen to sit on a
 # near-tangent source sliver within the documented numerical snap tolerance.
 for normal,constant in PLANES:
  aligned=np.abs(part.mesh.face_normals@(normal/np.linalg.norm(normal)))>1-1e-7
  on_plane=np.all(np.abs(part.mesh.triangles@normal-constant)<3e-5,axis=1)
  exterior&=~(aligned&on_plane)
 # After snapping the input plane at float32 precision, a very thin boundary
 # fragment can sit on the other original triangle's closest-point footprint.
 # In the one-micron engineering-cut band require complete source-corner
 # identity, instead of attributing such a fragment to another part's spool.
 from figuraforge.geometry.compare import unchanged_source_faces
 near_cut=np.zeros(len(part.mesh.faces),bool)
 for normal,constant in PLANES:
  near_cut|=np.all(np.abs(part.mesh.triangles@normal-constant)/np.linalg.norm(normal)<.001,axis=1)
 candidates=np.flatnonzero(exterior&near_cut)
 if len(candidates):
  proxy=type('SourceCornerSubset',(),{'faces':part.mesh.faces[candidates],'vertices':part.mesh.vertices})()
  exterior[candidates]&=unchanged_source_faces(surface,proxy,ids[candidates],tolerance_mm=3e-5)
 return exterior,ids,bary


def source_ownership(surface,parts):
 count=len(surface.mesh.faces);coverage=[]
 for part in parts:
  exterior,ids,_=exterior_face_mapping(surface,part);coverage.append(np.bincount(ids[exterior],weights=part.mesh.area_faces[exterior],minlength=count))
 coverage=np.array(coverage);owner=coverage.argmax(axis=0);matched=coverage.max(axis=0)>0;ambiguous=(coverage>1e-5).sum(axis=0)>1
 if ambiguous.any():raise GeometryError('Eine Pip-Quellflaeche gehoert zu mehreren mechanischen Bauteilen; Quelle an Schnittgrenzen vorbereiten.')
 missing=int((~matched).sum());area=float(surface.mesh.area_faces[~matched].sum())
 if missing>20 or area>.001:raise GeometryError('Pip-Aussenflaechenzuordnung ist unvollstaendig; keine automatische flaechige Umdeutung.')
 for _ in range(200):
  edges=surface.mesh.face_adjacency;edges=edges[matched[edges[:,0]]!=matched[edges[:,1]]]
  if not len(edges):break
  for a,b in edges:
   # Earlier edges may have filled the missing endpoint already. Never
   # overwrite an authentic exterior owner through such a stale edge.
   if matched[a] and not matched[b]:owner[b]=owner[a];matched[b]=True
   elif matched[b] and not matched[a]:owner[a]=owner[b];matched[a]=True
 if not matched.all():raise GeometryError('Pip-Quellkomponente hat keine Bauteilzuordnung.')
 return owner,{'unmapped_seam_source_faces':missing,'unmapped_seam_area_mm2':area,'multiple_part_source_faces':int(ambiguous.sum()),'seam_completion':'source-face adjacency only, maximum 20 faces / 0.001 square mm'}


def clean_body_light_components(surface,owner,source_classes,parts):
 """Source-bound de-lighting: keep the main belly/chin, not isolated gold highlights.

 This deliberately excludes eye/pupil parts, whose isolated pale glints are
 character features. It changes material labels only, never mesh/UV geometry.
 """
 from figuraforge.geometry.colors import rgb_hex
 classes=np.array(source_classes,copy=True);report={};sample=surface.sample()
 for index,part in enumerate(parts):
  if part.id not in ['body-front','jaw']:continue
  mask=(owner==index)&np.isin(classes,[1,3])
  components=sorted(face_components(surface.mesh,mask),key=lambda ids:-surface.mesh.area_faces[ids].sum())
  if not components:continue
  removed=np.concatenate(components[1:]) if len(components)>1 else np.array([],int)
  classes[removed]=0
  report[part.id]={'kept_light_area_mm2':float(surface.mesh.area_faces[components[0]].sum()),'removed_islands':len(components)-1,'reassigned_source_faces':removed.tolist(),'reassigned_area_mm2':float(surface.mesh.area_faces[removed].sum()),'reassigned_average_source_hex':rgb_hex(np.average(sample[removed],axis=0,weights=surface.mesh.area_faces[removed])) if len(removed) else None,'method':'Keep largest connected belly/chin light region; isolated source highlights become base green. Eye glints untouched.'}
 return classes,report


def _semantic_plan(surface,parts,mesh_hash,stock,pair):
 from figuraforge.geometry.colors import rgb_hex
 owner,coverage=source_ownership(surface,parts);labels=np.full(len(owner),-1,int);source_classes=classify(surface.sample(),PALETTE);regions=[];part_regions={};rid=0
 source_classes,light_cleanup=clean_body_light_components(surface,owner,source_classes,parts);coverage['body_light_cleanup']=light_cleanup
 for index,part in enumerate(parts):
  mask=owner==index;used=[]
  mixed_body=part.id in ['body-rear','head-upper']
  choices=([pair[0],None] if mixed_body else [BEIGE] if part.id in ['floor-cream','tail-cream'] else [pair[0],BEIGE] if part.id in ['body-front','jaw'] else [pair[1],BEIGE] if 'iris' in part.id else [BLACK,BEIGE])
  slots=(source_classes==2).astype(int) if mixed_body else np.isin(source_classes,[1,3]).astype(int) if len(choices)==2 else np.zeros(len(owner),int)
  for slot,ident in enumerate(choices or [None]):
   selected=mask&(slots==slot)
   if not selected.any():continue
   color=stock[ident]['hex'] if ident else rgb_hex(np.average(surface.sample()[selected],axis=0,weights=surface.mesh.area_faces[selected]));labels[selected]=rid
   regions.append({'id':rid,'name':part.name+(' · '+stock[ident]['name'] if ident else ' · Mixed'), 'strategy':'part','color_mode':'mixed' if ident is None else 'solid','color':color,'part_group':index+1,'cut_type':'whole','filament_id':ident,'face_count':int(selected.sum()),'area_mm2':float(surface.mesh.area_faces[selected].sum()),'reason':'Modellgebundene Anatomie. Creme/helle Augenreflexe bleiben eigene helle Regionen; keine falsche Gruenzuordnung durch ausschliesslich naechste Bestandsfarbe.'});used.append(rid);rid+=1
  part_regions[part.id]=used
 return {'version':1,'mesh_hash':mesh_hash,'face_count':len(owner),'face_regions':labels.tolist(),'regions':regions,'nozzle_count':2,'filament_ids':list(pair),'ratio_step_percent':5,'construction_preset':PRESET,'note':'Pip: zehn anatomische Teile, getrennte Montagefolge. Radialspiel 0,05 mm; physische Passung und ungemessene Druckfarben offen.'},part_regions,coverage


def suggest_pip_plan(surface,reference_plan,settings,mesh_hash,filaments,*,current_plan=None):
 if hasattr(settings,'model_dump'):settings=settings.model_dump()
 if hasattr(current_plan,'model_dump'):current_plan=current_plan.model_dump()
 _guard(surface,settings,mesh_hash)
 rows=filaments.values() if isinstance(filaments,dict) else filaments;stock={f['id']:f for f in rows};pair=(current_plan or {}).get('filament_ids') or [GREEN,BROWN]
 if len(pair)!=2 or len(set(pair))!=2:raise GeometryError('Pip braucht zwei konkrete verschiedene Mixed-Basisfilamente.')
 for ident in [*pair,BEIGE,BLACK]:
  f=stock.get(ident)
  if not f or not f.get('allowed',True) or settings.get('owned_filaments_only',True) and not f.get('owned'):raise GeometryError('Pip-Bestandsspule fehlt oder ist gesperrt: '+ident)
 if len({stock[i]['material'].casefold() for i in [*pair,BEIGE,BLACK]})!=1:raise GeometryError('Pip-Spulen muessen dieselbe Materialart verwenden.')
 parts,report=build_draft(surface,clearance=float(settings.get('pin_clearance_mm',.05)));document,mapping,coverage=_semantic_plan(surface,parts,mesh_hash,stock,pair)
 return document,{'construction_preset':PRESET,'source_sha256_required':SOURCE_SHA256,'source_signature':REFERENCE_SIGNATURE,'parts':list(PART_KEYS),'part_region_ids':mapping,'source_ownership':coverage,'pins':sum(len(p.connectors) for p in parts),'physical_fit_verified':False,'physical_color_verified':False,'automatic_approval':False,'geometry_checks':report['combined_checks']}


def construct_pip(surface,plan,settings,*,reference_plan):
 if hasattr(settings,'model_dump'):settings=settings.model_dump()
 if hasattr(plan,'model_dump'):plan=plan.model_dump()
 _guard(surface,settings,plan.get('mesh_hash'))
 if plan.get('construction_preset')!=PRESET:raise GeometryError('Pip braucht den ausdruecklich ausgewaehlten Anatomieplan.')
 parts,report=build_draft(surface,clearance=float(settings.get('pin_clearance_mm',.05)));owner,coverage=source_ownership(surface,parts);labels=np.asarray(plan.get('face_regions',[]));regions={r['id']:r for r in plan['regions']};mapping={}
 if labels.shape!=owner.shape:raise GeometryError('Pip-Farbplan passt nicht zur Quelle.')
 for index,part in enumerate(parts):
  ids=sorted(int(x) for x in np.unique(labels[owner==index]));mapping[part.id]=ids
  if not ids or any(i not in regions or regions[i]['strategy']!='part' or regions[i].get('part_group')!=index+1 or regions[i].get('cut_type')!='whole' for i in ids):raise GeometryError('Pip-Anatomiemasken oder Bauteilgruppen wurden veraendert; fuer freie Schnitte Preset aufheben.')
  part.color_index=index+1;part.color=regions[ids[0]]['color'];part.warnings.append('0,05 mm radiales Steckspiel basiert auf separater Nasenprobe, nicht auf einem bereits gedruckten Pip. Lokale Montage nur stichprobengeprueft.')
 report['assembly_interfaces']=[{'male_part':'body-front','female_part':'body-rear','pins':2,'joint':'front torso'}, {'male_part':'body-front','female_part':'jaw','pins':2,'joint':'vertical neck; assemble jaw/head group first'}, {'male_part':'jaw','female_part':'head-upper','pins':2,'joint':'chin'}, {'male_part':'floor-cream','female_part':'body-rear','pins':2,'joint':'floor inlay'}, {'male_part':'tail-cream','female_part':'body-rear','pins':2,'joint':'tail inlay'}, {'male_part':'left-iris','female_part':'head-upper','pins':2,'joint':'left eye'}, {'male_part':'right-iris','female_part':'head-upper','pins':2,'joint':'right eye'}, {'male_part':'left-pupil','female_part':'left-iris','pins':1,'joint':'left pupil'}, {'male_part':'right-pupil','female_part':'right-iris','pins':1,'joint':'right pupil'}]
 report['assembly_instructions_de']=['Rumpffront in den hinteren Rumpf stecken. Halsstifte bleiben frei.','Boden- und Schwanzunterseiteneinsatz an den Rumpf stecken.','Unterkiefer zuerst am oberen Kopf montieren, solange der Kopf noch vom Rumpf getrennt ist.','Vormontierte Kopfgruppe senkrecht auf die beiden Halsstifte am vorderen Rumpf setzen.','Beide Iris-/Augenrahmen am montierten Kopf einsetzen.','Zuletzt die dunklen Pupillen mit ihren hellen Reflexen in die Irisrahmen stecken.','Nie mit Gewalt montieren: 0,05 mm Radialspiel und kleine Stifte sind am realen Pip noch nicht kalibriert.']
 report.update(strategy='source-bound Pip anatomical preset',construction_preset=PRESET,mesh_hash=plan['mesh_hash'],part_region_ids=mapping,source_ownership=coverage,pins=sum(len(p.connectors) for p in parts),physical_color_verified=False,warnings=['Apple Green und Beige sind deutlich heller/anders gesaettigt als die Quell-Albedo. Mischungen und Inventar-HEX sind ungemessen.','Stuetzwirkung, Druckbarkeit und physische Verbindung werden separat geprueft.'])
 return parts,report


def pack_pip_parts(parts,volume=(300,320,320),margin=8,gap=8):
 """One part per plate isolates supports; pin axes point up, no horizontal pins."""
 from figuraforge.geometry.packing import validate_packing
 lookup={p.id:p for p in parts}
 if set(lookup)!=set(PART_KEYS):raise GeometryError('Pip-Druckplanung erwartet genau zehn Teile.')
 plates=[]
 for part in parts:
  up=(np.array([0.,1.,.5])/np.linalg.norm([0,1,.5])+[0,0,1]) if part.id=='body-front' else -np.asarray(part.assembly_direction) if part.connectors else np.array([0.,0.,1.]);up=up/np.linalg.norm(up);rotation=frame(up.copy()).T;v=part.mesh.vertices@rotation.T;lo=v.min(axis=0);extent=np.ptp(v,axis=0)
  if np.any(extent[:2]+2*margin>np.asarray(volume)[:2]) or extent[2]>volume[2]:raise GeometryError('Pip-Bauteil passt nicht in die sichere Druckausrichtung.')
  transform=np.eye(4);transform[:3,:3]=rotation;transform[:3,3]=-lo+[margin,margin,0]
  placement={'part_id':part.id,'transform':transform.tolist(),'rect':[float(margin),float(margin),float(extent[0]),float(extent[1])],'height_mm':float(extent[2]),'color':part.color,'support_status':'Isolierte Platte; Baumstuetzen und Raft als Vorschlag, GCode und physische Haftung separat pruefen.','orientation_reason':'Stifte nach oben; Rumpffront mit Winkelhalbierender zwischen Hals- und Rumpfstiften.' if part.connectors else 'Urspruengliche Z-Achse, Anschlussflaechen zur Platte pruefen.'}
  plates.append({'id':len(plates)+1,'colors':[part.color],'placements':[placement],'volume_mm':list(volume),'physical_spool_count':2,'material_batch':'Pip '+part.id,'utilization_percent':float(extent[0]*extent[1]/(volume[0]*volume[1])*100)})
 check=validate_packing(parts,plates)
 if not check['passed']:raise GeometryError('Ungueltige Pip-Druckplatte: '+str(check))
 return plates


def configure_pip_plate(config,plate):
 from copy import deepcopy
 from .mixed_filament import mark_explicit_process_overrides
 keys={x['part_id'] for x in plate.get('placements',[])}
 if len(keys)!=1 or not keys<=set(PART_KEYS):raise GeometryError('Pip-Stuetzvorschlag braucht eine isolierte, bekannte Bauteilplatte.')
 result=deepcopy(config);result.update(layer_height='0.2',initial_layer_print_height='0.2',enable_support='1',support_type='tree(auto)',support_on_build_plate_only='1',support_threshold_angle='20',support_top_z_distance='0.2',brim_type='outer_only',brim_width='5',raft_layers='3',support_filament='0',support_interface_filament='0',wipe_tower_x=['235'],wipe_tower_y=['250'])
 return mark_explicit_process_overrides(result,config)


def pip_eye_interior_cap(points):
 """Keep the exact anatomical outer loop, deepen only internal cap anchors."""
 cap=interior_cap(points);distance,_=cKDTree(points).query(cap.vertices);normal=np.average(cap.face_normals,axis=0,weights=cap.area_faces);length=np.linalg.norm(normal)
 if length<1e-9:raise GeometryError('Pip-Augenkappe hat keine eindeutige innere Richtung.')
 cap.vertices[distance>1e-6]+=normal/length*.15
 return cap


def repair_projected_mask(mesh,mask):
 """Resolve bounded local projection folds, without eroding a whole eye rim."""
 from shapely.geometry import LineString
 from shapely.strtree import STRtree
 from figuraforge.geometry.topology import boundary_loops
 def conflicts(selected):
  patch=patch_from_faces(mesh,np.flatnonzero(selected));loops=boundary_loops(patch)
  if len(loops)!=1:return 100000,[]
  points=patch.vertices[loops[0]];_,_,axes=np.linalg.svd(points-points.mean(axis=0),full_matrices=False);xy=points@frame(axes[-1]);edges=[LineString([a[:2],b[:2]]) for a,b in zip(xy,np.roll(xy,-1,axis=0))];tree=STRtree(edges);pairs=set()
  for i,line in enumerate(edges):
   for j in tree.query(line,predicate='intersects'):
    if i==j or (i-j)%len(edges) in (1,len(edges)-1):continue
    pairs.add(tuple(sorted((i,int(j)))))
  positions=[]
  for a,b in pairs:positions.extend(points[[a,(a+1)%len(points),b,(b+1)%len(points)]])
  return len(pairs),positions
 selected=mask.copy();tree=cKDTree(mesh.vertices);changes=[];area=0.
 for _ in range(20):
  number,points=conflicts(selected)
  if not number:return selected,changes
  if number>20:raise GeometryError('Pip-Augenkontur hat zu viele Projektionsfalten fuer die begrenzte lokale Korrektur.')
  vertices=tree.query(points)[1];candidates=np.unique(mesh.vertex_faces[vertices]);candidates=candidates[candidates>=0];winner=None
  for index in candidates:
   trial=selected.copy();trial[index]=not trial[index]
   if _branches(mesh,trial):continue
   try:remaining,_=conflicts(trial)
   except GeometryError:continue
   score=(remaining,float(mesh.area_faces[index])*(1.5 if selected[index] else 1.))
   if remaining<number and (winner is None or score<winner[0]):winner=(score,int(index),trial)
  if winner is None:raise GeometryError('Keine begrenzte lokale Aufloesung der Pip-Augenkontur gefunden.')
  score,index,selected=winner;area+=float(mesh.area_faces[index])
  if area>1:raise GeometryError('Pip-Augenkonturkorrektur wuerde mehr als 1 mm2 umdeuten.')
  changes.append({'face':index,'included':bool(selected[index]),'area_mm2':float(mesh.area_faces[index]),'remaining_conflicts':score[0]})
 raise GeometryError('Pip-Augenkontur braucht mehr als 20 lokale Korrekturen.')



def closed_eye_triangles(triangles):
    mesh=mesh_from_triangles(triangles,check=False)
    mesh,_=split_existing_tjunctions(mesh)
    valid(mesh)
    return mesh



def make_head_receiver(mesh):
    """Female-only upper head; retained by two jaw and four iris pins."""
    return Part('head-upper','Pip oberer Kopf · Buchsenteil',mesh,PALETTE[0],
                role='socket-body',assembly_direction=[0,0,1],
                warnings=['Buchsenteil ohne eigene Stifte: nimmt zwei Kieferstifte und je zwei Irisstifte auf. Die vormontierte Kopfgruppe wird ueber die Halsbuchsen im Kiefer befestigt.'])
