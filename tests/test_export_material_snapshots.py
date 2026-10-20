"""Approved mixed basis spools cannot silently change during native export."""
from copy import deepcopy
import pytest
from figuraforge.db import Conflict
from figuraforge.services.jobs import color_export_inventory


def state():
    green={'id':'green','name':'Green','hex':'#C2E189','material':'PLA','owned':True,'allowed':True}
    beige={'id':'beige','name':'Beige','hex':'#F7E6DE','material':'PLA','owned':True,'allowed':True}
    colors={'filaments':{'body':deepcopy(green)},'planned_materials':{'body':{
        'filament_ids':['green','beige'],'filaments':deepcopy([green,beige])}}}
    return colors,[green,beige]


def test_unchanged_export_freezes_checked_inventory_without_aliasing_approved_snapshots():
    colors,inventory=state();before=deepcopy(colors)
    checked=color_export_inventory(colors,inventory)
    inventory[1]['hex']='#272729'
    assert checked[1]['hex']=='#F7E6DE' and colors==before


@pytest.mark.parametrize('field,value',[('hex','#272729'),('material','PETG'),('allowed',False),('owned',False)])
def test_nonrepresentative_mixed_basis_changes_cannot_pass_unchanged_color_approval(field,value):
    colors,inventory=state();inventory[1][field]=value
    with pytest.raises(Conflict,match='Filamente neu zuordnen'):
        color_export_inventory(colors,inventory)


def test_deleted_basis_and_incomplete_approved_snapshot_block_native_export():
    colors,inventory=state()
    with pytest.raises(Conflict,match='geändert oder entfernt'):color_export_inventory(colors,inventory[:1])
    colors['planned_materials']['body']['filaments'].pop()
    with pytest.raises(Conflict,match='unvollständig'):color_export_inventory(colors,inventory)


def test_unrelated_inventory_changes_do_not_invalidate_approved_used_spools():
    colors,inventory=state();inventory.append({'id':'unused','hex':'#123456'})
    assert color_export_inventory(colors,inventory)==inventory


def test_conflicting_snapshots_for_same_spool_cannot_be_exported():
    colors,inventory=state();colors['planned_materials']['body']['filaments'][0]['hex']='#000000'
    with pytest.raises(Conflict,match='widersprechen'):color_export_inventory(colors,inventory)
