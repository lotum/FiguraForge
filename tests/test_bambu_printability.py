"""The Bambu reader uses atoi for printable; XML's true spelling becomes zero."""
import zipfile
from xml.etree import ElementTree as ET
import pytest
import trimesh
from figuraforge.geometry.types import Part,GeometryError
from figuraforge.services.export import write_3mf,validate_3mf,tag


def test_core_export_uses_bambu_readable_numeric_true_for_every_instance(tmp_path):
    parts=[Part(str(i),'piece',trimesh.creation.box(),'#CC7722') for i in range(2)]
    path=tmp_path/'plate.3mf';result=write_3mf(parts,path)
    with zipfile.ZipFile(path) as archive:
        model=ET.fromstring(archive.read('3D/3dmodel.model'))
    items=model.find(tag('build')).findall(tag('item'))
    assert len(items)==2 and all(item.get('printable')=='1' for item in items)
    assert result['bambu_printable_items'] is True


@pytest.mark.parametrize('flag',['true','0','false'])
def test_geometry_roundtrip_alone_cannot_accept_an_unsliceable_build_flag(tmp_path,flag):
    path=tmp_path/'good.3mf';write_3mf([Part('one','piece',trimesh.creation.box(),'#CC7722')],path)
    broken=tmp_path/'broken.3mf'
    with zipfile.ZipFile(path) as source,zipfile.ZipFile(broken,'w') as target:
        for info in source.infolist():
            raw=source.read(info.filename)
            if info.filename=='3D/3dmodel.model':raw=raw.replace(b'printable="1"',f'printable="{flag}"'.encode())
            target.writestr(info,raw)
    with pytest.raises(GeometryError,match='numeric printable'):
        validate_3mf(broken)
