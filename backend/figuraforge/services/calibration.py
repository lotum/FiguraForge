"""Physical fit coupons made by the same joint kernel as the production parts."""
from pathlib import Path
import numpy as np
import trimesh
from ..geometry.split import split_with_joint
from ..geometry.types import Part
from ..geometry.packing import pack_parts
from .export import export_bundle


def create_calibration(directory:Path,shape='round',radius=1.5,length=4):
    directory.mkdir(parents=True,exist_ok=True)
    parts=[]; pairs=[]
    width=max(18,6*radius+8); height=max(9,length+radius+2)
    for i,clearance in enumerate((.10,.15,.20,.25,.30)):
        body=trimesh.creation.box([width,width,2*height]); body.apply_translation([i*(width+4),0,height])
        male,female,connectors,d=split_with_joint(body,2,height,radius,length,clearance,shape,count=1)
        if len(connectors)!=1: raise ValueError('Could not place the calibration connector')
        pair=f'{shape}-{int(round(clearance*100)):02d}'
        for role,mesh in [('pin',male),('socket',female)]:
            parts.append(Part(f'{pair}-{role}',f'{shape} / {clearance:.2f} mm / {role}',mesh,'#899C89',0,
                'calibration',d.tolist(),connectors,[]))
        pairs.append({'pair':pair,'radial_clearance_mm':clearance,'diametral_clearance_mm':clearance*2,
            'pin_id':pair+'-pin','socket_id':pair+'-socket'})
    plates=pack_parts(parts,max_colors=1)
    instructions=['# Steckverbinder-Passungstest','',
        'Dies sind reale Testkoerper aus demselben Geometriekern wie die Figurenteile.',
        'Die im Objektnamen genannte Zahl ist das RADIALE Spiel; der Durchmesserunterschied ist doppelt so gross.',
        'Stift und Buchse mit denselben Filamenten, derselben Duese und aehnlicher Orientierung wie die Figur drucken.',
        'Nach Abkuehlen entgraten und das kleinste Spiel waehlen, das ohne Kraft passt. Keine Presspassung erzwingen.',
        'Den ermittelten Wert in Konstruktion > Radiales Spiel eintragen. Das ist kein zertifizierter Belastungstest.',
        'Runde und kantige Verbinder sind Fuegungen mit Spiel, keine selbstverriegelnden Schnapphaken.',
        'Die Teile sind nicht erhaben beschriftet: Zuordnung ueber Objektnamen und die folgende Plattenliste.',
        '', '| Platte | Objekt | XY-Mittelpunkt / mm |', '|---|---|---|']
    for plate in plates:
        for item in plate['placements']:
            part=next(p for p in parts if p.id==item['part_id']); tf=np.asarray(item['transform'])
            point=np.r_[part.mesh.bounds.mean(axis=0),1]@tf.T
            instructions.append(f"| {plate['id']} | {part.id} | {point[0]:.1f}, {point[1]:.1f} |")
    (directory/'PASSUNG.md').write_text('\n'.join(instructions),encoding='utf-8')
    return export_bundle(parts,plates,directory,{'kind':'connector-calibration','shape':shape,
        'radius_mm':radius,'length_mm':length,'pairs':pairs,'physical_print_test':False})
