/**
 * §7d Parity Gate — node qa/parity.js marly
 * Renders /marly at 1440px headless, screenshots each section,
 * composites side-by-side with Figma screenshots in /qa/{page}--{section}.png
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const http = require('http');
const { execSync } = require('child_process');

const PAGE = process.argv[2] || 'marly';
const QA_DIR = path.join(__dirname);
const REPO_ROOT = path.join(__dirname, '..');

// Sections: selector to find the element, output slug, figma screenshot filename
const SECTIONS = [
  { slug: 'hero',  figma: 'marly--hero--figma.png', selector: '.ml-hero-section' },
  { slug: '01',    figma: 'marly--01--figma.png',   selector: '.ml-body-section .ml-section:nth-child(1)' },
  { slug: '02a',   figma: 'marly--02a--figma.png',  selector: '.ml-body-section .ml-section:nth-child(3)' },
  { slug: '02b',   figma: 'marly--02b--figma.png',  selector: '.ml-body-section .ml-section:nth-child(5)' },
  { slug: '02c',   figma: 'marly--02c--figma.png',  selector: '.ml-body-section .ml-section:nth-child(7)' },
  { slug: '03',    figma: 'marly--03--figma.png',   selector: '.ml-body-section .ml-section:nth-child(9)' },
  { slug: '04',    figma: 'marly--04--figma.png',   selector: '.ml-body-section .ml-section:nth-child(11)' },
  { slug: '05',    figma: 'marly--05--figma.png',   selector: '.ml-body-section .ml-section:nth-child(13)' },
];

// Serve static files from repo root
function startServer(root, port) {
  return new Promise((resolve) => {
    const mime = { html: 'text/html', css: 'text/css', js: 'application/javascript', png: 'image/png', svg: 'image/svg+xml', ico: 'image/x-icon' };
    const server = http.createServer((req, res) => {
      let urlPath = req.url.split('?')[0];
      if (urlPath.endsWith('/')) urlPath += 'index.html';
      let file = path.join(root, urlPath);
      // directory fallback
      if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
      else if (!path.extname(file) && !fs.existsSync(file)) file = path.join(file, 'index.html');
      const ext = path.extname(file).slice(1);
      try {
        const data = fs.readFileSync(file);
        res.writeHead(200, { 'Content-Type': mime[ext] || 'application/octet-stream' });
        res.end(data);
      } catch {
        res.writeHead(404); res.end();
      }
    });
    server.listen(port, () => resolve(server));
  });
}

// Stitch two PNG files side-by-side using sharp if available, else save individually
async function stitch(leftPath, rightPath, outPath) {
  try {
    const sharp = require('sharp');
    const left = sharp(leftPath);
    const right = sharp(rightPath);
    const lm = await left.metadata();
    const rm = await right.metadata();
    const h = Math.max(lm.height, rm.height);
    const GAP = 8;
    const w = lm.width + GAP + rm.width;
    await sharp({
      create: { width: w, height: h, channels: 4, background: { r: 240, g: 240, b: 240, alpha: 1 } }
    })
      .composite([
        { input: leftPath, top: 0, left: 0 },
        { input: rightPath, top: 0, left: lm.width + GAP },
      ])
      .png()
      .toFile(outPath);
    console.log(`  ✓ composite → ${path.basename(outPath)}`);
  } catch {
    // sharp not available — save rendered screenshot with --rendered suffix
    const renderedOut = outPath.replace('.png', '--rendered.png');
    fs.copyFileSync(rightPath, renderedOut);
    console.log(`  ⚠ sharp not installed — saved rendered: ${path.basename(renderedOut)}`);
    console.log(`    Figma reference: ${path.basename(leftPath)}`);
  }
}

(async () => {
  const PORT = 7741;
  const server = await startServer(REPO_ROOT, PORT);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1440, height: 900 });

  const url = `http://localhost:${PORT}/${PAGE}`;
  console.log(`Loading ${url} at 1440px…`);
  await page.goto(url, { waitUntil: 'networkidle' });

  // Wait for fade-up animations to settle
  await page.waitForTimeout(800);

  for (const section of SECTIONS) {
    const outRendered = path.join(QA_DIR, `marly--${section.slug}--rendered.png`);
    const outComposite = path.join(QA_DIR, `marly--${section.slug}.png`);
    const figmaPath = path.join(QA_DIR, section.figma);

    const el = page.locator(section.selector).first();
    const count = await el.count();
    if (!count) {
      console.log(`  ✗ ${section.slug}: selector not found — ${section.selector}`);
      continue;
    }

    await el.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);
    await el.screenshot({ path: outRendered });
    console.log(`  captured ${section.slug}`);

    if (fs.existsSync(figmaPath)) {
      await stitch(figmaPath, outRendered, outComposite);
    } else {
      console.log(`  ⚠ no figma reference for ${section.slug}`);
    }
  }

  await browser.close();
  server.close();
  console.log('\nParity gate complete. Review /qa/ for comparison strips.');
})();
