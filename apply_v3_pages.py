#!/usr/bin/env python3
"""
apply_v3_pages.py — Treat Week rebuilt + RIPCO and West Elm created.
Also activates their Home cards (they were .card--pending) and closes the
nav ring across all six case studies.

All images are .ph placeholders with data-asset names, so the export session
is a checklist. All-or-nothing. Undo: git checkout .
"""
import re, sys, subprocess, pathlib

REPO   = pathlib.Path("/Users/wma/Desktop/portfolio")
BRANCH = "v3-restyle"
PAGES_CSS = """
/* ------------------------------------------------------------
   CASE STUDY — gallery blocks (Treat Week, RIPCO, West Elm)
   ------------------------------------------------------------ */
.cs-stack { display: flex; flex-direction: column; gap: var(--space-80); }

/* Five logo lockup explorations across */
.lockup-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: var(--space-24); }

/* Labelled brand-system subsection */
.brand-sys { display: flex; flex-direction: column; gap: var(--space-24); }
.brand-sys-label { color: var(--color-ink); }

/* Wide horizontal strips that overflow the 1080 column */
.cs-strip { overflow-x: auto; -webkit-overflow-scrolling: touch; padding-bottom: var(--space-8); }
.cs-strip > .ph { min-width: 1600px; }

@media (max-width: 900px) {
  .cs-stack { gap: var(--space-60); }
  .lockup-row { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 700px) {
  .lockup-row { grid-template-columns: repeat(2, 1fr); }
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
css_path = REPO / "css" / "site.css"
if not css_path.exists(): fail("css/site.css missing")
else:
    css = css_path.read_text()
    if ".ph {" not in css: fail("placeholder system missing - run apply_v3_ge.py first")
if errors:
    print("\nABORTED:"); [print("  x "+e) for e in errors]; sys.exit(1)

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

CL = '<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CR = '<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M6 3l5 5-5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def ph(w, h, asset, cls=""):
    c = ("ph " + cls).strip()
    return f'<div class="{c}" style="aspect-ratio:{w}/{h}" data-asset="{asset}"></div>'

def csnav(pslug, plabel, nslug, nlabel):
    return f'''    <nav class="cs-nav-outer" aria-label="Project navigation">
      <div class="cs-nav-divider"></div>
      <div class="cs-nav-row">
        <div class="cs-nav-side cs-nav-side--left">
          <a href="{pslug}" class="cs-nav-btn" aria-label="Previous project: {plabel}">{CL}</a>
          <a href="{pslug}" class="cs-nav-label">
            <span class="cs-nav-direction">Previous project:</span>
            <span class="cs-nav-project">{plabel}</span>
          </a>
        </div>
        <div class="cs-nav-side cs-nav-side--right">
          <a href="{nslug}" class="cs-nav-label" style="text-align:right;">
            <span class="cs-nav-direction">Next project:</span>
            <span class="cs-nav-project">{nlabel}</span>
          </a>
          <a href="{nslug}" class="cs-nav-btn" aria-label="Next project: {nlabel}">{CR}</a>
        </div>
      </div>
    </nav>'''

def shell(title, h1, sub, intro, hero_asset, body, nav):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} &#8212; Wilson Ma</title>
  <link rel="preload" href="/assets/fonts/Switzer-Variable.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="/css/site.css">
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

    <section class="hero" aria-label="{title}">
      <div class="hero-inner">
        <div class="hero-copy hero-copy--narrow fade-up">
          <h1 class="display-hero">{h1}</h1>
          <p class="heading-subhead hero-sub">{sub}</p>
          <p class="body-default hero-intro">{intro}</p>
        </div>
        <div class="hero-portrait ph ph--circle fade-up" data-asset="{hero_asset}" aria-hidden="true"></div>
      </div>
    </section>

    <section class="cs-body" aria-label="Gallery">
      <div class="cs-body-inner cs-stack">
{body}
      </div>
    </section>

{nav}

  </main>

{FOOTER}

</div><!-- .page -->
<script src="/js/site.js"></script>
</body>
</html>
'''

# ---------------------------------------------------------------- Treat Week
lockups = "\n          ".join(
    ph(159,159,f"treatweek/lockup-{i}.png") for i in range(1,6))
BRAND_SYS = "\n".join(
    f'''        <div class="brand-sys fade-up">
          <p class="brand-sys-label body-strong">{lbl}</p>
          {ph(1080,h,f"treatweek/{slug}.png")}
        </div>'''
    for lbl, slug, h in [("Logo","system-logo",249),("Typography","system-type",129),
                          ("Graphical Elements","system-graphics",253),("Color Palette","system-color",474)])

TW_BODY = f'''        <div class="fade-up">{ph(1080,479,"treatweek/01-campaign.png")}</div>
        <div class="lockup-row fade-up">
          {lockups}
        </div>
        <div class="fade-up">{ph(1080,200,"treatweek/02-band.png")}</div>
{BRAND_SYS}
        <div class="fade-up">{ph(1080,511,"treatweek/03-applications.png")}</div>
        <div class="fade-up">{ph(966,591,"treatweek/04-email.png")}</div>
        <div class="fade-up">{ph(1080,500,"treatweek/05-devices.png")}</div>'''

TW = shell("Treat Week", "Treat Week", "A brand built for a sale.",
  "Workhuman&#8217;s fall Store Sale had no identity of its own. Every year it borrowed whatever campaign assets were lying around, and employees treated it like background noise instead of a moment worth opening an email for.",
  "treatweek/hero.png", TW_BODY,
  csnav("/workhuman","Workhuman","/ripco","RIPCO Real Estate"))

# ---------------------------------------------------------------- RIPCO
RIPCO_BODY = f'''        <div class="fade-up">{ph(1080,1649,"ripco/01-work.png")}</div>
        <div class="cs-strip fade-up">{ph(4175,540,"ripco/02-strip.png")}</div>'''
RIPCO = shell("RIPCO Real Estate", "RIPCO Real Estate", "Commercial Real Estate",
  "RIPCO is one of the largest independent commercial real estate brokerages in the New York metro. As the sole production designer, I owned visual output across the firm: broker presentations, property marketing, signage, and the WordPress sites and eBlast campaigns that carried listings to market.",
  "ripco/hero.png", RIPCO_BODY,
  csnav("/treat-week","Treat Week","/west-elm","West Elm, Williams Sonoma"))

# ---------------------------------------------------------------- West Elm
WE_BODY = f'''        <div class="fade-up">{ph(1080,810,"westelm/01-devices.png")}</div>
        <div class="cs-strip fade-up">{ph(3891,639,"westelm/02-strip.png")}</div>'''
WE = shell("West Elm, Williams Sonoma", "West Elm,<br>Williams Sonoma",
  "Consumer Retail and Home Furnishings",
  "At West Elm I led digital design execution for D2C and B2B email programs spanning West Elm, Williams Sonoma, and Pottery Barn, reaching millions of subscribers weekly. I owned campaigns end to end, from concept through production, across main-line, Outlet, and cross-brand initiatives.",
  "westelm/hero.png", WE_BODY,
  csnav("/ripco","RIPCO Real Estate","/ge-terminal","GE Terminal"))

# ---------------------------------------------------------------- write set
pending = {}
for rel, content in [("treat-week/index.html", TW), ("ripco/index.html", RIPCO),
                     ("west-elm/index.html", WE)]:
    (REPO / rel).parent.mkdir(parents=True, exist_ok=True)
    pending[REPO / rel] = content
    note(f"{rel:26} {len(content.splitlines())} lines")

# GE Terminal prev -> West Elm (now exists); Marly next stays Workhuman
ge = REPO / "ge-terminal/index.html"
s = ge.read_text()
s2 = s.replace('href="/treat-week"', 'href="/west-elm"')
s2 = s2.replace('Previous project: Treat Week', 'Previous project: West Elm')
s2 = s2.replace('<span class="cs-nav-project">Treat Week</span>',
                '<span class="cs-nav-project">West Elm, Williams Sonoma</span>')
if s2 == s: fail("GE Terminal prev/next rewrite matched nothing")
pending[ge] = s2; note("ge-terminal   prev -> West Elm")

# Home: activate the two pending cards
home = REPO / "index.html"; h = home.read_text()
for slug, name in [("/west-elm","West Elm"), ("/ripco","RIPCO Real Estate")]:
    pat = re.compile(r'<span class="card card--pending">\s*<span class="card-title heading-card">'
                     + re.escape(name) + r'</span>(.*?)</span>', re.S)
    m = pat.search(h)
    if not m: fail(f"Home card not found: {name}")
    else:
        h = h.replace(m.group(0),
            f'<a href="{slug}" class="card">\n            <span class="card-title heading-card">{name}</span>{m.group(1)}</a>')
        note(f"home card activated: {name} -> {slug}")
h = re.sub(r'\s*<!-- Not linked until /(west-elm|ripco) exists -->', '', h)
if "card--pending" in h: fail("a pending card survived on Home")
pending[home] = h

new_css = css
if ".cs-stack {" not in new_css:
    a = "/* ---- CASE STUDY SHARED COMPONENTS ---- */"
    if a not in new_css: fail("case-study anchor missing")
    else: new_css = new_css.replace(a, PAGES_CSS.rstrip() + "\n\n" + a, 1); note("gallery CSS inserted")
pending[css_path] = new_css

print("\n" + "=" * 62); print("PLAN"); print("=" * 62)
[print("  - " + n) for n in notes]
if errors:
    print("\nABORTED - nothing written:"); [print("  x "+e) for e in errors]; sys.exit(1)
for p, c in pending.items(): p.write_text(c)

print("\n" + "=" * 62); print(f"WROTE {len(pending)} FILES"); print("=" * 62)
[print("  " + str(p.relative_to(REPO))) for p in pending]
print("\nRing: Marly -> Workhuman -> Treat Week -> RIPCO -> West Elm -> GE Terminal -> Marly")
print("Placeholders:  grep -rho 'data-asset=\"[^\"]*\"' --include=\"*.html\" . | sort | uniq -c")
print("\n  git add -A && git commit -m 'V3 Treat Week rebuild; RIPCO and West Elm pages' && git push")
