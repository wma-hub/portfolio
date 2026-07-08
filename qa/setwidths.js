#!/usr/bin/env node
/**
 * /qa/setwidths.js
 * For every <img class="export"> whose src is a numbered section export,
 * reads intrinsic pixel width W via sharp and sets width attr per scale map:
 *   assets/marly     → display = Math.round(intrinsic / 2)
 *   assets/treatweek → display = intrinsic (exports are @1x)
 * Flags any result > 1080. Writes updated HTML back to the relevant page.
 *
 * Usage:
 *   node qa/setwidths.js marly
 *   node qa/setwidths.js treat-week
 */
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const PAGES = {
  marly: {
    html: path.join(__dirname, '..', 'marly', 'index.html'),
    re: /^\/assets\/marly\/\d{2}[a-c]?-\d{2}\.png$/,
    scale: 2,
  },
  'treat-week': {
    html: path.join(__dirname, '..', 'treat-week', 'index.html'),
    re: /^\/assets\/treatweek\/\d{2}(-\d+)?\.png$/,
    scale: 1,
  },
};

const pageName = process.argv[2];
if (!pageName || !PAGES[pageName]) {
  console.error(`Usage: node qa/setwidths.js <page>\nKnown pages: ${Object.keys(PAGES).join(', ')}`);
  process.exit(1);
}

const { html: HTML_PATH, re: EXPORT_RE, scale: SCALE } = PAGES[pageName];
const REPO_ROOT = path.join(__dirname, '..');

async function main() {
  let html = fs.readFileSync(HTML_PATH, 'utf8');

  const IMG_RE = /<img\b([^>]*)>/g;
  const matches = [];
  let m;
  while ((m = IMG_RE.exec(html)) !== null) {
    const attrs = m[1];
    const srcM = attrs.match(/src="([^"]+)"/);
    if (!srcM) continue;
    const src = srcM[1];
    if (!EXPORT_RE.test(src)) continue;
    matches.push({ full: m[0], attrs, src, start: m.index, end: m.index + m[0].length });
  }

  const rows = [];
  for (const item of matches) {
    const filePath = path.join(REPO_ROOT, item.src);
    if (!fs.existsSync(filePath)) {
      rows.push({ filename: path.basename(item.src), intrinsic: 'MISSING', displayW: '—', flag: '⚠ FILE NOT FOUND' });
      continue;
    }
    const meta = await sharp(filePath).metadata();
    const intrinsic = meta.width;
    const displayW = Math.round(intrinsic / SCALE);
    const flag = displayW > 1080 ? '⚠ EXCEEDS 1080' : '';
    rows.push({ filename: path.basename(item.src), intrinsic, displayW, scale: `÷${SCALE}`, flag });
    item.displayW = displayW;
  }

  const toUpdate = matches.filter(item => item.displayW !== undefined);
  toUpdate.sort((a, b) => b.start - a.start);

  for (const item of toUpdate) {
    let tag = item.full;
    tag = tag.replace(/\s+width="\d+"/, '');
    tag = tag.replace(/^<img\b/, `<img width="${item.displayW}"`);
    html = html.slice(0, item.start) + tag + html.slice(item.end);
  }

  fs.writeFileSync(HTML_PATH, html, 'utf8');

  console.log(`\nPage: ${pageName} (scale ÷${SCALE})\n`);
  console.log('filename          | intrinsic px | display px | scale | flag');
  console.log('------------------|--------------|------------|-------|-----');
  rows.sort((a, b) => String(a.filename).localeCompare(String(b.filename)));
  for (const r of rows) {
    console.log(
      `${String(r.filename).padEnd(17)} | ${String(r.intrinsic).padEnd(12)} | ${String(r.displayW).padEnd(10)} | ${String(r.scale || '').padEnd(5)} | ${r.flag}`
    );
  }
}

main().catch(e => { console.error(e); process.exit(1); });
