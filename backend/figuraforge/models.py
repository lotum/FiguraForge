from __future__ import annotations
from typing import Literal
from pydantic import BaseModel,Field,ConfigDict,field_validator,model_validator


class Settings(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    height_mm:float=Field(180,ge=20,le=2000)
    up_axis:Literal['X','Y','Z']='Y'
    model_type:Literal['figurine','bust','relief','custom']='figurine'
    prompt:str=Field('',max_length=10000)
    identity_notes:str=Field('',max_length=10000)
    image_provider:Literal['openai','gemini','gemini-legacy']='openai'
    image_model:str=Field('gpt-image-2.5-sunburst',max_length=120)
    image_quality:Literal['low','medium','high','max']='max'
    image_size:str=Field('1024x1536',max_length=30)
    image_views:list[Literal['front','left','back','right']]=Field(default_factory=lambda:['front','left','back','right'],min_length=1,max_length=4)
    mesh_provider:Literal['meshy','tripo','local']='meshy'
    mesh_model:str=Field('latest',max_length=120)
    mesh_target_faces:int=Field(150000,ge=1000,le=300000)
    precision_mode:Literal['auto','fixed']='auto'
    review_model:str=Field('',max_length=120)
    review_effort:Literal['low','medium','high','xhigh']='high'
    auto_image_retries:int=Field(0,ge=0,le=2)
    budget_eur:float|None=Field(None,ge=0,le=10000)
    image_call_estimate_eur:float=Field(2,ge=0,le=100)
    mesh_call_estimate_eur:float=Field(10,ge=0,le=500)
    review_call_estimate_eur:float=Field(.5,ge=0,le=100)
    advice_model:str=Field('gpt-6-astra',max_length=120)
    construction_strategy:Literal['inlays','surface_parts']='inlays'
    palette_size:int=Field(3,ge=1,le=12)
    palette:list[str]=Field(default_factory=list,max_length=16)
    base_color:int=Field(0,ge=0,le=15)
    boundary_tolerance_mm:float=Field(.65,ge=.15,le=5)
    coarse_sampling_mm:float=Field(4,ge=.5,le=15)
    max_refined_faces:int=Field(350000,ge=10000,le=1000000)
    inlay_depth_mm:float=Field(3.2,ge=.8,le=40)
    seam_mm:float=Field(.15,ge=0,le=.8)
    pin_radius_mm:float=Field(1.5,ge=.8,le=12)
    pin_length_mm:float=Field(4,ge=1,le=30)
    pin_clearance_mm:float=Field(.2,ge=.05,le=.6)
    connector_shape:Literal['round','keyed']='round'
    min_region_area_mm2:float=Field(3,ge=0,le=300)
    adaptive_small_pins:bool=True
    validate_paths:bool=True
    printer_id:Literal['h2d-dual','h2d-single','custom']='h2d-dual'
    build_volume_mm:list[float]=Field(default_factory=lambda:[300,320,320],min_length=3,max_length=3)
    plate_margin_mm:float=Field(6,ge=2,le=40)
    part_gap_mm:float=Field(5,ge=1,le=30)
    colors_per_plate:int=Field(1,ge=1,le=2)
    auto_tile:bool=True
    owned_filaments_only:bool=False
    preferred_brands:list[str]=Field(default_factory=lambda:['Elegoo','Bambu Lab'],max_length=30)
    direction_overrides:dict[str,list[float]]=Field(default_factory=dict)

    @field_validator('palette')
    @classmethod
    def colors(cls,values):
        import re
        if any(not re.fullmatch('#[0-9a-fA-F]{6}',v) for v in values): raise ValueError('Palette colors must be #RRGGBB')
        return [v.upper() for v in values]
    @field_validator('build_volume_mm')
    @classmethod
    def volume(cls,value):
        if any(v<40 or v>2000 for v in value): raise ValueError('Build dimensions must be 40..2000 mm')
        return value
    @field_validator('image_views')
    @classmethod
    def views(cls,value):
        if len(set(value))!=len(value) or value[0]!='front': raise ValueError('Views must be unique and begin with front')
        return value
    @field_validator('direction_overrides')
    @classmethod
    def directions(cls,value):
        import math
        for k,v in value.items():
            if not k.isdigit() or len(v)!=3 or not all(math.isfinite(x) for x in v) or sum(x*x for x in v)<1e-8:
                raise ValueError('Direction overrides require a pocket index and a nonzero XYZ vector')
        return value


class NewProject(BaseModel):
    title:str=Field('Neue Figur',min_length=1,max_length=120)
    settings:Settings=Field(default_factory=Settings)


class JobRequest(BaseModel):
    operation:Literal['pose','reconstruct','inspect','segment','export','review_pose','rig','advise','plan','preview']
    advice_stage:Literal['pose','mesh','segments','colors','export','plan']|None=None
    advice_view_png:str|None=Field(None,max_length=2_000_000)
    advice_prompt:str=Field('',max_length=6000)
    advice_plan_document:ColorPlanDocument|None=None
    confirm_cloud_upload:bool=False
    budget_override:bool=False


class ApprovalRequest(BaseModel):
    stage:Literal['pose','mesh','colors']
    artifact_hash:str=Field(min_length=64,max_length=64)
    warnings_acknowledged:bool=False


class Filament(BaseModel):
    model_config=ConfigDict(extra='allow',allow_inf_nan=False)
    id:str=Field(min_length=1,max_length=120)
    brand:str=Field(max_length=120)
    name:str=Field(max_length=200)
    material:str=Field('PLA',max_length=30)
    hex:str=Field(pattern='^#[0-9a-fA-F]{6}$')
    owned:bool=False
    allowed:bool=True
    measured:bool=False
    finish:str='unknown'
    lab_d65:list[float]|None=None
    @field_validator('lab_d65')
    @classmethod
    def lab(cls,v):
        import math
        if v is not None and (len(v)!=3 or not all(math.isfinite(n) for n in v) or not 0<=v[0]<=100):
            raise ValueError('Expected finite Lab D65 values, L=0..100')
        return v


class ColorAssignment(BaseModel):
    assignments:dict[str,str]=Field(default_factory=dict)


class SecretRequest(BaseModel):
    provider:Literal['openai','gemini','meshy','tripo','local']
    key:str=Field(min_length=8,max_length=1000)


class CalibrationRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    shape:Literal['round','keyed']='round'
    radius_mm:float=Field(1.5,ge=.8,le=12)
    length_mm:float=Field(4,ge=1,le=30)


class ColorRegion(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    id:int=Field(ge=0,le=10000)
    name:str=Field(min_length=1,max_length=80)
    strategy:Literal['body','part']='body'
    color_mode:Literal['solid','mixed']='solid'

    @model_validator(mode='before')
    @classmethod
    def migrate_legacy_mixed(cls,value):
        if isinstance(value,dict) and value.get('strategy')=='mixed':
            value={**value,'strategy':'body','color_mode':'mixed'}
        return value
    color:str=Field(pattern='^#[0-9a-fA-F]{6}$')
    part_group:int=Field(0,ge=0,le=10000)
    cut_type:Literal['inlay','whole']='inlay'
    filament_id:str|None=Field(None,max_length=120)
    reason:str=Field('',max_length=300)
    face_count:int=Field(0,ge=0,le=1_000_000)
    area_mm2:float=Field(0,ge=0)


class ColorPlanDocument(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    version:Literal[1]=1
    mesh_hash:str=Field(min_length=64,max_length=64)
    face_count:int=Field(ge=1,le=1_000_000)
    face_regions:list[int]=Field(min_length=1,max_length=1_000_000)
    regions:list[ColorRegion]=Field(min_length=1,max_length=256)
    nozzle_count:int=Field(2,ge=1,le=4)
    filament_ids:list[str]=Field(default_factory=list,max_length=2)
    ratio_step_percent:Literal[5,10,20]=5
    construction_preset:Literal['mochi-anatomical-v1','mochi-anatomical-detail-v2','pip-anatomical-v1','buddy-anatomical-v1']|None=None
    note:str=Field('',max_length=500)


class ColorPlanUpdate(BaseModel):
    expected_hash:str=Field(min_length=64,max_length=64)
    document:ColorPlanDocument


class AdviceSettingEdit(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    key:str
    after:object


class AdviceRegionEdit(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    id:int=Field(ge=0,le=10000)
    strategy:Literal['body','part']
    color_mode:Literal['solid','mixed']='solid'

    @model_validator(mode='before')
    @classmethod
    def migrate_legacy_mixed(cls,value):
        if isinstance(value,dict) and value.get('strategy')=='mixed':
            value={**value,'strategy':'body','color_mode':'mixed'}
        return value
    filament_id:str|None=Field(max_length=120)
    part_group:int=Field(ge=0,le=10000)
    cut_type:Literal['inlay','whole']
    reason:str=Field('',max_length=1000)


class AdviceAssignmentEdit(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    part_id:str=Field(min_length=1,max_length=120)
    filament_id:str=Field(min_length=1,max_length=120)
    reason:str=Field('',max_length=1000)


class AdviceApplyRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    changes:list[AdviceSettingEdit]|None=Field(None,max_length=50)
    region_changes:list[AdviceRegionEdit]|None=Field(None,max_length=256)
    assignments:list[AdviceAssignmentEdit]|None=Field(None,max_length=10000)
    filament_ids:list[str]|None=Field(None,max_length=2)


JobRequest.model_rebuild()


class DetailMeshAdoptRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    expected_revision:int=Field(ge=0)
    expected_mesh_hash:str=Field(min_length=64,max_length=64)
    expected_plan_hash:str=Field(min_length=64,max_length=64)
