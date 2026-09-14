#!/usr/bin/env node
/* Inspect a generated local deck in an isolated browser. No user session access. */
'use strict';
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const {reviewTemplate, assessReview} = require('./visual_review.cjs');

// Compare page structure in slide coordinates, independent of viewport/print zoom.
function slideFrames() {
  return [...document.querySelectorAll('.slide')].filter(s => s.getBoundingClientRect().width).map(s => {
    const r = s.getBoundingClientRect(), scale = 1920 / r.width;
    return {id: s.id, regions: ['header', 'main', 'footer'].map(selector => {
      const b = s.querySelector(selector).getBoundingClientRect();
      return [(b.x-r.x)*scale, (b.y-r.y)*scale, b.width*scale, b.height*scale];
    })};
  });
}
function matchingFrames(expected, actual) {
  return expected.length === actual.length && expected.every((s, i) => s.id === actual[i].id &&
    s.regions.every((r, j) => r.every((v, k) => Math.abs(v-actual[i].regions[j][k]) < 2.5)));
}

async function run() {
  const args = process.argv.slice(2), filename = args.shift();
  let out, channel, reviewFile, pdf = false; // PDF geometry is verified by export_pdf.cjs when a PDF is actually exported
  while (args.length) {
    const flag = args.shift();
    if (flag === '--out') out = args.shift();
    else if (flag === '--browser') channel = args.shift();
    else if (flag === '--pdf') pdf = true;
    else if (flag === '--no-pdf') pdf = false; // kept for older commands; already the default
    else if (flag === '--visual-review') reviewFile = args.shift();
    else throw new Error(`未知参数：${flag}`);
  }
  if (!filename || !out) throw new Error('用法：node audit_deck.cjs 演示稿.html --out qa [--browser chrome] [--pdf] [--visual-review review.json]');
  let chromium;
  try { ({chromium} = require('playwright')); }
  catch { throw new Error('找不到 Playwright。请使用当前环境已有的 Node.js + Playwright，或按用户授权准备依赖。'); }
  out = path.resolve(out); fs.mkdirSync(out, {recursive: true});
  const report = {file: path.resolve(filename), pages: [], errors: [], functions: {}, screenshots: [], externalRequests: []};
  const browser = await chromium.launch({headless: true, ...(channel ? {channel} : {})});
  try {
    const context = await browser.newContext({viewport: {width: 1944, height: 1172}, deviceScaleFactor: 1, acceptDownloads: true});
    await context.route(/^https?:\/\//i, route => {report.externalRequests.push(route.request().url()); return route.abort();});
    const page = await context.newPage();
    page.on('pageerror', e => report.errors.push(e.message));
    await page.goto(pathToFileURL(path.resolve(filename)).href, {waitUntil: 'load'});
    await page.evaluate(async () => {await document.fonts.ready; await Promise.all([...document.images].map(im => im.decode().catch(() => {})));});
    const count = await page.locator('.slide').count();
    if (!count) throw new Error('没有找到演示页面');
    report.count = count;
    report.style = await page.evaluate(() => document.body.dataset.style || 'scene-white');
    report.presentation_mode = await page.evaluate(() => document.body.dataset.presentationMode || 'speech');
    report.selfContained = await page.evaluate(() => ({
      externalElements: [...document.querySelectorAll('img[src],script[src],link[href],iframe[src],audio[src],video[src],source[src],image[href]')]
        .filter(el => !/^(data:|#)/.test(el.getAttribute('src') || el.getAttribute('href') || '')).map(el => el.tagName),
      cssImports: /@import\b/i.test([...document.querySelectorAll('style')].map(s => s.textContent).join('\n')),
      externalCssUrls: /url\s*\(\s*["']?(?!data:|#)[^\s"')]+/i.test([...document.querySelectorAll('style')].map(s => s.textContent).join('\n')),
      draft: document.body.classList.contains('draft') || !!document.querySelector('.missing-image')
    }));
    const screenFrames = [];
    for (let i = 0; i < count; i++) {
      await page.evaluate(n => window.deckAPI.show(n), i);
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      const checks = await page.evaluate(() => {
        const s = document.querySelector('.slide.active'), sr = s.getBoundingClientRect(), footer = s.querySelector('footer').getBoundingClientRect();
        const issues = [], rect = el => {const r = el.getBoundingClientRect(); return {x:r.x-sr.x,y:r.y-sr.y,w:r.width,h:r.height,right:r.right-sr.x,bottom:r.bottom-sr.y};};
        const styleDefaults={max_radius:8,page_number_min:100,cover_labels_expected:true};
        let styleContract=styleDefaults;
        if(document.body.dataset.styleContract){
          try{
            const parsed=JSON.parse(document.body.dataset.styleContract);
            if(!parsed||!Number.isFinite(parsed.max_radius)||parsed.max_radius<0||!Number.isFinite(parsed.page_number_min)||parsed.page_number_min<1||typeof parsed.cover_labels_expected!=='boolean')throw new Error('invalid values');
            styleContract=parsed;
          }catch{issues.push({type:'invalid-style-contract'});}
        }else if(document.body.dataset.style&&document.body.dataset.style!=='scene-white')issues.push({type:'missing-style-contract'});
        const textEls = [...s.querySelectorAll('[data-edit],.page-number')].filter(el => el.textContent.trim() && el.getBoundingClientRect().width > 0);
        const readingMode = document.body.dataset.presentationMode === 'reading';
        const label = el => el.textContent.trim().slice(0,70);
        for (const el of textEls) {
          const r = rect(el);
          if (r.x < -1 || r.y < -1 || r.right > sr.width+1 || r.bottom > sr.height+1) issues.push({type:'out-of-bounds',text:label(el),rect:r});
          if (el.closest('main') && r.bottom > footer.top-sr.top-8) issues.push({type:'footer-collision',text:label(el),bottom:r.bottom});
          const cs=getComputedStyle(el), clippedY=['hidden','clip','auto','scroll'].includes(cs.overflowY);
          if(readingMode&&el.closest('main')&&parseFloat(cs.fontSize)<21)issues.push({type:'reading-text-too-small',text:label(el),size:parseFloat(cs.fontSize),minimum:21});
          // Visible font ascenders can exceed a line box without clipping. Only
          // flag vertical scroll metrics when the element actually clips them.
          if (el.clientWidth && (el.scrollWidth > el.clientWidth+2 || (clippedY && el.scrollHeight > el.clientHeight+2))) issues.push({type:'text-overflow',text:label(el)});
        }
        for (let a=0; a<textEls.length; a++) for (let b=a+1; b<textEls.length; b++) {
          const x=textEls[a],y=textEls[b]; if (x.contains(y)||y.contains(x)) continue;
          const xr=rect(x),yr=rect(y),w=Math.min(xr.right,yr.right)-Math.max(xr.x,yr.x),h=Math.min(xr.bottom,yr.bottom)-Math.max(xr.y,yr.y);
          if (w>2 && h>2) issues.push({type:'text-overlap',a:label(x),b:label(y),width:w,height:h});
        }
        const brokenImages=[...s.querySelectorAll('img')].filter(im => !im.complete || !im.naturalWidth).map(im => im.alt);
        for (const el of s.querySelectorAll('*')) {
          const cs=getComputedStyle(el);
          if (Math.max(...['borderTopLeftRadius','borderTopRightRadius','borderBottomLeftRadius','borderBottomRightRadius'].map(k=>parseFloat(cs[k])||0))>styleContract.max_radius+.01) issues.push({type:'radius-over-style-limit',limit:styleContract.max_radius,element:el.className.baseVal??el.className});
          if (el.classList.contains('architecture-label') && (cs.backgroundColor!=='rgba(0, 0, 0, 0)' || parseFloat(cs.borderTopWidth)>0)) issues.push({type:'architecture-label-box',text:label(el)});
        }
        const designIssues=[], counts={}, texts={}, featureNames={icons:'icon',panels:'panel',tags:'tag',states:'state',architecture_labels:'architecture-label',relations:'relation',visual_blocks:'visual-block',tables:'table',layers:'layer',charts:'chart'};
        const transparent=c=>c==='transparent'||c==='rgba(0, 0, 0, 0)'||/rgba\([^)]*,\s*0\s*\)/.test(c);
        const visible=el=>{
          const r=el.getBoundingClientRect();
          if(r.width<1||r.height<1||r.right<=sr.left||r.left>=sr.right||r.bottom<=sr.top||r.top>=sr.bottom)return false;
          for(let p=el;p&&p!==s.parentElement;p=p.parentElement){const cs=getComputedStyle(p);if(cs.display==='none'||cs.visibility==='hidden'||Number(cs.opacity)===0)return false;}
          return true;
        };
        const grouped=el=>{const cs=getComputedStyle(el);return (!transparent(cs.backgroundColor)&&cs.backgroundColor!==getComputedStyle(s).backgroundColor)||['Top','Right','Bottom','Left'].every(k=>parseFloat(cs['border'+k+'Width'])>0&&cs['border'+k+'Style']!=='none');};
        for(const [feature,component] of Object.entries(featureNames)){
          const found=[...s.querySelectorAll(`[data-component="${component}"]`)].filter(el=>{
            if(!visible(el))return false;
            if(feature==='icons')return el.tagName.toLowerCase()==='svg'&&!!el.querySelector('path,circle,rect,line,polyline,polygon,ellipse')&&!transparent(getComputedStyle(el).color);
            if(['panels','tags','states'].includes(feature))return grouped(el);
            if(feature==='relations')return el.querySelectorAll('[data-component="tag"]').length>=2&&!!el.querySelector('.relation-link,[data-connection]');
            if(feature==='tables')return el.tagName.toLowerCase()==='table'&&el.rows.length>=2&&el.rows[0].cells.length>=2;
            if(feature==='charts')return el.dataset.chartReady==='true'&&!!el.querySelector('svg path');
            if(feature==='layers')return !!el.querySelector('.reading-layer-name')&&el.querySelectorAll('[data-component="tag"]').length>=1;
            if(feature==='visual_blocks')return !!el.querySelector('h3')&&((el.dataset.visualType==='process'&&el.querySelectorAll('[data-step]').length>=3)||(el.dataset.visualType==='matrix'&&el.querySelectorAll('table tr').length>=3)||(el.dataset.visualType==='layers'&&el.querySelectorAll('[data-component="layer"]').length>=2)||(el.dataset.visualType==='facts'&&el.querySelectorAll('dl>div').length>=2)||(el.dataset.visualType==='chart'&&!!el.querySelector('.echart[data-chart-ready="true"] svg path')));
            return true;
          });
          counts[feature]=found.length;
          texts[feature]=found.map(el=>feature==='icons'?(el.closest('.icon-heading,.relation-node')||el.parentElement).textContent.trim():feature==='tables'?(el.closest('.reading-block')||el).textContent.trim():el.textContent.trim());
        }
        const steps=[...s.querySelectorAll('[data-step]')].filter(visible);counts.steps=steps.length;texts.steps=steps.map(el=>el.textContent.trim());
        let contract=null,imageBalance=null;
        try{contract=JSON.parse(s.dataset.designContract);}catch{designIssues.push({type:'missing-design-contract',detail:'本页缺少独立设计决策，不能把功能通过当成设计通过'});}
        if(contract){
          for(const e of contract.errors||[])designIssues.push({type:'invalid-design-plan',detail:e});
          for(const req of contract.expected||[]){
            if((counts[req.feature]||0)<req.min)designIssues.push({type:'missing-design-component',feature:req.feature,expected:req.min,actual:counts[req.feature]||0,source:req.source});
            for(const text of req.texts||[])if(!(texts[req.feature]||[]).some(t=>t.includes(text)))designIssues.push({type:'missing-design-text',feature:req.feature,text,source:req.source});
          }
          if(contract.image_balance){
            const target=contract.image_balance,frame=s.querySelector('main .scene-image'),captions=s.querySelector('.journey-labels,[data-captions]'),im=frame?.querySelector('img'),mainEl=s.querySelector('main'),scale=sr.width/1920;
            if(!frame||!im)designIssues.push({type:'missing-upper-image'});
            else{
              const fr=frame.getBoundingClientRect(),ir=im.getBoundingClientRect();
              // fillRatio: the visible image spans the frame's width or height, i.e. it is as large as the frame allows at its aspect ratio.
              const widthRatio=Math.max(0,Math.min(ir.right,fr.right)-Math.max(ir.left,fr.left))/fr.width,heightRatio=Math.max(0,Math.min(ir.bottom,fr.bottom)-Math.max(ir.top,fr.top))/fr.height;
              imageBalance={height:fr.height/scale,mainRatio:fr.height/mainEl.getBoundingClientRect().height,widthRatio,heightRatio,fillRatio:Math.max(widthRatio,heightRatio),captionHeight:captions?captions.getBoundingClientRect().height/scale:0};
              if(imageBalance.height+1<target.min_height||imageBalance.mainRatio+.005<target.min_main_ratio||imageBalance.fillRatio+.005<target.min_fill_ratio||imageBalance.captionHeight-1>target.max_caption_height)designIssues.push({type:'image-area-too-small',actual:imageBalance,expected:target,hint:'图框高度、图框占 main 比例、配图贴满图框宽或高、下方文字行高四项须同时达标；主体是否横向铺开仍需看图。'});
            }
          }
        }
        // Brand invariants: the default header/footer/cover/closing conventions, read from the theme tokens so a deck-level theme override still passes.
        const brandIssues=[],warnings=[],restyle=document.body.hasAttribute('data-restyle');
        for(const group of s.querySelectorAll('.control-group')) {
          for(const row of group.querySelectorAll('dl>div')) {
            const label=row.querySelector('dt'),cs=label&&getComputedStyle(label);
            if(label&&getComputedStyle(row).display==='grid'&&label.getBoundingClientRect().height>parseFloat(cs.lineHeight)*(sr.width/1920)*1.6)warnings.push({type:'control-label-wrapped',text:label.textContent,hint:'检查短标签断行；可用 rows_layout: stacked 或重新分配栏宽'});
          }
        }
        const journey=s.querySelector('.journey'),captionItems=[...s.querySelectorAll('.journey-item')];
        if(readingMode&&journey&&captionItems.some(el=>el.getBoundingClientRect().width/(sr.width/1920)<240))warnings.push({type:'journey-caption-narrow',hint:'阶段栏宽较窄；核对最长内容，优先调整场景构图及图文占幅，再选择短字段或其他版式'});
        const token=n=>{const h=getComputedStyle(document.documentElement).getPropertyValue(n).trim();const m=/^#([0-9a-f]{6})$/i.exec(h);return m?`rgb(${parseInt(m[1].slice(0,2),16)}, ${parseInt(m[1].slice(2,4),16)}, ${parseInt(m[1].slice(4,6),16)})`:h;};
        const isCover=s.classList.contains('layout-cover'),isClosing=s.classList.contains('layout-closing'),main=s.querySelector('main');
        if(!restyle){
          const slideBg=getComputedStyle(s).backgroundColor;if(slideBg!==token('--paper'))brandIssues.push({type:'slide-background',actual:slideBg,expected:token('--paper')});
          const h1=s.querySelector('h1'),sub=s.querySelector('.subtitle'),ch=s.querySelector('.chapter'),pn=s.querySelector('.page-number'),ft=s.querySelector('footer'),logo=s.querySelector('.brand-logo');
          if(h1){const hcs=getComputedStyle(h1),hs=parseFloat(hcs.fontSize);
            if(sub){const scs=getComputedStyle(sub),ss=parseFloat(scs.fontSize);if(ss*1.3>hs)brandIssues.push({type:'subtitle-competes-with-title',title:hs,subtitle:ss});if(parseInt(scs.fontWeight)>=600)brandIssues.push({type:'subtitle-bold'});if(!isCover&&!isClosing&&scs.color!==token('--muted'))brandIssues.push({type:'subtitle-color',actual:scs.color});}
            if(!isCover&&!isClosing){if(hcs.color!==token('--ink'))brandIssues.push({type:'title-color',actual:hcs.color});if(hs<36)brandIssues.push({type:'title-too-small',actual:hs});}
            if(isClosing&&hcs.color!==token(styleContract.closing_title_token||'--blue'))brandIssues.push({type:'closing-title-color',actual:hcs.color});}
          if(ch&&!isClosing&&styleContract.chapter_panel!==false&&transparent(getComputedStyle(ch).backgroundColor))brandIssues.push({type:'chapter-without-panel'});
          if(!pn||!visible(pn)||parseFloat(getComputedStyle(pn).fontSize)<styleContract.page_number_min)brandIssues.push({type:'page-number-missing-or-small',minimum:styleContract.page_number_min});
          if(!ft||!visible(ft)||!logo||!visible(logo))brandIssues.push({type:'footer-or-logo-missing'});
          if(isCover){const copy=s.querySelector('.cover-copy'),hero=s.querySelector('.hero-scene');if(!copy||rect(copy).x>120)brandIssues.push({type:'cover-copy-not-left'});if(!hero||rect(hero).x<sr.width*0.45)brandIssues.push({type:'cover-image-not-right'});if(styleContract.cover_labels_expected&&!s.querySelector('.cover-labels>div'))warnings.push({type:'cover-without-labels'});}
        }
        // Reading illustration area uses the WHOLE slide, not main or figure boxes.
        // Intersect actual rendered image rectangles with clipping ancestors, then take their union.
        const intersection=(a,b)=>({left:Math.max(a.left,b.left),right:Math.min(a.right,b.right),top:Math.max(a.top,b.top),bottom:Math.min(a.bottom,b.bottom)});
        const imageRects=[...s.querySelectorAll('main .scene-image img')].filter(visible).map(img=>{
          let r=intersection(img.getBoundingClientRect(),s.getBoundingClientRect());
          for(let el=img.parentElement;el&&el!==s;el=el.parentElement){
            const cs=getComputedStyle(el),clip=el.getBoundingClientRect();
            if(/hidden|clip|scroll|auto/.test(cs.overflowX)){r.left=Math.max(r.left,clip.left);r.right=Math.min(r.right,clip.right);}
            if(/hidden|clip|scroll|auto/.test(cs.overflowY)){r.top=Math.max(r.top,clip.top);r.bottom=Math.min(r.bottom,clip.bottom);}
          }
          return r;
        }).filter(r=>r.right>r.left&&r.bottom>r.top);
        const xs=[...new Set(imageRects.flatMap(r=>[r.left,r.right]))].sort((a,b)=>a-b);
        let union=0;
        for(let x=1;x<xs.length;x++){
          const intervals=imageRects.filter(r=>r.left<xs[x]&&r.right>xs[x-1]).map(r=>[r.top,r.bottom]).sort((a,b)=>a[0]-b[0]);
          let end=-Infinity,height=0;
          for(const [lo,hi] of intervals){height+=Math.max(0,hi-Math.max(lo,end));end=Math.max(end,hi);}
          union+=(xs[x]-xs[x-1])*height;
        }
        const illustrationRatio=union/(sr.width*sr.height),illustrationArea=Math.round(illustrationRatio*1000)/1000;
        let compositionBalance=null;
        if(readingMode&&s.classList.contains('layout-reading')){
          const body=s.querySelector('.reading-body'),br=body.getBoundingClientRect(),media=[...body.querySelectorAll('.reading-media-item')],blocks=[...body.querySelectorAll('.reading-block')];
          const imageRegions=media.reduce((sum,el)=>{const r=el.getBoundingClientRect();return sum+r.width*r.height;},0);
          const expected=contract?.illustration_region_ratio,actual=imageRegions/(br.width*br.height),coverage=union/imageRegions;
          // Per illustration: the visible image spans its region's width or height (as large as the region allows at its aspect ratio).
          const fills=media.map(el=>{
            const cs=getComputedStyle(el),r=el.getBoundingClientRect(),w=r.width-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight),h=r.height-parseFloat(cs.paddingTop)-parseFloat(cs.paddingBottom),im=el.querySelector('.scene-image img');
            if(!im||!visible(im)||w<=0||h<=0)return 0;
            const b=im.getBoundingClientRect(),ir={left:b.left,right:b.right,top:b.top,bottom:b.bottom};
            for(let p=im.parentElement;p&&p!==el;p=p.parentElement){const pc=getComputedStyle(p),clip=p.getBoundingClientRect();if(/hidden|clip|scroll|auto/.test(pc.overflowX)){ir.left=Math.max(ir.left,clip.left);ir.right=Math.min(ir.right,clip.right);}if(/hidden|clip|scroll|auto/.test(pc.overflowY)){ir.top=Math.max(ir.top,clip.top);ir.bottom=Math.min(ir.bottom,clip.bottom);}}
            return Math.max(Math.max(0,ir.right-ir.left)/w,Math.max(0,ir.bottom-ir.top)/h);
          });
          const imageFill=fills.length?Math.min(...fills):0,minFill=contract?.illustration_fill?.min_fill_ratio;
          const composition=s.querySelector('[data-composition]')?.dataset.composition;
          const at=(el,x,y)=>{const r=el.getBoundingClientRect();return ((r.left+r.width/2-br.left)/br.width<.5?0:1)===x&&((r.top+r.height/2-br.top)/br.height<.5?0:1)===y;};
          let placement=true;
          if(composition==='half_lr')placement=media.length===1&&media.every(el=>at(el,0,0)||at(el,0,1))&&blocks.every(el=>at(el,1,0)||at(el,1,1));
          else if(composition==='half_tb')placement=media.every(el=>at(el,0,0)||at(el,1,0))&&blocks.every(el=>at(el,0,1)||at(el,1,1));
          else if(composition==='half_diagonal')placement=media.length===2&&blocks.length===2&&at(media[0],0,0)&&at(media[1],1,1)&&at(blocks[0],1,0)&&at(blocks[1],0,1);
          else if(composition==='quarter')placement=media.length===1&&blocks.length===3&&at(media[0],0,0)&&at(blocks[0],1,0)&&at(blocks[1],0,1)&&at(blocks[2],1,1);
          else placement=false;
          compositionBalance={composition,expected,regionRatio:actual,imageCoverage:coverage,imageFill,placement};
          if(!Number.isFinite(expected)||Math.abs(actual-expected)>.04||!placement)designIssues.push({type:'reading-composition-mismatch',...compositionBalance,hint:'按主体版面核对左右、上下、对角或四分之一分区，不以图片像素面积替代分区比例。'});
          if(!Number.isFinite(minFill)||imageFill+.005<minFill)designIssues.push({type:'reading-image-underfilled',imageFill,minimum:minFill,hint:`每张配图至少达到所在图区宽或高的 ${Math.round((minFill||0)*100)}%；按可见本体缩放，不用空图框或缩小的图片凑分区。`});
        }
        for(const host of s.querySelectorAll('.echart')){
          const hr=host.getBoundingClientRect(),svg=host.querySelector('svg');
          if(!svg||host.dataset.chartReady!=='true')designIssues.push({type:'chart-not-rendered'});
          for(const label of host.querySelectorAll('svg text')){const lr=label.getBoundingClientRect();if(lr.width&&lr.height&&(lr.left<hr.left-3||lr.right>hr.right+3||lr.top<hr.top-3||lr.bottom>hr.bottom+3))issues.push({type:'chart-label-clipped',text:label.textContent});}
        }
        // Preserve speech-mode advisory checks against the content area.
        let imageArea=null;const heroImg=s.querySelector('main .scene-image img');
        if(heroImg&&main&&!isCover&&!isClosing){const ir=heroImg.getBoundingClientRect(),mr=main.getBoundingClientRect();const w=Math.max(0,Math.min(ir.right,mr.right)-Math.max(ir.left,mr.left)),h=Math.max(0,Math.min(ir.bottom,mr.bottom)-Math.max(ir.top,mr.top));imageArea=Math.round((w*h)/(mr.width*mr.height)*1000)/1000;const floor=s.classList.contains('layout-table')?.08:.30;if(!readingMode&&imageArea<floor)warnings.push({type:'image-area-small',imageArea,floor,hint:'放大场景本体、收窄文字或换左右排布；不要用小图配大段文字'});}
        if(readingMode&&s.classList.contains('layout-reading')){
          // Alignment rule: a block heading stays on the region's top edge (so headings align across a row); the body below it, or an image with its caption, is centred in the remaining space (equal free space above and below, 12px tolerance).
          for(const cell of s.querySelectorAll('.reading-body .reading-block,.reading-body .reading-media-item')){
            const cs=getComputedStyle(cell),cr=cell.getBoundingClientRect(),kids=[...cell.children].filter(el=>visible(el)&&el.getBoundingClientRect().height>0);if(!kids.length)continue;
            const contentTop=cr.top+parseFloat(cs.borderTopWidth)+parseFloat(cs.paddingTop),contentBottom=cr.bottom-parseFloat(cs.borderBottomWidth)-parseFloat(cs.paddingBottom),region=cell.classList.contains('reading-block')?cell.dataset.visualType:'image';
            const heading=kids[0].matches('h3')?kids[0]:null,body=heading?kids.slice(1):kids;
            if(heading&&heading.getBoundingClientRect().top-contentTop>4)designIssues.push({type:'reading-heading-not-top',region,text:label(heading).slice(0,40),hint:'模块标题贴分区上沿，同一行的标题对齐。'});
            if(!body.length)continue;
            const top=Math.min(...body.map(el=>el.getBoundingClientRect().top))-(heading?heading.getBoundingClientRect().bottom+parseFloat(getComputedStyle(heading).marginBottom):contentTop),bottom=contentBottom-Math.max(...body.map(el=>el.getBoundingClientRect().bottom));
            if(bottom<-1)designIssues.push({type:'reading-block-overflow',region,text:label(cell).slice(0,40),overflow:Math.round(-bottom),hint:'模块内容超出分区高度；减少条目、让整行模块用 span: 2，或拆页，不靠缩小字号。'});
            else if(Math.abs(top-bottom)>12)designIssues.push({type:'reading-region-not-centered',region,text:label(cell).slice(0,40),above:Math.round(top),below:Math.round(bottom),hint:'标题下方的内容（或配图与说明）在分区剩余空间内垂直居中；不用顶对齐或底对齐填充空位。'});
          }
        }
        let structuredArea=null;
        if(s.classList.contains('layout-reading')){const mr=main.getBoundingClientRect();structuredArea=[...s.querySelectorAll('[data-component="visual-block"]')].reduce((sum,el)=>{const r=el.getBoundingClientRect();return sum+Math.max(0,Math.min(r.right,mr.right)-Math.max(r.left,mr.left))*Math.max(0,Math.min(r.bottom,mr.bottom)-Math.max(r.top,mr.top));},0)/(mr.width*mr.height);if(counts.visual_blocks<1)designIssues.push({type:'reading-visual-blocks-missing'});}
        return {page:Number(document.querySelector('#page-input').value),id:s.id,title:s.querySelector('h1').textContent,issues,brokenImages,design:{ok:!designIssues.length,counts,issues:designIssues,imageBalance,structuredArea,compositionBalance,manualReview:contract?.manual||[],rationale:contract?.rationale||'',omissions:contract?.omissions||[]},brand:{ok:!brandIssues.length,restyle,issues:brandIssues},imageArea,illustrationArea,imageCount:imageRects.length,warnings};
      });
      report.pages.push(checks);
      screenFrames.push((await page.evaluate(slideFrames))[0]);
      const shot = path.join(out, `p${String(i+1).padStart(2,'0')}.png`);
      await page.locator('.slide.active').screenshot({path: shot}); report.screenshots.push(shot);
    }
    const f = report.functions;
    await page.keyboard.press('Home');
    f.home = await page.evaluate(() => window.deckAPI.current === 1);
    f.firstPrevDisabled = await page.locator('#prev').isDisabled();
    if (count>1) {await page.keyboard.press('ArrowRight'); f.arrow = await page.evaluate(() => window.deckAPI.current === 2);}
    else f.arrow = true;
    await page.keyboard.press('End');
    f.end = await page.evaluate(n => window.deckAPI.current === n, count);
    f.lastNextDisabled = await page.locator('#next').isDisabled();
    f.pageCount = Number(await page.locator('#page-input').getAttribute('max'))===count;
    await page.locator('#overview').click();
    f.overview = await page.locator('.slide:visible').count()===count;
    f.overviewLayout = matchingFrames(screenFrames, await page.evaluate(slideFrames));
    await page.locator('.slide').nth(Math.min(1,count-1)).click();
    f.overviewJump = await page.evaluate(n => window.deckAPI.current === n && !document.body.classList.contains('overview-mode'), Math.min(2,count));
    await page.locator('#notes').click();
    f.notes = await page.locator('#notes-panel').isVisible() && await page.evaluate(() => document.querySelector('#notes-content').textContent === document.querySelector('.slide.active').dataset.speakerNotes);
    await page.locator('#close-notes').click();
    await page.locator('#edit').click();
    const editTarget = page.locator('.slide.active h1 [data-edit],.slide.active h1[data-edit]').first();
    const marker = '保存验证 · 可编辑文字';
    await editTarget.fill(marker);
    f.edit = await editTarget.textContent()===marker;
    const chartSlide = await page.evaluate(()=>[...document.querySelectorAll('.slide')].findIndex(s=>s.querySelector('.chart-data')));
    if(chartSlide>=0){
      await page.evaluate(index=>window.deckAPI.show(index),chartSlide);
      await page.locator('.slide.active .chart-editor').first().evaluate(el=>el.open=true);
      const cell=page.locator('.slide.active .chart-data tbody tr').first().locator('td').first();
      await cell.fill('invalid');
      const rejected=await page.locator('.slide.active .chart-shell[data-invalid]').count()===1;
      await cell.fill('97');
      f.chartDataEdit=rejected&&await page.evaluate(()=>{const shell=document.querySelector('.slide.active .chart-shell'),config=JSON.parse(shell.querySelector('.chart-config').textContent),series=echarts.getInstanceByDom(shell.querySelector('.echart')).getOption().series[0];return config.series[0].values[0]===97&&(series.data[0]?.value??series.data[0])===97&&!shell.hasAttribute('data-invalid');});
      await page.locator('.slide.active .chart-editor').first().evaluate(el=>el.open=false);
    }
    const downloadPromise = page.waitForEvent('download'); await page.locator('#save').click();
    const downloaded = await downloadPromise, savedPath = path.join(out,'save-test.html'); await downloaded.saveAs(savedPath);
    const saved = await context.newPage(); await saved.goto(pathToFileURL(savedPath).href);
    await saved.evaluate(async () => {await Promise.all([...document.images].map(im => im.decode().catch(() => {})));});
    f.saveReopen = await saved.evaluate(({marker,count}) => [...document.querySelectorAll('h1')].some(h => h.textContent.includes(marker)) && document.querySelectorAll('.slide').length===count && [...document.images].every(im => im.naturalWidth>0) && !document.body.classList.contains('editing'), {marker,count});
    if(chartSlide>=0){
      await saved.evaluate(index=>window.deckAPI.show(index),chartSlide);
      f.chartSaveReopen=await saved.evaluate(()=>{const shell=document.querySelector('.slide.active .chart-shell'),config=JSON.parse(shell.querySelector('.chart-config').textContent),host=shell.querySelector('.echart'),series=echarts.getInstanceByDom(host).getOption().series[0];return config.series[0].values[0]===97&&(series.data[0]?.value??series.data[0])===97&&!!host.querySelector('svg path');});
    }
    await saved.close();
    // Editable PPTX export from the toolbar: a real zip comes back and the player returns to its previous page.
    if (await page.locator('#pptx').count()) {
      const pptxPromise = page.waitForEvent('download'); await page.locator('#pptx').click();
      const pptxPath = path.join(out, 'export-test.pptx'); await (await pptxPromise).saveAs(pptxPath);
      const head = fs.readFileSync(pptxPath);
      report.pptxBytes = head.length;
      f.pptxExport = head.length > 1000 && head[0] === 0x50 && head[1] === 0x4B && head.includes('ppt/presentation.xml') && !await page.evaluate(() => document.body.classList.contains('editing'));
    }
    await page.goto(pathToFileURL(path.resolve(filename)).href);
    await page.setViewportSize({width:390,height:844});
    // Resize handlers run asynchronously; settle the scale before measuring.
    await page.evaluate(() => new Promise(resolve => {window.deckAPI.fit(); requestAnimationFrame(() => requestAnimationFrame(resolve));}));
    f.mobileFit = await page.evaluate(() => {const r=document.querySelector('.slide.active').getBoundingClientRect();return r.width<=innerWidth && r.left>=-1 && r.right<=innerWidth+1 && r.bottom<=innerHeight-60;});
    await page.setViewportSize({width:1920,height:1080});
    await page.locator('#fullscreen').click();
    f.fullscreen = await page.evaluate(() => !!document.fullscreenElement);
    report.fullscreenSizes = [];
    for (const size of [{width:1920,height:1080},{width:1440,height:900},{width:2560,height:1080},{width:1024,height:768}]) {
      await page.setViewportSize(size);
      const fits = await page.evaluate(() => {
        window.deckAPI.fit();
        const r=document.querySelector('.slide.active').getBoundingClientRect(),scale=Math.min(innerWidth/1920,innerHeight/1080);
        return Math.abs(r.width-1920*scale)<1 && Math.abs(r.height-1080*scale)<1 &&
          Math.abs(r.x-(innerWidth-r.width)/2)<1 && Math.abs(r.y-(innerHeight-r.height)/2)<1;
      });
      report.fullscreenSizes.push({...size, fits});
    }
    f.fullscreenFit = report.fullscreenSizes.every(s=>s.fits);
    await page.setViewportSize({width:1920,height:1080});
    if (f.fullscreen) {
      await page.locator('.toolbar').hover();
      const revealed = await page.locator('.toolbar').evaluate(el=>getComputedStyle(el).opacity==='1');
      await page.mouse.move(0,0);
      f.fullscreenToolbar = revealed && await page.locator('.toolbar').evaluate(el=>getComputedStyle(el).opacity==='0');
      await page.locator('#edit').evaluate(el=>el.click());
      f.fullscreenEditFit = await page.evaluate(() => {
        const r=document.querySelector('.slide.active').getBoundingClientRect(),bar=document.querySelector('.toolbar').getBoundingClientRect();
        return r.bottom<=bar.top && getComputedStyle(document.querySelector('.toolbar')).opacity==='1';
      });
      await page.locator('#edit').click();
      await page.evaluate(() => document.exitFullscreen());
    }
    await page.setViewportSize({width:1944,height:1172});
    if (pdf) {
      // Export from overview with another slide selected: inactive pages must keep
      // the same header/body/footer geometry as single-slide viewing.
      await page.evaluate(()=>window.deckAPI.show(window.deckAPI.count-1));
      await page.locator('#overview').click();
      await page.emulateMedia({media:'print'});
      await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
      f.printLayout = matchingFrames(screenFrames, await page.evaluate(slideFrames));
      const {writePresentationPdf} = require('./export_pdf.cjs');
      const printed = await writePresentationPdf(page, path.join(out,'print-check.pdf'), count);
      report.printPages = printed.pages;
      report.printPageSizes = printed.sizes;
      f.printCount = report.printPages===count;
      f.printSize = printed.sizes.every(s=>Math.abs(s.width-960)<.5 && Math.abs(s.height-540)<.5);
      f.printReturnLayout = matchingFrames(screenFrames, await page.evaluate(slideFrames));
    }
    try {
      const sharp = require('sharp'), cols=3, thumbWidth=640, thumbHeight=360, gap=20, rows=Math.ceil(count/cols);
      const tiles = await Promise.all(report.screenshots.map(async (file,i) => ({input:await sharp(file).resize(thumbWidth,thumbHeight).toBuffer(),left:gap+(i%cols)*(thumbWidth+gap),top:gap+Math.floor(i/cols)*(thumbHeight+gap)})));
      await sharp({create:{width:cols*(thumbWidth+gap)+gap,height:rows*(thumbHeight+gap)+gap,channels:3,background:'#E3E6EA'}}).composite(tiles).png().toFile(path.join(out,'overview.png'));
      report.overview = path.join(out,'overview.png');
    } catch(e) {report.overviewNote = '联系表未生成；逐页截图可用。'+e.message;}
    report.technicalOK = report.pages.every(p => !p.issues.length && !p.brokenImages.length) && !report.errors.length && !report.externalRequests.length && Object.values(f).every(Boolean) && !report.selfContained.externalElements.length && !report.selfContained.cssImports && !report.selfContained.externalCssUrls && !report.selfContained.draft;
    report.designContractOK = report.pages.every(p=>p.design.ok);
    report.restyle = report.pages.some(p=>p.brand.restyle);
    report.brandOK = report.pages.every(p=>p.brand.ok);
    report.warnings = report.pages.flatMap(p=>p.warnings.map(w=>({page:p.page,...w})));
    report.ok = report.technicalOK && report.designContractOK && report.brandOK;
    report.automatedOK = report.ok; // Preserve the existing meaning of ok for callers.
    const template = reviewTemplate(path.resolve(filename), report.pages, pdf);
    fs.writeFileSync(path.join(out, 'visual-review.template.json'), JSON.stringify(template,null,2)+'\n');
    let supplied;
    try {
      if (reviewFile) supplied = JSON.parse(fs.readFileSync(path.resolve(reviewFile),'utf8'));
      report.visualReview = assessReview(template, supplied);
    } catch(e) {report.visualReview = {status:'invalid',issues:[e.message],pending:[]};}
    report.readyForDelivery = report.automatedOK && report.visualReview.status === 'passed';
    fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify({ok:report.ok,automatedOK:report.automatedOK,visualReview:report.visualReview.status,readyForDelivery:report.readyForDelivery,style:report.style,technicalOK:report.technicalOK,designContractOK:report.designContractOK,brandOK:report.brandOK,restyle:report.restyle,pages:count,layoutIssues:report.pages.reduce((sum,p)=>sum+p.issues.length,0),designIssues:report.pages.reduce((sum,p)=>sum+p.design.issues.length,0),brandIssues:report.pages.reduce((sum,p)=>sum+p.brand.issues.length,0),warnings:report.warnings.length,functions:f,report:path.join(out,'report.json')},null,2));
    if (!report.ok || (reviewFile && report.visualReview.status !== 'passed')) process.exitCode=1;
  } finally {await browser.close();}
}
run().catch(e => {console.error('检查失败：'+e.message);process.exitCode=1;});
