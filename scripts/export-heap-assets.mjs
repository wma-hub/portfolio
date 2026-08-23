#!/usr/bin/env node
/**
 * export-heap-assets.mjs
 *
 * Exports the four HEAP evidence frames from Figma (title + screenshot + date caption
 * baked into each frame) and writes PNG + WebP pairs into assets/careers/.
 *
 * Usage:
 *   FIGMA_TOKEN=figd_xxx node scripts/export-heap-assets.mjs
 *   FIGMA_TOKEN=figd_xxx node scripts/export-heap-assets.mjs --scale 3 --out assets/careers
 *
 * Requires: Node 18+ (built-in fetch). WebP conversion uses `cwebp` if present,
 * otherwise `sharp` if installed, otherwise it skips WebP with a warning.
 *
 * Get a token at figma.com → Settings → Security → Personal access tokens.
 * Scope needed: File content (read). Never commit the token.
 */

import { writeFile, mkdir, access } from 'node:fs/promises';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';

const run = promisify(execFile);

const FILE_KEY = 'yL4hnNAJKHlEWVLT5OUhvx';

/** Figma node id → output basename. Each frame already contains title + image + date line. */
const FRAMES = [
  { id: '4418:34426', name: '01-funnel-sep',          label: 'Exit rate funnel — September 2025' },
  { id: '4418:34427', name: '01-funnel-oct-dec',      label: 'Exit rate funnel — October–December 2025' },
  { id: '4421:34491', name: '03-heap-strip-sep',      label: 'Page performance — September 2025' },
  { id: '4421:34494', name: '03-heap-strip-oct-dec',  label: 'Page performance — October–December 2025' },
];

// ---------- args ----------
const args = process.argv.slice(2);
const argVal = (flag, fallback) => {
  const i = args.indexOf(flag);
  return i !== -1 && args[i + 1] ? args[i + 1] : fallback;
};
const SCALE = Number(argVal('--scale', '2'));
const OUT_DIR = argVal('--out', 'assets/careers');
const QUALITY = Number(argVal('--quality', '82'));

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

/** Read PNG width/height straight from the IHDR chunk — no dependencies. */
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
console.log(`\nFigma export → ${OUT_DIR}  (scale ${SCALE}x, webp q${QUALITY})\n`);

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
    console.error(`✗ ${frame.name.padEnd(24)} no render URL returned for ${frame.id}`);
    failures++;
    continue;
  }

  const imgRes = await fetch(url);
  if (!imgRes.ok) {
    console.error(`✗ ${frame.name.padEnd(24)} download failed (${imgRes.status})`);
    failures++;
    continue;
  }

  const buf = Buffer.from(await imgRes.arrayBuffer());
  const size = pngSize(buf);
  if (!size) {
    console.error(`✗ ${frame.name.padEnd(24)} response was not a PNG — check the node id`);
    failures++;
    continue;
  }

  const pngPath = path.join(OUT_DIR, `${frame.name}.png`);
  const webpPath = path.join(OUT_DIR, `${frame.name}.webp`);
  await writeFile(pngPath, buf);

  const tool = await toWebp(pngPath, webpPath);
  webpTool ??= tool;

  const kb = (buf.length / 1024).toFixed(0);
  const warn = size.w < 1400 ? '  ⚠ under 1400px wide — raise --scale' : '';
  console.log(`✓ ${frame.name.padEnd(24)} ${size.w}×${size.h}  ${kb}KB  ${tool ? 'png+webp' : 'png only'}${warn}`);
  written.push({ ...frame, ...size, pngPath, webpPath: tool ? webpPath : null });
}

if (!webpTool) {
  console.warn(
    '\n⚠ No WebP written — install one of:\n' +
    '    brew install webp        (gives you cwebp)\n' +
    '    npm i -D sharp\n' +
    '  Then re-run. The markup expects a .webp sibling for each .png.'
  );
}

// Old files these replace — flag them so nothing stale lingers.
for (const stale of ['01-funnel', '03-heap-strip']) {
  for (const ext of ['png', 'webp']) {
    const p = path.join(OUT_DIR, `${stale}.${ext}`);
    try { await access(p); console.log(`\n⚠ superseded file still on disk: ${p}`); } catch {}
  }
}

console.log(`\n${written.length}/${FRAMES.length} frames exported.`);
if (failures) { console.error(`${failures} failed.`); process.exit(1); }
console.log('Next: run the pass-6 brief so Claude Code rewires the two <figure> blocks.\n');
