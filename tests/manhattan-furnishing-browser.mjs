import {chromium} from 'playwright';
import fs from 'node:fs';import assert from 'node:assert/strict';
const out='docs/qa/manhattan';fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {}),headless:true});
const page=await browser.newPage({viewport:{width:1600,height:1150},deviceScaleFactor:1});const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(process.env.PREVIEW_URL||'http://127.0.0.1:8773');await page.waitForFunction(()=>window.roomStudio?.parts.length>0);await page.waitForTimeout(700);
 assert.equal(await page.locator('[data-room]').count(),20);
 await page.screenshot({path:out+'/A2-overview.png',fullPage:true});
 await page.locator('#plan').click();await page.waitForTimeout(300);await page.screenshot({path:out+'/A2-plan.png',fullPage:true});
 for(const id of ['gallery','living','kitchen','dining','bedroom','study','bathroom']){await page.locator(`[data-room="${id}"]`).click();await page.waitForTimeout(350);await page.screenshot({path:`${out}/A2-${id}.png`,fullPage:true})}
 await page.setViewportSize({width:390,height:844});await page.locator('[data-room="all"]').click();await page.waitForTimeout(300);
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:out+'/A2-mobile.png',fullPage:true});
 const gl=await page.evaluate(()=>{const c=window.roomStudio.renderer.getContext();return {version:c.getParameter(c.VERSION),error:c.getError()}});assert.equal(gl.error,0);assert.deepEqual(errors,[]);
 fs.writeFileSync(out+'/A2-browser-results.json',JSON.stringify({status:'PASS',preview:'http://127.0.0.1:8773',navigation:20,gl,pageErrors:errors,checks:['overview and plan cutaway','seven authored room views','390px no horizontal overflow']},null,2));console.log('PASS',gl);
}finally{await browser.close()}
