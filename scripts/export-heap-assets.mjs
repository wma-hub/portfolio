#!/usr/bin/env node
/**
 * export-heap-assets.mjs  (v2 — bitmaps only, no baked-in text)
 *
 * Exports the four HEAP screenshots from Figma as clean images. Titles and date
 * ranges are NOT included — those are typed as HTML on the page so they stay
 * selectable, translatable, and legible at any width.
 *
 * Targets the inner screenshot layers, not their wrapper frames:
 *   4418:34420  exit-rate funnel, September
 *   4418:34421  exit-rate funnel, October–December
 *   4418:34477  page performance table, September
 *   4418:34433  page performance table, October–December
 *
 * Usage:
 *   FIGMA_TOKEN=figd_xxx node scripts/export-heap-assets.mjs
 *   FIGMA_TOKEN=figd_xxx node scripts/export-heap-assets.mjs --scale 4
 *
 * Requires Node 18+. WebP via `cwebp` (brew install webp) or `sharp`.
 * Never commit the token.
 */

import { writeFile, mkdir, access } from 'node:fs/promises';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';

const run = promisify(execFile);

const FILE_KEY = 'yL4hnNAJKHlEWVLT5OUhvx';

/**
 * Inner screenshot layers only. Figma widths are small (752–800px) because the
 * frames are laid out at that size, but the underlying bitmaps were captured at
 * ~2600px — so scale 3 lands near native without upscaling. Scale 4 will
 * interpolate past the source; only use it if 3x looks soft in situ.
 */
const FRAMES = [
  { id: '4418:34420', name: '01-exit-sep',      figmaW: 800, note: 'Exit funnel, September' },
  { id: '4418:34421', name: '01-exit-oct-dec',  figmaW: 800, note: 'Exit funnel, Oct–Dec' },
  { id: '4418:34477', name: '03-pages-sep',     figmaW: 752, note: 'Page performance, September' },
  { id: '4418:34433', name: '03-pages-oct-dec', figmaW: 752, note: 'Page performance, Oct–Dec' },
];

// ---------- args ----------
const args = process.argv.slice(2);
const argVal = (flag, fallback) => {
  const i = args.indexOf(flag);
  return i !== -1 && args[i + 1] ? args[i + 1] : fallback;
};
const SCALE = Number(argVal('--scale', '3'));
const OUT_DIR = argVal('--out', 'assets/careers');
const QUALITY = Number(argVal('--quality', '84'));

const TOKEN = process.env.FIGMA_TOKEN;
if (!TOKEN) {
  console.error('✗ FIGMA_TOKEN is not set.\n  FIGMA_TOKEN=figd_xxx node scripts/export-heap-assets.mjs');
  process.exit(1);
}
if (!Number.isFinite(SCALE) || SCALE < 1 || SCALE > 4) {
  console.error(`✗ --scale must be between 1 and 4 (got ${SCALE})`);
  process.exit(1);
}

// ---------- helpers ----------
const has = async (cmd) => {
  try { await run('which', [cmd]); return true; } catch { return false; }
};

/** Read PNG width/height from the IHDR chunk — no dependencies. */
const pngSize = (buf) => {
  if (buf.length < 24 || buf.readUInt32BE(0) !== 0x89504e47) return null;
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
};

async function toWebp(pngPath, webpPath) {
  if (await has('cwebp')) {
    await run('cwebp', ['-quiet', '-q', String(QUALITY), pngPath, '-o', webpPath]);
    return 'cwebp';
  }
  try {
    const { default: sharp } = await import('sharp');
    await sharp(pngPath).webp({ quality: QUALITY }).toFile(webpPath);
    return 'sharp';
  } catch {
    return null;
  }
}

// ---------- main ----------
console.log(`\nFigma export → ${OUT_DIR}   scale ${SCALE}x · webp q${QUALITY} · bitmaps only\n`);

await mkdir(OUT_DIR, { recursive: true });

const ids = FRAMES.map((f) => f.id).join(',');
const endpoint =
  `https://api.figma.com/v1/images/${FILE_KEY}` +
  `?ids=${encodeURIComponent(ids)}&format=png&scale=${SCALE}`;

const res = await fetch(endpoint, { headers: { 'X-Figma-Token': TOKEN } });
if (!res.ok) {
  console.error(`✗ Figma API ${res.status} ${res.statusText}`);
  console.error(await res.text());
  process.exit(1);
}

const body = await res.json();
if (body.err) {
  console.error(`✗ Figma API error: ${body.err}`);
  process.exit(1);
}

let webpTool = null;
let failures = 0;
const written = [];

for (const frame of FRAMES) {
  const url = body.images?.[frame.id];
  if (!url) {
    console.error(`✗ ${frame.name.padEnd(20)} no render URL for ${frame.id}`);
    failures++;
    continue;
  }

  const imgRes = await fetch(url);
  if (!imgRes.ok) {
    console.error(`✗ ${frame.name.padEnd(20)} download failed (${imgRes.status})`);
    failures++;
    continue;
  }

  const buf = Buffer.from(await imgRes.arrayBuffer());
  const size = pngSize(buf);
  if (!size) {
    console.error(`✗ ${frame.name.padEnd(20)} response was not a PNG — check the node id`);
    failures++;
    continue;
  }

  const pngPath = path.join(OUT_DIR, `${frame.name}.png`);
  const webpPath = path.join(OUT_DIR, `${frame.name}.webp`);
  await writeFile(pngPath, buf);

  const tool = await toWebp(pngPath, webpPath);
  webpTool ??= tool;

  const kb = (buf.length / 1024).toFixed(0);
  const warn = size.w < 1800 ? '  ⚠ under 1800px — these render full width, raise --scale' : '';
  console.log(`✓ ${frame.name.padEnd(20)} ${size.w}×${size.h}  ${kb}KB  ${tool ? 'png+webp' : 'png only'}${warn}`);
  written.push({ ...frame, ...size });
}

if (!webpTool) {
  console.warn(
    '\n⚠ No WebP written — install one of:\n' +
    '    brew install webp        (gives you cwebp)\n' +
    '    npm i -D sharp\n' +
    '  Then re-run. The markup expects a .webp sibling for each .png.'
  );
}

// Anything these supersede — flag so nothing stale ships.
const stale = [
  '01-funnel', '03-heap-strip',
  '01-funnel-sep', '01-funnel-oct-dec',
  '03-heap-strip-sep', '03-heap-strip-oct-dec',
];
const found = [];
for (const s of stale) {
  for (const ext of ['png', 'webp']) {
    const p = path.join(OUT_DIR, `${s}.${ext}`);
    try { await access(p); found.push(p); } catch {}
  }
}
if (found.length) {
  console.log('\n⚠ superseded files still on disk — delete after the markup is rewired:');
  for (const p of found) console.log(`    ${p}`);
}

console.log(`\n${written.length}/${FRAMES.length} exported.`);
if (failures) { console.error(`${failures} failed.`); process.exit(1); }
console.log('Titles and date ranges are NOT in these images — they are typed in the markup.\n');
