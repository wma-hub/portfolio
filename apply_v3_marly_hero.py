#!/usr/bin/env python3
"""
apply_v3_marly_hero.py — wire the Marly hero ad slot + snap both carousels.

marly/portrait.png is not a Figma node. The hero circle is a live rotating
300x250 slot using the six unit-b.html brands in reverse order, so it never
shows the same brand as the body slot (which runs forward). initSlot uses only
the global ROTATE_MS; natural jitter [12000,16000] plus reverse order is enough.

Changes:
  1. marly/index.html: .ph hero-portrait div → <div id="slot-hero">
  2. marly/index.html: initSlot({id:'slot-hero',...}) before AD_SLOTS.forEach
  3. site.css: scroll-snap-type + scroll-snap-align on .cs-strip / .cs-strip > img

After this run the only remaining placeholder is workhuman/hero.png.
All-or-nothing. Undo: git checkout .
"""
import pathlib, re, subprocess, sys

REPO   = pathlib.Path("/Users/wma/Desktop/portfolio")
BRANCH = "v3-restyle"

errors, notes = [], []
def fail(m): errors.append(m)
def note(m): notes.append(m)
def git(*a): return subprocess.run(["git","-C",str(REPO)]+list(a),
                                   capture_output=True, text=True).stdout.strip()

print("=" * 62); print("PRECONDITIONS"); print("=" * 62)
b = git("rev-parse","--abbrev-ref","HEAD")
d = git("status","--porcelain","--untracked-files=no")
print(f"  branch : {b}\n  tracked changes: {'none' if not d else 'DIRTY'}")
if b != BRANCH: fail(f"expected branch {BRANCH}, found {b}")
if d: fail("uncommitted tracked changes — commit or stash first")
if errors:
    print("\nABORTED:"); [print("  x " + e) for e in errors]; sys.exit(1)

pending = {}

# ── 1+2. marly/index.html ─────────────────────────────────────────────────────
marly_p = REPO / "marly/index.html"
marly   = marly_p.read_text()

OLD_PH  = ('<div class="hero-portrait ph ph--circle fade-up"'
           ' data-asset="marly/portrait.png" aria-hidden="true"></div>')
NEW_DIV = ('<div class="ad-slot" style="width:300px;height:250px;"'
           ' id="slot-hero" aria-label="Marly client work sample"></div>')
if OLD_PH in marly:
    marly = marly.replace(OLD_PH, NEW_DIV, 1)
    note("hero-portrait .ph → #slot-hero ad-slot div")
else:
    fail("marly: hero-portrait .ph placeholder not found")

FOREACH = "AD_SLOTS.forEach(function(cfg) { initSlot(cfg); });"
HERO_INIT = """\
initSlot({ id: 'slot-hero', nativeW: 300, nativeH: 250, displayW: 300,
  units: [
    { src: '/marly-work/tumblerware/unit-b.html', label: 'Tumblerware' },
    { src: '/marly-work/ghia/unit-b.html',        label: 'Ghia' },
    { src: '/marly-work/byredo/unit-b.html',      label: 'Byredo' },
    { src: '/marly-work/graza/unit-b.html',       label: 'Graza' },
    { src: '/marly-work/ritual/unit-b.html',      label: 'Ritual' },
    { src: '/marly-work/magic-spoon/unit-b.html', label: 'Magic Spoon' }
  ]
});
"""
if FOREACH in marly and "slot-hero" not in marly.split(FOREACH)[0]:
    marly = marly.replace(FOREACH, HERO_INIT + FOREACH, 1)
    note("slot-hero initSlot call inserted before AD_SLOTS.forEach (reverse unit-b order)")
elif "slot-hero" in marly.split(FOREACH)[0]:
    note("slot-hero init already present — skipped")
else:
    fail("marly: AD_SLOTS.forEach anchor not found")

if "marly/portrait.png" in marly:
    fail("marly/portrait.png survived the rewrite — inspect manually")
if "slot-hero" not in marly:
    fail("slot-hero missing after rewrite")

pending[marly_p] = marly

# ── 3. site.css: scroll-snap on both .cs-strip carousels ─────────────────────
css_p = REPO / "css/site.css"
css   = css_p.read_text()

OLD_STRIP = (
    ".cs-strip { display: flex; gap: var(--space-4); overflow-x: auto;"
    " -webkit-overflow-scrolling: touch; align-items: flex-start; }\n"
    ".cs-strip > img { flex-shrink: 0; height: auto; }"
)
NEW_STRIP = (
    ".cs-strip { display: flex; gap: var(--space-4); overflow-x: auto;"
    " -webkit-overflow-scrolling: touch; align-items: flex-start;"
    " scroll-snap-type: x mandatory; }\n"
    ".cs-strip > img { flex-shrink: 0; height: auto; scroll-snap-align: start; }"
)
if OLD_STRIP in css:
    css = css.replace(OLD_STRIP, NEW_STRIP, 1)
    note("site.css: scroll-snap-type mandatory on .cs-strip, scroll-snap-align start on > img")
    pending[css_p] = css
elif NEW_STRIP in css:
    note("site.css: scroll-snap already present — skipped")
else:
    fail("site.css: .cs-strip pattern not found — update manually")

# ── write ─────────────────────────────────────────────────────────────────────
print("\nPLAN"); [print("  + " + n) for n in notes]
if errors:
    print("\nABORTED — nothing written:"); [print("  x " + e) for e in errors]; sys.exit(1)

for p, content in pending.items():
    p.write_text(content)
print(f"\nWROTE {len(pending)} files")
[print("  " + str(p.relative_to(REPO))) for p in pending]

remaining = []
for f in sorted(REPO.rglob("*.html")):
    for i, line in enumerate(f.read_text().splitlines(), 1):
        if re.search(r'class="[^"]*\bph\b[^"]*"', line):
            remaining.append(f"{f.relative_to(REPO)}:{i}: {line.strip()[:70]}")
print(f"\nPlaceholders remaining: {len(remaining)}")
for r in remaining: print("  " + r)

print("\n  git add -A && git commit -m 'V3 Marly: wire hero ad slot; scroll-snap on RIPCO+West Elm carousels' && git push")
print("Undo:  git checkout .")
