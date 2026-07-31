#!/usr/bin/env python3
# apply_v3_workhuman3.py - close the last two gaps.
#
#   1. HERO : replace the cs-hero-outer / cs-hero-feature block with the
#             shared V3 hero (copy left, portrait circle right), matching
#             every other page. Copy taken verbatim from the V3 Figma.
#   2. TYPE : .ch-eyebrow / .ch-title / .ch-subhead are private Workhuman
#             classes. Rather than re-classing 15 nodes, they are redefined
#             at the end of the inline <style> to resolve to the shared
#             scale - same specificity, later in source order, so they win.
#
# Chapter content and all 28 screenshots are untouched.
# All-or-nothing. Undo: git checkout .

import re, sys, subprocess, pathlib

REPO = pathlib.Path("/Users/wma/Desktop/portfolio")
WH   = REPO / "workhuman" / "index.html"

HERO = '''    <section class="hero" aria-label="Workhuman">
      <div class="hero-inner">
        <div class="hero-copy hero-copy--narrow fade-up">
          <h1 class="display-hero">Workhuman</h1>
          <p class="heading-card hero-sub">Same instinct, five layers.</p>
          <p class="body-default hero-intro">Workhuman is a B2B SaaS platform for employee recognition. Over four years I worked across conversion design, product systems, production infrastructure, creative technology, and interactive tooling &#8212; different problems at different scales, but the same underlying move: identify the problem, build the solution.</p>
        </div>
        <div class="hero-portrait ph ph--circle fade-up" data-asset="workhuman/hero.png" aria-hidden="true"></div>
      </div>
    </section>'''

TYPE_MAP = '''
/* V3 alignment: Workhuman's private heading classes resolve to the shared
   scale. Defined last so they win on source order, no markup re-classing. */
.ch-eyebrow {
  font-size: var(--type-section);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-normal);
  color: var(--color-ink-muted);
}
.ch-title {
  font-size: var(--type-display);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-normal);
  color: var(--color-ink);
}
.ch-subhead {
  font-size: var(--type-subhead);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-normal);
  color: var(--color-ink);
}
.ch-header { display: flex; flex-direction: column; gap: var(--space-16); }
'''

errors, notes = [], []
def fail(m): errors.append(m)
def git(*a): return subprocess.run(["git","-C",str(REPO)]+list(a),
                                   capture_output=True, text=True).stdout.strip()

print("=" * 62); print("PRECONDITIONS"); print("=" * 62)
b, d = git("rev-parse","--abbrev-ref","HEAD"), git("status","--porcelain")
print("  branch : " + b)
print("  tree   : " + ("clean" if not d else "DIRTY"))
if d: fail("uncommitted changes - commit or stash first")
if not WH.exists(): fail("workhuman/index.html missing")
if errors:
    print("\nABORTED:"); [print("  x " + e) for e in errors]; sys.exit(1)

src = WH.read_text()

# --- 1. hero -------------------------------------------------------------
m = re.search(r'[ \t]*<(section|div)[^>]*class="[^"]*cs-hero-outer[^"]*"[^>]*>.*?</\1>\s*',
              src, re.S)
if not m:
    fail("cs-hero-outer block not found - inspect the markup manually")
else:
    before = m.group(0)
    print("\n  replacing %d lines of V2 hero markup" % len(before.splitlines()))
    src = src.replace(before, HERO + "\n\n", 1)
    notes.append("V3 hero written (copy left, portrait circle right)")

n_rem = src.count("cs-hero-")
if n_rem: fail("cs-hero-* remnants survive in markup: %d" % n_rem)

# --- 2. type map ---------------------------------------------------------
if "--type-display" not in src.split("</style>")[0][-2000:]:
    if "</style>" not in src:
        fail("no inline <style> block found")
    else:
        src = src.replace("</style>", TYPE_MAP + "  </style>", 1)
        notes.append("ch-eyebrow / ch-title / ch-subhead mapped to shared scale")

# --- verify --------------------------------------------------------------
for need in ('class="hero-inner"', 'class="display-hero"',
             'hero-portrait ph ph--circle', 'data-asset="workhuman/hero.png"'):
    if need not in src: fail("missing after rewrite: " + need)

print("\nPLAN"); [print("  - " + n) for n in notes]
if errors:
    print("\nABORTED - nothing written:"); [print("  x " + e) for e in errors]; sys.exit(1)

WH.write_text(src)
print("\nWROTE  workhuman/index.html")
print("Placeholders now 32 (workhuman/hero.png added)")
print("\n  git add -A && git commit -m 'Workhuman: V3 hero, map chapter headings to shared type scale' && git push")
print("Undo:  git checkout .")
