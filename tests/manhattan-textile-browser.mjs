import {chromium} from 'playwright';import fs from 'node:fs';import assert from 'node:assert/strict';
const out='docs/qa/manhattan';const browser=await chromium.launch({...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {}),headless:true});const page=await browser.newPage({viewport:{width:1600,height:1100}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto('http://127.0.0.1:8773');await page.waitForFunction(()=>window.roomStudio?.scene.entities['living.throw']?.drape_profile);const revision=await page.evaluate(()=>window.roomStudio.scene.revision);
 const surfaces=await page.evaluate(()=>['living.throw','bedroom.coverlet','bedroom2.coverlet','study.coverlet'].map(id=>{const root=window.roomStudio.objects.get(id+'/woven_cloth'),p=root.userData.p;return{id,shape:p.shape,textile:p.textile,minZ:Math.min(...p.vertices.map(v=>v[2])),maxZ:Math.max(...p.vertices.map(v=>v[2])),meshVertices:root.userData.item.geometry.getAttribute('position').count}}));
 for(const surface of surfaces){assert.equal(surface.shape,'mesh');assert.equal(surface.textile,true);assert(surface.maxZ-surface.minZ>.2)}
 for(const rid of ['living','bedroom','bedroom2','study']){await page.locator(`[data-room="${rid}"]`).click();await page.waitForTimeout(250);await page.locator('#stage').screenshot({path:`${out}/A2-textile-${rid}.png`})}
 // Inspection camera changes exist only in this browser object; scene on disk is untouched.
 const scale=await page.evaluate(()=>window.roomStudio.scene.layout.scale_factor);
 await page.evaluate(({scale})=>{window.roomStudio.scene.rooms.living.camera={position:[6.4*scale,8.4*scale,1.05],target:[4.6*scale,8.55*scale,.42]};window.roomStudio.scene.rooms.bedroom.camera={position:[-6.55*scale,10.2*scale,1.4],target:[-8.5*scale,8.7*scale,.62]}},{scale});
 for(const rid of ['living','bedroom']){await page.locator(`[data-room="${rid}"]`).click();await page.waitForTimeout(250);await page.locator('#stage').screenshot({path:`${out}/A2-textile-${rid}-contact.png`})}
 const gl=await page.evaluate(()=>window.roomStudio.renderer.getContext().getError());assert.equal(gl,0);assert.deepEqual(errors,[]);
 const current=await page.evaluate(async()=>(await(await fetch('/api/scene')).json()).scene.revision);assert.equal(current,revision);
 fs.writeFileSync(out+'/A2-textile-browser.json',JSON.stringify({status:'PASS',revision,surfaces,gl,pageErrors:errors,cameraChanges:'browser memory only; disk revision unchanged'},null,2));console.log('PASS textile WebGL inspection, revision',revision);
}finally{await browser.close()}
