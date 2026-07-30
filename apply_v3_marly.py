#!/usr/bin/env python3
"""
apply_v3_marly.py — rebuild marly/index.html to the V3 design.

Reuse-first: the brand logo row, the ad-slot markup and the entire rotation
script are EXTRACTED VERBATIM from the current page, never retyped. Only the
page shell around them is new.

Deletes (not in V3 Figma): cs-hero gradient block, intro section, pipeline
diagram, three tier rows, animation section, four build steps, the Tumblerware
review iframe, and the whole 146-line inline <style>.

Also retokenizes the SHARED .cs-nav-* block in site.css, which treat-week,
ge-terminal and selected-works all use.

All-or-nothing. Undo: git checkout .
"""

import re, sys, subprocess, pathlib

REPO   = pathlib.Path("/Users/wma/Desktop/portfolio")
BRANCH = "v3-restyle"
MARLY  = REPO / "marly" / "index.html"

MARLY_CSS = """
/* ------------------------------------------------------------
   CASE STUDY — shared body shell
   ------------------------------------------------------------ */
.cs-body {
  background: var(--bg);
  padding: 0 var(--px-outer) var(--space-120);
}
.cs-body-inner {
  width: 100%;
  max-width: var(--content-width);
  margin-inline: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-80);
}
.hero-copy--narrow { max-width: 540px; }

/* Copy left, live ad units right — 513 / 447 of the 1080 column */
.problem-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-120);
}
.problem-copy {
  flex: 1 1 513px;
  max-width: 513px;
  display: flex;
  flex-direction: column;
  gap: var(--space-24);
}
.problem-copy p { color: var(--color-ink-muted); }

/* ---- Brand range: logos + rotating units (markup reused as-is) ---- */
.brand-logos {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  justify-content: space-between;
  gap: clamp(12px, 2.2vw, 24px);
  padding: var(--space-24) 0;
}
.brand-logo-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 72px;
  flex: 1 1 0;
  min-width: 0;
  max-width: 168px;
}
.brand-logo-cell img { height: auto; max-width: 100%; object-fit: contain; display: block; }

.ad-slots-col { display: flex; flex-direction: column; gap: var(--space-40); align-items: center; }
.ad-slot-wrap { display: flex; flex-direction: column; align-items: center; gap: var(--space-8); }
.ad-slot-label { font-size: var(--type-micro); color: var(--color-ink-subtle); text-align: center; }
.ad-slot { position: relative; overflow: hidden; background: var(--color-background-acc); flex-shrink: 0; }
.ad-slot iframe { position: absolute; top: 0; left: 0; border: 0; display: block; }
.brand-range-slots-wrap { overflow-x: auto; }

@media (max-width: 900px) {
  .problem-row { flex-direction: column; gap: var(--space-60); }
  .problem-copy { max-width: none; flex: 1 1 auto; }
  .cs-body { padding-bottom: var(--space-80); }
  .cs-body-inner { gap: var(--space-60); }
}
@media (max-width: 700px) {
  .brand-logos { flex-wrap: wrap; justify-content: flex-start; gap: var(--space-24); }
  .brand-logo-cell { flex: 0 0 calc(33.333% - var(--space-16)); }
}
"""
CSNAV_CSS = """/* ── CS Nav — prev/next, matching the nav-page component ─────── */
.cs-nav-outer {
  background: var(--bg);
  padding: var(--space-80) var(--px-outer);
  display: flex;
  flex-direction: column;
  gap: var(--space-40);
}
.cs-nav-divider { height: 1px; background: var(--color-rule); width: 100%; }
.cs-nav-row {
  width: 100%;
  max-width: var(--content-width);
  margin-inline: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-24);
}
.cs-nav-side { display: flex; gap: var(--space-16); align-items: center; }
.cs-nav-side--right { justify-content: flex-end; }
.cs-nav-label { display: flex; flex-direction: column; gap: var(--space-4); }
.cs-nav-direction {
  font-size: var(--type-body);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-normal);
}
.cs-nav-project {
  font-size: var(--type-body-sm);
  font-weight: var(--font-weight-regular);
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-normal);
}
.cs-nav-side a { color: inherit; }
.cs-nav-side--left  .cs-nav-direction { color: var(--color-accent); }
.cs-nav-side--left  .cs-nav-project   { color: var(--color-accent); }
.cs-nav-side--right .cs-nav-direction { color: var(--color-ink); }
.cs-nav-side--right .cs-nav-project   { color: var(--color-ink-muted); }
.cs-nav-btn {
  border: 1px solid var(--color-rule);
  border-radius: var(--radius-sm);
  padding: var(--space-14);
  display: flex;
  align-items: center;
  justify-content: center;
  background: none;
  text-decoration: none;
  flex-shrink: 0;
}
.cs-nav-btn svg { width: 16px; height: 16px; display: block; }
.cs-nav-side--left  .cs-nav-btn svg { color: var(--color-accent); }
.cs-nav-side--right .cs-nav-btn svg { color: var(--color-ink-muted); }

@media (max-width: 700px) {
  .cs-nav-outer { padding: var(--space-40) var(--px-outer); }
  .cs-nav-row { flex-direction: column; gap: var(--space-24); align-items: flex-start; }
}
"""

errors, notes = [], []
def fail(m): errors.append(m)
def note(m): notes.append(m)
def git(*a): return subprocess.run(["git","-C",str(REPO)]+list(a),
                                   capture_output=True, text=True).stdout.strip()

print("=" * 62); print("PRECONDITIONS"); print("=" * 62)
if not REPO.exists(): fail(f"repo not found: {REPO}")
else:
    b, d = git("rev-parse","--abbrev-ref","HEAD"), git("status","--porcelain")
    print(f"  branch : {b}\n  tree   : {'clean' if not d else 'DIRTY'}")
    if b != BRANCH: fail(f"expected branch {BRANCH}, found {b}")
    if d: fail("uncommitted changes - commit or stash first")
if not MARLY.exists(): fail("marly/index.html missing")
css_path = REPO / "css" / "site.css"
if not css_path.exists(): fail("css/site.css missing")
if errors:
    print("\nABORTED - nothing written:"); [print("  x "+e) for e in errors]; sys.exit(1)

src = MARLY.read_text()
css = css_path.read_text()

# ---------------------------------------------------- extract, never retype
def grab(pattern, label, flags=re.S):
    m = re.search(pattern, src, flags)
    if not m: fail(f"could not extract {label}"); return ""
    note(f"extracted {label} ({len(m.group(0))} bytes)")
    return m.group(0)

LOGOS = grab(r'<div class="brand-logos">.*?\n        </div>', "brand logo row")
SLOTS = grab(r'<div class="ad-slots-col brand-range-slots-wrap"[^>]*>.*?\n        </div>', "ad slot markup")

i = src.find("Brand Range rotating showcase")
if i == -1: fail("rotation script not found")
else:
    s0 = src.rfind("<script>", 0, i); s1 = src.find("</script>", i)
    if s0 == -1 or s1 == -1: fail("rotation script boundaries not found")
    else:
        SCRIPT = src[s0:s1 + len("</script>")]
        note(f"extracted rotation script ({len(SCRIPT)} bytes)")

for must in ("magic-spoon-logo", "tumblerware-logo", "slot-728x90", "slot-160x600"):
    if must not in LOGOS + SLOTS: fail(f"extraction incomplete, missing: {must}")
if errors:
    print("\nABORTED - nothing written:"); [print("  x "+e) for e in errors]; sys.exit(1)

# reindent extracted blocks from 8 spaces to 10
LOGOS = "\n".join(("  " + l) if l.strip() else l for l in LOGOS.split("\n"))
SLOTS = "\n".join(("  " + l) if l.strip() else l for l in SLOTS.split("\n"))

NAV = '''  <nav class="site-nav" role="navigation" aria-label="Main navigation">
    <a href="/" class="nav-wordmark">wilson ma</a>
    <div class="nav-links">
      <a href="/#work" class="ui-nav" aria-current="page">projects</a>
      <a href="/about" class="ui-nav">about</a>
    </div>
  </nav>'''

FOOTER = '''  <footer class="site-footer" role="contentinfo">
    <div class="footer-inner">
      <div class="footer-mark">
        <span class="heading-wordmark">wma.nyc</span>
        <p class="footer-copy meta-small">&#169; 2026 Wilson Ma</p>
      </div>
      <nav class="footer-links" aria-label="Footer navigation">
        <a href="/#work" class="ui-nav">projects</a>
        <a href="/about" class="ui-nav">about</a>
        <a href="https://www.linkedin.com/in/wilsonxma/" target="_blank" rel="noopener noreferrer" class="ui-nav">linkedin</a>
        <a href="mailto:ny.wilson.ma@gmail.com" class="ui-nav">email</a>
      </nav>
    </div>
  </footer>'''

CHEV_L = '<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CHEV_R = '<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M6 3l5 5-5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'

PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MARLY Creative Concepts — Wilson Ma</title>
  <link rel="preload" href="/assets/fonts/Switzer-Variable.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/css/site.css">
  <!-- Google tag (gtag.js) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-L3KK0FQDE6"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-L3KK0FQDE6');
  </script>
</head>
<body>
<div class="page">

{NAV}

  <main>

    <section class="hero" aria-label="MARLY Creative Concepts">
      <div class="hero-inner">
        <div class="hero-copy hero-copy--narrow fade-up">
          <h1 class="display-hero">MARLY Creative Concepts</h1>
          <p class="heading-subhead hero-sub">Animated HTML5 display, built like a system.</p>
          <p class="body-default hero-intro">Marly is the solo studio I founded and run: a Figma-to-production pipeline that turns brand design systems into animated ad sets. I&#8217;m the creative director, the pipeline architect, and the final QA gate, which is why the system below exists at all.</p>
        </div>
        <div class="hero-portrait hero-portrait--placeholder fade-up" aria-hidden="true"></div>
      </div>
    </section>

    <section class="cs-body" aria-label="Brand range">
      <div class="cs-body-inner">

        <div class="fade-up">
{LOGOS}
        </div>

        <div class="problem-row fade-up">
          <div class="problem-copy">
            <p class="body-default">Enterprise platforms like Celtra automate at scale but assume someone else is producing the creative. Agencies charge $350&#8211;1,500 per ad set and reset the file handoff with every campaign. DIY tools produce output that looks like Canva, because it is.</p>
            <p class="body-default">D2C brands spend real money on type, palette, and a product with a shape worth showing, and still can&#8217;t get those choices honored downstream.</p>
          </div>
{SLOTS}
        </div>

      </div>
    </section>

    <nav class="cs-nav-outer" aria-label="Project navigation">
      <div class="cs-nav-divider"></div>
      <div class="cs-nav-row">
        <div class="cs-nav-side cs-nav-side--left">
          <a href="/ge-terminal" class="cs-nav-btn" aria-label="Previous project: GE Terminal">{CHEV_L}</a>
          <a href="/ge-terminal" class="cs-nav-label">
            <span class="cs-nav-direction">Previous project:</span>
            <span class="cs-nav-project">GE Terminal</span>
          </a>
        </div>
        <div class="cs-nav-side cs-nav-side--right">
          <a href="/workhuman" class="cs-nav-label" style="text-align:right;">
            <span class="cs-nav-direction">Next project:</span>
            <span class="cs-nav-project">Workhuman</span>
          </a>
          <a href="/workhuman" class="cs-nav-btn" aria-label="Next project: Workhuman">{CHEV_R}</a>
        </div>
      </div>
    </nav>

  </main>

{FOOTER}

</div><!-- .page -->
<script src="/js/site.js"></script>
{SCRIPT}
</body>
</html>
'''

# ---------------------------------------------------------------- css work
new_css = css
old_nav = re.search(r'/\* .. CS Nav .*?(?=/\* .. CS Hero responsive|\Z)', new_css, re.S)
if old_nav:
    new_css = new_css.replace(old_nav.group(0), CSNAV_CSS.rstrip() + "\n\n", 1)
    note("cs-nav block retokenized (shared by 4 pages)")
else:
    fail("cs-nav CSS block not found")

if ".cs-body {" not in new_css:
    anchor = "/* ---- CASE STUDY SHARED COMPONENTS ---- */"
    if anchor not in new_css: fail("case-study anchor missing")
    else:
        new_css = new_css.replace(anchor, MARLY_CSS.rstrip() + "\n\n" + anchor, 1)
        note("Marly body CSS inserted")

# ---------------------------------------------------------------- verify
for gone in ("pipeline-diagram", "tier-row", "anim-layout", "build-step", "ml-section-heading", "<style>"):
    if gone in PAGE: fail(f"deleted component leaked into new page: {gone}")
for kept in ("AD_SLOTS", "slot-300x250", "tumblerware-logo", "ROTATE_MS", "magic-spoon"):
    if kept not in PAGE: fail(f"reused block missing from new page: {kept}")
if "#ff00ee" in PAGE.lower(): note("NOTE: magenta annotation carried through")

print("\n" + "=" * 62); print("PLAN"); print("=" * 62)
[print("  - " + n) for n in notes]
print(f"  - marly/index.html  {len(src.splitlines())} -> {len(PAGE.splitlines())} lines")
if errors:
    print("\nABORTED - nothing written:"); [print("  x "+e) for e in errors]; sys.exit(1)

MARLY.write_text(PAGE)
css_path.write_text(new_css)
print("\n" + "=" * 62); print("WROTE 2 FILES"); print("=" * 62)
print("  marly/index.html\n  css/site.css")
print("\nCheck: logos render, all three slots rotate, prev/next reads GE Terminal / Workhuman")
print("  git add -A && git commit -m 'V3 Marly: rebuild to design, retokenize shared cs-nav'")
print("Undo:  git checkout .")
