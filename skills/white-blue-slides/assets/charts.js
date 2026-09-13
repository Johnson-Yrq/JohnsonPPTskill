/* Apache ECharts adapter: local SVG charts with editable, serializable source data. */
(()=>{'use strict';
 const instances=new Map();
 const palette=()=>{const css=getComputedStyle(document.documentElement),get=(key,fallback)=>css.getPropertyValue(key).trim()||fallback;return [get('--diagram-accent','#477F80'),get('--diagram-strong','#1D3446'),get('--chart-tertiary',get('--saas-gold','#BC9B59'))];};
 function option(data){
  const colors=palette(),muted=getComputedStyle(document.documentElement).getPropertyValue('--muted').trim(),font=getComputedStyle(document.body).fontFamily;
  const base={animation:false,backgroundColor:'transparent',color:colors,textStyle:{fontFamily:font,fontSize:21,color:muted},tooltip:{trigger:data.chart_type==='donut'?'item':'axis',renderMode:'richText',textStyle:{fontFamily:font,fontSize:21}},aria:{enabled:true,description:data.title}};
  if(data.chart_type==='donut'){
   const total=data.series[0].values.reduce((a,b)=>a+b,0);
   return {...base,title:{text:String(total),subtext:data.series[0].name,left:'32%',top:'33%',textAlign:'center',textStyle:{fontSize:34,color:colors[1],fontFamily:font},subtextStyle:{fontSize:21,color:muted,fontFamily:font}},legend:{orient:'vertical',right:24,top:'middle',itemWidth:16,itemHeight:16,itemGap:20,formatter:name=>name+'   '+Math.round(data.series[0].values[data.categories.indexOf(name)]/total*100)+'%',textStyle:{fontSize:21,color:muted,fontFamily:font}},series:[{name:data.series[0].name,type:'pie',radius:['55%','83%'],center:['32%','50%'],label:{show:false},labelLine:{show:false},data:data.categories.map((name,i)=>({name,value:data.series[0].values[i]}))}]};
  }
  const horizontal=data.chart_type==='bar';
  const category={type:'category',data:data.categories,inverse:horizontal,axisLabel:{fontSize:21,interval:0,color:muted},axisTick:{show:false},axisLine:{show:false}};
  // Single-series charts print the unit beside each value; multi-series charts keep it as the axis name (below the axis for horizontal bars so it never collides with the last tick).
  const single=data.series.length===1,unit=single?'':data.unit;
  const gridColor=getComputedStyle(document.documentElement).getPropertyValue('--chart-grid').trim()||'#DAE3E1';
  const value={type:'value',min:0,minInterval:1,splitNumber:3,name:unit,nameLocation:horizontal?'middle':'end',nameGap:horizontal?34:14,nameTextStyle:{fontSize:21,color:muted},axisLabel:{fontSize:21,color:muted},splitLine:{lineStyle:{color:gridColor,type:'dashed'}}};
  const legend=!single,top=(horizontal?12:46)+(legend?38:0),bottom=horizontal&&!single?58:32;
  return {...base,grid:{left:horizontal?100:55,right:horizontal?88:48,top,bottom,containLabel:false},legend:{show:legend,top:0,textStyle:{fontSize:21,color:muted,fontFamily:font}},xAxis:horizontal?value:category,yAxis:horizontal?category:value,series:data.series.map((s,i)=>({name:s.name,type:data.chart_type,data:s.values,barMaxWidth:26,symbolSize:9,smooth:false,lineStyle:{width:3},label:{show:single,position:horizontal?'right':'top',distance:horizontal?8:7,fontSize:21,color:colors[i],formatter:({value})=>data.unit?value+' '+data.unit:String(value)},emphasis:{focus:'series'}}))};
 }
 function render(host,data){
  let chart=instances.get(host);
  if(!chart){host.innerHTML='';host.removeAttribute('_echarts_instance_');chart=echarts.init(host,null,{renderer:'svg'});instances.set(host,chart);}
  // Intrinsic height: bars get a band per category, other charts a fixed drawing height; bounded cells still stretch or shrink the shell through flex.
  const shell=host.closest('.chart-shell');if(shell)shell.style.height=(data.chart_type==='bar'?Math.max(220,data.categories.length*66+58):320)+'px';
  chart.resize();chart.setOption(option(data),true);host.dataset.chartReady='true';
 }
 function refresh(){document.querySelectorAll('.chart-shell').forEach(shell=>{const host=shell.querySelector('.echart');if(host.clientWidth&&host.clientHeight)render(host,JSON.parse(shell.querySelector('.chart-config').textContent));});}
 document.addEventListener('input',event=>{
  const table=event.target.closest('.chart-data');if(!table)return;
  const shell=table.closest('.chart-shell'),config=shell.querySelector('.chart-config'),data=JSON.parse(config.textContent),rows=[...table.tBodies[0].rows];
  const categories=rows.map(row=>row.cells[0].textContent.trim());
  const series=data.series.map((s,col)=>({name:table.tHead.rows[0].cells[col+1].textContent.trim(),values:rows.map(row=>{const raw=row.cells[col+1].textContent.trim();return raw===''?NaN:Number(raw);})}));
  const valid=categories.every(Boolean)&&series.every(s=>s.name&&s.values.every(v=>Number.isFinite(v)&&v>=0))&&(data.chart_type!=='donut'||series[0].values.reduce((a,b)=>a+b,0)>0);
  shell.toggleAttribute('data-invalid',!valid);if(!valid)return;
  const next={...data,categories,series};config.textContent=JSON.stringify(next).replace(/</g,'\\u003c');render(shell.querySelector('.echart'),next);
 });
 window.slideCharts={refresh};
 window.addEventListener('beforeprint',refresh);
})();
