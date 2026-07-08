#!/usr/bin/env node
/**
 * /qa/setwidths.js
 * For every <img class="export"> whose src is a numbered section export,
 * reads intrinsic pixel width W via sharp and sets width attr = Math.round(W/2).
 * Flags any result > 1080. Writes updated HTML back to marly/index.html.
 *
 * Usage: node qa/setwidths.js
 */
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const HTML_PATH = path.join(__dirname, '..', 'marly', 'index.html');
const REPO_ROOT = path.join(__dirname, '..');

// Match numbered section exports: /assets/marly/NN[a-c]-NN.png
const EXPORT_RE = /^\/assets\/marly\/\d{2}[a-c]?-\d{2}\.png$/;

async function main() {
  let html = fs.readFileSync(HTML_PATH, 'utf8');

  // Collect all img tags, their positions, and src attrs
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

  // Measure each export
  const rows = [];
  for (const item of matches) {
    const filePath = path.join(REPO_ROOT, item.src);
    if (!fs.existsSync(filePath)) {
      rows.push({ filename: path.basename(item.src), intrinsic: 'MISSING', displayW: '—', flag: '⚠ FILE NOT FOUND' });
      continue;
    }
    const meta = await sharp(filePath).metadata();
    const intrinsic = meta.width;
    const displayW = Math.round(intrinsic / 2);
    const flag = displayW > 1080 ? '⚠ EXCEEDS 1080' : '';
    rows.push({ filename: path.basename(item.src), intrinsic, displayW, flag });
    item.displayW = displayW;
  }

  // Apply replacements end→start to preserve string positions
  const toUpdate = matches.filter(item => item.displayW !== undefined);
  toUpdate.sort((a, b) => b.start - a.start);

  for (const item of toUpdate) {
    // Remove existing width attr, insert new one after <img or class/src
    let tag = item.full;
    tag = tag.replace(/\s+width="\d+"/, '');
    tag = tag.replace(/^<img\b/, `<img width="${item.displayW}"`);
    html = html.slice(0, item.start) + tag + html.slice(item.end);
  }

  fs.writeFileSync(HTML_PATH, html, 'utf8');

  // Print table
  console.log('\nfilename          | intrinsic px | width set | flag');
  console.log('------------------|--------------|-----------|-----');
  rows.sort((a, b) => String(a.filename).localeCompare(String(b.filename)));
  for (const r of rows) {
    console.log(
      `${String(r.filename).padEnd(17)} | ${String(r.intrinsic).padEnd(12)} | ${String(r.displayW).padEnd(9)} | ${r.flag}`
    );
  }
}

main().catch(e => { console.error(e); process.exit(1); });
