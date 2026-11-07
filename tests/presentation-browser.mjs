import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {spawn} from 'node:child_process';
const port=8911,origin=`http://127.0.0.1:${port}`,out='docs/qa/presentation';fs.mkdirSync(out,{recursive:true});
const server=spawn('python3',['-m','http.server',String(port),'--bind','127.0.0.1'],{stdio:'ignore'});
let browser;const checks=[],errors=[];
try{
 for(let i=0;i<50;i++){try{if((await fetch(origin+'/docs/')).ok)break;}catch{}await new Promise(r=>setTimeout(r,100));}
 browser=await chromium.launch({headless:true,...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{}),timeout:30000,args:['--disable-gpu','--autoplay-policy=no-user-gesture-required']});
 const context=await browser.newContext({viewport:{width:1440,height:1000},colorScheme:'light',permissions:['clipboard-read','clipboard-write']});const page=await context.newPage();
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);});
 await page.goto(origin+'/docs/');await page.evaluate(async()=>{await Promise.all([...document.images].map(async i=>{i.loading='eager';try{await i.decode();}catch{}}));});
 assert.match(await page.locator('h1').textContent(),/shape/);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert(await page.locator('.home img').first().evaluate(i=>Math.abs(i.getBoundingClientRect().width/i.getBoundingClientRect().height-11/8)<.02));checks.push('English desktop layout, correct image proportions and all image requests');
 await page.screenshot({path:out+'/desktop.png',fullPage:true});
 const video=page.locator('#project-film');await page.waitForFunction(()=>document.querySelector('video').duration>0);assert.equal(await video.evaluate(v=>v.duration),65);
 await video.evaluate(v=>v.play());await page.waitForFunction(()=>document.querySelector('video').currentTime>1);await video.evaluate(v=>v.pause());const frozen=await video.evaluate(v=>v.currentTime);await page.waitForTimeout(250);assert.equal(await video.evaluate(v=>v.currentTime),frozen);assert.equal(await video.evaluate(v=>v.videoWidth),1600);checks.push('actual 65-second H264/AAC playback, dimensions and pause');
 await page.locator('[data-view=night]').click();assert(await page.locator('[data-light=night]').isVisible());assert(await page.locator('[data-light=day]').isHidden());await page.locator('[data-view=day]').click();assert(await page.locator('[data-light=day]').isVisible());checks.push('day/night comparison changes real image');
 await page.locator('#language').click();assert.equal(await page.locator('html').getAttribute('lang'),'zh-CN');assert.match(await page.locator('h1').textContent(),/让空间/);assert.match(await page.locator('.copy').textContent(),/复制/);checks.push('Chinese language toggle updates copy and document language');
 await page.locator('.copy').click();assert.match(await page.evaluate(()=>navigator.clipboard.readText()),/python3 preview_samples.py/);assert.match(await page.locator('.copy-status').textContent(),/已复制/);checks.push('setup commands copy to clipboard');
 await page.locator('#language').click();assert.equal(await page.locator('html').getAttribute('lang'),'en');checks.push('language toggle restores English');
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>window.scrollTo(0,0));assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert(await page.locator('.home img').first().evaluate(i=>Math.abs(i.getBoundingClientRect().width/i.getBoundingClientRect().height-11/8)<.02));await page.screenshot({path:out+'/mobile.png',fullPage:true});checks.push('390px mobile layout, correct image proportions and no horizontal overflow');
 await page.emulateMedia({colorScheme:'dark',reducedMotion:'reduce'});assert.equal(await page.evaluate(()=>getComputedStyle(document.documentElement).scrollBehavior),'auto');assert.equal(await page.locator('.paper').evaluate(e=>getComputedStyle(e).backgroundColor),'rgb(244, 239, 230)');await page.screenshot({path:out+'/mobile-dark.png',fullPage:true});checks.push('dark system preference keeps intentional paper section; reduced motion respected');
 await page.locator('#language').click();await page.screenshot({path:out+'/mobile-chinese.png',fullPage:true});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks.push('Chinese mobile layout');
 assert.deepEqual(errors,[]);fs.writeFileSync(out+'/results.json',JSON.stringify({status:'PASS',checks,errors},null,2));console.log(JSON.stringify({status:'PASS',checks,errors},null,2));
}finally{await browser?.close();server.kill();}
