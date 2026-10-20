from __future__ import annotations
import io
import json
import zipfile
import hashlib
from pathlib import Path
from xml.etree import ElementTree as ET
import numpy as np
import trimesh
from ..geometry.types import Part, GeometryError
from ..geometry.validation import validate_mesh
from ..geometry.packing import validate_packing

CORE='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
REL='http://schemas.openxmlformats.org/package/2006/relationships'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
ET.register_namespace('',CORE)


def tag(name): return f'{{{CORE}}}{name}'


def write_3mf(parts:list[Part],path:Path,placements:list[dict]|None=None,metadata:dict|None=None):
    """3MF Core in millimeters, standard base materials, named separate objects.

    This is not advertised as a complete native Bambu multi-plate project. Each
    plate is exported separately; users keep their own machine/filament profiles.
    """
    if not parts: raise GeometryError('Cannot export an empty model')
    model=ET.Element(tag('model'),{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    ET.SubElement(model,tag('metadata'),{'name':'Title'}).text='FiguraForge printable parts'
    ET.SubElement(model,tag('metadata'),{'name':'Application'}).text='FiguraForge 0.1.0'
    resources=ET.SubElement(model,tag('resources'))
    colors=list(dict.fromkeys(p.color for p in parts))
    mats=ET.SubElement(resources,tag('basematerials'),{'id':'1'})
    for color in colors: ET.SubElement(mats,tag('base'),{'name':color,'displaycolor':color+'FF'})
    ids={}; origins={}
    for i,p in enumerate(parts,2):
        if not validate_mesh(p.mesh)['valid']: raise GeometryError(f'Cannot export invalid part: {p.id}')
        ids[p.id]=str(i)
        # Slicers store mesh coordinates as float32 before applying instances.
        # Keep small curved inserts near zero so distant assembly coordinates
        # do not collapse narrow triangles. Placement restores the exact origin.
        origins[p.id]=p.mesh.bounds.mean(axis=0)
        obj=ET.SubElement(resources,tag('object'),{'id':str(i),'type':'model','name':p.name,
            'partnumber':p.id,'pid':'1','pindex':str(colors.index(p.color))})
        mesh=ET.SubElement(obj,tag('mesh')); vertices=ET.SubElement(mesh,tag('vertices'))
        for x,y,z in np.asarray(p.mesh.vertices)-origins[p.id]:
            ET.SubElement(vertices,tag('vertex'),{'x':format(x,'.10g'),'y':format(y,'.10g'),'z':format(z,'.10g')})
        faces=ET.SubElement(mesh,tag('triangles'))
        for a,b,c in np.asarray(p.mesh.faces):
            ET.SubElement(faces,tag('triangle'),{'v1':str(a),'v2':str(b),'v3':str(c)})
    build=ET.SubElement(model,tag('build'))
    if placements is None: placements=[{'part_id':p.id,'transform':np.eye(4).tolist()} for p in parts]
    for item in placements:
        tf=np.asarray(item['transform'],dtype=float).copy()
        tf[:3,3]+=tf[:3,:3]@origins[item['part_id']]
        # 3MF transform order: 3x3 row-vector matrix, then translation (12 values).
        values=np.r_[tf[:3,:3].T.reshape(-1),tf[:3,3]]
        ET.SubElement(build,tag('item'),{'objectid':ids[item['part_id']],
            # Bambu's 3MF reader parses this XML boolean with atoi: the valid
            # spelling "true" becomes false there. Numeric 1 works in both
            # the 3MF schema and Bambu, keeping geometry eligible for slicing.
            'transform':' '.join(format(v,'.10g') for v in values),'printable':'1'})
    content=ET.Element('Types',{'xmlns':CT})
    ET.SubElement(content,'Default',{'Extension':'rels','ContentType':'application/vnd.openxmlformats-package.relationships+xml'})
    ET.SubElement(content,'Default',{'Extension':'model','ContentType':'application/vnd.ms-package.3dmanufacturing-3dmodel+xml'})
    ET.SubElement(content,'Default',{'Extension':'json','ContentType':'application/json'})
    rels=ET.Element('Relationships',{'xmlns':REL})
    ET.SubElement(rels,'Relationship',{'Target':'/3D/3dmodel.model','Id':'rel0','Type':'http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel'})
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',ET.tostring(content,encoding='utf-8',xml_declaration=True))
        z.writestr('_rels/.rels',ET.tostring(rels,encoding='utf-8',xml_declaration=True))
        z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
        z.writestr('Metadata/figuraforge.json',json.dumps(metadata or {},indent=2,allow_nan=False))
    return validate_3mf(path)


def validate_3mf(path:Path):
    with zipfile.ZipFile(path) as z:
        required={'[Content_Types].xml','_rels/.rels','3D/3dmodel.model'}
        if not required.issubset(z.namelist()): raise GeometryError('Incomplete 3MF package')
        doc=ET.fromstring(z.read('3D/3dmodel.model'))
        if doc.get('unit')!='millimeter': raise GeometryError('3MF unit mismatch')
        resources=doc.find(tag('resources')); ids=set(); meshes=[]
        for obj in resources.findall(tag('object')):
            ids.add(obj.get('id')); block=obj.find(tag('mesh'))
            vs=np.array([[float(v.get(c)) for c in ('x','y','z')] for v in block.find(tag('vertices'))])
            fs=np.array([[int(t.get(c)) for c in ('v1','v2','v3')] for t in block.find(tag('triangles'))])
            if not len(vs) or fs.min()<0 or fs.max()>=len(vs): raise GeometryError('Invalid 3MF indices')
            m=trimesh.Trimesh(vs,fs,process=False)
            if not m.is_volume: raise GeometryError('3MF round-trip mesh is not a volume')
            meshes.append({'id':obj.get('id'),'triangles':len(fs),'volume_mm3':float(m.volume)})
        for item in doc.find(tag('build')):
            if item.get('objectid') not in ids: raise GeometryError('Invalid 3MF build reference')
            if item.get('printable')!='1':
                raise GeometryError('3MF item is not explicitly Bambu-printable; numeric printable="1" is required')
            transform=np.fromstring(item.get('transform',''),sep=' ')
            if len(transform)!=12 or not np.isfinite(transform).all(): raise GeometryError('Invalid 3MF transform')
    return {'passed':True,'objects':len(meshes),'meshes':meshes,'bambu_printable_items':True,
            'validation':'independent XML/geometry round-trip, not an official 3MF conformance certificate',
            'bambu_studio_live_test':False}


def export_bundle(parts,plates,directory:Path,metadata=None,*,additional_files=()):
    directory.mkdir(parents=True,exist_ok=True)
    packcheck=validate_packing(parts,plates)
    if not packcheck['passed']: raise GeometryError('Invalid plate placement')
    meta=dict(metadata or {}); meta['plates']=plates; meta['parts']=[p.summary() for p in parts]
    meta['packing_validation']=packcheck
    meta['format_notes']={
        '3mf':'Core 3MF, one file per plate. No machine profile is silently invented.',
        'colors':'Standard material colors are included. Confirm real filament/nozzle assignments in Bambu Studio.',
        'profiles':'Use your actual H2D profile, supports and material temperatures.',
        'slicing':'Not sliced. Brims, supports, purge tower and collision/exclusion zones need slicer review.',
    }
    if meta.get('native_color_export'):
        meta['format_notes']['native']='plate-XX-native.3mf contains the planned per-face native recipes; experimental, GUI and slicing unverified.'
        meta['format_notes']['colors']='Core 3MF and GLB companions show one color per part; native files preserve planned regional colors.'
    validations={}
    validations['assembly']=write_3mf(parts,directory/'assembly.3mf',metadata=meta)
    for plate in plates:
        selected=[next(p for p in parts if p.id==i['part_id']) for i in plate['placements']]
        validations[f"plate-{plate['id']:02d}"]=write_3mf(selected,directory/f"plate-{plate['id']:02d}.3mf",plate['placements'],meta)
    for p in parts:
        write_3mf([p],directory/f'{p.id}.3mf',metadata=p.summary())
    scene=trimesh.Scene()
    from ..geometry.colors import hex_rgb
    for p in parts:
        m=p.mesh.copy(); m.visual.face_colors=np.r_[hex_rgb(p.color)*255,255].astype(np.uint8)
        scene.add_geometry(m,node_name=p.id,geom_name=p.id)
    # GLB uses meters and Y-up. Print files stay in mm and Z-up.
    tf=np.array([[.001,0,0,0],[0,0,.001,0],[0,-.001,0,0],[0,0,0,1]])
    scene.apply_transform(tf); (directory/'assembly.glb').write_bytes(scene.export(file_type='glb'))
    (directory/'manifest.json').write_text(json.dumps(meta,indent=2,allow_nan=False),encoding='utf-8')
    (directory/'validation.json').write_text(json.dumps(validations,indent=2,allow_nan=False),encoding='utf-8')
    lines=['# Montage und Druckvorbereitung','',
           ('1. PASSUNG.md lesen und die Testpaare drucken.' if meta.get('kind')=='connector-calibration' else '1. Zuerst die Steckverbinder-Kalibrierung mit den tatsaechlichen Filamenten drucken.'),
           ('2. Je plate-XX-native.3mf als natives Projekt in Bambu Studio oeffnen; reale H2D-Duesen und Filamente pruefen.' if meta.get('native_color_export') else '2. Je plate-XX.3mf als Geometrie in Bambu Studio importieren. H2D-Profil und Filamente selbst bestaetigen.'),
           '3. Stuetzmaterial, Brim, Druckbett-Sperrflaechen und Ausrichtung vor dem Slicen kontrollieren.',
           '4. Verbindungen entgraten; die unten dokumentierte Montagefolge beachten. Nicht mit Gewalt stecken.']
    construction=meta.get('geometry_report',{}).get('construction',{})
    connections=construction.get('assembly_connections',{})
    if not connections and construction.get('construction_preset')=='buddy-anatomical-v1':
        from .buddy_pipeline import connection_summary
        connections=connection_summary(construction)
    if connections.get('total_keys'):
        lines+=['',f"Konstruktionsübersicht: {connections['total_keys']} Schlüssel an {connections['total_keyed_interfaces']} Steckanschlüssen. Strukturkacheln können mehrere Anschlussebenen besitzen; ihre lokalen Connectorlisten sind kein vollständiger Gesamtzähler."]
    instructions=construction.get('assembly_instructions_de',[])
    if not instructions and construction.get('construction_preset')=='buddy-anatomical-v1':
        from .buddy_pipeline import assembly_instructions
        instructions=assembly_instructions(construction)
    if instructions:
        lines+=['','## Modellgebundene Montagefolge','']+[f'{i}. {step}' for i,step in enumerate(instructions,1)]
    else:
        lines+=['5. Einsaetze entlang des im Manifest angegebenen Vektors einsetzen (Montage entgegen dem Auszugsvektor).']
    lines+=['','## Teile','']
    structural=set(connections.get('structural_leaf_part_ids',[]))
    glue=set(connections.get('glue_part_ids',[]))
    for p in parts:
        connection_note=(('gefangenes/Klebefragment; Montagefolge beachten' if p.id=='collar-neck-1' else 'Klebeteil; reale Klebepassung prüfen') if p.id in glue else
                         'Strukturkachel mit Schlüsselflächen; Montagebaum beachten' if p.id in structural else
                         'Buchsenteil für Halsbandgegenstück' if connections and p.id=='collar-right' else
                         f'{len(p.connectors)} Verbinder')
        lines.append(f'- {p.id}: {p.name}; {p.color}; {connection_note}.')
        lines.extend(f'  - Hinweis: {w}' for w in p.warnings)
    lines+=['','## Grenzen','',
            'Die digitale Pruefung ist kein realer Passungs-, Festigkeits- oder Kipptest. Die Gesamtmontage dieser Figur ist noch nicht physisch geprueft.']
    if meta.get('native_color_export'):
        lines+=['','## Native Farbdateien','',
                'Fuer die geplanten Flaechenfarben plate-XX-native.3mf oeffnen. Die Core-Dateien und assembly.glb sind einfarbige Geometriebegleiter je Teil.',
                'H2D-Duesenzuordnung und Slicing vor dem Druck pruefen; eine GUI-/Druckabnahme wird durch den Export allein nicht behauptet.']
    (directory/'MONTAGE.md').write_text('\n'.join(lines),encoding='utf-8')
    names={'assembly.3mf','assembly.glb','manifest.json','validation.json','MONTAGE.md'}
    names.update(f"plate-{plate['id']:02d}.3mf" for plate in plates)
    names.update(f'{p.id}.3mf' for p in parts)
    for name in additional_files:
        if Path(name).name!=name or not (directory/name).is_file():
            raise GeometryError('Invalid additional export artifact')
        names.add(name)
    if meta.get('kind')=='connector-calibration' and (directory/'PASSUNG.md').exists(): names.add('PASSUNG.md')
    # Only this export's files are included, even when a CLI output directory is reused.
    checksums={name:hashlib.sha256((directory/name).read_bytes()).hexdigest() for name in sorted(names)}
    (directory/'SHA256.json').write_text(json.dumps(checksums,indent=2))
    names.add('SHA256.json')
    bundle=directory/'print-package.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(names): z.write(directory/name,name)
    return {'bundle':bundle.name,'files':sorted(names|{bundle.name}),
            'plates':len(plates),'parts':len(parts),'validation':validations}
