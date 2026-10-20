"""Reproduce Buddy's source-preserving local construction experiment.

No project mutation, approval, paid call or printer submission. Every run writes
new artifacts. Source-bound seeds are a reviewed model preset, not general AI
anatomy recognition. Physical tolerance and H2D native slicing remain separate.
"""
from pathlib import Path
import argparse,json,sqlite3,hashlib,time,copy
from itertools import permutations
import numpy as np
from scipy.spatial import cKDTree
from figuraforge.config import Config
from figuraforge.db import uid,digest
from figuraforge.security import safe_asset_path
from figuraforge.geometry.io import load_surface
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
from figuraforge.services.export import export_bundle,validate_3mf

PROJECT='2c9a7959d13a438fbeb5b8340d8eefd4'
SOURCE_SHA='1fbf9afb006d912cb612702232d7eb0e194e35407ad0e293b6550b4337bce61c'
MESH_HASH='5d60b394adfbf92e46b0b6d3a70fbbeb2b02d3284557297a48aba5cad14f43af'
PLAN_HASH='64833d22e43f0c5cac360f0ffdae5d9a5b5f0e32b1671dccbf9dabb7eac834fe'

from figuraforge.services import buddy_pipeline as _buddy_kernel


def fit_cap(*args,**kwargs):
    return _buddy_kernel.fit_cap(*args,query=query,**kwargs)


def common_axis(*args,**kwargs):
    return _buddy_kernel.common_axis(*args,query=query,**kwargs)


source_mask=_buddy_kernel.source_mask
single_solid=_buddy_kernel.single_solid
fits_h2d=_buddy_kernel.fits_h2d
tile_connected=_buddy_kernel.tile_connected


def review_html(out,surface,parts,plates,filename='review.html',material_preview=None,parts_material_preview=None):
    # Embed renderer and all arrays/textures: no server, CDN or remote asset needed.
    viewer=Path('frontend/viewer.js').read_text().split('\n',1)[1].replace('export class Viewer','class Viewer')
    constants="const STRATEGY_COLORS={body:'#728197',part:'#00B2FF',mixed:'#CFFF00'};const isMixedRegion=r=>r?.strategy==='mixed'||r?.color_mode==='mixed';\n"
    source=surface_preview(surface);assembled=parts_material_preview or parts_preview(parts)
    # Source bodies split into structural tiles must also move in explosion.
    for record in assembled['meshes']:
        if record['role']=='body' and len(parts)>1:record['role']='structural-body'
    html='''<!doctype html><meta charset="utf-8"><title>Buddy – lokale Geometrieprüfung</title>
<style>body{margin:0;font:18px system-ui;background:#eef0ea;color:#17323b}header{padding:14px 20px}button,select{font:inherit;padding:9px;margin:4px}canvas{display:block;width:100vw;height:78vh}p{margin:8px}small{font-size:15px}</style>
<header><b>Buddy – 1.000 mm · lokale Geometrieprüfung</b><p>Originaltextur und neue Teile getrennt vergleichen. Ziehen: drehen · Mausrad: zoomen · Umschalt+Ziehen: verschieben.</p>
<button id="original">Originaltextur</button><button id="material">Materialvorschlag</button><button id="assembly">Geometrieteile</button><button id="explode">Explodiert</button><button id="plates">Druckplatten</button><select id="plate"></select><button id="turn">45° drehen</button>
<p><small>Experiment, keine Druckfreigabe. Core-Farben sind Platzhalter; Support, reale Filamente, Lasten und Passung ungeprüft.</small></p></header><canvas id="view"></canvas><script>'''
    if material_preview is not None:html=html.replace('Core-Farben sind Platzhalter; Support, reale Filamente, Lasten und Passung ungeprüft.', 'Vorschau mit unkalibrierten Bestands-HEX. Core-Dateien nur Geometrie; native Profile, Support, Lasten und Passung noch prüfen.')
    html+=constants+viewer+'\nconst material='+json.dumps(material_preview,separators=(',',':'))+';const original='+json.dumps(source,separators=(',',':'))+';const assembled='+json.dumps(assembled,separators=(',',':'))+';const plates='+json.dumps(plates,separators=(',',':'))+';\n'
    html+='''const v=new Viewer(document.querySelector('#view'));v.setData(original);
const select=document.querySelector('#plate');plates.forEach((p,i)=>select.add(new Option('Platte '+(i+1),i)));
document.querySelector('#original').onclick=()=>{v.mode='assembly';v.setData(original)};
const materialButton=document.querySelector('#material');materialButton.disabled=!material;materialButton.onclick=()=>{v.mode='assembly';v.setData(material)};
for(const mode of ['assembly','explode','plates'])document.querySelector('#'+mode).onclick=()=>{v.mode=mode;v.setData(assembled);v.setPlates(plates);v.setMode(mode)};
select.onchange=()=>{v.plate=+select.value;v.reset()};document.querySelector('#turn').onclick=()=>{v.yaw+=Math.PI/4;v.draw()};</script>'''
    (out/filename).write_text(html)


def main():
    global query
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-root',type=Path,default=Path('benchmarks/buddy-production'))
    parser.add_argument('--skip-tiling',action='store_true');parser.add_argument('--include-collar',action='store_true',help='Build the reviewed local Blender collar assembly sequence');args=parser.parse_args();config=Config()
    with sqlite3.connect(f'file:{config.data_dir/"forge.sqlite3"}?mode=ro',uri=True) as db:
        row=db.execute('SELECT data FROM projects WHERE id=?',(PROJECT,)).fetchone()
    if not row:raise GeometryError('Reviewed Buddy project missing')
    project=json.loads(row[0]);root=config.data_dir/'projects'/PROJECT;artifact=project['artifacts']['mesh'];plan_info=project['artifacts']['plan']
    source_path=safe_asset_path(root,artifact['source']['path'])
    if artifact['hash']!=MESH_HASH or artifact['source']['sha256']!=SOURCE_SHA or hashlib.sha256(source_path.read_bytes()).hexdigest()!=SOURCE_SHA:
        raise GeometryError('Buddy working source changed; review seeds before running')
    if project['settings']['height_mm']!=1000 or project['settings']['up_axis']!='Y':raise GeometryError('Buddy scale changed')
    plan=json.loads(safe_asset_path(root,plan_info['document']).read_text())
    if digest(plan)!=PLAN_HASH or plan_info['hash']!=PLAN_HASH or plan['mesh_hash']!=MESH_HASH or plan_info['mesh_hash']!=MESH_HASH:raise GeometryError('Buddy plan/source binding changed')
    surface=load_surface(source_path,1000,'Y');mesh=surface.mesh;single_solid(mesh);query=DistanceQuery(mesh)
    labels=np.asarray(plan['face_regions']);centers=mesh.triangles_center
    if len(labels)!=len(mesh.faces):raise GeometryError('Source face count changed')
    out=args.output_root/('construction-'+uid());out.mkdir(parents=True);print(str(out),flush=True)
    report={'source_project':PROJECT,'source_sha256':SOURCE_SHA,'mesh_hash':MESH_HASH,'plan_hash':plan_info['hash'],
      'source_quality':validate_mesh(mesh),'human_mesh_approval':project['approvals'].get('mesh'),
      'source_volume_mm3':float(mesh.volume),'source_original_preserved':True,'physical_verified':False,'native_color_verified':False,
      'warnings':['Experimental model-bound geometry, not a production approval.',
       'Radial clearance .05 mm follows the user physical four-pair test on 2026-10-16: .10/.15/.20 loose, .05 just retained with slight residual play. Larger keys still need load/retention verification; no .04 inferred.',
       '12-mm keys / 16-mm structural engagement are geometric choices, not load-bearing or FEA certification.',
       'Gold/black display colors are placeholders; approved source plan remains unchanged. Native per-region material mapping and H2D slicing are separate.'],
      'anatomical_attempts':[]}
    ears=sorted(face_components(mesh,labels==2),key=lambda ids:-mesh.area_faces[ids].sum())[:2]
    remaining=mesh.copy();parts=[]
    dark=sorted(face_components(mesh,labels==4),key=lambda ids:-mesh.area_faces[ids].sum())
    nose_seed=dark[0];domain=seed_geodesic_faces(mesh,nose_seed,12)
    nose_ids,nose_cut=anatomical_seed_cut(mesh,nose_seed,np.setdiff1d(np.arange(len(mesh.faces)),domain),smoothing_iterations=30,concavity_scale=.06)
    built,nose_check=common_axis(remaining,nose_ids,[0,-1,0],radius=6,length=10,cap_anchor_offset=2.)
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
        built,eye_check=common_axis(remaining,source_mask(surface,remaining,eye_ids),[sign*.2,-1,0],radius=1.5,length=3,cap_anchor_offset=20.,minimum_cap_refinements=1,dense_cap_check=True)
        for part in built:single_solid(part.mesh)
        eye=built[1];eye.id=side+'-eye';eye.name='Buddy '+side+' Auge – Creme und Pupille';eye.color='#E2B16D';eye.role='color-body'
        if not eye.connectors:eye.warnings.append('Geschlossenes Klebeteil: keine sichere Steckverbindung mit den geprüften Parametern. Keine Press-/Steckpassung behauptet; Klebespalt und reale Montage noch prüfen.')
        parts.append(eye);remaining=built[0].mesh;np.save(out/(side+'-eye-source-face-ids.npy'),eye_ids)
        report['anatomical_attempts'].append({'part_id':eye.id,'cut':eye_cut,'cap_anchor_offset_mm':20.,'minimum_cap_refinements':1,'dense_cap_check':True,'path_check':eye_check,'parts':[eye.summary()]})
        print(side+' eye built with '+str(len(eye.connectors))+' keys (zero explicitly means glue-on)',flush=True)
    cream=sorted(face_components(mesh,labels==5),key=lambda ids:-mesh.area_faces[ids].sum())[0]
    paper_domain=seed_geodesic_faces(mesh,cream,20)
    paper_ids,paper_cut=anatomical_seed_cut(mesh,cream,np.setdiff1d(np.arange(len(mesh.faces)),paper_domain),smoothing_iterations=30,concavity_scale=.06)
    built,paper_check=common_axis(remaining,source_mask(surface,remaining,paper_ids),[.2,.15,1],radius=3,length=6,cap_anchor_offset=2.)
    for part in built:single_solid(part.mesh)
    paper=built[1];paper.id='rolled-map';paper.name='Buddy gerollte Karte';paper.color='#E2B16D';paper.role='color-body'
    parts.append(paper);remaining=built[0].mesh;np.save(out/'rolled-map-source-face-ids.npy',paper_ids)
    report['anatomical_attempts'].append({'part_id':'rolled-map','cut':paper_cut,'cap_anchor_offset_mm':2.,'path_check':paper_check,'parts':[paper.summary()]})
    print('rolled map built with '+str(len(paper.connectors))+' keys',flush=True)
    for index,name,direction,grow in [(0,'right-ear',[1,0,0],2),(1,'left-ear',[-1,0,0],5)]:
        core=np.flatnonzero((np.abs(centers[:,0])<100)|(centers[:,2]<680)|(centers[:,1]<-445));seed=np.setdiff1d(ears[index],core)
        ids,cut=anatomical_seed_cut(mesh,seed,core,smoothing_iterations=30,concavity_scale=.06)
        ids=seed_geodesic_faces(mesh,ids,grow);np.save(out/(name+'-source-face-ids.npy'),ids)
        built,check=common_axis(remaining,source_mask(surface,remaining,ids),direction,cap_anchor_offset=1.)
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
    for part in parts:part.save(out/'anatomical-parts')
    try:report['anatomical_combined_checks']=_combined_checks(parts,40)
    except GeometryError as error:
        report['construction_error']=str(error)
        (out/'blocked-geometry-check.json').write_text(json.dumps(report,indent=2)+'\n')
        review_html(out,surface,parts,[])
        raise
    (out/'anatomical-check.json').write_text(json.dumps(report,indent=2)+'\n')
    review_html(out,surface,parts,[])
    if not args.skip_tiling:
        parts,splits=tile_connected(parts,out);report['structural_splits']=splits
    else:report['warnings'].append('Tiling deliberately skipped: anatomical parts may exceed H2D envelope.')
    report['quality']={part.id:single_solid(part.mesh) for part in parts}
    report['part_region_ids']={}
    report['part_region_source_areas_mm2']={}
    for part in parts:
        distances,source_ids,_=nearest(surface,part.mesh.triangles_center)
        exterior=(distances<=.03)&((part.mesh.face_normals*mesh.face_normals[source_ids]).sum(axis=1)>.95)
        regions=labels[source_ids[exterior]]
        report['part_region_ids'][part.id]=list(map(int,np.unique(regions)))
        report['part_region_source_areas_mm2'][part.id]={str(int(region)):float(part.mesh.area_faces[exterior][regions==region].sum()) for region in np.unique(regions)}
    report['part_region_mapping_limitation']='Original-plan region union on exterior faces within .03 mm of source. Interior caps excluded. Includes unresolved source shade/material distinctions; no approval inferred.'
    from figuraforge.geometry.buddy_materials import propose_materials
    material_masks={name:np.load(out/(name+'-source-face-ids.npy')) for name in ['nose','left-eye','right-eye','rolled-map']}
    material_document,material_report,material_rgb=propose_materials(surface,plan,material_masks,parts)
    (out/'material-proposal.json').write_text(json.dumps(material_document,indent=2)+'\n')
    (out/'material-proposal-report.json').write_text(json.dumps(material_report,indent=2)+'\n')
    report['material_proposal']={'document':'material-proposal.json','report':'material-proposal-report.json','approved':False,'requires_real_filament_assignment':True,'two_materials_per_part_passed':material_report['two_materials_per_part_passed']}
    report['draft_part_region_ids']=material_report['part_region_ids']
    material_surface=Surface(mesh,np.zeros_like(surface.corner_uv),np.repeat(material_rgb[:,None,:],3,axis=1),np.zeros(len(mesh.faces),dtype=int))
    material_preview=surface_preview(material_surface)
    report['parts_volume_mm3']=sum(float(part.mesh.volume) for part in parts)
    report['clearance_void_mm3']=report['source_volume_mm3']-report['parts_volume_mm3']
    if report['clearance_void_mm3']<-.1:raise GeometryError('Parts exceed source volume')
    report['global_final_motion_verified']=False
    report['warnings'].append('Structural sibling motions are checked in the explicit assembly tree. A simultaneous global straight motion of every final tile is not claimed.')
    if args.skip_tiling:
        (out/'geometry-check.json').write_text(json.dumps(report,indent=2)+'\n');return
    plates=pack_parts(parts,volume=(300,320,320),margin=8,gap=5,max_colors=1)
    for plate in plates:
        for item in plate['placements']:
            item['transform'][0][3]+=25;item['rect'][0]+=25
        plate['volume_mm']=[350,320,320]
    packing=validate_packing(parts,plates)
    if not packing['passed']:raise GeometryError(str(packing))
    world_bounds=[]
    for plate in plates:
        for item in plate['placements']:
            part=next(p for p in parts if p.id==item['part_id']);tf=np.asarray(item['transform']);points=part.mesh.vertices@tf[:3,:3].T+tf[:3,3]
            if np.min(points[:,0])<33-1e-5 or np.max(points[:,0])>317+1e-5:raise GeometryError('Part leaves shared dual-nozzle X envelope including 8 mm margin')
            if points[:,1].min()<8-1e-5 or points[:,1].max()>312+1e-5 or points[:,2].min()< -1e-5 or points[:,2].max()>320+1e-5:raise GeometryError('Part leaves H2D shared Y/Z envelope')
            world_bounds.append({'plate_id':plate.get('id'), 'part_id':part.id,'bounds_mm':[points.min(axis=0).tolist(),points.max(axis=0).tolist()]})
    report['shared_build_volume_mm']=[300,320,320];report['xy_margin_mm']=8;report['physical_world_bounds']=world_bounds;report['actual_max_world_z_mm']=max(row['bounds_mm'][1][2] for row in world_bounds)
    report['packing']=packing;report['plates']=plates
    for part in parts:part.save(out/'parts')
    result=export_bundle(parts,plates,out,metadata=report)
    report['three_mf_roundtrips']={p.name:validate_3mf(p) for p in out.glob('*.3mf')}
    review_html(out,surface,parts,plates,material_preview=material_preview)
    (out/'geometry-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'output':str(out),'parts':len(parts),'plates':result['plates'],'numeric_printable_items':True}),flush=True)


if __name__=='__main__':main()
