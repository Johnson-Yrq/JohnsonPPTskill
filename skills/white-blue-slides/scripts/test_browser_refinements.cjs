/* Run against a fixture containing flow, architecture and journey pages with the new fields. */
'use strict';
const assert = require('assert/strict');
const {pathToFileURL} = require('url');
const path = require('path');
const {chromium} = require('playwright');

(async () => {
  if (!process.argv[2]) throw new Error('用法：node test_browser_refinements.cjs 包含三种新版式的验证稿.html');
  const browser = await chromium.launch({headless:true,channel:'chrome'});
  try {
    const page = await browser.newPage({viewport:{width:1944,height:1172}});
    await page.goto(pathToFileURL(path.resolve(process.argv[2])).href);
    await page.evaluate(async()=>{await document.fonts.ready; await Promise.all([...document.images].map(im=>im.decode()));});
    const flow = await page.evaluate(() => {
      const s=document.querySelector('.layout-flow');window.deckAPI.show([...document.querySelectorAll('.slide')].indexOf(s));
      const groups=[...s.querySelectorAll('.control-group')];
      return groups.map(g=>[...g.querySelectorAll('dl>div')].map(r=>r.getBoundingClientRect().top));
    });
    assert.ok(flow.length>=2);
    const shared=Math.min(flow[0].length,flow[1].length);
    assert.ok(shared>=1,'both groups have rows');
    for(let i=0;i<shared;i++)assert.ok(Math.abs(flow[0][i]-flow[1][i])<2,'parallel control rows align without fixed heights');
    const mode = async width => page.evaluate(async width => {
      const group=document.querySelector('.layout-flow .control-group');group.closest('.control-groups').dataset.alignRows='false';group.dataset.rowsLayout='auto';group.style.width=width+'px';
      await new Promise(resolve=>requestAnimationFrame(resolve));
      return getComputedStyle(group.querySelector('dl>div')).display;
    },width);
    assert.equal(await mode(340),'block');
    assert.equal(await mode(500),'grid');
    await page.reload();
    const semantic = await page.evaluate(() => {
      const architecture=document.querySelector('.layout-architecture');
      return {prefixes:architecture.querySelectorAll('.arch-prefix[data-edit]').length,
              details:architecture.querySelectorAll('.arch-detail[data-edit]').length,
              periods:document.querySelectorAll('.period-tag[data-edit]').length,
              fields:document.querySelectorAll('.journey-fields dd[data-edit]').length};
    });
    assert.ok(semantic.prefixes>0&&semantic.details>0&&semantic.periods>0&&semantic.fields>0);
    // Check the same native canvas path used by PPTX export, including alpha preservation.
    const tinted = await page.evaluate(async () => {
      const img=[...document.images].find(im=>im.style.filter.includes('deck-paper-tone'));await img.decode();
      const canvas=document.createElement('canvas');canvas.width=img.naturalWidth;canvas.height=img.naturalHeight;const ctx=canvas.getContext('2d');
      ctx.drawImage(img,0,0);const original=[...ctx.getImageData(2,2,1,1).data];ctx.clearRect(0,0,canvas.width,canvas.height);
      ctx.filter=getComputedStyle(img).filter;ctx.drawImage(img,0,0);const output=[...ctx.getImageData(2,2,1,1).data];
      const paper=getComputedStyle(document.documentElement).getPropertyValue('--paper').trim();
      const rgb=[1,3,5].map(i=>parseInt(paper.slice(i,i+2),16));return {original,output,rgb};
    });
    tinted.rgb.forEach((c,i)=>assert.ok(Math.abs(tinted.output[i]-Math.round(tinted.original[i]*c/255))<=2));
    assert.equal(tinted.output[3],tinted.original[3]);
    console.log('PASS browser: shared row heights, narrow/wide control layout, editable labels/fields and paper mapping for export');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
