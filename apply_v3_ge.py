#!/usr/bin/env python3
"""
apply_v3_ge.py — GE Terminal rebuilt to V3, plus the site-wide placeholder system.

  1. CSS  : add .ph placeholder system + GE section styles; drop
            .hero-portrait--placeholder in favour of .ph .ph--circle
  2. HTML : rewrite ge-terminal/index.html (rb-* classes retired with it)
  3. MIGRATE: Home, About and Marly portrait circles -> .ph .ph--circle
            so one grep finds every outstanding asset site-wide

All-or-nothing. Undo: git checkout .
"""
import re, sys, subprocess, pathlib

REPO   = pathlib.Path("/Users/wma/Desktop/portfolio")
BRANCH = "v3-restyle"
GE_CSS = """
/* ------------------------------------------------------------
   PLACEHOLDER SYSTEM — every un-exported asset, site-wide.
   Merge gate: grep -rc 'class="[^"]*\bph\b' --include="*.html" .
   must return 0 before v3-restyle merges to main.
   ------------------------------------------------------------ */
.ph {
  display: block;
  width: 100%;
  position: relative;
  background: var(--color-background-acc);
  border: 1px solid var(--color-rule);
  border-radius: var(--radius-sm);
}
.ph::after {
  content: attr(data-asset);
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--type-micro);
  color: var(--color-ink-subtle);
  letter-spacing: var(--tracking-snug);
  text-align: center;
  padding: var(--space-8);
}
.ph--circle { border-radius: 50%; }
.hero-portrait.ph { height: 256px; }

/* ------------------------------------------------------------
   GE TERMINAL — numbered sections
   ------------------------------------------------------------ */
.ge-sections {
  display: flex;
  flex-direction: column;
  gap: var(--space-120);
}
.ge-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-40);
}
.ge-head {
  display: flex;
  flex-direction: column;
  gap: var(--space-16);
  max-width: 1032px;
}
.ge-num { color: var(--color-ink-muted); }
.ge-title { color: var(--color-ink); }
.ge-body { color: var(--color-ink-muted); max-width: 720px; }
.ge-body + .ge-body { margin-top: var(--space-16); }

.ge-quote {
  margin: 0;
  color: var(--color-ink);
  max-width: 720px;
}
.ge-callout {
  margin: 0;
  padding: var(--space-32);
  border-left: 2px solid var(--color-accent);
  background: var(--color-background-acc);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
}
.ge-caption { color: var(--color-ink-muted); }

.ge-split {
  display: flex;
  align-items: flex-start;
  gap: var(--space-80);
}
.ge-split-copy { flex: 1 1 409px; max-width: 409px; }
.ge-split-visual { flex: 1 1 591px; max-width: 591px; }

@media (max-width: 900px) {
  .ge-sections { gap: var(--space-80); }
  .ge-split { flex-direction: column; gap: var(--space-40); }
  .ge-split-copy, .ge-split-visual { max-width: none; flex: 1 1 auto; width: 100%; }
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
targets  = ["index.html", "about/index.html", "marly/index.html"]
for rel in targets + ["ge-terminal/index.html"]:
    if not (REPO / rel).exists(): fail(f"missing: {rel}")
if not css_path.exists(): fail("css/site.css missing")
if errors:
    print("\nABORTED - nothing written:"); [print("  x "+e) for e in errors]; sys.exit(1)

css = css_path.read_text()

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

def ph(w, h, asset):
    return f'<div class="ph" style="aspect-ratio:{w}/{h}" data-asset="{asset}"></div>'

SECTIONS = [
  ("01", "Problem",
   ["Flipping items on the Grand Exchange is a decision-making problem under noisy data. Prices spike and crash hourly, some items dump on predictable cycles, and the wiki&#8217;s raw price API tells you what happened without telling you what it means.",
    "Every trade came down to the same question:"],
   [ph(683,349,"ge-terminal/01-signal.png"),
    '<blockquote class="ge-quote heading-subhead">&#8220;Is this signal real, or am I about to chase a correction?&#8221;</blockquote>']),

  ("02", "The Signal Engine",
   ["GE Terminal answers that with a layered signal engine. It pulls live and historical prices across four timeframes, scores movers on momentum and volume, then runs each candidate through graded buy and sell checklists before anything surfaces as an action."],
   [ph(1080,623,"ge-terminal/02-engine.png"),
    '<p class="ge-callout body-default">The algorithm serves the interface, and the interface serves a decision a human has to make under uncertainty.</p>',
    '<p class="ge-body body-default">A verdict engine weighs 7-day, 30-day, and 90-day percentile position into plain-English calls, from SELL NOW to DON&#8217;T SELL, each with its reasoning attached. Nothing appears on screen without a letter-grade and a reason why.</p>']),

  ("03", "The Override Layer",
   ["The most interesting engineering is the override layer. Momentum algorithms chase corrections they shouldn&#8217;t trust, so GE Terminal runs a two-layer regime-break check:",
    "When longer-timeframe structure contradicts a short-term signal, the label gets hard-replaced and the grade takes a penalty.",
    "The machine still surfaces the signal, but it arrives demoted, with the disagreement visible. That pattern, letting a system flag its own uncertainty instead of hiding it, is the thing I keep taking into design work with AI systems."],
   [ph(1080,446,"ge-terminal/03-override.png"),
    '<p class="ge-caption meta-caption">Dump detection doesn&#8217;t just classify the drop, it also measures how long recovery historically takes.</p>']),

  ("04", "Daily Operation",
   ["Running daily, positions, realized P&amp;L, and a full signal history persist all locally. A Discord webhook fires alerts only when a signal passes every metric gate, because an alert you learn to ignore is worse than no alert."],
   [ph(1080,470,"ge-terminal/04-daily.png")]),
]

sec_html = []
for num, title, paras, blocks in SECTIONS:
    body = "\n            ".join(f'<p class="ge-body body-default">{p}</p>' for p in paras)
    extra = "\n          ".join(blocks)
    sec_html.append(f'''        <section class="ge-section fade-up">
          <div class="ge-head">
            <p class="ge-num heading-wordmark">{num}</p>
            <h2 class="ge-title display-page">{title}</h2>
            {body}
          </div>
          {extra}
        </section>''')

ORIGIN = f'''        <section class="ge-section fade-up">
          <div class="ge-split">
            <div class="ge-split-copy">
              <p class="ge-num heading-wordmark">05</p>
              <h2 class="ge-title display-page">Origin</h2>
              <p class="ge-body body-default">I started this with zero Python background. GE Terminal became a way to learn by building something I&#8217;d actually use. 18+ versions later, it isn&#8217;t shipped software, but it&#8217;s built like it wants to be: cached API layers, state persistence, alert thresholds a user can trust.</p>
              <p class="ge-body body-default">It&#8217;s what happens when the barrier between an idea and a working tool gets low enough that a designer stops waiting for an engineer.</p>
            </div>
            <div class="ge-split-visual">{ph(591,406,"ge-terminal/05-origin.png")}</div>
          </div>
        </section>'''

PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GE Terminal &#8212; Wilson Ma</title>
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

    <section class="hero" aria-label="GE Terminal">
      <div class="hero-inner">
        <div class="hero-copy hero-copy--narrow fade-up">
          <h1 class="display-hero">GE Terminal</h1>
          <p class="heading-subhead hero-sub">Bloomberg for a game economy.</p>
          <p class="body-default hero-intro">The Grand Exchange is Old School RuneScape&#8217;s player-driven commodities market: 3,000+ items, real volatility, visible volume, and nothing but a raw price API to read it with. GE Terminal is the market intelligence terminal I built and run daily, with a layered signal engine, verdicts that explain themselves, and an override that keeps a human in the loop.</p>
        </div>
        <div class="hero-portrait ph ph--circle fade-up" data-asset="ge-terminal/hero.png" aria-hidden="true"></div>
      </div>
    </section>

    <section class="cs-body" aria-label="Case study">
      <div class="cs-body-inner ge-sections">
{chr(10).join(sec_html)}
{ORIGIN}
      </div>
    </section>

    <nav class="cs-nav-outer" aria-label="Project navigation">
      <div class="cs-nav-divider"></div>
      <div class="cs-nav-row">
        <div class="cs-nav-side cs-nav-side--left">
          <a href="/west-elm" class="cs-nav-btn" aria-label="Previous project: West Elm">{CL}</a>
          <a href="/west-elm" class="cs-nav-label">
            <span class="cs-nav-direction">Previous project:</span>
            <span class="cs-nav-project">West Elm, Williams Sonoma</span>
          </a>
        </div>
        <div class="cs-nav-side cs-nav-side--right">
          <a href="/marly" class="cs-nav-label" style="text-align:right;">
            <span class="cs-nav-direction">Next project:</span>
            <span class="cs-nav-project">MARLY Creative Concepts</span>
          </a>
          <a href="/marly" class="cs-nav-btn" aria-label="Next project: MARLY Creative Concepts">{CR}</a>
        </div>
      </div>
    </nav>

  </main>

{FOOTER}

</div><!-- .page -->
<script src="/js/site.js"></script>
</body>
</html>
'''

# ------------------------------------------------------------------ css
new_css = css
if ".ph {" not in new_css:
    anchor = "/* ---- CASE STUDY SHARED COMPONENTS ---- */"
    if anchor not in new_css: fail("case-study anchor missing")
    else:
        new_css = new_css.replace(anchor, GE_CSS.rstrip() + "\n\n" + anchor, 1)
        note("placeholder system + GE section CSS inserted")

old_ph = re.search(r'\.hero-portrait--placeholder \{[^}]*\}\n', new_css)
if old_ph:
    new_css = new_css.replace(old_ph.group(0), "", 1)
    note(".hero-portrait--placeholder removed (superseded by .ph)")

# ------------------------------------------------------------------ html
pending = {css_path: new_css, REPO / "ge-terminal/index.html": PAGE}
ASSET = {"index.html": "home/portrait.png", "about/index.html": "about/portrait.png",
         "marly/index.html": "marly/portrait.png"}
for rel in targets:
    p = REPO / rel
    out, n = re.subn(r'class="hero-portrait hero-portrait--placeholder([^"]*)"',
                     lambda m: f'class="hero-portrait ph ph--circle{m.group(1)}" data-asset="{ASSET[rel]}"',
                     p.read_text())
    if n != 1: fail(f"{rel}: expected 1 portrait placeholder, found {n}")
    else: note(f"{rel:22} portrait -> .ph")
    pending[p] = out

for gone in ("rb-section", "rb-img", "rb-text", "Runeberg"):
    if gone in PAGE: fail(f"legacy class survived: {gone}")

print("\n" + "=" * 62); print("PLAN"); print("=" * 62)
[print("  - " + n) for n in notes]
if errors:
    print("\nABORTED - nothing written:"); [print("  x "+e) for e in errors]; sys.exit(1)

for path, content in pending.items(): path.write_text(content)
print("\n" + "=" * 62); print(f"WROTE {len(pending)} FILES"); print("=" * 62)
[print("  " + str(p.relative_to(REPO))) for p in pending]
print("\nOutstanding placeholders:")
print("  grep -rho 'data-asset=\"[^\"]*\"' --include=\"*.html\" . | sort | uniq -c")
print("\n  git add -A && git commit -m 'V3 GE Terminal; site-wide .ph placeholder system'")
print("Undo:  git checkout .")
