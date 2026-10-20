// Run: node tests/frontend_color_plan_regressions.mjs
// Verify normalization against the real Pydantic contract, without API/cloud calls.
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {dirname,join} from 'node:path';
import {ColorPlanEditor,normalizeColorPlan} from '../frontend/color-plan.js';
const root=dirname(dirname(fileURLToPath(import.meta.url)));
const canonical=value=>JSON.stringify(value,(key,item)=>item&&typeof item==='object'&&!Array.isArray(item)?Object.fromEntries(Object.entries(item).sort(([a],[b])=>a.localeCompare(b))):item);
const base={mesh_hash:'a'.repeat(64),face_count:2,face_regions:[0,1],regions:[{id:0,name:'Body',strategy:'body',color:'#112233'},{id:1,name:'Tail',strategy:'mixed',color:'#445566'}]};
const cases=[base,{...base,regions:[base.regions[0],{...base.regions[1],strategy:'part',color_mode:'mixed',cut_type:'whole',part_group:7}]}];
const expected=JSON.parse(execFileSync(join(root,'.venv/bin/python'),['-c','import json,sys;from figuraforge.models import ColorPlanDocument;print(json.dumps([ColorPlanDocument.model_validate(p).model_dump() for p in json.load(sys.stdin)]))'],{cwd:root,env:{...process.env,PYTHONPATH:join(root,'backend')},input:JSON.stringify(cases),encoding:'utf8'}));
for(let i=0;i<cases.length;i++)assert.equal(canonical(normalizeColorPlan(cases[i])),canonical(expected[i]),'Frontend defaults/migration diverge from the backend');
assert.equal(base.regions[1].strategy,'mixed','Normalization modified its input');
const edited=structuredClone(base);edited.regions[1].name='User edit';assert.notEqual(canonical(normalizeColorPlan(edited)),canonical(normalizeColorPlan(base)),'Real user edits must remain detectable');
const editor=Object.create(ColorPlanEditor.prototype);let stock=[{id:'a',hex:'#112233',material:'PLA',allowed:true,owned:true},{id:'b',hex:'#445566',material:'PLA',allowed:true,owned:true}];
Object.assign(editor,{plan:{...normalizeColorPlan(base),filament_ids:['a','b']},project:{artifacts:{plan:{hash:'plan-hash'}},settings:{owned_filaments_only:true},bambu_template:{sha256:'template-a',info:{config:{layer_height:.2}}}},getFilaments:()=>stock});
const initial=editor.mixedKey();editor.project.bambu_template.sha256='template-b';assert.notEqual(editor.mixedKey(),initial,'New native profiles must invalidate the cache');editor.project.bambu_template.sha256='template-a';
editor.project.bambu_template.info.config.layer_height=.16;assert.notEqual(editor.mixedKey(),initial,'Different profile layer height must invalidate the cache');editor.project.bambu_template.info.config.layer_height=.2;
for(const [field,value] of [['hex','#334455'],['material','PETG'],['allowed',false],['owned',false]]){const before=stock;stock=structuredClone(before);stock[0][field]=value;assert.notEqual(editor.mixedKey(),initial,`${field} inventory change must invalidate the cache`);stock=before;}
stock=[...stock,{id:'unrelated',hex:'#FFFFFF',material:'TPU'}];assert.equal(editor.mixedKey(),initial,'Unrelated inventory changes should not trigger a full recomputation');
console.log('PASS: backend-equivalent legacy/default normalization, real edit detection, native-profile/layer-height cache invalidation and live inventory changes');

const {materialVariants}=await import('../frontend/color-plan.js');
const materialPlan={filament_ids:['a','b'],regions:[{id:0,color_mode:'mixed',color:'#aa4712'},{id:1,color_mode:'solid',color:'#101010',filament_id:'black'}]};
const baseVariant={title:'Originalhelligkeit · Ausgewogen',document:structuredClone(materialPlan)};
baseVariant.document.regions[1].filament_id=null;baseVariant.document.regions[1].color='#202020';
const materialOptions=materialVariants(Array.from({length:9},()=>structuredClone(baseVariant)),materialPlan,[{id:'a',hex:'#F7E6DE'},{id:'b',hex:'#805947'}]);
assert.equal(materialOptions.length,9);
assert.equal(materialOptions[1].document.regions[0].color,'#aa4712');
assert.notEqual(materialOptions[0].document.regions[0].color,materialOptions[2].document.regions[0].color);
for(const variant of materialOptions){assert.equal(variant.document.regions[1].filament_id,'black');assert.equal(variant.document.regions[1].color,'#101010');}
assert.equal(materialPlan.regions[0].color,'#aa4712','Comparisons must not mutate the current saved plan');
assert.equal(baseVariant.document.regions[1].filament_id,null);
assert.equal(materialVariants([baseVariant],materialPlan,[]),null);
console.log('PASS: textured material variants preserve solid spools and vary real basis directions without mutating the plan');
