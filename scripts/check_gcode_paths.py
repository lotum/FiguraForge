#!/usr/bin/env python3
"""Independent same-Z, cross-object extrusion footprint screening; no printer I/O.

Bambu start/stop printing comments own moves; OBJECT_ID does not. This checks
planar linear/G17 I/J arc extrusions, not complete nozzle clearance, dynamics
or physics. Arc chord error is bounded and added conservatively to footprints.
"""
from __future__ import annotations
import argparse,hashlib,json,re,struct,tempfile,zipfile,math,time
from pathlib import Path
from contextlib import ExitStack
import numpy as np
from shapely.geometry import LineString,box
from shapely.strtree import STRtree
FIELDS=np.dtype([('z','<f8'),('x1','<f8'),('y1','<f8'),('x2','<f8'),('y2','<f8'),('width','<f8'),('owner','<i8'),('kind','<i8'),('line','<i8'),('height','<f8')])
PACK=struct.Struct('<6d3qd');NUM=re.compile(r'([XYZEFIJKRP])\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+))');START=re.compile(r'^; start printing object, unique label id:\s*(-?\d+)');STOP='; stop printing object,'

ARC_CHORD_ERROR_MM=.005


def arc_points(start,end,offsets,clockwise,*,max_chord_error_mm=ARC_CHORD_ERROR_MM):
    """Approximate a G17 relative-I/J circle; endpoints remain exact.

    Rounded I/J endpoints may have a small radius mismatch. Its full amount is
    deducted from the chord-error budget. Larger mismatches fail explicitly.
    """
    start=np.asarray(start,dtype=float);end=np.asarray(end,dtype=float);offsets=np.asarray(offsets,dtype=float)
    if not np.isfinite(np.r_[start,end,offsets,max_chord_error_mm]).all() or max_chord_error_mm<=0:raise ValueError('Invalid arc coordinates/error bound')
    center=start+offsets;radius=float(np.linalg.norm(offsets));endradius=float(np.linalg.norm(end-center));mismatch=abs(radius-endradius)
    if radius<=1e-9:raise ValueError('Arc center must differ from start')
    if mismatch>max_chord_error_mm/2:raise ValueError(f'Arc endpoint radius mismatch {mismatch:.6f} mm exceeds supported rounding budget')
    first=math.atan2(start[1]-center[1],start[0]-center[0]);last=math.atan2(end[1]-center[1],end[0]-center[0]);full=np.linalg.norm(end-start)<=1e-9
    sweep=(-1 if clockwise else 1)*(2*math.pi if full else ((first-last) if clockwise else (last-first))%(2*math.pi))
    if abs(sweep)<1e-10:raise ValueError('Degenerate arc sweep')
    budget=max_chord_error_mm-mismatch
    # <= pi/2 also preserves winding for circles smaller than error budget.
    max_angle=min(math.pi/2,2*math.acos(max(-1.,min(1.,1-budget/radius))))
    count=max(1,math.ceil(abs(sweep)/max_angle))
    if count>1000000:raise ValueError('Arc subdivision exceeds bounded segment limit')
    angles=np.linspace(first,first+sweep,count+1);points=center+radius*np.column_stack([np.cos(angles),np.sin(angles)]);points[0]=start;points[-1]=end
    bound=radius*(1-math.cos(abs(sweep)/(2*count)))+mismatch
    return points,float(bound),mismatch


def parse(lines, *, single_object_id=None,stats=None):
    xyz=np.zeros(3);e=0.;absolute=True;erel=False;owner=-1 if single_object_id is None else single_object_id;kind=0;width=.4;height=.2;plane='G17';absolute_centers=False
    for number,raw in enumerate(lines,1):
        line=raw.strip();match=START.match(line)
        if match:owner=int(match[1]);continue
        if line.startswith(STOP):owner=-3;continue
        if line.startswith('; FEATURE:'):
            feature=line.split(':',1)[1].strip().lower();kind=2 if 'prime tower' in feature else 1 if feature.startswith('support') else 0 if feature!='custom' else 3
            continue
        if line.startswith('; LINE_WIDTH:'):width=float(line.split(':',1)[1]);continue
        if line.startswith('; LAYER_HEIGHT:'):height=float(line.split(':',1)[1]);continue
        cmd=line.split(';',1)[0].strip();op=cmd.split(' ',1)[0]
        if op in ('G17','G18','G19'):plane=op;continue
        if op=='G90.1':absolute_centers=True;continue
        if op=='G91.1':absolute_centers=False;continue
        if op=='G90':absolute=True;continue
        if op=='G91':absolute=False;continue
        if op=='M82':erel=False;continue
        if op=='M83':erel=True;continue
        if op not in ('G0','G1','G2','G3','G92'):continue
        values={k:float(v) for k,v in NUM.findall(cmd)}
        if op=='G92':
            for i,k in enumerate('XYZ'):
                if k in values:xyz[i]=values[k]
            if 'E' in values:e=values['E']
            continue
        nxt=xyz.copy()
        for i,k in enumerate('XYZ'):
            if k in values:nxt[i]=values[k] if absolute else xyz[i]+values[k]
        de=values.get('E',0.) if erel else values.get('E',e)-e
        if 'E' in values:e=e+values['E'] if erel else values['E']
        is_arc=op in ('G2','G3');segments=None;effective_width=width
        eligible=de>1e-9 and kind!=3 and (owner!=-3 or kind==2)
        if is_arc and not eligible:
            # Travel/startup arcs have no screened printed bead. Update their
            # exact endpoint/modal state even for helical or vendor parameters.
            if stats is not None:stats['ignored_nonprinting_arc_commands']=stats.get('ignored_nonprinting_arc_commands',0)+1
            xyz=nxt;continue
        if is_arc:
            if plane!='G17':raise ValueError(f'Arc plane {plane} unsupported at line {number}; only G17 XY')
            if absolute_centers:raise ValueError(f'Absolute arc centers G90.1 unsupported at line {number}')
            if 'R' in values:raise ValueError(f'R-encoded arc unsupported at line {number}; require relative I/J')
            if abs(values.get('K',0))>1e-9 or values.get('P',1)!=1:raise ValueError(f'Unsupported arc K/P parameters at line {number}')
            if 'I' not in values and 'J' not in values:raise ValueError(f'Arc needs relative I/J center at line {number}')
            if abs(nxt[2]-xyz[2])>1e-5:raise ValueError(f'Helical arc/nonplanar Z unsupported at line {number}')
            segments,error,mismatch=arc_points(xyz[:2],nxt[:2],[values.get('I',0),values.get('J',0)],op=='G2')
            effective_width=width+2*error
            if stats is not None:
                stats['arc_commands']=stats.get('arc_commands',0)+1
                stats['maximum_arc_chord_error_bound_mm']=max(stats.get('maximum_arc_chord_error_bound_mm',0),error)
                stats['maximum_arc_radius_mismatch_mm']=max(stats.get('maximum_arc_radius_mismatch_mm',0),mismatch)
        eligible=de>1e-9 and kind!=3 and (owner!=-3 or kind==2)
        if eligible and (is_arc or np.linalg.norm(nxt[:2]-xyz[:2])>1e-8):
            if abs(nxt[2]-xyz[2])>1e-5:raise ValueError(f'Nonplanar extrusion at line {number}; unsupported, not a passed screening')
            if is_arc:
                if stats is not None:
                    stats['extrusion_arcs']=stats.get('extrusion_arcs',0)+1
                    stats['arc_generated_segments']=stats.get('arc_generated_segments',0)+len(segments)-1
                points=segments
            else:points=[xyz[:2],nxt[:2]]
            for a,b in zip(points[:-1],points[1:]):
                yield (round(float(nxt[2]),5),float(a[0]),float(a[1]),float(b[0]),float(b[1]),effective_width,owner if kind!=2 else -2,kind,number,height)
        xyz=nxt

def candidate_kind(a,b):
    if int(a['owner'])==int(b['owner']):return None
    ka,kb=int(a['kind']),int(b['kind'])
    if 2 in (ka,kb):return 'prime-model' if 0 in (ka,kb) else None
    return {(0,0):'model-model',(0,1):'support-model',(1,0):'support-model',(1,1):'support-support'}.get((ka,kb))

def cross_owner_bbox_mask(rows):
    """Conservative symmetric segment/other-owner XY broadphase.

    Every segment AABB already includes half its full effective line width
    (including arc error). No distance tolerance is subtracted here. If two
    footprints can overlap, each segment box necessarily overlaps the other
    owner's union AABB, so both original rows survive with unchanged indices.
    """
    possible=np.zeros(len(rows),dtype=bool)
    radius=rows['width']/2
    bounds=np.column_stack([np.minimum(rows['x1'],rows['x2'])-radius,
                            np.minimum(rows['y1'],rows['y2'])-radius,
                            np.maximum(rows['x1'],rows['x2'])+radius,
                            np.maximum(rows['y1'],rows['y2'])+radius])
    owner_bounds={}
    for owner in np.unique(rows['owner']):
        selection=bounds[rows['owner']==owner]
        owner_bounds[int(owner)]=[selection[:,0].min(),selection[:,1].min(),selection[:,2].max(),selection[:,3].max()]
    for other,b in owner_bounds.items():
        possible|=((rows['owner']!=other)&(bounds[:,0]<=b[2])&(bounds[:,2]>=b[0])&
                   (bounds[:,1]<=b[3])&(bounds[:,3]>=b[1]))
    return possible


def screen_records(rows,tolerance_mm=.02,max_examples=25,*,current_z=None):
    # Keep the original row indices. NumPy filters only pairs that cannot
    # geometrically meet any other owner's width-expanded XY union box.
    active=cross_owner_bbox_mask(rows)
    lines={int(i):LineString([(rows[i]['x1'],rows[i]['y1']),(rows[i]['x2'],rows[i]['y2'])]) for i in np.flatnonzero(active)}
    groups={}
    for owner in np.unique(rows['owner'][active]):
        indices=np.flatnonzero(active&(rows['owner']==owner))
        groups[int(owner)]={'indices':indices,'tree':STRtree([lines[int(i)] for i in indices]),
                            'maxwidth':float(rows['width'][indices].max())}
    hits=[];counts={}
    for i,line in lines.items():
        a=rows[i]
        if current_z is not None and a['z']!=current_z:continue
        for owner,group in groups.items():
            if owner==int(a['owner']):continue
            radius=(float(a['width'])+group['maxwidth'])/2-tolerance_mm
            if radius<=0:continue
            for local in group['tree'].query(box(*(np.array(line.bounds)+[-radius,-radius,radius,radius]))):
                j=int(group['indices'][int(local)])
                if current_z is None and j<=i:continue
                if current_z is not None and rows[j]['z']==current_z and j<=i:continue
                b=rows[j];kind=candidate_kind(a,b)
                if min(a['z'],b['z'])-max(a['z']-a['height'],b['z']-b['height'])<=1e-6:continue
                if not kind:continue
                limit=(float(a['width'])+float(b['width']))/2-tolerance_mm;distance=line.distance(lines[j])
                if distance>=limit:continue
                counts[kind]=counts.get(kind,0)+1
                if len(hits)<max_examples:hits.append({'z_mm':float(a['z']),'other_z_mm':float(b['z']),'heights_mm':[float(a['height']),float(b['height'])],'type':kind,'owners':[int(a['owner']),int(b['owner'])],'lines':[int(a['line']),int(b['line'])],'centerline_distance_mm':distance,'widths_mm':[float(a['width']),float(b['width'])]})
    return counts,hits

def check(path,max_examples=25,*,z_indices=None):
    started=time.monotonic();path=Path(path);digest=hashlib.sha256();report={'source':str(path.resolve()),'scope':'Planar linear and G17 I/J arc positive-extrusion footprints across different owners with overlapping physical Z intervals [Z-LAYER_HEIGHT,Z]; not full nozzle/dynamic/physical collision certification','passed':False,'tolerance_mm':.02,'conflict_counts':{},'examples':[],'extrusion_segments':0,'z_groups':0,'unsupported_arcs':0,'arc_chord_error_limit_mm':ARC_CHORD_ERROR_MM,'arc_footprint_inflation':'Each arc chord gets twice its conservative geometric error added to LINE_WIDTH'}
    with tempfile.TemporaryDirectory(prefix='figuraforge-gcode-') as temp:
        binary=Path(temp)/'segments.bin'
        single_object_id=None
        sidecar=path.parent/'result.json'
        if path.suffix!='.3mf' and sidecar.is_file():
            sliced=json.loads(sidecar.read_text()).get('sliced_plates',[])
            objects=sliced[0].get('objects',[]) if len(sliced)==1 else []
            if len(objects)==1:
                single_object_id=int(objects[0]['id']);report['single_object_owner_evidence']={'sidecar':str(sidecar.resolve()),'object_id':single_object_id,'name':objects[0].get('name'),'objects':1}

        with ExitStack() as inputs:
            if path.suffix=='.3mf':
                archive=inputs.enter_context(zipfile.ZipFile(path));members=[n for n in archive.namelist() if n.endswith('.gcode')]
                if len(members)!=1:raise ValueError('Expected exactly one embedded G-code')
                stream=inputs.enter_context(archive.open(members[0]));report['embedded_gcode']=members[0]
            else:stream=inputs.enter_context(path.open('rb'))
            def textlines():
                for raw in stream:
                    digest.update(raw)
                    yield raw.decode('utf-8',errors='strict')
            with binary.open('wb') as out:
                for row in parse(textlines(),single_object_id=single_object_id,stats=report):
                    if row[6]<0 and row[7]!=2:raise ValueError(f'Unassigned extrusion at line {row[8]}; require explicit object markers or verified one-object slicer sidecar')
                    out.write(PACK.pack(*row));report['extrusion_segments']+=1
        report['gcode_sha256']=digest.hexdigest()
        if not report['extrusion_segments']:raise ValueError('No labeled extrusions; unsupported input')
        data=np.memmap(binary,dtype=FIELDS,mode='r');order=np.argsort(data['z'],kind='stable');sorted_z=data['z'][order];maxheight=float(data['height'].max())
        owners={}
        for owner in np.unique(data['owner']):
            subset=data[data['owner']==owner];r=float(subset['width'].max())/2
            owners[int(owner)]=[float(min(subset['x1'].min(),subset['x2'].min())-r),float(min(subset['y1'].min(),subset['y2'].min())-r),float(max(subset['x1'].max(),subset['x2'].max())+r),float(max(subset['y1'].max(),subset['y2'].max())+r)]
        report['owner_extrusion_xy_bounds_mm']=owners
        def intersects(a,b):return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]
        overlapping_owners={owner for owner,bounds in owners.items() for other,otherbounds in owners.items() if owner!=other and intersects(bounds,otherbounds)}
        report['globally_overlapping_owner_ids']=sorted(overlapping_owners)
        starts=np.r_[0,np.flatnonzero(np.diff(data['z'][order]))+1,len(data)]
        for z_index,(left,right) in enumerate(zip(starts[:-1],starts[1:]),1):
            report['z_groups']+=1
            if z_indices is not None and not any(abs(z_index-target)<=25 for target in z_indices):continue
            current_z=float(sorted_z[left]);window_left=int(np.searchsorted(sorted_z,current_z-maxheight,side='right'))
            rows=data[order[window_left:right]]
            if z_indices is not None:report.setdefault('selected_z_groups',[]).append({'one_based_z_index':z_index,'z_mm':float(rows['z'][0]),'segments':len(rows)})
            if not overlapping_owners or len(set(rows['owner']))<2:continue
            counts,hits=screen_records(rows,max_examples=max_examples-len(report['examples']),current_z=current_z)
            for key,value in counts.items():report['conflict_counts'][key]=report['conflict_counts'].get(key,0)+value
            report['examples'].extend(hits)
        del data
    report['passed']=not bool(report['conflict_counts']);report['wall_time_seconds']=time.monotonic()-started;return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('sources',nargs='+',type=Path);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--z-index',type=int,action='append',help='One-based sorted extrusion-Z index; screen +/-25 neighbors, not a GUI layer index');args=parser.parse_args();report={'checks':[]}
    for source in args.sources:
        result=check(source,z_indices=args.z_index);report['checks'].append(result);args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['source','passed','extrusion_segments','conflict_counts']}),flush=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
