from copy import deepcopy
import pytest
from figuraforge.services.native_recipe_library import allocate_native_recipes,NativeRecipeCapacityError
from figuraforge.services.mixed_filament import MixedFilamentError


def settings():
    percentages=[85,75,65,55,45,35,25,15];n=11
    return {'enable_mixed_color_sublayer':'1','filament_colour':['#000000','#FFFFFF','#00FF00']+['#888888']*8,
            'default_filament_colour':['#000000']*n,'filament_is_mixed':['0']*3+['1']*8,
            'filament_mixed_components':['']*3+['1,2']*8,
            'filament_mixed_sublayer_ratios':['']*3+[f'{p/100:.2f},{(100-p)/100:.2f}' for p in percentages],
            'filament_mixed_gradient':['0']*n,'filament_mixed_gradient_range':['']*n,
            'filament_mixed_gradient_curve':['']*n,'filament_mixed_gradient_per_part':['0']*n,
            'filament_settings_id':['existing profile']*n,
            'nozzle_temperature':[200,220]*n,'flush_volumes_matrix':list(range(2*n*n)),
            'inherits_group':['inherited']*(n+2),'unknown_nested_schema':{'keep':['unchanged']}}


def test_exact_requested_colors_reuse_virtual_slots_without_changing_physical_profiles():
    source=settings();original=deepcopy(source)
    result=allocate_native_recipes(source,[1,2],[0,100,10,30,50,70,90])
    out=result['settings'];mapping=result['percent_to_slot']
    assert mapping[100]==1 and mapping[0]==2
    assert len({mapping[p] for p in [10,30,50,70,90]})==5
    assert out['filament_mixed_sublayer_ratios'][mapping[50]-1]=='0.50,0.50'
    assert out['filament_colour'][mapping[50]-1]=='#BCBCBC'
    assert out['nozzle_temperature']==source['nozzle_temperature']
    assert out['flush_volumes_matrix']==source['flush_volumes_matrix']
    assert out['inherits_group']==source['inherits_group']
    assert out['filament_settings_id'][:3]==source['filament_settings_id'][:3]
    assert out['filament_colour'][:3]==source['filament_colour'][:3]
    assert source==original
    assert not result['report']['preview_palette_coarsened']


def test_existing_exact_ratios_are_preferred_and_reverse_component_order_supported():
    source=settings();source['filament_mixed_components'][3]='2,1';source['filament_mixed_sublayer_ratios'][3]='0.15,0.85'
    result=allocate_native_recipes(source,[1,2],[85,50])
    assert result['percent_to_slot'][85]==4
    assert result['settings']['filament_mixed_sublayer_ratios'][3]=='0.85,0.15'


def test_nineteen_color_library_blocks_instead_of_coarsening_eight_slot_template():
    source=settings();original=deepcopy(source)
    with pytest.raises(NativeRecipeCapacityError,match='17 verschiedene Mischrezepte'):
        allocate_native_recipes(source,[1,2],[0,*range(10,91,5),100])
    assert source==original


@pytest.mark.parametrize('pair',[[1,1],[1,4],[0,2],[1]])
def test_wrong_physical_pair_rejected(pair):
    with pytest.raises(MixedFilamentError):allocate_native_recipes(settings(),pair,[50])


@pytest.mark.parametrize('ratio',[5,95,-1,101,50.5,float('nan'),True])
def test_invalid_percentages_rejected(ratio):
    with pytest.raises(MixedFilamentError):allocate_native_recipes(settings(),[1,2],[ratio])


def test_other_existing_pair_not_reused():
    source=settings()
    with pytest.raises(NativeRecipeCapacityError,match='0 vorhandene Mischslots'):
        allocate_native_recipes(source,[1,3],[50])


def test_complete_seventeen_slot_native_template_preserves_all_dimensions():
    source=settings();extra=list(range(10,91,10));n=20
    source['filament_is_mixed']+=['1']*9
    source['filament_mixed_components']+=['1,2']*9
    source['filament_mixed_sublayer_ratios']+=[f'{p/100:.2f},{(100-p)/100:.2f}' for p in extra]
    source['filament_mixed_gradient']+=['0']*9
    source['filament_mixed_gradient_per_part']+=['0']*9
    source['filament_mixed_gradient_range']+=['']*9
    source['filament_mixed_gradient_curve']+=['']*9
    source['filament_colour']+=['#888888']*9
    source['default_filament_colour']+=['#888888']*9
    source['filament_settings_id']+=['native generated mixed profile']*9
    source['nozzle_temperature']=[200,220]*n
    source['flush_volumes_matrix']=list(range(2*n*n))
    source['inherits_group']=['native profile']*(n+2)
    requested=[0,*range(10,91,5),100]
    before=deepcopy(source)
    result=allocate_native_recipes(source,[1,2],[{'first_percent':p} for p in requested])
    assert len(result['percent_to_slot'])==19
    assert len(set(result['percent_to_slot'].values()))==19
    assert result['report']['slot_count_after']==20
    assert result['report']['required_mixed_recipe_count']==17
    assert result['settings']['nozzle_temperature']==before['nozzle_temperature']
    assert result['settings']['flush_volumes_matrix']==before['flush_volumes_matrix']
    assert result['settings']['inherits_group']==before['inherits_group']
    assert source==before
