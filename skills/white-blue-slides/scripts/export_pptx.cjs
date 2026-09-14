#!/usr/bin/env node
'use strict';
/* Export an editable PPTX (universal font) from a built deck, using the same in-page exporter as the player's
   "导出 PPTX" button. Older decks without the embedded exporter get assets/pptx-export.js injected. */
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');

const EXPORTER = path.join(__dirname, '..', 'assets', 'pptx-export.js');

async function exportPptx(page, {font} = {}) {
  await page.evaluate(async () => {await document.fonts.ready; await Promise.all([...document.images].map(im => im.decode().catch(() => {})));});
  if (!await page.evaluate(() => !!window.deckPptx)) {
    await page.addScriptTag({content: fs.readFileSync(EXPORTER, 'utf8')});
  }
  const result = await page.evaluate(async font => {
    const r = await window.deckPptx.build({font});
    let s = '';
    for (let i = 0; i < r.bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, r.bytes.subarray(i, i + 0x8000));
    return {...r, bytes: btoa(s)};
  }, font || null);
  return {...result, bytes: Buffer.from(result.bytes, 'base64')};
}

async function run() {
  const args = process.argv.slice(2), filename = args.shift();
  let out, channel, font;
  while (args.length) {
    const flag = args.shift();
    if (flag === '--out') out = args.shift();
    else if (flag === '--browser') channel = args.shift();
    else if (flag === '--font') font = args.shift();
    else throw new Error('未知参数：' + flag);
  }
  if (!filename || !out) throw new Error('用法：node export_pptx.cjs 演示稿.html --out 演示稿.pptx [--browser chrome] [--font "Microsoft YaHei"]');
  if (path.resolve(filename) === path.resolve(out)) throw new Error('PPTX 输出路径不能覆盖源 HTML。');
  let chromium;
  try { ({chromium} = require('playwright')); }
  catch { throw new Error('找不到 Playwright。请使用当前环境已有的 Node.js + Playwright，或按用户授权准备依赖。'); }
  const browser = await chromium.launch({headless: true, ...(channel ? {channel} : {})});
  try {
    const page = await browser.newPage({viewport: {width: 1920, height: 1080}});
    await page.route(/^https?:\/\//i, route => route.abort());
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(pathToFileURL(path.resolve(filename)).href, {waitUntil: 'load'});
    const count = await page.locator('.slide').count();
    if (!count || await page.locator('body.draft,.missing-image,.chart-shell[data-invalid]').count()) {
      throw new Error('需要图片齐全、图表数据有效的正式演示稿。');
    }
    const result = await exportPptx(page, {font});
    if (errors.length) throw new Error('页面脚本错误：' + errors.join('; '));
    fs.mkdirSync(path.dirname(path.resolve(out)), {recursive: true});
    fs.writeFileSync(path.resolve(out), result.bytes);
    console.log(JSON.stringify({output: path.resolve(out), pages: result.pages, font: result.font, bytes: result.bytes.length, stats: result.stats, warnings: result.warnings}, null, 2));
  } finally {await browser.close();}
}

module.exports = {exportPptx, EXPORTER};
if (require.main === module) run().catch(e => {console.error('导出失败：' + e.message); process.exitCode = 1;});
