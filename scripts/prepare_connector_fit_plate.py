"""New small Pip/Buddy connector calibration plate, actual kernel profiles only.

No project/original writes or printer communication. All .05 mm radial; not a
claim that the accepted Mochi nose fit transfers to different shapes/materials.
"""
from pathlib import Path
import argparse,hashlib,json,uuid
import numpy as np
import trimesh
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from figuraforge.geometry.connectors import Connector
from figuraforge.geometry.topology import triangulate_polygon,orient_local,mesh_from_triangles
from figuraforge.geometry.types import Part
from figuraforge.geometry.validation import validate_mesh
from figuraforge.geometry.packing import validate_packing
from figuraforge.services.export import write_3mf
from figuraforge.services.mixed_filament import read_native_template,build_native_from_parts
ROOT=Path(__file__).resolve().parents[1]
SPECS=[('A','Buddy collar main',6.,10.,'keyed'),('B','Buddy collar small',2.,6.,'keyed'),('C','Pip pupil',.9,1.5,'round'),('D','Pip iris',1.2,2.5,'round')]

def cap(poly,z,positive):
    t=triangulate_polygon(poly);return orient_local(np.dstack([t,np.full(t.shape[:2],z)]),positive)

def walls(poly,z0,z1,scale1=1.,origin=(0.,0.),reverse=False):
    poly=orient(poly,sign=1.);out=[]
    for ring in [poly.exterior,*poly.interiors]:
        xy=np.asarray(ring.coords)[:-1];hi=(xy-origin)*scale1+origin;lo=np.c_[xy,np.full(len(xy),z0)];up=np.c_[hi,np.full(len(xy),z1)]
        for i in range(len(xy)):
            j=(i+1)%len(xy);out.extend([[lo[i],lo[j],up[j]],[lo[i],up[j],up[i]]])
    t=np.asarray(out);return t[:,::-1] if reverse else t

def label_polygon(letter):
    rings=TextPath((0,0),letter,size=4.5,prop=FontProperties(family='DejaVu Sans',weight='bold')).to_polygons();shape=Polygon()
    for ring in rings:shape=shape.symmetric_difference(Polygon(ring))
    from shapely.affinity import translate
    bounds=shape.bounds;return translate(shape,xoff=-(bounds[0]+bounds[2])/2,yoff=-8-(bounds[1]+bounds[3])/2)

def coupon(letter,radius,length,shape,female):
    # Same Connector.profile and full-length .85 tip taper as root_with_connectors.
    pin=Connector(0,4,radius,length,-length,shape,.05,.35);profile=orient(pin.profile(socket=female),sign=1.);label=label_polygon(letter);base=box(-10,-12,10,12);top=2+length+.35 if female else 2.
    triangles=[cap(base,0,False),walls(base,0,top),cap(base.difference(profile.union(label)),top,True)]
    if female:triangles.extend([walls(profile,2,top,reverse=True),cap(profile,2,True)])
    else:
        from shapely.affinity import scale
        tip=scale(profile,xfact=.85,yfact=.85,origin=(0,4));triangles.extend([walls(profile,top,top+length,scale1=.85,origin=(0,4)),cap(tip,top+length,True)])
    triangles.extend([walls(label,top,top+.4),cap(label,top+.4,True)])
    mesh=mesh_from_triangles(np.concatenate(triangles));q=validate_mesh(mesh)
    if not q['valid'] or q['components']!=1:raise ValueError(q)
    overhang=float(mesh.area_faces[(mesh.face_normals[:,2]<-.707)&(mesh.triangles[:,:,2].min(1)>.001)].sum())
    if overhang>1e-6:raise ValueError('Unexpected downward/bridged surface above bed')
    profile_volume=profile.area*(length+.35) if female else profile.area*length*(1+.85+.85**2)/3
    expected=base.area*top+label.area*.4+(-profile_volume if female else profile_volume)
    if abs(mesh.volume-expected)>1e-4:raise ValueError('Coupon volume mismatch')
    return mesh,{'quality':q,'above_bed_downward_area_mm2':overhang,'expected_volume_mm3':expected,'volume_error_mm3':float(mesh.volume-expected),'label':letter,'role':'female' if female else 'male','nominal_diameter_or_key_width_mm':radius*2,'nominal_pin_length_mm':length,'radial_clearance_mm':.05,'tip_clearance_mm':.35,'shape':shape,'pin_tip_scale':.85,'flat_floor_mm':2}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'benchmarks/connector-fit-pip-buddy');parser.add_argument('--template',type=Path,default=ROOT/'data/native-templates/h2d-dragon-profiles-only.3mf');args=parser.parse_args();work=args.output.resolve()/('fit-'+uuid.uuid4().hex);work.mkdir(parents=True);parts=[];placements=[];report={'physical_fit_verified':False,'printer_communication':False,'coupons':{},'source_specs':{},'bed_origin_offset_mm':[25,0,0]}
    for row,(letter,name,radius,length,shape) in enumerate(SPECS):
        report['source_specs'][letter]={'purpose':name,'radius_mm':radius,'length_mm':length,'shape':shape}
        for column,female in enumerate([False,True]):
            mesh,qa=coupon(letter,radius,length,shape,female);ident=letter+('-socket' if female else '-pin');part=Part(ident,f'{letter} {name} '+('socket' if female else 'pin'),mesh,'#F7E6DE',filament_id='richard-inventory-202609-31');parts.append(part);report['coupons'][ident]=qa
            tf=np.eye(4);tf[:3,3]=[45+column*34,25+row*36,0];placements.append({'part_id':ident,'transform':tf.tolist(),'rect':[35+column*34,13+row*36,20.,24.],'height_mm':float(mesh.bounds[1,2]),'color':'#F7E6DE'})
    # Coordinates already native/shared-bed coordinates; no second +25 shift.
    packing=validate_packing(parts,[{'id':1,'placements':placements,'volume_mm':[350,320,320]}])
    if not packing['passed']:raise ValueError(packing)
    report['packing']=packing;report['placements']=placements
    for part in parts:part.save(work/'parts')
    write_3mf(parts,work/'geometry-core.3mf',placements,{'kind':'connector-calibration'})
    settings,_=read_native_template(args.template)
    settings.update(layer_height='0.12',initial_layer_print_height='0.2',enable_support='0',raft_layers='0',brim_type='no_brim',brim_width='0',support_filament='2',support_interface_filament='2',enable_mixed_color_sublayer='0')
    settings['filament_is_mixed']=['0']*len(settings['filament_colour'])
    output=work/'Pip-Buddy-Passung-Beige-H2D.3mf';report['native']=build_native_from_parts(args.template,output,parts,placements,settings,{p.id:[2]*len(p.mesh.faces) for p in parts})
    report['profile']={'native_slot':2,'actual_hex':settings['filament_colour'][1],'profile_name':settings.get('filament_settings_id',[None,None])[1],'nozzle_diameter':settings['nozzle_diameter'],'layer_height_mm':.12,'initial_layer_height_mm':.2,'support':False,'raft':False,'brim':False,'actual_spool':'Bambu PLA Basic Beige31; physical stock loading is user action'}
    report['source_code_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'backend/figuraforge/geometry/connectors.py',ROOT/'backend/figuraforge/geometry/buddy_collar.py',ROOT/'backend/figuraforge/services/pip_pipeline.py']}
    (work/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(str(work),flush=True)
    (work/'PASSUNG.md').write_text('''# Optionaler Pip-/Buddy-Passungstest\n\nEine Platte, acht beschriftete Teile, genau vier Paare. Kein automatischer Druckstart.\n\n| Buchstabe | Anschluss | Form | Nennmaß | Länge |\n|---|---|---|---|---|\n| A | Buddy großer Kragenstift | keyed, angefastes Quadrat | 12 mm Schlüsselbreite | 10 mm |\n| B | Buddy kleiner Kragenstift | keyed, angefastes Quadrat | 4 mm Schlüsselbreite | 6 mm |\n| C | Pip Pupille | rund | Ø1,8 mm | 1,5 mm |\n| D | Pip Iris | rund | Ø2,4 mm | 2,5 mm |\n\n1. Native Datei in Bambu Studio öffnen: H2D, beide Düsen0,4 mm, tatsächliches Beige31 in Slot2, Layer0,12 mm.\n2. Ausrichtung beibehalten: Stifte stehen aufrecht, Taschen oben offen. Supports/Raft/Brim sind ausgeschaltet; innerhalb der Taschen ist keine Stütze nötig.\n3. Nach Abkühlen die Teile mit gleichem Buchstaben zusammenstecken. Alle vier Paare haben0,05 mm nominales radiales Spiel; keine engeren Varianten.\n4. Pro Paar Sitz, Einsteckkraft und verbleibendes Spiel beurteilen. Nicht mit Gewalt stecken. Erst diese Ergebnisse auf die jeweiligen Figuranschlüsse übertragen.\n\nDies sind neue Größen und teils neue Profilformen. Die akzeptierte Mochi-Nasenprobe ist keine physische Abnahme dieser Anschlüsse. Keyed-Maße bezeichnen die nominelle Quadratbreite, keinen kreisförmigen Durchmesser; die echten Ecken reichen weiter. Spitzen folgen exakt der85%-Verjüngung des Konstruktionskerns, Taschen besitzen0,35 mm axiales Spitzenspiel und2 mm geschlossenen Boden.\n''')
if __name__=='__main__':main()
