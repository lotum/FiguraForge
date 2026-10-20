"""Compare actual native XML meshes, per-triangle paint and complete settings."""
from pathlib import Path
import argparse,json,zipfile,hashlib
from xml.etree import ElementTree as E
import numpy as np
NS='{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
PS='{http://schemas.microsoft.com/3dmanufacturing/production/2015/06}'

def matrix(raw):
    out=np.eye(4)
    if raw:out[:3,:]=np.asarray(list(map(float,raw.split()))).reshape(4,3).T
    return out

def records(path):
    with zipfile.ZipFile(path) as z:
        roots={};result={}
        def root(name):
            if name not in roots:roots[name]=E.fromstring(z.read(name))
            return roots[name]
        metadata=E.fromstring(z.read('Metadata/model_settings.config'))
        names={o.get('id'):next((m.get('value') for m in o.findall('metadata') if m.get('key')=='name'),o.get('id')) for o in metadata.findall('object')}
        def walk(name,ident,tf):
            obj=next(o for o in root(name).findall(NS+'resources/'+NS+'object') if o.get('id')==ident)
            mesh=obj.find(NS+'mesh')
            if mesh is not None:
                vertices=np.asarray([[float(v.get(k)) for k in ('x','y','z')] for v in mesh.find(NS+'vertices')])
                faces=np.asarray([[int(t.get(k)) for k in ('v1','v2','v3')] for t in mesh.find(NS+'triangles')])
                paint=[t.get('paint_color') for t in mesh.find(NS+'triangles')]
                return [(vertices@tf[:3,:3].T+tf[:3,3],faces,paint)]
            return [r for c in obj.findall(NS+'components/'+NS+'component') for r in walk(c.get(PS+'path',name).lstrip('/'),c.get('objectid'),tf@matrix(c.get('transform')))]
        for item in root('3D/3dmodel.model').findall(NS+'build/'+NS+'item'):
            result[names[item.get('objectid')]]=walk('3D/3dmodel.model',item.get('objectid'),matrix(item.get('transform')))
        return result,json.loads(z.read('Metadata/project_settings.config'))

def compare(a,b):
    left,lc=records(a);right,rc=records(b);parts={}
    if set(left)!=set(right):raise ValueError('Native object identities differ')
    for name,items in left.items():
        other=right[name]
        if len(items)!=len(other):raise ValueError('Native component counts differ')
        errors=[];triangles=0
        for (v,f,p),(w,g,q) in zip(items,other):
            if v.shape!=w.shape or not np.array_equal(f,g) or p!=q:raise ValueError('Native triangle geometry or paint changed: '+name)
            error=float(np.max(abs(v-w)));errors.append(error);triangles+=len(f)
            if error>1e-5:raise ValueError('Native world position changed: '+name)
        parts[name]={'triangles':triangles,'paint_identical':True,'maximum_world_vertex_error_mm':max(errors)}
    if lc!=rc:raise ValueError('Native settings changed')
    return {'reference_sha256':hashlib.sha256(Path(a).read_bytes()).hexdigest(),
            'actual_sha256':hashlib.sha256(Path(b).read_bytes()).hexdigest(),
            'parts':parts,'complete_project_settings_identical':True,'passed':True}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('reference',type=Path);parser.add_argument('actual',type=Path);parser.add_argument('--report',required=True,type=Path)
    args=parser.parse_args();result=compare(args.reference,args.actual);args.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
