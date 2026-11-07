import {chromium} from 'playwright';
import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import net from 'node:net';import {spawn} from 'node:child_process';import assert from 'node:assert/strict';
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'room-samples-'));
const registry=JSON.parse(fs.readFileSync('examples/samples.json'));
for(const item of registry.samples)fs.copyFileSync('examples/'+item.scene,path.join(tmp,item.scene));
const manifest=path.join(tmp,'samples.json');fs.writeFileSync(manifest,JSON.stringify(registry));
const listener=net.createServer();await new Promise(r=>listener.listen(0,'127.0.0.1',r));const port=listener.address().port;await new Promise(r=>listener.close(r));
const server=spawn('python3',['skills/room-studio/scripts/room.py','serve',path.join(tmp,'japanese-three-gardens.scene.json'),'--samples',manifest,'--port',String(port)]);
await new Promise((resolve,reject)=>{server.stdout.once('data',resolve);server.once('error',reject);server.once('exit',c=>reject(Error('server exit '+c)))});
const browser=await chromium.launch({...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{}),headless:true});
const page=await browser.newPage({viewport:{width:1600,height:1080}}),errors=[],checks=[];
// Software WebGL can block input while compiling a newly lit 3,049-part view.
// Keep real clicks and every state/geometry assertion, but bound CI actions at 90s.
if(process.env.CI)page.setDefaultTimeout(90000);
page.on('pageerror',e=>errors.push(e.message));const url=`http://127.0.0.1:${port}`;fs.mkdirSync('docs/qa/samples',{recursive:true});
const snapshot=id=>JSON.parse(fs.readFileSync(path.join(tmp,registry.samples.find(s=>s.id===id).scene)));
async function loaded(id){await page.waitForFunction(id=>document.querySelector('#sampleSelect').value===id&&window.roomStudio?.scene.name.includes(id==='japanese'?'三庭':'曼哈顿')&&!document.querySelector('#sampleSelect').disabled,id)}
async function change(selector,predicate){await page.locator(selector).click();await page.waitForFunction(predicate)}
try{
 assert.equal((await fetch(url+'/api/scene?sample=../../etc/passwd')).status,400);
 const unknown=await fetch(url+'/api/undo?sample=unknown',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});assert.equal(unknown.status,400);checks.push('unknown IDs and filesystem paths rejected');
 await page.goto(url);await loaded('japanese');
 // CPU-only CI runners verify real WebGL/state with a smaller render budget.
 // Local captures retain full resolution and shadows.
 if(process.env.CI)await page.evaluate(()=>{const v=window.roomStudio;v.renderer.shadowMap.enabled=false;v.renderer.setPixelRatio(.25);v.renderer.render(v.world,v.camera)});
assert.equal(await page.locator('[data-room]').count(),16);assert.equal(await page.locator('#sampleSelect option').count(),2);
 assert.equal(await page.locator('#gardenChoices').isVisible(),true);checks.push('Japanese default with 15 room views and three garden shortcuts');
 await page.waitForTimeout(700);await page.locator('#stage').screenshot({path:'docs/qa/samples/japanese-overview.png'});
 for(const id of ['engawa','zashiki','bedroom','front_garden','courtyard','main_garden']){console.time('navigate '+id);await page.locator(`[data-room="${id}"]`).click();await page.waitForFunction(id=>window.roomStudio.room===id,id);console.timeEnd('navigate '+id)}
 await page.locator('[data-room="engawa"]').click();await page.waitForTimeout(700);await page.locator('#stage').screenshot({path:'docs/qa/samples/japanese-engawa.png'});
 assert(await page.locator('#curtain').isEnabled());const target=await page.locator('#curtain').getAttribute('data-target'),manhattanBefore=JSON.stringify(snapshot('manhattan'));
 const positionsBefore=await page.evaluate(target=>window.roomStudio.parts.filter(p=>p.entity===target).map(p=>p.position),target);
 await page.locator('#curtain').fill('25');await page.locator('#curtain').dispatchEvent('change');await page.waitForFunction(target=>window.roomStudio.scene.entities[target].params.openness===.25,target);
 const positionsAfter=await page.evaluate(target=>window.roomStudio.parts.filter(p=>p.entity===target).map(p=>p.position),target);assert.notDeepEqual(positionsBefore,positionsAfter);assert.equal(JSON.stringify(snapshot('manhattan')),manhattanBefore);checks.push('shoji geometry changes only the Japanese file');
 await change('#undo',()=>window.roomStudio.scene.redo.length>0);await change('[data-period="night"]',()=>window.roomStudio.scene.period==='night');
 await page.locator('#sampleSelect').selectOption('manhattan');await loaded('manhattan');assert.equal(await page.locator('[data-room]').count(),20);assert.equal(await page.locator('#planLabels > *').count(),19);assert.equal(await page.locator('#environments').isVisible(),true);assert.equal(await page.locator('#roofControl').isVisible(),false);assert.equal(await page.locator('#undo').isEnabled(),false);
 await page.locator('[data-room="living"]').click();await page.waitForTimeout(650);await page.locator('#stage').screenshot({path:'docs/qa/samples/manhattan-living.png'});
 const japaneseBefore=JSON.stringify(snapshot('japanese'));
 await page.locator('#curtain').fill('20');await page.locator('#curtain').dispatchEvent('change');await page.waitForFunction(()=>window.roomStudio.scene.entities['living.sheer'].params.openness===.2);assert.equal(JSON.stringify(snapshot('japanese')),japaneseBefore);checks.push('Manhattan curtains retained; editing/history isolated across samples');
 await page.locator('#sampleSelect').selectOption('japanese');await loaded('japanese');assert.equal(await page.locator('#planLabels > *').count(),15);assert.equal(await page.evaluate(()=>window.roomStudio.scene.period),'night');
 await page.reload();await loaded('japanese');assert.equal(await page.evaluate(()=>window.roomStudio.scene.period),'night');checks.push('switch back and reload preserve the selected sample and saved edits');
 await change('#undo',()=>window.roomStudio.scene.period==='day');await page.locator('#roofs').check();assert(await page.evaluate(()=>[...window.roomStudio.objects.values()].some(o=>o.userData.p.roof&&o.visible)));await page.locator('#roofs').uncheck();checks.push('roof toggle shows actual Japanese roof geometry');
 await page.locator('[data-garden="courtyard"]').click();await page.waitForTimeout(700);await page.locator('#stage').screenshot({path:'docs/qa/samples/japanese-courtyard.png'});
 for(const sample of ['manhattan','japanese']){await page.locator('#sampleSelect').selectOption(sample);await loaded(sample);await page.setViewportSize({width:390,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.setViewportSize({width:1600,height:1080})}checks.push('both sample controls fit 390px mobile width');
 const gl=await page.evaluate(()=>{const g=window.roomStudio.renderer.getContext();return {version:g.getParameter(g.VERSION),error:g.getError()}});assert.equal(gl.error,0);assert.deepEqual(errors,[]);checks.push('actual WebGL2 with no page exceptions or GL errors');
 const report={status:'PASS',renderProfile:process.env.CI?'software CI: quarter pixel ratio, shadow maps disabled, 90s action budget':'full-quality',checks,gl,pageErrors:errors};fs.writeFileSync('docs/qa/samples/browser-results.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}catch(e){console.error(JSON.stringify({errors:[...new Set(errors)],state:await page.evaluate(()=>({name:window.roomStudio?.scene.name,selected:document.querySelector('#sampleSelect').value,status:document.querySelector('#status').textContent,loading:document.querySelector('#loading').textContent}))}));throw e}finally{await browser.close();server.kill();fs.rmSync(tmp,{recursive:true,force:true})}
