"""New, source-bound nose clearance comparison with fixed vertical pin axes.

No project writes, paid calls, printer submission or automatic support geometry.
Bambu slicing must add support/brim below each curved, pin-up nose.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import sqlite3
import numpy as np
from figuraforge.config import Config
from figuraforge.db import uid,digest
from figuraforge.geometry.construct import patch_from_faces
from figuraforge.geometry.connectors import pick_connectors,root_with_connectors
from figuraforge.geometry.io import load_surface
from figuraforge.geometry.mochi_masks import mochi_masks
from figuraforge.geometry.packing import validate_packing
from figuraforge.geometry.planned_parts import _combined_checks
from figuraforge.geometry.split import clip_half
from figuraforge.geometry.surface_parts import interior_cap,make_surface_parts
from figuraforge.geometry.topology import boundary_loops,frame,mesh_from_triangles,projected_outline
from figuraforge.geometry.types import Part,GeometryError
from figuraforge.geometry.validation import validate_mesh,require_solid
from figuraforge.security import safe_asset_path
from figuraforge.services.export import write_3mf

SOURCE_SHA256='c8b50eee6cce4bf76ca8ef17050c44694e6db0ee7d18bdd47cf48507fc065643'


def metrics(mesh):
    z=mesh.triangles[:,:,2]
    return {'overhang_area_below_45deg_mm2':float(mesh.area_faces[(mesh.face_normals[:,2]<-.707)&(z.min(axis=1)>.3)].sum()),
            'bed_contact_below_0_22mm_mm2':float(mesh.area_faces[z.max(axis=1)<.22].sum()),
            'method':'geometric 45-degree normal / 0.22-mm bed-zone proxy; not a sliced support assessment'}



def plate_image(parts,placements,path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    fig=plt.figure(figsize=(12,8),layout='constrained')
    top=fig.add_subplot(211);three=fig.add_subplot(212,projection='3d')
    colors=['#a76a36','#bb5536','#598565','#546ead']
    for part,placement in zip(parts,placements):
        tf=np.asarray(placement['transform']);tri=part.mesh.triangles@tf[:3,:3].T+tf[:3,3]
        color=colors[['A005','B010','C015','D020'].index(part.id.split('-')[0])]
        top.add_collection(PolyCollection(tri[:,:,:2],facecolor=color,edgecolor='none'))
        x,y,w,h=placement['rect'];top.text(x+w/2,y+h+2,part.id,ha='center',fontsize=11,weight='bold')
        three.add_collection3d(Poly3DCollection(tri,facecolor=color,edgecolor='none',alpha=.98))
    top.set(xlim=(25,185),ylim=(10,85),aspect='equal',xlabel='X (mm)',ylabel='Y (mm)',
        title='Links → rechts: 0,05 / 0,10 / 0,15 / 0,20 mm radial. Vorne Nase, hinten Tasche.')
    three.set(xlim=(25,185),ylim=(10,85),zlim=(0,25),xlabel='X',ylabel='Y',zlabel='Z')
    three.set_box_aspect((160,75,25));three.view_init(elev=25,azim=-65)
    fig.suptitle('Ø3 × 3 mm keyed · Nasenstift +Z · Taschenöffnung +Z\nNasen: Support + Brim einschalten; nicht automatisch neu orientieren',fontsize=14)
    fig.savefig(path,dpi=170);plt.close(fig)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',default='1b0e2fdd463d4f15ac64f1c7b3e8acc7')
    parser.add_argument('--output-root',type=Path,default=Path('benchmarks/nose-fit-comparison'))
    args=parser.parse_args();config=Config()
    with sqlite3.connect(f'file:{config.data_dir / "forge.sqlite3"}?mode=ro',uri=True) as connection:
        row=connection.execute('SELECT data FROM projects WHERE id=?',(args.project,)).fetchone()
    if not row:raise GeometryError('Source project is missing')
    project=json.loads(row[0]);project_root=config.data_dir/'projects'/args.project
    artifact=project['artifacts']['mesh'];plan_artifact=project['artifacts']['plan']
    source_path=safe_asset_path(project_root,artifact['source']['path'])
    if hashlib.sha256(source_path.read_bytes()).hexdigest()!=SOURCE_SHA256 or artifact['source']['sha256']!=SOURCE_SHA256:
        raise GeometryError('Reference working GLB changed')
    if project['settings']['height_mm']!=180 or project['settings']['up_axis']!='Y':raise GeometryError('Reference scale changed')
    document=json.loads(safe_asset_path(project_root,plan_artifact['document']).read_text())
    if digest(document)!=plan_artifact['hash'] or document['mesh_hash']!=artifact['hash'] or plan_artifact['mesh_hash']!=artifact['hash']:
        raise GeometryError('Reference plan binding changed')
    surface=load_surface(source_path,180,'Y');source=surface.mesh
    masks,anatomy=mochi_masks(surface,document);indexes=masks['nose'];labels=np.zeros(len(source.faces),int);labels[indexes]=1
    built,canonical_report=make_surface_parts(source,labels,['#AF440A','#090505'],pin_radius_mm=1.5,
        pin_length_mm=3,pin_clearance_mm=.2,connector_shape='keyed',min_region_area_mm2=0,validate_paths=True)
    nose=next(part for part in built if part.role!='body')
    if len(nose.connectors)!=1:raise GeometryError('Reference nose must contain one safe connector')
    patch=patch_from_faces(source,indexes);loops=boundary_loops(patch)
    if len(loops)!=1:raise GeometryError('One reference nose interface required')
    cap=interior_cap(patch.vertices[loops[0]]);root=cap.copy();root.invert()
    n=np.asarray(nose.assembly_direction);basis=frame(n)
    connectors=pick_connectors(projected_outline(root,basis),root,basis,0,radius=1.5,length=3,clearance=.2,count=2,shape='keyed')
    canonical_position=np.asarray(nose.connectors[0]['position_mm'])
    connector=min(connectors,key=lambda c:np.linalg.norm(np.asarray(c.summary(basis)['position_mm'])-canonical_position))
    if np.linalg.norm(np.asarray(connector.summary(basis)['position_mm'])-canonical_position)>1e-7:
        raise GeometryError('Canonical connector position mismatch')
    reproduced=mesh_from_triangles(np.concatenate([patch.triangles,root_with_connectors(root,basis,[connector],socket=False)]))
    if not np.allclose(reproduced.vertices,nose.mesh.vertices,atol=1e-9) or not np.array_equal(reproduced.faces,nose.mesh.faces):
        raise GeometryError('Reference male connector geometry was not reproduced exactly')
    keep=labels==0
    # For the male, -n is the pin direction. For the female, +n opens the hole.
    male_rotation=frame(-n).T;female_rotation=basis.T
    if not np.allclose(male_rotation@(-n),[0,0,1],atol=1e-10) or not np.allclose(female_rotation@n,[0,0,1],atol=1e-10):
        raise GeometryError('Connector print axes are not vertical')
    out=args.output_root/('vertical-'+uid());out.mkdir(parents=True)
    np.save(out/'nose-source-face-ids.npy',indexes)
    variants=[];parts=[];placements=[];quality={};row_labels=[]
    for row_index,(code,clearance) in enumerate([('A005',.05),('B010',.10),('C015',.15),('D020',.20)]):
        socket_connector=copy.copy(connector);socket_connector.clearance=clearance
        # Clearance changes only the female footprint; the four male meshes are identical.
        body=mesh_from_triangles(np.concatenate([source.triangles[keep],root_with_connectors(root,basis,[socket_connector],socket=True)]))
        require_solid(body)
        socket=body.copy()
        # Crop the already verified world-aligned local neighborhood first;
        # distant textured-fur contours are irrelevant to this pocket coupon.
        for axis,low,high in [(1,-70.000137,-55.000137),(2,120.000137,141.000137),(0,-10.000137,10.000137)]:
            socket=clip_half(socket,axis,low,True);socket=clip_half(socket,axis,high,False)
        tf=np.eye(4);tf[:3,:3]=female_rotation;socket.apply_transform(tf)
        # A final horizontal cut creates a real flat base below the cavity tip.
        bottom=connector.tip_z-.35-2.000137
        socket=clip_half(socket,2,bottom,True)
        require_solid(socket)
        # Check true mating geometry in assembled source coordinates before moving to the bed.
        socket_assembled=socket.copy();inverse=np.eye(4);inverse[:3,:3]=female_rotation.T;socket_assembled.apply_transform(inverse)
        pair=[Part(f'{code}-socket','Socket',socket_assembled,'#EFB27C',role='body'),copy.deepcopy(nose)]
        pair[1].id=f'{code}-nose'
        checks=_combined_checks(pair,10)
        variant={'id':code,'radial_clearance_mm':clearance,'diameter_clearance_mm':2*clearance,
                 'male_nominal_diameter_mm':3.,'male_length_mm':3.,'socket_tip_clearance_mm':.35,
                 'connector_world':socket_connector.summary(basis),'mating_checks':checks,'parts':[]}
        for kind,mesh,rotation,column in [('nose',nose.mesh,male_rotation,0),('socket',socket,female_rotation,1)]:
            # Socket is already rotated for clipping. Keep the full source->print transform in the report.
            printable=mesh.copy()
            if kind=='nose':
                tf=np.eye(4);tf[:3,:3]=rotation;printable.apply_transform(tf)
            origin=printable.bounds[0].copy();printable.apply_translation(-origin)
            pid=f'{code}-{kind}';part=Part(pid,f'{code} {kind} radial {clearance:.2f} mm',printable,'#EFB27C',role='fit-test')
            q=validate_mesh(printable)
            if not q['valid'] or q['components']!=1:raise GeometryError(f'{pid} is not one closed solid')
            quality[pid]=q;part.save(out/'parts');parts.append(part)
            x=35.+row_index*40.;y=20.+column*30.;transform=np.eye(4);transform[:3,3]=[x,y,0]
            extents=printable.extents;met=metrics(printable)
            placements.append({'part_id':pid,'transform':transform.tolist(),'rect':[x,y,*extents[:2].tolist()],
                'height_mm':float(extents[2]),'color':part.color,**met,
                'support_status':'ENABLE SUPPORT + BRIM; curved visible nose faces bed' if kind=='nose' else 'hole up; slicer review required'})
            source_to_print=np.eye(4);source_to_print[:3,:3]=rotation;source_to_print[:3,3]=-origin
            variant['parts'].append({'part_id':pid,'source_to_print_transform':source_to_print.tolist(),
                'source_to_plate_transform':(transform@source_to_print).tolist(),'axis_to_plus_z_angle_deg':0.,
                'bounds_on_plate_mm':[(printable.bounds[0]+[x,y,0]).tolist(),(printable.bounds[1]+[x,y,0]).tolist()],
                'support_required':kind=='nose',**met})
        variants.append(variant);row_labels.append(f'{code}: X={35+row_index*40} mm; front nose / rear socket; radial {clearance:.2f} mm')
        print(f'{code} geometry and mating checks passed',flush=True)
    plates=[{'id':1,'colors':['#EFB27C'],'volume_mm':[300,320,320],'placements':placements}]
    packing=validate_packing(parts,plates)
    if not packing['passed']:raise GeometryError(str(packing))
    males=[part.mesh for part in parts if part.id.endswith('-nose')]
    if any(not np.array_equal(males[0].faces,mesh.faces) or not np.array_equal(males[0].vertices,mesh.vertices) for mesh in males[1:]):
        raise GeometryError('Comparison male specimens differ')
    report={'purpose':'Physical radial-clearance comparison with fixed vertical keyed pins, original anatomical nose and cropped exact sockets',
        'source_project':args.project,'source_sha256':SOURCE_SHA256,'mesh_hash':artifact['hash'],'plan_hash':plan_artifact['hash'],
        'source_face_count':len(indexes),'canonical_construction':canonical_report,'anatomical_proposal':anatomy,
        'male_specimens_identical':True,'variants':variants,'quality':quality,'packing':packing,'plates':plates,'layout_rows':row_labels,
        'prior_orientation':{'old_color_only_nose_axis_above_bed_deg':.4832,'old_socket_opening_tilt_from_plus_z_deg':14.79,
          'anatomical_previous_nose_pin_tilt_from_plus_z_deg':109.38,
          'cause':'Previous heuristic selected an almost horizontal pin; unsupported key flank may confound clearance results.'},
        'material':'User reports PLA, 0.4-mm nozzle; actual spool unknown. Prior screenshot profile: 0.12 Fine H2D.',
        'warnings':['Enable slicer supports and brim for ALL FOUR NOSES: curved visible face points down and has little bed contact.',
          'Do not auto-orient these parts: pins must remain +Z and socket openings +Z.',
          'All clearances are positive; this is neither a press-fit nor a snap-fit. All noses have identical male geometry. Clearance only changes the female contour; no retention or antirotation success is claimed.',
          'A005/B010/C015/D020 are object names and layout rows, not embossed labels. Keep row order or label parts after printing.',
          'Core geometry files contain no machine, filament or support presets. Bambu support/slice verification remains required.',
          'The complete 210-face anatomical nose differs from the earlier 151-face color-only probe; compare the four new pairs against each other.'],
        'physical_print_verified':False,'bambu_sliced':False,'sent_to_printer':False}
    roundtrips={'plate-01.3mf':write_3mf(parts,out/'plate-01.3mf',placements,metadata=report)}
    for part in parts:roundtrips[part.id+'.3mf']=write_3mf([part],out/(part.id+'.3mf'),metadata={'part_id':part.id,'support_required':part.id.endswith('-nose'),'comparison':True})
    if not all(row['bambu_printable_items'] for row in roundtrips.values()):raise GeometryError('Numeric printable=1 missing')
    report['three_mf_roundtrips']=roundtrips
    (out/'geometry-check.json').write_text(json.dumps(report,indent=2)+'\n')
    plate_image(parts,placements,out/'plate-layout.png')
    (out/'README.md').write_text('# Nasen-Passungsvergleich – senkrechte Stifte\n\n'
        'Vier identische Ø3 × 3 mm keyed Stifte; nur die Taschen unterscheiden sich.\n\n'
        '| Spalte (X) | IDs | Radiales Spiel | Durchmesserspiel |\n|---|---|---|---|\n'
        '| links (35 mm) | A005-nose / A005-socket | 0,05 mm | 0,10 mm |\n'
        '| zweite (75 mm) | B010-nose / B010-socket | 0,10 mm | 0,20 mm |\n'
        '| dritte (115 mm) | C015-nose / C015-socket | 0,15 mm | 0,30 mm |\n'
        '| rechts (155 mm) | D020-nose / D020-socket | 0,20 mm | 0,40 mm |\n\n'
        '**Alle Nasen mit Support und Brim slicen.** Der Stift zeigt senkrecht nach oben; die gewölbte Sichtseite liegt unten. '
        'Taschenöffnungen zeigen senkrecht nach oben, der Taschenblock besitzt eine ebene Unterseite. Nicht automatisch neu orientieren. '
        'Vorne liegen die Nasen, dahinter die Taschen. Links → rechts: 0,05 / 0,10 / 0,15 / 0,20 mm. IDs sind Objektnamen und Positionen, nicht eingeprägte Beschriftungen. Nach dem Druck sofort markieren.\n\n'
        'Die frühere Probe lag mit fast waagerechtem Stift (0,48° über dem Bett). Deren beschädigte Schlüsselflanke '
        'vermischt Überhangfehler mit Passung. Die neue vollständige anatomische Nase enthält 210 Quellflächen und unterscheidet sich '
        'von der alten 151-Flächen-Nase. Nur die vier neuen Paare untereinander vergleichen.\n\n'
        'PLA / 0,4-mm-Düse gemeldet; konkrete Spule unbekannt. Geometrie- und Pfadprüfungen bestanden; '
        'reale Haltekraft, Verdrehspiel und Druckqualität noch ungeprüft. Alle Spiele sind positiv: keine Presspassung und kein Schnappverschluss. Core-3MF ohne Maschinen-/Supportprofil; '
        'Slicing in Bambu Studio folgt separat. Nichts an den Drucker gesendet.\n')
    print(json.dumps({'output':str(out),'parts':len(parts),'packing':packing,'numeric_printable_items':True}),flush=True)


if __name__=='__main__':main()
