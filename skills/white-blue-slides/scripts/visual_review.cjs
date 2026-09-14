/* A review record documents observations; it never infers aesthetic quality. */
'use strict';
const fs = require('fs');
const crypto = require('crypto');

function reviewTemplate(filename, pages, pdf) {
  return {
    version: 1,
    html_sha256: crypto.createHash('sha256').update(fs.readFileSync(filename)).digest('hex'),
    pages: pages.map(page => ({
      id: page.id,
      checks: Object.fromEntries(['background', 'hierarchy', 'composition', 'alignment', ...(pdf ? ['pdf'] : [])].map(key => [key, 'pending'])),
      observation: ''
    }))
  };
}

function assessReview(expected, supplied) {
  if (!supplied) return {status: 'pending', issues: [], pending: expected.pages.map(p => p.id)};
  const issues = [], pending = [];
  if (supplied.version !== 1 || supplied.html_sha256 !== expected.html_sha256) issues.push('复核记录版本或 HTML 指纹不匹配；修改后重新查看受影响页面并更新记录');
  if (!Array.isArray(supplied.pages)) return {status: 'invalid', issues: [...issues, '缺少逐页复核记录'], pending};
  const ids = supplied.pages.map(p => p?.id);
  if (ids.length !== expected.pages.length || new Set(ids).size !== ids.length || ids.some(id => !expected.pages.some(p => p.id === id))) issues.push('复核页码缺失、重复或不属于当前稿件');
  for (const page of expected.pages) {
    const actual = supplied.pages.find(p => p?.id === page.id);
    if (!actual) {pending.push(page.id); continue;}
    for (const check of Object.keys(page.checks)) {
      const value = actual.checks?.[check];
      if (!['passed', 'pending', 'needs_changes'].includes(value)) issues.push(`${page.id}: ${check} 状态无效`);
      if (value !== 'passed' && !pending.includes(page.id)) pending.push(page.id);
    }
    if (typeof actual.observation !== 'string' || !actual.observation.trim()) {
      issues.push(`${page.id}: 缺少实际观察与修正说明`);
    }
  }
  return {status: issues.length ? 'invalid' : pending.length ? 'pending' : 'passed', issues, pending};
}

module.exports = {reviewTemplate, assessReview};
