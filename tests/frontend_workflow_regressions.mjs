import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {Viewer} from '../frontend/viewer.js';
const a={role:'body',center:[-5,0,0]},b={role:'body',center:[5,0,0]};
const state={mode:'explode',meshes:[a,b],center:[0,0,0],radius:10,explode:.5};
assert(Viewer.prototype.transform.call(state,a)[3]<0);
assert(Viewer.prototype.transform.call(state,b)[3]>0);
state.meshes=[a];assert.equal(Viewer.prototype.transform.call(state,a)[3],0);
const source=fs.readFileSync(new URL('../frontend/app.js',import.meta.url),'utf8');
const fn=source.slice(source.indexOf('function schedulePoll()'),source.indexOf('async function renderProject'));
let callbacks=[],attempts=0,rendered=0,notices=[];const status={textContent:''};
const context={project:{id:'a',jobs:[]},busy:false,loading:false,pollTimer:null,pollDisconnected:false,
 setTimeout:fn=>{callbacks.push(fn);return callbacks.length;},clearTimeout:()=>{},
 api:async()=>{if(++attempts===1)throw new Error('offline');return {id:'a',jobs:[]};},
 renderProject:async()=>rendered++,toast:text=>notices.push(text),$:()=>status};
vm.createContext(context);vm.runInContext(fn,context);context.schedulePoll();
await callbacks.shift()();assert.equal(attempts,1);assert.equal(callbacks.length,1);
assert.match(status.textContent,/Verbindung unterbrochen/);
await callbacks.shift()();assert.equal(attempts,2);assert.equal(rendered,1);
assert.equal(callbacks.length,1);assert.equal(context.pollDisconnected,false);
assert.deepEqual(notices,['Verbindung wiederhergestellt.']);
// A late poll response from the previous project must not replace the new one.
context.api=async()=>{context.project={id:'new',jobs:[]};return {id:'old',jobs:[]};};
await callbacks.shift()();assert.equal(context.project.id,'new');assert.equal(rendered,1);
console.log('PASS: structural body explosion, polling reconnect, stale project response ignored');
const {ColorPlanEditor}=await import('../frontend/color-plan.js');
let saved=0;
const editor={ready:Promise.resolve(),plan:{regions:[]},project:{artifacts:{plan:{hash:'h',validated:true}}},dirty:false,onSave:async()=>saved++};
assert.equal(await ColorPlanEditor.prototype.save.call(editor),false);
assert.equal(saved,0,'Revisiting an unchanged validated plan must not invalidate constructed parts');
editor.dirty=true;assert.equal(await ColorPlanEditor.prototype.save.call(editor),true);assert.equal(saved,1);
const navfn=source.slice(source.indexOf('async function navigateStage('),source.indexOf('async function loadProject('));
const navigation={stage:'plan',planEditor:{save:async()=>{throw new Error('Invalid draft');}},renderInspector:()=>{},refreshPreview:async()=>{}};
vm.createContext(navigation);vm.runInContext(navfn,navigation);
await assert.rejects(navigation.navigateStage('segments'),/Invalid draft/);
assert.equal(navigation.stage,'plan','Invalid draft must remain visible rather than constructing an older saved plan');
await navigation.navigateStage('mesh');assert.equal(navigation.stage,'mesh','Back navigation must preserve an unfinished draft');
console.log('PASS: unchanged plan preserves construction, forward navigation validates edits, backward navigation preserves draft');

// A response captured before job submission must not replace the just-started
// job or send the user back to the previous operation's screen.
context.project={id:'same',revision:3,jobs:[{id:'new-export',status:'queued'}]};
context.api=async()=>({id:'same',revision:3,jobs:[{id:'old-segment',status:'succeeded'}]});
const beforeRender=rendered;await callbacks.shift()();
assert.equal(context.project.jobs[0].id,'new-export');assert.equal(rendered,beforeRender);
context.project={id:'same',revision:5,jobs:[]};
context.api=async()=>({id:'same',revision:4,jobs:[]});await callbacks.shift()();
assert.equal(context.project.revision,5);assert.equal(rendered,beforeRender);
// An already in-flight poll must not render an old header over the loading screen.
context.loading=true;context.project={id:'same',revision:5,jobs:[]};
context.api=async()=>({id:'same',revision:6,jobs:[]});await callbacks.shift()();
assert.equal(context.project.revision,5);assert.equal(rendered,beforeRender);
context.loading=false;
console.log('PASS: polling cannot discard a just-started job or a newer project revision');

// Loading is a real async state, including the gap after project GET while the
// project list still loads. A stale empty-screen button must never mutate Pip.
const html=fs.readFileSync(new URL('../frontend/index.html',import.meta.url),'utf8');
assert.match(html,/<main[^>]*id="workspace"[^>]*\binert\b[^>]*aria-busy="true"/);
assert.match(html,/<button[^>]*id="demo-load"[^>]*\bdisabled\b/);
assert.match(html,/<div id="viewer-empty"><p role="status">Projekt und Vorschau werden geladen/);
const loadingFns=source.slice(source.indexOf('function setProjectLoading('),source.indexOf('function schedulePoll()'))+'\n'+source.split('\n').find(l=>l.startsWith('async function loadDemo('));
const nodes=new Map();const node=id=>{if(!nodes.has(id))nodes.set(id,{hidden:false,textContent:'',innerHTML:'',setAttribute(k,v){this[k]=v}});return nodes.get(id)};
let pendingGets=new Map(),releaseProjects,loadingRenders=0;const demoRequests=[];
const loadContext={project:null,projectLoadTicket:0,previewTicket:0,loading:true,busy:false,pollTimer:null,revision:0,previewKey:'',stage:'pose',
 clearTimeout(){},localStorage:{setItem(){}},$:node,toast(){},schedulePoll(){},
 refreshProjects:()=>new Promise(resolve=>{releaseProjects=resolve}),renderProject:async()=>loadingRenders++,
 api:async(path,options)=>{if(options?.method==='POST'){demoRequests.push(path);return {id:'demo-job',status:'queued'}}return new Promise(resolve=>pendingGets.set(path,resolve))}};
vm.createContext(loadContext);vm.runInContext(loadingFns,loadContext);
await loadContext.loadDemo();assert.deepEqual(demoRequests,[],'Startup placeholder cannot create a demo/new project');
const loadPip=loadContext.loadProject('pip');assert.equal(loadContext.loading,true);assert.equal(node('#workspace').inert,true);
pendingGets.get('/projects/pip')({id:'pip',artifacts:{mesh:{}},jobs:[]});await new Promise(resolve=>setImmediate(resolve));
assert.equal(loadContext.project.id,'pip');assert.equal(loadingRenders,0);assert.match(node('#project-title').textContent,/geladen/);
await loadContext.loadDemo();assert.deepEqual(demoRequests,[],'No POST /pip/demo during the GET-to-render window');
releaseProjects();await loadPip;assert.equal(loadContext.loading,false);assert.equal(node('#workspace').inert,false);
await loadContext.loadDemo();assert.deepEqual(demoRequests,['/projects/pip/demo'],'Intentional demo works normally after the project finishes loading');
// A late project load cannot replace a more recent explicit selection.
loadContext.refreshProjects=async()=>{};
const loadOld=loadContext.loadProject('old');const loadNew=loadContext.loadProject('new');
pendingGets.get('/projects/new')({id:'new',artifacts:{},jobs:[]});await loadNew;
pendingGets.get('/projects/old')({id:'old',artifacts:{},jobs:[]});await loadOld;
assert.equal(loadContext.project.id,'new');assert.equal(loadContext.loading,false);
console.log('PASS: initial inert loading screen, demo blocked throughout async project load, intentional demo preserved, stale project load ignored');

// Buddy tiling preserves keys in geometry/report but intentionally drops many
// per-piece annotations. Count each original interface once, never 15 annotations.
const connectionFns=source.slice(source.indexOf('function displayPartName('),source.indexOf('function approvalUI()'));
const reportContext={project:{artifacts:{plan:{construction_preset:'buddy-anatomical-v1'}}},esc:x=>String(x??'')};
vm.createContext(reportContext);vm.runInContext(connectionFns,reportContext);
const keys=n=>Array.from({length:n},()=>({shape:'keyed'}));
const anatomy=[['nose',2],['left-eye',0],['right-eye',0],['rolled-map',2],['left-ear',3],['right-ear',3]].map(([id,n])=>({part_id:id,parts:[{id,connectors:keys(n)}]}));anatomy.push({part_id:'tail',pins:keys(2)});
const collar=[['collar-body',3],['collar-left',2],['collar-right',0],['collar-neck-0',3],['collar-neck-1',0],['collar-head',0]].map(([id,n])=>({id,connectors:keys(n)}));
const splits=Array.from({length:24},(_,i)=>({id:'joint-'+i,parent:i?'body-'+i:'tail',children:i?['body-'+i+'-a','body-'+i+'-b']:['tail-a','tail-b'],pins:keys(2)}));
const connectionReport={construction_preset:'buddy-anatomical-v1',anatomical_attempts:anatomy,collar_assembly:{parts:collar},structural_splits:splits};
const buddyParts=['left-eye','right-eye','collar-neck-1','tail-a','tail-b','unexpected'].map(id=>({id,name:id,role:'color-body',connectors:[],dimensions_mm:[1,2,3],color:'#FFFFFF'}));
const buddySegments={summary:{pins:15},parts:buddyParts,geometry_report:{construction:connectionReport}};
const calculated=reportContext.buddyAssemblyView(buddySegments);
assert.equal(calculated.total_keys,68);assert.equal(calculated.total_keyed_interfaces,32);
assert.match(reportContext.assemblyCountLabel(buddySegments),/68 SCHLÜSSEL \/ 32 ANSCHLÜSSE/);
assert.match(reportContext.partRowHTML(buddyParts[3],buddySegments),/Strukturschlüssel/);
assert.doesNotMatch(reportContext.partRowHTML(buddyParts[3],buddySegments),/0 Verbinder/);
assert.equal(reportContext.partConnectionDisplay(buddyParts[0],buddySegments).kind,'Klebeteil');
assert.equal(reportContext.partConnectionDisplay(buddyParts[2],buddySegments).kind,'Montageteil');
const retention=reportContext.retentionNotice(buddySegments);assert.match(retention,/unexpected/);assert.doesNotMatch(retention,/left-eye|right-eye|tail-a|tail-b|collar-neck-1/);
assert.match(reportContext.displayPartName({id:'left-ear',name:'English'}),/linkes Ohr/);
assert.match(reportContext.displayPartName({id:'collar-body-a-b',name:'English'}),/Unterkörper · Kachel A\/B/);
// New backend canonical metadata takes precedence; the UI cannot hardcode 68.
connectionReport.assembly_connections={...calculated,total_keys:70,total_keyed_interfaces:33};
assert.match(reportContext.assemblyCountLabel(buddySegments),/70 SCHLÜSSEL \/ 33 ANSCHLÜSSE/);
reportContext.project.artifacts.plan.construction_preset='other';
assert.equal(reportContext.buddyAssemblyView(buddySegments),null);
assert.match(reportContext.retentionNotice(buddySegments),/left-eye/,'Unrelated source/preset cannot suppress unresolved retention warnings');
console.log('PASS: Buddy report/canonical interface counts, tiled assembly hints, explicit glue/capture exceptions, unknown loose parts still warn, localized labels');

// Buddy's source-bound limits must be reviewable form values before starting
// geometry, not a read-only stale 0.2 clearance or an implicit database write.
const presetFn=source.slice(source.indexOf('function showPresetControls('),source.indexOf('async function saveSettings('));
for(const values of [{pin_clearance_mm:.2,plate_margin_mm:8,part_gap_mm:5,colors_per_plate:1},{pin_clearance_mm:.05,plate_margin_mm:10,part_gap_mm:20,colors_per_plate:2},{pin_clearance_mm:.05,plate_margin_mm:15,part_gap_mm:25,colors_per_plate:2}]){
 const inputs=Object.fromEntries(Object.entries(values).map(([key,value])=>[key,{value:String(value),closest:()=>({setAttribute(){}})}]));
 const volume={value:'300, 320, 325'},notice={insertAdjacentHTML(where,text){this.html=text}},persisted={...values,build_volume_mm:[300,320,325]};
 const before=JSON.stringify(persisted);const presetContext={stage:'segments',project:{settings:persisted,artifacts:{plan:{construction_preset:'buddy-anatomical-v1'}}},document:{querySelector(selector){return inputs[selector.match(/data-setting="([^"]+)"/)?.[1]]||null}},$:selector=>selector==='#volume-input'?volume:selector==='#inspector-body'?notice:null,api:()=>{throw Error('Rendering must never write settings')}};
 vm.createContext(presetContext);vm.runInContext(presetFn,presetContext);presetContext.showPresetControls();
 assert.equal(inputs.pin_clearance_mm.value,'0.05');assert.equal(inputs.pin_clearance_mm.readOnly,true);
 assert.equal(inputs.plate_margin_mm.value,String(Math.max(10,values.plate_margin_mm)));assert.equal(inputs.plate_margin_mm.min,'10');
 assert.equal(inputs.part_gap_mm.value,String(Math.max(20,values.part_gap_mm)));assert.equal(inputs.part_gap_mm.min,'20');
 assert.equal(inputs.colors_per_plate.value,'2');assert.equal(volume.value,'300, 320, 320');
 assert.match(notice.html,/erst beim nächsten Bau gespeichert/);assert.equal(JSON.stringify(persisted),before,'Only DOM defaults change; saved project remains untouched');
}
console.log('PASS: Buddy defaults are reviewable form values, fixed clearance and packing minima apply without API writes, valid larger margins remain');

// Old un-applied paid advice is history, not a reviewable current proposal.
// Rendering it must never start another paid call or expose Apply controls.
const adviceFn=source.slice(source.indexOf('function adviceReview('),source.indexOf('function editedAdvice('));
const adviceLine=source.split('\n').find(line=>line.trim().startsWith('const adviceHTML='));
const adviceContext={esc:x=>String(x??''),stage:'segments',busy:false,s:{},adviceExamples:{segments:''},adviceDraft:()=>'',warnBlock:()=>'',api:()=>{throw Error('Rendering must not call providers')}};
vm.createContext(adviceContext);vm.runInContext(adviceFn,adviceContext);
const renderAdvice=suggestion=>{adviceContext.suggestion=suggestion;vm.runInContext(adviceLine.replace('const adviceHTML=','globalThis.renderedAdvice='),adviceContext);return adviceContext.renderedAdvice};
const staleHTML=renderAdvice({stale:true,applied:false,summary:'Earlier summary',changes:[{key:'obsolete',after:123}]});
assert.match(staleHTML,/früherer Vorschlag/);assert.match(staleHTML,/Eingaben geändert; dieser Vorschlag gehört zu einem früheren Stand/);assert.match(staleHTML,/Earlier summary/);
assert.doesNotMatch(staleHTML,/<details class="advice-preparation" open/);assert.doesNotMatch(staleHTML,/id="apply-suggestion"|data-advice-change|data-advice-region/);
const currentHTML=renderAdvice({stale:false,applied:false,summary:'Current',changes:[]});
assert.match(currentHTML,/<details class="advice-preparation" open/);assert.match(currentHTML,/id="apply-suggestion"/);
const appliedHTML=renderAdvice({stale:true,applied:true,summary:'Applied',changes:[]});
assert.match(appliedHTML,/Vorschlag übernommen/);assert.doesNotMatch(appliedHTML,/früherer Vorschlag|id="apply-suggestion"/);
console.log('PASS: stale advice is collapsed read-only history, current advice remains reviewable, applied advice unchanged, no automatic paid call');

// Imported Bambu print editions show explicit immutable downloads, no AI action.
const archiveFns=source.slice(source.indexOf('function savedPrintsHTML('),source.indexOf('function renderInspector('));
const archived={esc:s=>String(s).replaceAll('<','&lt;').replaceAll('>','&gt;'),url:p=>'/project/files/'+p};
vm.createContext(archived);vm.runInContext(archiveFns,archived);
const archiveHTML=archived.savedPrintsHTML({note:'Nur Körper gedruckt',files:[{label:'Mochi 320 mm',path:'editions/mochi.3mf',primary:true,note:'Zwei Düsen'}]});
assert.match(archiveHTML,/editions\/mochi\.3mf/);assert.match(archiveHTML,/Nur Körper gedruckt/);assert.doesNotMatch(archiveHTML,/data-operation|suggest-settings/);
assert(source.includes("stage=a.saved_prints||a.export?'export'"));
console.log('PASS: saved Bambu editions open at print package with download labels and no generation controls');
