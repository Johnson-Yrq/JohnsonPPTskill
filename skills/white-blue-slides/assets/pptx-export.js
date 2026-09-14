/* pptx-export.js · export the rendered deck as an editable PPTX with one universal font.
   No dependencies: walks each slide's DOM, measures every box in slide pixels and writes OOXML into a zip.
   Text stays text (runs keep size, weight, colour and spacing), panels and rules become shapes, ECharts become
   native charts with an embedded workbook, pictures and icons become images, speaker notes become slide notes.
   The same file is embedded by the player ("导出 PPTX") and injected by scripts/export_pptx.cjs for older decks. */
(()=>{'use strict';
 const EMU=6350,SLIDE_W=1920,SLIDE_H=1080,DEFAULT_FONT='Microsoft YaHei';
 const NS_A='http://schemas.openxmlformats.org/drawingml/2006/main',NS_P='http://schemas.openxmlformats.org/presentationml/2006/main',NS_R='http://schemas.openxmlformats.org/officeDocument/2006/relationships',NS_C='http://schemas.openxmlformats.org/drawingml/2006/chart';
 const REL='http://schemas.openxmlformats.org/officeDocument/2006/relationships/',XLINK='http://www.w3.org/1999/xlink',SVG='http://www.w3.org/2000/svg';
 const SKIP='script,style,template,noscript,.chart-editor,.chart-config,.toolbar,#notes-panel,#status,[hidden]';
 const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
 const emu=v=>Math.round(v*EMU);
 const pt100=v=>Math.round(v*50); // px → hundredths of a point (1920 px = 960 pt)
 const cs=(el,pseudo)=>getComputedStyle(el,pseudo||null);
 const num=v=>{const n=parseFloat(v);return Number.isFinite(n)?n:0};

 /* ---- colours, gradients, shadows ---- */
 function color(str){
  const m=/^rgba?\(([^)]+)\)$/.exec((str||'').trim());if(!m)return null;
  const p=m[1].split(/[\s,\/]+/).filter(Boolean).map(Number),a=p.length>3?p[3]:1;
  if(!(a>0))return null;
  return {hex:p.slice(0,3).map(v=>Math.max(0,Math.min(255,Math.round(v))).toString(16).padStart(2,'0')).join('').toUpperCase(),a};
 }
 const clr=c=>`<a:srgbClr val="${c.hex}">${c.a<1?`<a:alpha val="${Math.round(c.a*100000)}"/>`:''}</a:srgbClr>`;
 const fill=c=>`<a:solidFill>${clr(c)}</a:solidFill>`;
 function hexOf(value,fallback){
  const v=(value||'').trim();
  if(/^#[0-9a-f]{6}$/i.test(v))return v.slice(1).toUpperCase();
  if(/^#[0-9a-f]{3}$/i.test(v))return v.slice(1).split('').map(ch=>ch+ch).join('').toUpperCase();
  const c=color(v);return c?c.hex:fallback;
 }
 function gradient(image){
  const m=/^linear-gradient\((.*)\)$/s.exec((image||'').trim());if(!m)return null;
  const parts=m[1].split(/,(?![^(]*\))/).map(s=>s.trim());
  let angle=180;
  if(/^-?[\d.]+deg$/.test(parts[0]))angle=num(parts.shift());
  else if(/^to /.test(parts[0])){const dir=parts.shift();angle={'to top':0,'to right':90,'to bottom':180,'to left':270}[dir]??180}
  const stops=parts.map((p,i)=>{const cm=/^(rgba?\([^)]*\))\s*([\d.]+%)?/.exec(p);const c=cm&&color(cm[1]);if(!c)return null;const pos=cm[2]?num(cm[2]):i/(parts.length-1)*100;return {c,pos}}).filter(Boolean);
  return stops.length>=2?{angle,stops}:null;
 }
 const gradXml=g=>`<a:gradFill rotWithShape="1"><a:gsLst>${g.stops.map(s=>`<a:gs pos="${Math.round(s.pos*1000)}">${clr(s.c)}</a:gs>`).join('')}</a:gsLst><a:lin ang="${Math.round((((g.angle-90)%360)+360)%360*60000)}" scaled="0"/></a:gradFill>`;
 function shadowOf(value){
  if(!value||value==='none')return null;
  for(const part of value.split(/,(?![^(]*\))/)){
   if(/inset/.test(part))continue;
   const m=/^\s*(rgba?\([^)]*\))\s+(-?[\d.]+)px\s+(-?[\d.]+)px(?:\s+(-?[\d.]+)px)?/.exec(part);
   if(!m)continue;
   const c=color(m[1]),x=num(m[2]),y=num(m[3]),blur=num(m[4]);
   if(!c||(!x&&!y&&!blur))continue;
   return {c,blur,dist:Math.hypot(x,y),dir:Math.round(((Math.atan2(y,x)*180/Math.PI)+360)%360*60000)};
  }
  return null;
 }

 /* ---- zip writer (deflate through CompressionStream when available, otherwise stored) ---- */
 const CRC_TABLE=(()=>{const t=new Uint32Array(256);for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;t[n]=c>>>0}return t})();
 function crc32(bytes){let c=0xFFFFFFFF;for(let i=0;i<bytes.length;i++)c=CRC_TABLE[(c^bytes[i])&0xFF]^(c>>>8);return (c^0xFFFFFFFF)>>>0}
 async function deflate(bytes){
  if(typeof CompressionStream!=='function')return null;
  try{return new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new CompressionStream('deflate-raw'))).arrayBuffer())}catch{return null}
 }
 async function zip(entries){
  const enc=new TextEncoder(),chunks=[],central=[];let offset=0;
  const now=new Date(),time=(now.getHours()<<11)|(now.getMinutes()<<5)|(now.getSeconds()>>1),date=((now.getFullYear()-1980)<<9)|((now.getMonth()+1)<<5)|now.getDate();
  for(const e of entries){
   const name=enc.encode(e.name),data=e.data instanceof Uint8Array?e.data:enc.encode(e.data),crc=crc32(data);
   let method=0,body=data;
   if(e.compress!==false&&data.length>80){const d=await deflate(data);if(d&&d.length<data.length){method=8;body=d}}
   const head=new DataView(new ArrayBuffer(30));
   head.setUint32(0,0x04034b50,true);head.setUint16(4,20,true);head.setUint16(6,0x0800,true);head.setUint16(8,method,true);head.setUint16(10,time,true);head.setUint16(12,date,true);
   head.setUint32(14,crc,true);head.setUint32(18,body.length,true);head.setUint32(22,data.length,true);head.setUint16(26,name.length,true);head.setUint16(28,0,true);
   chunks.push(new Uint8Array(head.buffer),name,body);
   const cd=new DataView(new ArrayBuffer(46));
   cd.setUint32(0,0x02014b50,true);cd.setUint16(4,20,true);cd.setUint16(6,20,true);cd.setUint16(8,0x0800,true);cd.setUint16(10,method,true);cd.setUint16(12,time,true);cd.setUint16(14,date,true);
   cd.setUint32(16,crc,true);cd.setUint32(20,body.length,true);cd.setUint32(24,data.length,true);cd.setUint16(28,name.length,true);cd.setUint32(42,offset,true);
   central.push(new Uint8Array(cd.buffer),name);
   offset+=30+name.length+body.length;
  }
  const cdSize=central.reduce((n,c)=>n+c.length,0),end=new DataView(new ArrayBuffer(22));
  end.setUint32(0,0x06054b50,true);end.setUint16(8,entries.length,true);end.setUint16(10,entries.length,true);end.setUint32(12,cdSize,true);end.setUint32(16,offset,true);
  const all=[...chunks,...central,new Uint8Array(end.buffer)],out=new Uint8Array(all.reduce((n,c)=>n+c.length,0));
  let pos=0;for(const c of all){out.set(c,pos);pos+=c.length}
  return out;
 }
 const b64=s=>{const bin=atob(s),out=new Uint8Array(bin.length);for(let i=0;i<bin.length;i++)out[i]=bin.charCodeAt(i);return out};
 const DATA_URL=/^data:(image\/[a-z+]+);base64,(.*)$/s;

 /* ---- OOXML fragments ---- */
 const xfrm=r=>`<a:xfrm><a:off x="${emu(r.x)}" y="${emu(r.y)}"/><a:ext cx="${Math.max(1,emu(r.w))}" cy="${Math.max(1,emu(r.h))}"/></a:xfrm>`;
 const rels=list=>`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">${list.map((r,i)=>`<Relationship Id="rId${i+1}" Type="${r.type}" Target="${esc(r.target)}"${r.mode?` TargetMode="${r.mode}"`:''}/>`).join('')}</Relationships>`;
 const XML_HEAD='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>';
 const NS_PRES=`xmlns:a="${NS_A}" xmlns:r="${NS_R}" xmlns:p="${NS_P}"`;
 const EMPTY_TREE='<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>';
 const CLR_MAP='<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>';
 function themeXml(font,name){
  const scheme=[['dk1','2B3140'],['lt1','FFFFFF'],['dk2','1D3446'],['lt2','F7F6F2'],['accent1','3B7BC8'],['accent2','477F80'],['accent3','BC9B59'],['accent4','5A6373'],['accent5','9DBDE3'],['accent6','E7EEF6'],['hlink','3B7BC8'],['folHlink','5A6373']];
  const fonts=`<a:latin typeface="${esc(font)}"/><a:ea typeface="${esc(font)}"/><a:cs typeface=""/>`;
  return `${XML_HEAD}<a:theme xmlns:a="${NS_A}" name="${esc(name)}"><a:themeElements><a:clrScheme name="deck">${scheme.map(([k,v])=>`<a:${k}><a:srgbClr val="${v}"/></a:${k}>`).join('')}</a:clrScheme><a:fontScheme name="deck"><a:majorFont>${fonts}</a:majorFont><a:minorFont>${fonts}</a:minorFont></a:fontScheme><a:fmtScheme name="deck"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>`;
 }
 const lineHeightOf=st=>{const lh=parseFloat(st.lineHeight);return Number.isFinite(lh)?lh:num(st.fontSize)*1.4};
 function contentText(value){
  const v=(value||'').trim();
  const m=/^(["'])(.*)\1$/s.exec(v);if(!m)return '';
  return m[2].replace(/\\([0-9a-fA-F]{1,6}) ?/g,(_,h)=>String.fromCodePoint(parseInt(h,16))).replace(/\\(.)/g,'$1');
 }
 let measureCtx;
 function measureText(text,font){
  measureCtx=measureCtx||document.createElement('canvas').getContext('2d');
  try{measureCtx.font=font}catch{}
  return measureCtx.measureText(text).width;
 }

 /* ---- native charts (bar / line / donut) with an embedded workbook ---- */
 const colLetter=i=>String.fromCharCode(65+i);
 async function workbook(data){
  const cell=(ref,v)=>typeof v==='number'?`<c r="${ref}"><v>${v}</v></c>`:`<c r="${ref}" t="inlineStr"><is><t>${esc(v)}</t></is></c>`;
  let rows=`<row r="1">${data.series.map((s,i)=>cell(colLetter(i+1)+'1',s.name)).join('')}</row>`;
  data.categories.forEach((c,i)=>{rows+=`<row r="${i+2}">${cell('A'+(i+2),c)}${data.series.map((s,j)=>cell(colLetter(j+1)+(i+2),Number(s.values[i]))).join('')}</row>`});
  const ct=`${XML_HEAD}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>`;
  const wb=`${XML_HEAD}<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="${NS_R}"><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>`;
  const styles=`${XML_HEAD}<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>`;
  const sheet=`${XML_HEAD}<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${rows}</sheetData></worksheet>`;
  return zip([
   {name:'[Content_Types].xml',data:ct},
   {name:'_rels/.rels',data:rels([{type:REL+'officeDocument',target:'xl/workbook.xml'}])},
   {name:'xl/workbook.xml',data:wb},
   {name:'xl/_rels/workbook.xml.rels',data:rels([{type:REL+'worksheet',target:'worksheets/sheet1.xml'},{type:REL+'styles',target:'styles.xml'}])},
   {name:'xl/styles.xml',data:styles},
   {name:'xl/worksheets/sheet1.xml',data:sheet}
  ]);
 }
 function chartXml(data,o,frame){
  const n=data.categories.length,single=data.series.length===1,horizontal=data.chart_type==='bar',donut=data.chart_type==='donut';
  // Mirror the ECharts geometry (charts.js): grid insets for axes charts, centre 32 % / radius 83 % for the ring.
  const fx=v=>Math.max(0,Math.min(1,v)).toFixed(4);
  let inner;
  if(donut){const d=.83*Math.min(frame.w,frame.h);inner={x:(.32*frame.w-d/2)/frame.w,y:(.5*frame.h-d/2)/frame.h,w:d/frame.w,h:d/frame.h}}
  else{const legend=!single,left=horizontal?100:55,right=horizontal?88:48,top=(horizontal?12:46)+(legend?38:0),bottom=(horizontal&&!single?58:32)+12;inner={x:left/frame.w,y:top/frame.h,w:(frame.w-left-right)/frame.w,h:(frame.h-top-bottom)/frame.h}}
  const layout=`<c:layout><c:manualLayout><c:layoutTarget val="inner"/><c:xMode val="edge"/><c:yMode val="edge"/><c:x val="${fx(inner.x)}"/><c:y val="${fx(inner.y)}"/><c:w val="${fx(inner.w)}"/><c:h val="${fx(inner.h)}"/></c:manualLayout></c:layout>`;
  const txPr=(sz,hex,extra='')=>`<c:txPr><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="${sz}"${extra}><a:solidFill><a:srgbClr val="${hex}"/></a:solidFill><a:latin typeface="${esc(o.font)}"/><a:ea typeface="${esc(o.font)}"/></a:defRPr></a:pPr><a:endParaRPr lang="zh-CN"/></a:p></c:txPr>`;
  const strCache=values=>`<c:strCache><c:ptCount val="${values.length}"/>${values.map((v,i)=>`<c:pt idx="${i}"><c:v>${esc(v)}</c:v></c:pt>`).join('')}</c:strCache>`;
  const numCache=values=>`<c:numCache><c:formatCode>General</c:formatCode><c:ptCount val="${values.length}"/>${values.map((v,i)=>`<c:pt idx="${i}"><c:v>${Number(v)}</c:v></c:pt>`).join('')}</c:numCache>`;
  const cat=`<c:cat><c:strRef><c:f>Sheet1!$A$2:$A$${n+1}</c:f>${strCache(data.categories)}</c:strRef></c:cat>`;
  const unitFmt=data.unit?` formatCode="General&quot; ${esc(data.unit)}&quot;" sourceLinked="0"`:' formatCode="General" sourceLinked="1"';
  const labels=(hex,pos,percent)=>`<c:dLbls><c:numFmt${percent?' formatCode="0%" sourceLinked="0"':unitFmt}/><c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>${txPr(1050,hex)}${pos?`<c:dLblPos val="${pos}"/>`:''}<c:showLegendKey val="0"/><c:showVal val="${percent?0:1}"/><c:showCatName val="0"/><c:showSerName val="0"/><c:showPercent val="${percent?1:0}"/><c:showBubbleSize val="0"/></c:dLbls>`;
  const series=data.series.map((s,i)=>{
   const hex=o.colors[i%o.colors.length],col=colLetter(i+1);
   const tx=`<c:tx><c:strRef><c:f>Sheet1!$${col}$1</c:f>${strCache([s.name])}</c:strRef></c:tx>`;
   const val=`<c:val><c:numRef><c:f>Sheet1!$${col}$2:$${col}$${n+1}</c:f>${numCache(s.values)}</c:numRef></c:val>`;
   if(donut){
    const pts=data.categories.map((_,j)=>`<c:dPt><c:idx val="${j}"/><c:bubble3D val="0"/><c:spPr><a:solidFill><a:srgbClr val="${o.colors[j%o.colors.length]}"/></a:solidFill><a:ln><a:noFill/></a:ln></c:spPr></c:dPt>`).join('');
    return `<c:ser><c:idx val="${i}"/><c:order val="${i}"/>${tx}${pts}${labels('FFFFFF',null,true)}${cat}${val}</c:ser>`;
   }
   if(data.chart_type==='line'){
    return `<c:ser><c:idx val="${i}"/><c:order val="${i}"/>${tx}<c:spPr><a:ln w="${emu(3)}" cap="rnd"><a:solidFill><a:srgbClr val="${hex}"/></a:solidFill><a:round/></a:ln></c:spPr><c:marker><c:symbol val="circle"/><c:size val="5"/><c:spPr><a:solidFill><a:srgbClr val="${hex}"/></a:solidFill><a:ln><a:noFill/></a:ln></c:spPr></c:marker>${single?labels(hex,'t'):''}${cat}${val}<c:smooth val="0"/></c:ser>`;
   }
   return `<c:ser><c:idx val="${i}"/><c:order val="${i}"/>${tx}<c:spPr><a:solidFill><a:srgbClr val="${hex}"/></a:solidFill></c:spPr><c:invertIfNegative val="0"/>${single?labels(hex,horizontal?'outEnd':'outEnd'):''}${cat}${val}</c:ser>`;
  }).join('');
  let plot;
  if(donut)plot=`<c:doughnutChart><c:varyColors val="1"/>${series}<c:firstSliceAng val="0"/><c:holeSize val="66"/></c:doughnutChart>`;
  else{
   const axes='<c:axId val="10"/><c:axId val="20"/>';
   const kind=data.chart_type==='line'?`<c:lineChart><c:grouping val="standard"/><c:varyColors val="0"/>${series}<c:marker val="1"/>${axes}</c:lineChart>`:`<c:barChart><c:barDir val="${horizontal?'bar':'col'}"/><c:grouping val="clustered"/><c:varyColors val="0"/>${series}<c:gapWidth val="${single?150:80}"/>${axes}</c:barChart>`;
   const axisText=txPr(1050,o.muted);
   const unitTitle=!single&&data.unit?`<c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="1050" b="0"><a:solidFill><a:srgbClr val="${o.muted}"/></a:solidFill><a:latin typeface="${esc(o.font)}"/><a:ea typeface="${esc(o.font)}"/></a:defRPr></a:pPr><a:r><a:rPr lang="zh-CN" sz="1050" b="0"/><a:t>${esc(data.unit)}</a:t></a:r></a:p></c:rich></c:tx><c:overlay val="0"/></c:title>`:'';
   const catAx=`<c:catAx><c:axId val="10"/><c:scaling><c:orientation val="${horizontal?'maxMin':'minMax'}"/></c:scaling><c:delete val="0"/><c:axPos val="${horizontal?'l':'b'}"/><c:numFmt formatCode="General" sourceLinked="1"/><c:majorTickMark val="none"/><c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/><c:spPr><a:ln><a:noFill/></a:ln></c:spPr>${axisText}<c:crossAx val="20"/><c:crosses val="autoZero"/><c:auto val="1"/><c:lblAlgn val="ctr"/><c:lblOffset val="100"/><c:noMultiLvlLbl val="0"/></c:catAx>`;
   const valAx=`<c:valAx><c:axId val="20"/><c:scaling><c:orientation val="minMax"/><c:min val="0"/></c:scaling><c:delete val="0"/><c:axPos val="${horizontal?'b':'l'}"/><c:majorGridlines><c:spPr><a:ln w="${emu(1)}"><a:solidFill><a:srgbClr val="${o.grid}"/></a:solidFill><a:prstDash val="dash"/></a:ln></c:spPr></c:majorGridlines>${unitTitle}<c:numFmt formatCode="General" sourceLinked="1"/><c:majorTickMark val="none"/><c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/><c:spPr><a:ln><a:noFill/></a:ln></c:spPr>${axisText}<c:crossAx val="10"/><c:crosses val="${horizontal?'max':'autoZero'}"/><c:crossBetween val="between"/></c:valAx>`;
   plot=kind+catAx+valAx;
  }
  const legend=donut||!single?`<c:legend><c:legendPos val="${donut?'r':'t'}"/><c:overlay val="0"/>${txPr(1050,o.muted)}</c:legend>`:'';
  return `${XML_HEAD}<c:chartSpace xmlns:c="${NS_C}" xmlns:a="${NS_A}" xmlns:r="${NS_R}"><c:date1904 val="0"/><c:lang val="zh-CN"/><c:roundedCorners val="0"/><c:chart><c:autoTitleDeleted val="1"/><c:plotArea>${layout}${plot}<c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr></c:plotArea>${legend}<c:plotVisOnly val="1"/><c:dispBlanksAs val="gap"/></c:chart><c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>${txPr(1050,o.muted)}<c:externalData r:id="rId1"><c:autoUpdate val="0"/></c:externalData></c:chartSpace>`;
 }

 /* ---- package: parts, media, slides ---- */
 class Package{
  constructor(font){this.font=font;this.slides=[];this.media=new Map();this.mediaCount=0;this.charts=0;this.parts=[];this.stats={texts:0,shapes:0,images:0,charts:0,notes:0};this.warnings=[]}
  addMedia(key,mime,bytes){
   if(this.media.has(key))return this.media.get(key);
   const ext=mime==='image/png'?'png':'jpeg',name=`image${++this.mediaCount}.${ext}`;
   const m={target:`../media/${name}`,bytes};
   this.media.set(key,m);this.parts.push({name:`ppt/media/${name}`,data:bytes,compress:false});
   return m;
  }
  async addChart(data,palette,frame){
   const n=++this.charts;
   this.parts.push({name:`ppt/charts/chart${n}.xml`,data:chartXml(data,palette,frame)},
    {name:`ppt/charts/_rels/chart${n}.xml.rels`,data:rels([{type:REL+'package',target:`../embeddings/Microsoft_Excel_Sheet${n}.xlsx`}])},
    {name:`ppt/embeddings/Microsoft_Excel_Sheet${n}.xlsx`,data:await workbook(data),compress:false});
   return `../charts/chart${n}.xml`;
  }
  async pictureFromImg(el,st,paper){
   const src=el.currentSrc||el.src||'',fade=num(st.getPropertyValue('--image-fade'));
   const masked=fade>0&&((st.maskImage||st.webkitMaskImage||'none')!=='none');
   const key=src+'|'+(masked?fade:0);
   if(this.media.has(key))return this.media.get(key);
   const m=DATA_URL.exec(src);
   if(m&&!masked&&(m[1]==='image/png'||m[1]==='image/jpeg'))return this.addMedia(key,m[1],b64(m[2]));
   const nw=el.naturalWidth,nh=el.naturalHeight;if(!nw||!nh)return null;
   const k=Math.min(1,2048/Math.max(nw,nh)),w=Math.max(1,Math.round(nw*k)),h=Math.max(1,Math.round(nh*k));
   const c=document.createElement('canvas');c.width=w;c.height=h;const ctx=c.getContext('2d');
   ctx.drawImage(el,0,0,w,h);
   if(masked){
    ctx.globalCompositeOperation='destination-in';
    for(const vertical of [false,true]){
     const g=vertical?ctx.createLinearGradient(0,0,0,h):ctx.createLinearGradient(0,0,w,0);
     g.addColorStop(0,'rgba(0,0,0,0)');g.addColorStop(Math.min(.49,fade/100),'#000');g.addColorStop(Math.max(.51,1-fade/100),'#000');g.addColorStop(1,'rgba(0,0,0,0)');
     ctx.fillStyle=g;ctx.fillRect(0,0,w,h);
    }
    ctx.globalCompositeOperation='source-over';
   }
   const png=!!m&&m[1]==='image/png';
   let out=c;
   if(!png){out=document.createElement('canvas');out.width=w;out.height=h;const o=out.getContext('2d');o.fillStyle=paper;o.fillRect(0,0,w,h);o.drawImage(c,0,0)}
   let url;
   try{url=png?out.toDataURL('image/png'):out.toDataURL('image/jpeg',.92)}catch{this.warnings.push('图片无法读取（非内嵌数据）：'+src.slice(0,60));return null}
   const mm=DATA_URL.exec(url);
   return this.addMedia(key,mm[1],b64(mm[2]));
  }
  async pictureFromSvg(el,st,box){
   const href=u=>u.getAttribute('href')||u.getAttributeNS(XLINK,'href');
   const uses=[...el.querySelectorAll('use')];
   if(uses.length===1&&el.children.length===1){
    const sym=href(uses[0])&&/^#/.test(href(uses[0]))&&document.getElementById(href(uses[0]).slice(1));
    const image=sym&&sym.children.length===1&&sym.querySelector('image');
    const m=image&&DATA_URL.exec(href(image)||'');
    if(m&&(m[1]==='image/png'||m[1]==='image/jpeg'))return this.addMedia(href(image),m[1],b64(m[2]));
   }
   const clone=el.cloneNode(true);
   clone.querySelectorAll('use').forEach(u=>{
    const ref=href(u),sym=ref&&/^#/.test(ref)&&document.getElementById(ref.slice(1));if(!sym)return;
    const inner=document.createElementNS(SVG,'svg');
    for(const a of ['viewBox','preserveAspectRatio'])if(sym.hasAttribute(a))inner.setAttribute(a,sym.getAttribute(a));
    for(const a of ['x','y','width','height'])if(u.hasAttribute(a))inner.setAttribute(a,u.getAttribute(a));
    inner.innerHTML=sym.innerHTML;u.replaceWith(inner);
   });
   const scale=3,w=Math.max(1,Math.round(box.w*scale)),h=Math.max(1,Math.round(box.h*scale));
   clone.setAttribute('xmlns',SVG);clone.setAttribute('width',w);clone.setAttribute('height',h);clone.removeAttribute('class');clone.removeAttribute('style');
   if(!clone.hasAttribute('viewBox'))clone.setAttribute('viewBox',`0 0 ${box.w} ${box.h}`);
   clone.setAttribute('color',st.color);
   if(st.stroke&&st.stroke!=='none')clone.setAttribute('stroke',st.stroke);
   if(st.fill&&clone.getAttribute('fill')==='currentColor')clone.setAttribute('fill',st.fill);
   if(num(st.strokeWidth))clone.setAttribute('stroke-width',num(st.strokeWidth));
   const markup=new XMLSerializer().serializeToString(clone),key='svg:'+w+'x'+h+':'+markup;
   if(this.media.has(key))return this.media.get(key);
   const img=new Image();
   const ok=await new Promise(res=>{img.onload=()=>res(true);img.onerror=()=>res(false);img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(markup)});
   if(!ok)return null;
   const c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').drawImage(img,0,0,w,h);
   let url;try{url=c.toDataURL('image/png')}catch{return null}
   return this.addMedia(key,'image/png',b64(DATA_URL.exec(url)[2]));
  }
  async addSlide(slideEl,index){
   const walker=new SlideWalker(this,slideEl,index);
   await walker.run();
   this.slides.push(walker.entry);
  }
  async finish(){
   const font=this.font,parts=[];
   const slideOverrides=[],presRels=[{type:REL+'slideMaster',target:'slideMasters/slideMaster1.xml'},{type:REL+'notesMaster',target:'notesMasters/notesMaster1.xml'}];
   const sldIds=[];
   this.slides.forEach((s,i)=>{
    const n=i+1,slideRels=[{type:REL+'slideLayout',target:'../slideLayouts/slideLayout1.xml'},...s.rels];
    if(s.notes){
     this.stats.notes++;
     slideRels.push({type:REL+'notesSlide',target:`../notesSlides/notesSlide${n}.xml`});
     const paras=s.notes.split(/\r?\n/).map(line=>`<a:p><a:r><a:rPr lang="zh-CN" sz="1200"/><a:t>${esc(line)}</a:t></a:r></a:p>`).join('');
     parts.push({name:`ppt/notesSlides/notesSlide${n}.xml`,data:`${XML_HEAD}<p:notes ${NS_PRES}><p:cSld><p:spTree>${EMPTY_TREE}<p:sp><p:nvSpPr><p:cNvPr id="2" name="讲稿"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="685800" y="4343400"/><a:ext cx="5486400" cy="4114800"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr><p:txBody><a:bodyPr/><a:lstStyle/>${paras}</p:txBody></p:sp></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>`},
      {name:`ppt/notesSlides/_rels/notesSlide${n}.xml.rels`,data:rels([{type:REL+'notesMaster',target:'../notesMasters/notesMaster1.xml'},{type:REL+'slide',target:`../slides/slide${n}.xml`}])});
     slideOverrides.push(`<Override PartName="/ppt/notesSlides/notesSlide${n}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>`);
    }
    parts.push({name:`ppt/slides/slide${n}.xml`,data:`${XML_HEAD}<p:sld ${NS_PRES}><p:cSld name="${esc(s.name)}"><p:bg><p:bgPr><a:solidFill><a:srgbClr val="${s.paper}"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree>${EMPTY_TREE}${s.shapes}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>`},
     {name:`ppt/slides/_rels/slide${n}.xml.rels`,data:rels(slideRels)});
    slideOverrides.push(`<Override PartName="/ppt/slides/slide${n}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>`);
    presRels.push({type:REL+'slide',target:`slides/slide${n}.xml`});
    sldIds.push(`<p:sldId id="${256+i}" r:id="rId${presRels.length}"/>`);
   });
   presRels.push({type:REL+'theme',target:'theme/theme1.xml'});
   const chartOverrides=[];for(let i=1;i<=this.charts;i++)chartOverrides.push(`<Override PartName="/ppt/charts/chart${i}.xml" ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/>`);
   parts.push(
    {name:'[Content_Types].xml',data:`${XML_HEAD}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="jpeg" ContentType="image/jpeg"/><Default Extension="xlsx" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/><Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/><Override PartName="/ppt/notesMasters/notesMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"/><Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/><Override PartName="/ppt/theme/theme2.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>${slideOverrides.join('')}${chartOverrides.join('')}</Types>`},
    {name:'_rels/.rels',data:rels([{type:REL+'officeDocument',target:'ppt/presentation.xml'}])},
    {name:'ppt/presentation.xml',data:`${XML_HEAD}<p:presentation ${NS_PRES} saveSubsetFonts="1"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:notesMasterIdLst><p:notesMasterId r:id="rId2"/></p:notesMasterIdLst><p:sldIdLst>${sldIds.join('')}</p:sldIdLst><p:sldSz cx="${SLIDE_W*EMU}" cy="${SLIDE_H*EMU}"/><p:notesSz cx="6858000" cy="9144000"/><p:defaultTextStyle><a:defPPr><a:defRPr lang="zh-CN"/></a:defPPr></p:defaultTextStyle></p:presentation>`},
    {name:'ppt/_rels/presentation.xml.rels',data:rels(presRels)},
    {name:'ppt/slideMasters/slideMaster1.xml',data:`${XML_HEAD}<p:sldMaster ${NS_PRES}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg><p:spTree>${EMPTY_TREE}</p:spTree></p:cSld>${CLR_MAP}<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz="4400"/></a:lvl1pPr></p:titleStyle><p:bodyStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:bodyStyle><p:otherStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:otherStyle></p:txStyles></p:sldMaster>`},
    {name:'ppt/slideMasters/_rels/slideMaster1.xml.rels',data:rels([{type:REL+'slideLayout',target:'../slideLayouts/slideLayout1.xml'},{type:REL+'theme',target:'../theme/theme1.xml'}])},
    {name:'ppt/slideLayouts/slideLayout1.xml',data:`${XML_HEAD}<p:sldLayout ${NS_PRES} type="blank" preserve="1"><p:cSld name="Blank"><p:spTree>${EMPTY_TREE}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>`},
    {name:'ppt/slideLayouts/_rels/slideLayout1.xml.rels',data:rels([{type:REL+'slideMaster',target:'../slideMasters/slideMaster1.xml'}])},
    {name:'ppt/notesMasters/notesMaster1.xml',data:`${XML_HEAD}<p:notesMaster ${NS_PRES}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg><p:spTree>${EMPTY_TREE}</p:spTree></p:cSld>${CLR_MAP}<p:notesStyle><a:lvl1pPr><a:defRPr sz="1200"/></a:lvl1pPr></p:notesStyle></p:notesMaster>`},
    {name:'ppt/notesMasters/_rels/notesMaster1.xml.rels',data:rels([{type:REL+'theme',target:'../theme/theme2.xml'}])},
    {name:'ppt/theme/theme1.xml',data:themeXml(font,'deck')},
    {name:'ppt/theme/theme2.xml',data:themeXml(font,'notes')},
    ...this.parts
   );
   return zip(parts);
  }
 }

 /* ---- one slide: walk the DOM in paint order and emit shapes ---- */
 class SlideWalker{
  constructor(pkg,slide,index){
   this.pkg=pkg;this.slide=slide;this.index=index;this.id=1;this.items=[];this.zCache=new WeakMap();
   this.rect=slide.getBoundingClientRect();this.scale=this.rect.width/SLIDE_W||1;
   const paper=color(cs(slide).backgroundColor)||{hex:'FFFFFF',a:1};
   this.paper='#'+paper.hex;
   const title=slide.querySelector('h1');
   this.entry={name:(title?title.textContent.trim():'')||`第 ${index+1} 页`,paper:paper.hex,rels:[],notes:(slide.dataset.speakerNotes||'').trim(),shapes:''};
  }
  map(r){return {x:(r.left-this.rect.left)/this.scale,y:(r.top-this.rect.top)/this.scale,w:r.width/this.scale,h:r.height/this.scale}}
  rel(type,target){let i=this.entry.rels.findIndex(r=>r.type===type&&r.target===target);if(i<0){this.entry.rels.push({type,target});i=this.entry.rels.length-1}return `rId${i+2}`}
  zOf(el){
   if(this.zCache.has(el))return this.zCache.get(el);
   let z=0;
   for(let a=el;a&&a!==this.slide;a=a.parentElement){const s=cs(a);if(s.position!=='static'&&s.zIndex!=='auto'){z=parseInt(s.zIndex,10)||0;break}}
   this.zCache.set(el,z);return z;
  }
  push(el,xml){this.items.push({z:this.zOf(el),n:this.items.length,xml})}
  // transform: scale() on an ancestor (architecture artboards) changes rendered size but not computed styles
  zoomOf(el){const host=el instanceof SVGElement?el.parentElement:el;if(!host||!host.offsetWidth)return 1;const k=(host.getBoundingClientRect().width/this.scale)/host.offsetWidth;return Number.isFinite(k)&&k>0&&Math.abs(k-1)>.02?k:1}
  skip(el,st){return el.matches(SKIP)||st.display==='none'||st.visibility==='hidden'||num(st.opacity)===0&&st.opacity!==''}
  async run(){
   for(const child of this.slide.children)await this.walk(child);
   this.pseudo(this.slide,'::before');this.pseudo(this.slide,'::after');
   this.entry.shapes=this.items.sort((a,b)=>a.z-b.z||a.n-b.n).map(i=>i.xml).join('');
  }
  async walk(el){
   const st=cs(el);
   if(this.skip(el,st))return;
   if(el.tagName==='IMG'){await this.image(el,st);return}
   if(el.matches('.echart')){await this.chart(el);return}
   if(el instanceof SVGSVGElement){await this.svg(el,st);return}
   const r=this.map(el.getBoundingClientRect()),z=this.zoomOf(el);
   this.box(el,st,r,el.dataset.component||el.className&&String(el.className).split(' ')[0]||el.tagName.toLowerCase(),z);
   const kids=[...el.childNodes];
   const inlineLevel=n=>n.nodeType===3||n.tagName==='BR'||(n.nodeType===1&&!(n instanceof SVGElement)&&n.tagName!=='IMG'&&cs(n).display==='inline');
   const mixed=kids.some(n=>n.nodeType===1&&!inlineLevel(n)&&!this.skip(n,cs(n)));
   let inline=[];
   const flush=()=>{if(inline.length){this.text(el,st,inline,mixed,z);inline=[]}};
   for(const n of kids){
    if(n.nodeType===3){if(n.data.trim()||inline.length)inline.push(n);continue}
    if(n.nodeType!==1)continue;
    if(inlineLevel(n))inline.push(n);else{flush();await this.walk(n)}
   }
   flush();
   this.pseudo(el,'::before');this.pseudo(el,'::after');
  }
  box(el,st,r,name,z=1){
   if(r.w<=.5||r.h<=.5)return;
   const bg=color(st.backgroundColor),grad=gradient(st.backgroundImage),shadow=shadowOf(st.boxShadow);
   if(shadow){shadow.blur*=z;shadow.dist*=z}
   const sides=['Top','Right','Bottom','Left'].map(s=>{const w=num(st['border'+s+'Width'])*z,c=color(st['border'+s+'Color']),style=st['border'+s+'Style'];return w>0&&style!=='none'&&style!=='hidden'&&c?{w,c,style}:null});
   const uniform=sides.every(s=>s&&s.w===sides[0].w&&s.c.hex===sides[0].c.hex&&s.c.a===sides[0].c.a&&s.style===sides[0].style);
   const radius=[st.borderTopLeftRadius,st.borderTopRightRadius,st.borderBottomRightRadius,st.borderBottomLeftRadius].map(v=>num(v)*z);
   if(bg||grad||uniform||shadow){
    const ss=Math.min(r.w,r.h),adj=v=>Math.round(Math.min(50000,v/ss*100000));
    let geom='<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>';
    if(radius.some(v=>v>0)){
     if(radius.every(v=>v===radius[0]))geom=`<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val ${adj(radius[0])}"/></a:avLst></a:prstGeom>`;
     else if(radius[0]===radius[1]&&!radius[2]&&!radius[3])geom=`<a:prstGeom prst="round2SameRect"><a:avLst><a:gd name="adj1" fmla="val ${adj(radius[0])}"/><a:gd name="adj2" fmla="val 0"/></a:avLst></a:prstGeom>`;
     else geom=`<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val ${adj(Math.max(...radius))}"/></a:avLst></a:prstGeom>`;
    }
    const fillXml=grad?gradXml(grad):bg?fill(bg):'<a:noFill/>';
    const ln=uniform?`<a:ln w="${emu(sides[0].w)}">${fill(sides[0].c)}${sides[0].style==='dashed'?'<a:prstDash val="dash"/>':sides[0].style==='dotted'?'<a:prstDash val="sysDot"/>':''}</a:ln>`:'<a:ln><a:noFill/></a:ln>';
    const effect=shadow?`<a:effectLst><a:outerShdw blurRad="${emu(shadow.blur)}" dist="${emu(shadow.dist)}" dir="${shadow.dir}" algn="ctr" rotWithShape="0">${clr(shadow.c)}</a:outerShdw></a:effectLst>`:'';
    this.push(el,`<p:sp><p:nvSpPr><p:cNvPr id="${++this.id}" name="${esc(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>${xfrm(r)}${geom}${fillXml}${ln}${effect}</p:spPr></p:sp>`);
    this.pkg.stats.shapes++;
   }
   if(!uniform)sides.forEach((s,i)=>{
    if(!s)return;
    const line=i===0?{x:r.x,y:r.y,w:r.w,h:s.w}:i===1?{x:r.x+r.w-s.w,y:r.y,w:s.w,h:r.h}:i===2?{x:r.x,y:r.y+r.h-s.w,w:r.w,h:s.w}:{x:r.x,y:r.y,w:s.w,h:r.h};
    this.push(el,`<p:sp><p:nvSpPr><p:cNvPr id="${++this.id}" name="${esc(name)} rule"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>${xfrm(line)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>${fill(s.c)}<a:ln><a:noFill/></a:ln></p:spPr></p:sp>`);
    this.pkg.stats.shapes++;
   });
  }
  text(el,st,nodes,mixed,z=1){
   const ws=st.whiteSpace,keepNewlines=/^pre/.test(ws),collapse=!keepNewlines||ws==='pre-line';
   const raw=[];
   const collect=(node,style)=>{
    if(node.nodeType===3){raw.push({t:node.data,st:style});return}
    if(node.nodeType!==1)return;
    if(node.tagName==='BR'){raw.push({br:true});return}
    const s=cs(node);if(s.display==='none')return;
    for(const k of node.childNodes)collect(k,s);
   };
   for(const n of nodes)collect(n,n.nodeType===3?st:cs(n));
   const runs=[];
   for(const run of raw){
    if(run.br){runs.push(run);continue}
    let t=run.t;
    if(collapse)t=t.replace(/[ \t\r\f]+/g,' ');
    if(!keepNewlines)t=t.replace(/\n/g,' ').replace(/ {2,}/g,' ');
    const pieces=keepNewlines?t.split('\n'):[t];
    pieces.forEach((piece,i)=>{if(i)runs.push({br:true});if(piece)runs.push({t:piece,st:run.st})});
   }
   let atStart=true,last=null;
   for(const run of runs){
    if(run.br){if(last)last.t=last.t.replace(/ +$/,'');atStart=true;last=null;continue}
    if(atStart||(last&&/ $/.test(last.t)))run.t=run.t.replace(/^ +/,'');
    if(run.t){atStart=false;last=run}
   }
   if(last)last.t=last.t.replace(/ +$/,'');
   const final=runs.filter(r=>r.br||r.t);
   while(final.length&&final[0].br)final.shift();
   while(final.length&&final[final.length-1].br)final.pop();
   if(!final.some(r=>r.t))return;
   let r,ins;
   if(!mixed){
    r=this.map(el.getBoundingClientRect());
    ins=['Top','Right','Bottom','Left'].map(s=>(num(st['padding'+s])+num(st['border'+s+'Width']))*z);
   }else{
    const range=document.createRange();range.setStartBefore(nodes[0]);range.setEndAfter(nodes[nodes.length-1]);
    r=this.map(range.getBoundingClientRect());
    const lh=lineHeightOf(st)*z,lines=Math.max(1,Math.round(r.h/lh));
    r={x:r.x,y:r.y-(lines*lh-r.h)/2,w:r.w,h:lines*lh};ins=[0,0,0,0];
   }
   this.emitText(el,st,r,final,ins,z);
  }
  emitText(el,st,r,runs,ins,z=1){
   if(r.w<=0||r.h<=0)return;
   const font=this.pkg.font,lh=lineHeightOf(st)*z,fs=num(st.fontSize)*z;
   let algn={left:'l',start:'l',center:'ctr',right:'r',end:'r',justify:'just'}[st.textAlign]||'l',anchor='t';
   if(/flex/.test(st.display)){
    const col=/column/.test(st.flexDirection),h=col?st.alignItems:st.justifyContent,v=col?st.justifyContent:st.alignItems;
    const pick=(value,end,mid)=>/center|space-around|space-evenly/.test(value)?mid:/end/.test(value)?end:null;
    algn=pick(h,'r','ctr')||algn;anchor=pick(v,'b','ctr')||anchor;
   }
   // The universal font sets Latin text and digits wider than the web font. A block the browser rendered on one line
   // therefore stays unwrapped (the box anchors it the same way), and a multi-line block gets a little slack.
   const lines=Math.max(1,Math.round((r.h-ins[0]-ins[2])/lh));
   const single=lines===1||st.whiteSpace==='nowrap'||st.whiteSpace==='pre';
   if(!single){const slack=Math.max(12,r.w*.06);r=algn==='ctr'?{x:r.x-slack/2,y:r.y,w:r.w+slack,h:r.h}:algn==='r'?{x:r.x-slack,y:r.y,w:r.w+slack,h:r.h}:{x:r.x,y:r.y,w:r.w+slack,h:r.h}}
   // PowerPoint centres a line's glyphs inside exact spacing the same way CSS does; the box keeps the CSS padding as insets.
   const body=`<a:bodyPr wrap="${single?'none':'square'}" lIns="${emu(ins[3])}" tIns="${emu(ins[0])}" rIns="${emu(ins[1])}" bIns="${emu(ins[2])}" rtlCol="0" anchor="${anchor}"><a:noAutofit/></a:bodyPr><a:lstStyle/>`;
   const runXml=run=>{
    if(run.br)return '<a:br/>';
    const s=run.st,c=color(s.color)||{hex:'000000',a:1},weight=parseInt(s.fontWeight,10);
    const attrs=`lang="zh-CN" altLang="en-US" sz="${Math.max(100,pt100(num(s.fontSize)*z))}"${(weight>=600||s.fontWeight==='bold')?' b="1"':''}${s.fontStyle!=='normal'?' i="1"':''}${/underline/.test(s.textDecorationLine||'')?' u="sng"':''}${/line-through/.test(s.textDecorationLine||'')?' strike="sngStrike"':''}${num(s.letterSpacing)?` spc="${pt100(num(s.letterSpacing)*z)}"`:''}`;
    return `<a:r><a:rPr ${attrs} dirty="0">${fill(c)}<a:latin typeface="${esc(font)}"/><a:ea typeface="${esc(font)}"/></a:rPr><a:t>${esc(run.t)}</a:t></a:r>`;
   };
   const para=`<a:p><a:pPr algn="${algn}"><a:lnSpc><a:spcPts val="${pt100(lh)}"/></a:lnSpc><a:spcBef><a:spcPts val="0"/></a:spcBef><a:spcAft><a:spcPts val="0"/></a:spcAft></a:pPr>${runs.map(runXml).join('')}<a:endParaRPr lang="zh-CN" sz="${Math.max(100,pt100(fs))}"/></a:p>`;
   const label=runs.filter(x=>x.t).map(x=>x.t).join('').slice(0,40);
   this.push(el,`<p:sp><p:nvSpPr><p:cNvPr id="${++this.id}" name="${esc(label)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr>${xfrm(r)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr><p:txBody>${body}${para}</p:txBody></p:sp>`);
   this.pkg.stats.texts++;
  }
  pseudo(el,which){
   const st=cs(el,which),content=st.content;
   if(!content||content==='none'||content==='normal'||st.display==='none'||st.position!=='absolute')return;
   let cb=el;while(cb!==this.slide&&cs(cb).position==='static')cb=cb.parentElement;
   const cbs=cs(cb),cbr=cb.getBoundingClientRect(),bl=num(cbs.borderLeftWidth),bt=num(cbs.borderTopWidth);
   const block={x:cbr.left+bl,y:cbr.top+bt,w:(cbr.width-bl-num(cbs.borderRightWidth))*1,h:(cbr.height-bt-num(cbs.borderBottomWidth))*1};
   const z=this.zoomOf(el),s=this.scale*z,px=v=>v==='auto'?null:num(v)*s;
   const text=contentText(content),pad=['Top','Right','Bottom','Left'].map(k=>(num(st['padding'+k])+num(st['border'+k+'Width']))*z);
   let w=px(st.width),h=px(st.height);
   const l=px(st.left),rt=px(st.right),t=px(st.top),b=px(st.bottom);
   if(w==null)w=l!=null&&rt!=null?block.w-l-rt-(pad[1]+pad[3])*this.scale:measureText(text,st.font)*s;
   if(h==null)h=t!=null&&b!=null?block.h-t-b-(pad[0]+pad[2])*this.scale:(text?lineHeightOf(st):0)*s;
   const outerW=w+(pad[1]+pad[3])*this.scale,outerH=h+(pad[0]+pad[2])*this.scale;
   const x=l!=null?block.x+l:rt!=null?block.x+block.w-rt-outerW:block.x;
   const y=t!=null?block.y+t:b!=null?block.y+block.h-b-outerH:block.y;
   const r=this.map({left:x,top:y,width:outerW,height:outerH});
   this.box(el,st,r,which,z);
   if(text.trim())this.emitText(el,st,r,[{t:text,st}],pad,z);
  }
  async image(el,st){
   const raw=el.getBoundingClientRect();if(!raw.width||!raw.height)return;
   let clip={left:this.rect.left,top:this.rect.top,right:this.rect.right,bottom:this.rect.bottom};
   for(let a=el.parentElement;a&&a!==this.slide;a=a.parentElement){
    const s=cs(a);
    if(s.overflowX!=='visible'||s.overflowY!=='visible'){const b=a.getBoundingClientRect();clip={left:Math.max(clip.left,b.left),top:Math.max(clip.top,b.top),right:Math.min(clip.right,b.right),bottom:Math.min(clip.bottom,b.bottom)}}
   }
   const vis={left:Math.max(raw.left,clip.left),top:Math.max(raw.top,clip.top),right:Math.min(raw.right,clip.right),bottom:Math.min(raw.bottom,clip.bottom)};
   if(vis.right-vis.left<1||vis.bottom-vis.top<1)return;
   const media=await this.pkg.pictureFromImg(el,st,this.paper);if(!media)return;
   const pct=(v,total)=>Math.max(0,Math.round(v/total*100000));
   const src=`<a:srcRect l="${pct(vis.left-raw.left,raw.width)}" t="${pct(vis.top-raw.top,raw.height)}" r="${pct(raw.right-vis.right,raw.width)}" b="${pct(raw.bottom-vis.bottom,raw.height)}"/>`;
   const r=this.map({left:vis.left,top:vis.top,width:vis.right-vis.left,height:vis.bottom-vis.top});
   this.picture(el,r,media,el.alt||'配图',src);
  }
  picture(el,r,media,name,src=''){
   const rId=this.rel(REL+'image',media.target);
   this.push(el,`<p:pic><p:nvPicPr><p:cNvPr id="${++this.id}" name="${esc(name.slice(0,60))}" descr="${esc(name)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="${rId}"/>${src}<a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr>${xfrm(r)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>`);
   this.pkg.stats.images++;
  }
  async svg(el,st){
   const r=this.map(el.getBoundingClientRect());if(r.w<1||r.h<1)return;
   const z=this.zoomOf(el);
   this.box(el,st,r,'icon',z);
   const pad=['Top','Right','Bottom','Left'].map(s=>(num(st['padding'+s])+num(st['border'+s+'Width']))*z);
   const inner={x:r.x+pad[3],y:r.y+pad[0],w:r.w-pad[1]-pad[3],h:r.h-pad[0]-pad[2]};
   if(inner.w<1||inner.h<1)return;
   const media=await this.pkg.pictureFromSvg(el,st,inner);if(!media)return;
   this.picture(el,inner,media,el.getAttribute('aria-label')||'图标');
  }
  async chart(host){
   const shell=host.closest('.chart-shell'),cfg=shell&&shell.querySelector('.chart-config');if(!cfg)return;
   let data;try{data=JSON.parse(cfg.textContent)}catch{return}
   if(!data||!Array.isArray(data.categories)||!Array.isArray(data.series)||!data.series.length)return;
   const r=this.map(host.getBoundingClientRect());if(r.w<1||r.h<1)return;
   const root=cs(document.documentElement),get=(k,f)=>root.getPropertyValue(k).trim()||f;
   const palette={colors:[hexOf(get('--diagram-accent',''),'477F80'),hexOf(get('--diagram-strong',''),'1D3446'),hexOf(get('--chart-tertiary',get('--saas-gold','')),'BC9B59')],muted:hexOf(get('--muted',''),'5A6373'),grid:hexOf(get('--chart-grid',''),'DAE3E1'),font:this.pkg.font};
   const rId=this.rel(REL+'chart',await this.pkg.addChart(data,palette,r));
   this.push(host,`<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="${++this.id}" name="${esc(data.title||'图表')}"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><p:xfrm><a:off x="${emu(r.x)}" y="${emu(r.y)}"/><a:ext cx="${emu(r.w)}" cy="${emu(r.h)}"/></p:xfrm><a:graphic><a:graphicData uri="${NS_C}"><c:chart xmlns:c="${NS_C}" xmlns:r="${NS_R}" r:id="${rId}"/></a:graphicData></a:graphic></p:graphicFrame>`);
   this.pkg.stats.charts++;
   if(data.chart_type==='donut'){
    // ECharts prints the total and the series name in the ring; keep them as an editable text box.
    const total=data.series[0].values.reduce((a,b)=>a+Number(b),0),d=.83*Math.min(r.w,r.h),box={x:r.x+r.w*.32-d*.3,y:r.y+r.h*.5-36,w:d*.6,h:72};
    const mk=(size,hex,weight)=>({fontSize:size+'px',color:`rgb(${parseInt(hex.slice(0,2),16)}, ${parseInt(hex.slice(2,4),16)}, ${parseInt(hex.slice(4,6),16)})`,fontWeight:weight,fontStyle:'normal',textDecorationLine:'none',letterSpacing:'0px'});
    const style={display:'block',textAlign:'center',whiteSpace:'normal',lineHeight:'40px',fontSize:'34px'};
    this.emitText(host,style,box,[{t:String(total),st:mk(34,palette.colors[1],'400')},{br:true},{t:data.series[0].name,st:mk(21,palette.muted,'400')}],[0,0,0,0]);
   }
  }
 }

 /* ---- public API ---- */
 async function build(options={}){
  const font=(options.font||DEFAULT_FONT).trim()||DEFAULT_FONT;
  const slides=[...document.querySelectorAll('.slide')];
  if(!slides.length)throw new Error('没有找到演示页面');
  if(document.querySelector('body.draft,.missing-image'))throw new Error('草稿或缺图的演示稿不能导出 PPTX，请先补齐配图');
  if(document.querySelector('.chart-shell[data-invalid]'))throw new Error('请先修正图表数据');
  await document.fonts.ready;
  const api=window.deckAPI,before=api?api.current:null,active=slides.map(s=>s.classList.contains('active'));
  const pkg=new Package(font);
  try{
   for(let i=0;i<slides.length;i++){
    if(api)api.show(i);else slides.forEach((s,j)=>s.classList.toggle('active',i===j));
    await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
    await pkg.addSlide(slides[i],i);
   }
  }finally{
   if(api&&before)api.show(before-1);else slides.forEach((s,j)=>s.classList.toggle('active',active[j]));
  }
  const bytes=await pkg.finish();
  return {bytes,pages:slides.length,font,stats:pkg.stats,warnings:pkg.warnings};
 }
 async function download(options){
  const result=await build(options);
  const blob=new Blob([result.bytes],{type:'application/vnd.openxmlformats-officedocument.presentationml.presentation'});
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download=(document.title.replace(/[\\/:*?"<>|]/g,'-')||'演示稿')+'.pptx';a.click();
  setTimeout(()=>URL.revokeObjectURL(url),4000);
  return result;
 }
 window.deckPptx={build,download,defaultFont:DEFAULT_FONT,version:'1.0.0'};
})();
