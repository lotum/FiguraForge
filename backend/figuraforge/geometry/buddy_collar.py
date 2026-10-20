"""Reviewed, source-bound Buddy collar experiment, with explicit assembly order.

This is not general anatomy recognition. Visible source surfaces are retained
through local mesh booleans; only internal interfaces/keys are created. No API,
project mutation, approval or printer submission occurs here.
"""
from __future__ import annotations
import json, os, shutil, subprocess
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union
from .types import GeometryError, Part
from .topology import frame, mesh_from_triangles, projected_outline, orient_local, triangulate_polygon
from .connectors import pick_connectors
from .validation import DistanceQuery, validate_mesh, check_insert_path
from .planned_parts import _combined_checks

SOURCE_SHA = '1fbf9afb006d912cb612702232d7eb0e194e35407ad0e293b6550b4337bce61c'
MESH_HASH = '5d60b394adfbf92e46b0b6d3a70fbbeb2b02d3284557297a48aba5cad14f43af'
CENTER = np.array([-2.0980297910436962, -314.61054382351267, 622.0290047991385])
AXIS = np.array([-.006830915336330042, -.45604721243380275, .8899293672123794])
INNER_RADIUS = 89.85612099782783
HMIN, HMAX = -39.72241797006659, 32.33059292498005

_BLENDER = '''import bpy,numpy as np,json,sys
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--')+1]);bpy.ops.wm.read_factory_settings(use_empty=True)
def load(name):
 a=np.load(root/(name+'.npz'));m=bpy.data.meshes.new(name);m.from_pydata(a['vertices'].tolist(),[],a['faces'].tolist());m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);return o
def save(o,name):
 tri=o.modifiers.new('triangulate','TRIANGULATE');bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=tri.name)
 if not len(o.data.polygons):raise RuntimeError('Empty Boolean result '+name)
 np.savez_compressed(root/(name+'.npz'),vertices=np.array([v.co[:] for v in o.data.vertices]),faces=np.array([p.vertices[:] for p in o.data.polygons]))
for job in json.loads((root/sys.argv[-1]).read_text()):
 source=load(job['source']);cutter=load(job['cutter']);mod=source.modifiers.new('reviewed local geometry','BOOLEAN');mod.operation=job['operation'];mod.solver=job.get('solver','MANIFOLD');mod.object=cutter;name=mod.name;bpy.context.view_layer.objects.active=source;bpy.ops.object.modifier_apply(modifier=name)
 if name in source.modifiers:raise RuntimeError('Boolean rejected '+job['output'])
 save(source,job['output']);bpy.data.objects.remove(source,do_unlink=True);bpy.data.objects.remove(cutter,do_unlink=True)
'''


def _save(directory, name, mesh):
    np.savez_compressed(directory / (name+'.npz'), vertices=mesh.vertices, faces=mesh.faces)


def _load(directory, name):
    with np.load(directory/(name+'.npz'), allow_pickle=False) as a:
        return trimesh.Trimesh(a['vertices'], a['faces'], process=False)


def _solid(mesh):
    quality = validate_mesh(mesh)
    if not quality['valid'] or quality['components'] != 1:
        raise GeometryError('Buddy collar needs one closed connected physical body: '+str(quality))
    return quality


def _run(directory, batch, jobs):
    binary = shutil.which('blender') or '/Applications/Blender.app/Contents/MacOS/Blender'
    if not Path(binary).is_file():
        raise GeometryError('Reviewed Buddy collar construction needs a local Blender installation')
    script = directory/'boolean-worker.py'
    if not script.exists():script.write_text(_BLENDER)
    plan = directory/(batch+'.json');plan.write_text(json.dumps(jobs,indent=2)+'\n')
    result = subprocess.run([binary, '--background', '--threads', '2', '--python', str(script),
        '--', str(directory.resolve()), plan.name], capture_output=True, text=True, timeout=180,
        env={**os.environ, 'OPENBLAS_NUM_THREADS':'2', 'OMP_NUM_THREADS':'2'})
    (directory/(batch+'.log')).write_text(result.stdout+'\n'+result.stderr)
    if result.returncode:
        raise GeometryError(f'Local Blender collar batch {batch} failed (exit {result.returncode}); inspect its retained log. No remesh fallback applied.')
    for job in jobs:
        quality=validate_mesh(_load(directory,job['output']))
        if not quality['valid'] or (not job.get('allow_components') and quality['components']!=1):raise GeometryError('Rejected Boolean output '+job['output']+': '+str(quality))


def _box(axis, plane):
    # Explicit vertices avoid cancellation when a large translated cube encodes
    # a tiny plane offset. Blender still stores its documented Float32 vertices.
    lower=np.full(3,-4000.);upper=np.full(3,4000.);lower[axis]=plane
    vertices=np.array([[upper[i] if bits&(1<<i) else lower[i] for i in range(3)] for bits in range(8)])
    return trimesh.Trimesh(vertices, [[0,2,3],[0,3,1],[4,5,7],[4,7,6],[0,1,5],[0,5,4],
        [2,6,7],[2,7,3],[0,4,6],[0,6,2],[1,3,7],[1,7,5]], process=False)


def _primitive(pin, basis, socket):
    xy=np.asarray(pin.profile(socket).exterior.coords[:-1])
    bottom=pin.tip_z-(pin.tip_clearance if socket else 0)
    root=pin.tip_z+pin.length
    center=np.array([pin.x,pin.y])
    # Reach nominal R at the real mating plane. The extra 2 mm exists
    # only to overlap the parent solid; extending the taper there loosens fit.
    rings=[np.column_stack([center+(xy-center)*(1 if socket else .85),np.repeat(bottom,len(xy))]),
           np.column_stack([xy,np.repeat(root,len(xy))]),
           np.column_stack([xy,np.repeat(root+2,len(xy))])]
    triangles=[]
    for low,high in zip(rings,rings[1:]):
        for i in range(len(xy)):
            j=(i+1)%len(xy);triangles.extend([[high[i],low[i],low[j]],[high[i],low[j],high[j]]])
    for ring,reverse in [(rings[-1],False),(rings[0],True)]:
        for tri in triangulate_polygon(Polygon(ring[:,:2])):
            t=np.column_stack([tri,np.repeat(ring[0,2],3)]);triangles.append(t[::-1] if reverse else t)
    result=mesh_from_triangles(np.array(triangles)@basis.T)
    trimesh.repair.fix_normals(result);_solid(result)
    return result


def _axial_joint(low, high, plane, *, directory=None, batch=None):
    from .connectors import root_with_connectors
    lm=(abs(low.triangles[:,:,2]-plane)<1e-5).all(axis=1)&(np.linalg.norm(low.triangles_center[:,:2],axis=1)<INNER_RADIUS+.01)
    hm=(abs(high.triangles[:,:,2]-plane)<1e-5).all(axis=1)&(np.linalg.norm(high.triangles_center[:,:2],axis=1)<INNER_RADIUS+.01)
    if not lm.any() or not hm.any():raise GeometryError('Reviewed central neck cap missing')
    basis=frame(np.array([0.,0.,-1.]));root=low.submesh([np.flatnonzero(lm)],append=True,repair=False)
    root=mesh_from_triangles(orient_local(root.triangles@basis,True)@basis.T,check=False)
    other=high.submesh([np.flatnonzero(hm)],append=True,repair=False)
    def domain(patch):
        return unary_union([Polygon(tri[:,:2]) for tri in patch.triangles@basis if Polygon(tri[:,:2]).area>1e-10])
    outline=domain(root) if directory is not None else projected_outline(root,basis)
    other_outline=domain(other) if directory is not None else projected_outline(other,basis)
    if outline.symmetric_difference(other_outline).area>.01:
        raise GeometryError('Buddy neck interface domains do not match')
    pins=pick_connectors(outline,root,basis,0,radius=6,length=10,clearance=.05,count=3,shape='keyed')
    query=DistanceQuery(high)
    pins=[c for c in pins if query.values(np.array([[c.x,c.y,c.tip_z-.4]])@basis.T)[0]<-6.6]
    if len(pins)<2:raise GeometryError('Buddy central neck needs at least two safe keys')
    if directory is not None:
        _save(directory,batch+'-low',low);_save(directory,batch+'-high',high)
        low_name=batch+'-low';high_name=batch+'-high';jobs=[]
        for j,pin in enumerate(pins):
            for socket in [False,True]:_save(directory,f'{batch}-pin-{j}-{int(socket)}',_primitive(pin,basis,socket))
            jobs.extend([{'source':low_name,'cutter':f'{batch}-pin-{j}-0','operation':'UNION','output':f'{batch}-low-{j}'},
                         {'source':high_name,'cutter':f'{batch}-pin-{j}-1','operation':'DIFFERENCE','output':f'{batch}-high-{j}'}])
            low_name=f'{batch}-low-{j}';high_name=f'{batch}-high-{j}'
        _run(directory,batch,jobs)
        return _load(directory,low_name),_load(directory,high_name),[c.summary(basis) for c in pins]
    a=mesh_from_triangles(np.concatenate([low.triangles[~lm],root_with_connectors(root,basis,pins,False)]))
    b=mesh_from_triangles(np.concatenate([high.triangles[~hm],root_with_connectors(root,basis,pins,True)]))
    _solid(a);_solid(b)
    return a,b,[c.summary(basis) for c in pins]


def _annular_cutters(transform):
    # Core retains its nominal cylinder. Only the ring bore grows, producing
    # real radial sliding clearance instead of two coincident FDM surfaces.
    return tuple(trimesh.creation.annulus(r_min=INNER_RADIUS+offset,r_max=160,height=HMAX-HMIN,sections=128,transform=transform)
                 for offset in [0.,.05])


def build_collar(mesh, directory:Path, *, source_binding:dict):
    """Return source-preserving parts and a checked, ordered assembly proposal."""
    if source_binding.get('source_sha256')!=SOURCE_SHA or source_binding.get('mesh_hash')!=MESH_HASH or source_binding.get('height_mm')!=1000:
        raise GeometryError('Buddy collar preset is bound to the reviewed 1000-mm source')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False);_solid(mesh)
    basis=frame(AXIS);transform=np.eye(4);transform[:3,:3]=basis;transform[:3,3]=CENTER+basis[:,2]*(HMIN+HMAX)/2
    core_cutter,ring_cutter=_annular_cutters(transform)
    _save(directory,'source',mesh);_save(directory,'annular-cutter',core_cutter);_save(directory,'ring-clearance-cutter',ring_cutter)
    _run(directory,'annular',[
        {'source':'source','cutter':'ring-clearance-cutter','operation':'INTERSECT','output':'ring-world','solver':'EXACT'},
        {'source':'source','cutter':'annular-cutter','operation':'DIFFERENCE','output':'core-world','solver':'EXACT'}])
    ring=_load(directory,'ring-world');core=_load(directory,'core-world')
    for name,item in [('ring',ring),('core',core)]:
        item.vertices=(item.vertices-CENTER)@basis;_save(directory,name,item)
    lower_plane=float(np.float32(2000+HMIN+.001137))-2000;upper_plane=float(np.float32(2000+HMAX-.001137))-2000;ring_plane=float(np.float32(1000+.011137))-1000
    _save(directory,'lower-plane',_box(2,lower_plane));_save(directory,'upper-plane',_box(2,upper_plane));_save(directory,'ring-plane',_box(0,ring_plane))
    _run(directory,'sequence-cuts',[
        {'source':'core','cutter':'lower-plane','operation':'DIFFERENCE','output':'body'},
        {'source':'core','cutter':'lower-plane','operation':'INTERSECT','output':'headneck','allow_components':True},
        {'source':'headneck','cutter':'upper-plane','operation':'INTERSECT','output':'head'},
        {'source':'headneck','cutter':'upper-plane','operation':'DIFFERENCE','output':'middle','allow_components':True},
        {'source':'ring','cutter':'ring-plane','operation':'DIFFERENCE','output':'ring-left'},
        {'source':'ring','cutter':'ring-plane','operation':'INTERSECT','output':'ring-right'}])
    body=_load(directory,'body');head=_load(directory,'head');middle=_load(directory,'middle')
    components=sorted(middle.split(only_watertight=False),key=lambda m:-m.volume)
    for component in components:_solid(component)
    body,components[0],lowerpins=_axial_joint(body,components[0],float(body.bounds[1,2]),directory=directory,batch='lower-keys')
    components[0],head,upperpins=_axial_joint(components[0],head,float(head.bounds[0,2]),directory=directory,batch='upper-keys')
    left=_load(directory,'ring-left');right=_load(directory,'ring-right');plane=float(left.bounds[1,0]);joint_basis=frame(np.array([-1.,0,0]))
    cap=(abs(left.triangles[:,:,0]-plane)<1e-5).all(axis=1);root=left.submesh([np.flatnonzero(cap)],append=True,repair=False);triangles=root.triangles@joint_basis
    outline=unary_union([Polygon(tri[:,:2]) for tri in triangles if Polygon(tri[:,:2]).area>1e-8])
    pins=pick_connectors(outline,root,joint_basis,0,radius=2,length=6,clearance=.05,count=12,shape='keyed');query=DistanceQuery(right)
    pins=[c for c in pins if query.values(np.column_stack([np.asarray(c.profile(True).exterior.coords[:-1]),np.repeat(c.tip_z-.35,8)])@joint_basis.T).max()<-.6][:2]
    if len(pins)<2:raise GeometryError('Two collar seam keys with safe socket tip corners required')
    jobs=[];previous_left='ring-left';previous_right='ring-right'
    for j,pin in enumerate(pins):
        for socket in [False,True]:_save(directory,f'pin-{j}-{int(socket)}',_primitive(pin,joint_basis,socket))
        jobs.extend([{'source':previous_left,'cutter':f'pin-{j}-0','operation':'UNION','output':f'left-key-{j}'},
                     {'source':previous_right,'cutter':f'pin-{j}-1','operation':'DIFFERENCE','output':f'right-key-{j}'}])
        previous_left=f'left-key-{j}';previous_right=f'right-key-{j}'
    _run(directory,'ring-keys',jobs);left=_load(directory,previous_left);right=_load(directory,previous_right)
    parts=[Part('collar-body','Buddy Unterkörper',body,'#ECA24D',role='body',connectors=lowerpins),
           Part('collar-left','Buddy Halsband links',left,'#0C2842',role='body',connectors=[c.summary(joint_basis) for c in pins]),
           Part('collar-right','Buddy Halsband rechts',right,'#0C2842',role='body')]
    sequence=[('collar-left',[0,0,1]),('collar-right',[1,0,0])]
    for i,component in enumerate(components):
        center=component.center_mass;d=np.array([center[0],center[1],0.]) if np.linalg.norm(center[:2])>100 else np.array([0.,0.,1.]);d/=np.linalg.norm(d)
        part=Part('collar-neck-'+str(i),'Buddy Halskontur '+str(i+1),component,'#ECA24D',role='body',connectors=upperpins if i==0 else [])
        if i:part.warnings.append('Geschlossene Klebe-/gefangene Halskontur ohne eigene Stifte; reale Montage prüfen.')
        parts.append(part);sequence.append((part.id,d.tolist()))
    parts.append(Part('collar-head','Buddy Kopf',head,'#ECA24D',role='body'));sequence.append(('collar-head',[0,0,1]))
    _combined_checks(parts,80)  # All explicit body roles: static pairs only; order below.
    placed=[parts[0]];checks=[]
    for part_id,direction in sequence:
        part=next(p for p in parts if p.id==part_id)
        for other in placed:
            check=check_insert_path(part.mesh,other.mesh,np.asarray(direction,float),travel_mm=80)
            check.update(part_id=part.id,obstacle_part_id=other.id,assembly_stage=len(placed)+1)
            checks.append(check)
            if not check['passed']:raise GeometryError('Buddy collar assembly sequence blocked: '+str(check))
        placed.append(part)
    report={'source_binding':source_binding,'source_original_preserved':True,'local_frame':basis.tolist(),'origin_mm':CENTER.tolist(),
        'internal_cut_planes_local_mm':{'lower':lower_plane,'upper':upper_plane,'ring':ring_plane},'static_passed':True,'ordered_assembly_checks':checks,'ordered_part_ids':[p.id for p in placed],
        'quality':{p.id:_solid(p.mesh) for p in parts},'physical_verified':False,'ring_radial_clearance_mm':.05,
        'limitation':'Reviewed source-bound local construction; source coordinates pass through Blender Float32. Retained outer neck contours without keys need glue/capture and real fit verification. Structural tiling must preserve this assembly order.'}
    report['source_volume_mm3']=float(mesh.volume);report['parts_volume_mm3']=sum(float(p.mesh.volume) for p in parts)
    if report['parts_volume_mm3']>report['source_volume_mm3']+.5:raise GeometryError('Collar parts exceed original source volume')
    for part in parts:
        part.mesh.vertices=part.mesh.vertices@basis.T+CENTER
        for pin in part.connectors:pin['position_mm']=(basis@np.asarray(pin['position_mm'])+CENTER).tolist()
    report['parts']=[p.summary() for p in parts]
    (directory/'collar-check.json').write_text(json.dumps(report,indent=2)+'\n')
    return parts,report


def boolean_structural_split(mesh,axis,position,positive,directory):
    """Local closed-Boolean fallback for Buddy's Float32-derived structural cuts.

    Retains loose selected-side fragments on the connected opposite half. It
    changes internal caps/keys only and keeps all actual source solid volume.
    """
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=False);_solid(mesh)
    position=float(np.float32(position));_save(directory,'source',mesh);_save(directory,'plane',_box(axis,position))
    _run(directory,'halves',[
        {'source':'source','cutter':'plane','operation':'DIFFERENCE','output':'low-raw','allow_components':True},
        {'source':'source','cutter':'plane','operation':'INTERSECT','output':'high-raw','allow_components':True}])
    low=_load(directory,'low-raw');high=_load(directory,'high-raw');selected=high if positive else low
    components=sorted(selected.split(only_watertight=False),key=lambda m:-m.volume)
    retention={'loose_components_retained':len(components)-1,'source_visible_geometry_deleted':False}
    if len(components)>1:
        primary=components[0];loose=trimesh.util.concatenate(components[1:]);other=low if positive else high
        _save(directory,'retained-other',other);_save(directory,'retained-fragments',loose)
        _run(directory,'retain-fragments',[{'source':'retained-other','cutter':'retained-fragments','operation':'UNION','output':'retained-body'}])
        if positive:low=_load(directory,'retained-body');high=primary
        else:low=primary;high=_load(directory,'retained-body')
    _solid(low);_solid(high)
    basis=frame(-np.eye(3)[axis]);mask=(abs(low.triangles[:,:,axis]-position)<1e-5).all(axis=1)
    if not mask.any():raise GeometryError('Boolean structural cap missing')
    root=low.submesh([np.flatnonzero(mask)],append=True,repair=False);triangles=root.triangles@basis
    outline=unary_union([Polygon(tri[:,:2]) for tri in triangles if Polygon(tri[:,:2]).area>1e-8])
    pins=pick_connectors(outline,root,basis,0,radius=6,length=16,clearance=.05,count=12,shape='keyed');query=DistanceQuery(high)
    pins=[c for c in pins if query.values(np.column_stack([np.asarray(c.profile(True).exterior.coords[:-1]),np.repeat(c.tip_z-.35,8)])@basis.T).max()<-.6][:2]
    if not pins:raise GeometryError('No structural socket with safe keyed tip corners fits')
    _save(directory,'low',low);_save(directory,'high',high);low_name='low';high_name='high';jobs=[]
    for j,pin in enumerate(pins):
        for socket in [False,True]:_save(directory,f'pin-{j}-{int(socket)}',_primitive(pin,basis,socket))
        jobs.extend([{'source':low_name,'cutter':f'pin-{j}-0','operation':'UNION','output':f'low-key-{j}'},
                     {'source':high_name,'cutter':f'pin-{j}-1','operation':'DIFFERENCE','output':f'high-key-{j}'}])
        low_name=f'low-key-{j}';high_name=f'high-key-{j}'
    _run(directory,'keys',jobs);low=_load(directory,low_name);high=_load(directory,high_name)
    _combined_checks([Part('low','low',low,'#ECA24D',role='body'),Part('high','high',high,'#ECA24D',role='body')],40)
    return low,high,[c.summary(basis) for c in pins],-np.eye(3)[axis],retention
