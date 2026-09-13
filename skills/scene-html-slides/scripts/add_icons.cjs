#!/usr/bin/env node
/* Add Lucide icons to assets/icons.json by name. Offline: needs a local `lucide` npm package.
   Usage: node add_icons.cjs Users Hospital [--lucide /path/to/node_modules/lucide]
   Resolution order: --lucide, then NODE_PATH / normal require() resolution. */
'use strict';
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
let lucidePath;
const names = [];
while (args.length) {
  const a = args.shift();
  if (a === '--lucide') lucidePath = args.shift();
  else if (a === '--list') { const cur = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'assets', 'icons.json'), 'utf8')); console.log(Object.keys(cur).join(' ')); process.exit(0); }
  else names.push(a);
}
if (!names.length) { console.error('用法：node add_icons.cjs <IconName> [...] [--lucide <lucide 包目录>]；--list 列出现有图标'); process.exit(1); }
let lucide;
try { lucide = require(lucidePath ? path.resolve(lucidePath) : 'lucide'); }
catch (e) { console.error('找不到 lucide 包。用 --lucide 指向本地 node_modules/lucide，或设置 NODE_PATH。'); process.exit(1); }
const file = path.join(__dirname, '..', 'assets', 'icons.json');
const icons = JSON.parse(fs.readFileSync(file, 'utf8'));
const added = [], missing = [];
for (const name of names) {
  const node = lucide[name];
  if (!Array.isArray(node)) { missing.push(name); continue; }
  if (!icons[name]) added.push(name);
  icons[name] = node;
}
const sorted = Object.fromEntries(Object.keys(icons).sort().map(k => [k, icons[k]]));
fs.writeFileSync(file, JSON.stringify(sorted, null, 2) + '\n');
console.log(JSON.stringify({added, alreadyPresent: names.filter(n => !added.includes(n) && !missing.includes(n)), missing, total: Object.keys(sorted).length}));
if (missing.length) process.exitCode = 2;
