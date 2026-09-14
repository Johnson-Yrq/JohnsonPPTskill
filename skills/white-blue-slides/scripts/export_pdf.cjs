#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');

// Keep vector text/charts and give PDF readers a single-slide opening view.
async function writePresentationPdf(page, output, count) {
  const {PDFDocument, PDFName, PrintScaling} = require('pdf-lib');
  await page.emulateMedia({media: 'print'});
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(im => im.decode()));
    window.deckAPI?.fit();
    window.dispatchEvent(new Event('beforeprint'));
  });
  const bytes = await page.pdf({preferCSSPageSize: true, printBackground: true, displayHeaderFooter: false, scale: 1});
  const doc = await PDFDocument.load(bytes), pages = doc.getPages();
  const sizes = pages.map(p => ({width: p.getWidth(), height: p.getHeight()}));
  if (pages.length !== count || sizes.some(s => Math.abs(s.width - 960) > .5 || Math.abs(s.height - 540) > .5)) {
    throw new Error('PDF 必须一页一张、960 × 540 pt；请先使用新版套件重新构建 HTML。');
  }
  doc.catalog.set(PDFName.of('PageLayout'), PDFName.of('SinglePage'));
  doc.catalog.set(PDFName.of('OpenAction'), doc.context.obj([pages[0].ref, PDFName.of('Fit')]));
  const preferences = doc.catalog.getOrCreateViewerPreferences();
  preferences.setFitWindow(true);
  preferences.setCenterWindow(true);
  preferences.setPrintScaling(PrintScaling.None);
  fs.writeFileSync(output, await doc.save());
  await page.emulateMedia({media: 'screen'});
  await page.evaluate(() => window.dispatchEvent(new Event('afterprint')));
  return {pages: pages.length, sizes};
}

async function run() {
  const args = process.argv.slice(2), filename = args.shift();
  let out, channel;
  while (args.length) {
    const flag = args.shift();
    if (flag === '--out') out = args.shift();
    else if (flag === '--browser') channel = args.shift();
    else throw new Error('未知参数：' + flag);
  }
  if (!filename || !out) throw new Error('用法：node export_pdf.cjs 演示稿.html --out 演示稿.pdf [--browser chrome]');
  if (path.resolve(filename) === path.resolve(out)) throw new Error('PDF 输出路径不能覆盖源 HTML。');
  const {chromium} = require('playwright');
  const browser = await chromium.launch({headless: true, ...(channel ? {channel} : {})});
  try {
    const page = await browser.newPage({viewport: {width: 1920, height: 1080}});
    await page.route(/^https?:\/\//i, route => route.abort());
    await page.goto(pathToFileURL(path.resolve(filename)).href, {waitUntil: 'load'});
    const count = await page.locator('.slide').count();
    if (!count || await page.locator('body.draft,.missing-image,.chart-shell[data-invalid]').count()) {
      throw new Error('需要图片齐全、图表数据有效的正式演示稿。');
    }
    fs.mkdirSync(path.dirname(path.resolve(out)), {recursive: true});
    const result = await writePresentationPdf(page, path.resolve(out), count);
    console.log(JSON.stringify({output: path.resolve(out), ...result}, null, 2));
  } finally {await browser.close();}
}

module.exports = {writePresentationPdf};
if (require.main === module) run().catch(e => {console.error('导出失败：' + e.message);process.exitCode = 1;});
