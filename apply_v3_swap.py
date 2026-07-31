#!/usr/bin/env python3
"""
apply_v3_swap.py — replace all .ph placeholders with real <img> elements.

Run AFTER export_figma_assets.py has completed. All 38 exported assets
must exist in /assets/ before this script will proceed.

Two placeholders are not swapped here — their nodes were not in the export:
  - marly/portrait.png
  - workhuman/hero.png
These remain as .ph until exported separately.

Changes made:
  - home, about, ge-terminal, treat-week, ripco, west-elm: portrait → div > img
  - ge-terminal: 01-signal renamed to 01-problem; 02-callout inserted
  - treat-week: all path renames (lockup-*, system-*, band, applications, etc.)
  - ripco: single strip → 5 individual slide images
  - west-elm: single strip → 5 individual slide images
  - site.css: hero-portrait > img rule + cs-strip flex rule

All-or-nothing. Undo: git checkout .
"""
import pathlib, subprocess, sys

REPO   = pathlib.Path("/Users/wma/Desktop/portfolio")
BRANCH = "v3-restyle"

# All 38 assets from export_figma_assets.py (1x sizes for HTML width/height attrs)
EXPORTS = [
    ("about/portrait",               341, 317),
    ("home/portrait",                284, 261),
    ("ge-terminal/hero",             380, 291),
    ("ge-terminal/01-problem",       708, 349),
    ("ge-terminal/02-engine",       1079, 544),
    ("ge-terminal/02-callout",       480, 131),
    ("ge-terminal/03-override",     1080, 446),
    ("ge-terminal/04-daily",        1080, 470),
    ("ge-terminal/05-origin",        591, 408),
    ("treatweek/hero",               380, 242),
    ("treatweek/01-campaign",       1080, 479),
    ("treatweek/02-lockup-1",        160, 160),
    ("treatweek/02-lockup-2",        160, 160),
    ("treatweek/02-lockup-3",        160, 160),
    ("treatweek/02-lockup-4",        160, 160),
    ("treatweek/02-lockup-5",        160, 160),
    ("treatweek/03-band",           1080, 200),
    ("treatweek/04-system-logo",    1080, 239),
    ("treatweek/04-system-type",    1080, 103),
    ("treatweek/04-system-graphics",1080, 253),
    ("treatweek/04-system-color",   1080, 474),
    ("treatweek/05-applications",   1080, 511),
    ("treatweek/06-email",           966, 591),
    ("treatweek/07-devices",        1080, 500),
    ("ripco/hero",                   380, 307),
    ("ripco/01-work",               1080, 1649),
    ("ripco/02-slide-1",             842, 540),
    ("ripco/02-slide-2",             701, 540),
    ("ripco/02-slide-3",             703, 540),
    ("ripco/02-slide-4",             809, 540),
    ("ripco/02-slide-5",             960, 540),
    ("westelm/hero",                 379, 473),
    ("westelm/01-devices",          1080, 810),
    ("westelm/02-slide-1",           655, 680),
    ("westelm/02-slide-2",          1187, 680),
    ("westelm/02-slide-3",           834, 680),
    ("westelm/02-slide-4",           568, 680),
    ("westelm/02-slide-5",           610, 680),
]
EXP_DIM = {p: (w, h) for p, w, h in EXPORTS}

def img_tag(path, w, h, lazy=True):
    return f'<img src="/assets/{path}.png" width="{w}" height="{h}" alt="" loading="{"lazy" if lazy else "eager"}">'

errors, notes = [], []
def fail(m): errors.append(m)
def note(m): notes.append(m)
def git(*a): return subprocess.run(["git","-C",str(REPO)]+list(a),
                                   capture_output=True, text=True).stdout.strip()

print("=" * 64); print("PRECONDITIONS"); print("=" * 64)
b, d = git("rev-parse","--abbrev-ref","HEAD"), git("status","--porcelain")
print(f"  branch : {b}\n  tree   : {'clean' if not d else 'DIRTY'}")
if b != BRANCH: fail(f"expected branch {BRANCH}, found {b}")
if d: fail("uncommitted changes — commit or stash first")

missing = [p for p,_,_ in EXPORTS if not (REPO/"assets"/(p+".png")).exists()]
if missing:
    for m in missing: print("  x missing: assets/" + m + ".png")
    fail(f"{len(missing)} exported assets not found — run export_figma_assets.py first")

if errors:
    print("\nABORTED:"); [print("  x "+e) for e in errors]; sys.exit(1)

pending = {}

# ── helper: portrait div → div > img ─────────────────────────────────────────
def swap_portrait(src, old_asset, new_path):
    w, h = EXP_DIM[new_path]
    old = f'<div class="hero-portrait ph ph--circle fade-up" data-asset="{old_asset}" aria-hidden="true"></div>'
    new = f'<div class="hero-portrait fade-up" aria-hidden="true">{img_tag(new_path, w, h, lazy=False)}</div>'
    out = src.replace(old, new, 1)
    return out, out != src

# ── helper: generic .ph div → img ────────────────────────────────────────────
def swap_ph(src, old_asset, old_ar_w, old_ar_h, new_path, new_w, new_h, lazy=True):
    old = f'<div class="ph" style="aspect-ratio:{old_ar_w}/{old_ar_h}" data-asset="{old_asset}"></div>'
    new = img_tag(new_path, new_w, new_h, lazy)
    out = src.replace(old, new, 1)
    return out, out != src

# ── GE Terminal ───────────────────────────────────────────────────────────────
ge_p = REPO / "ge-terminal/index.html"
ge = ge_p.read_text(); ge_ok = []

ge, ok = swap_portrait(ge, "ge-terminal/hero.png", "ge-terminal/hero"); ge_ok.append(("hero portrait", ok))
ge, ok = swap_ph(ge, "ge-terminal/01-signal.png",  683, 349, "ge-terminal/01-problem",  708, 349); ge_ok.append(("01-signal → 01-problem", ok))
ge, ok = swap_ph(ge, "ge-terminal/02-engine.png",  1080,623, "ge-terminal/02-engine",  1079, 544); ge_ok.append(("02-engine", ok))
ge, ok = swap_ph(ge, "ge-terminal/03-override.png",1080,446, "ge-terminal/03-override",1080, 446); ge_ok.append(("03-override", ok))
ge, ok = swap_ph(ge, "ge-terminal/04-daily.png",   1080,470, "ge-terminal/04-daily",   1080, 470); ge_ok.append(("04-daily", ok))
ge, ok = swap_ph(ge, "ge-terminal/05-origin.png",  591, 406, "ge-terminal/05-origin",   591, 408); ge_ok.append(("05-origin", ok))

# insert 02-callout img directly after 02-engine img
engine_tag = img_tag("ge-terminal/02-engine", 1079, 544)
callout_tag = img_tag("ge-terminal/02-callout", 480, 131)
if engine_tag in ge and callout_tag not in ge:
    ge = ge.replace(engine_tag, engine_tag + "\n          " + callout_tag, 1)
    ge_ok.append(("02-callout inserted", True))
else:
    ge_ok.append(("02-callout", engine_tag not in ge))
    if engine_tag not in ge: fail("ge-terminal: 02-engine img not found for callout insertion")

for name, ok in ge_ok:
    if not ok: fail(f"ge-terminal: {name} — swap failed")
pending[ge_p] = ge
note(f"ge-terminal: {sum(ok for _,ok in ge_ok)}/{len(ge_ok)} operations")

# ── Treat Week ────────────────────────────────────────────────────────────────
tw_p = REPO / "treat-week/index.html"
tw = tw_p.read_text(); tw_ok = []

tw, ok = swap_portrait(tw, "treatweek/hero.png", "treatweek/hero"); tw_ok.append(("hero portrait", ok))
tw, ok = swap_ph(tw, "treatweek/01-campaign.png",    1080,479, "treatweek/01-campaign",      1080,479); tw_ok.append(("01-campaign", ok))
tw, ok = swap_ph(tw, "treatweek/lockup-1.png",        159,159, "treatweek/02-lockup-1",       160,160); tw_ok.append(("lockup-1", ok))
tw, ok = swap_ph(tw, "treatweek/lockup-2.png",        159,159, "treatweek/02-lockup-2",       160,160); tw_ok.append(("lockup-2", ok))
tw, ok = swap_ph(tw, "treatweek/lockup-3.png",        159,159, "treatweek/02-lockup-3",       160,160); tw_ok.append(("lockup-3", ok))
tw, ok = swap_ph(tw, "treatweek/lockup-4.png",        159,159, "treatweek/02-lockup-4",       160,160); tw_ok.append(("lockup-4", ok))
tw, ok = swap_ph(tw, "treatweek/lockup-5.png",        159,159, "treatweek/02-lockup-5",       160,160); tw_ok.append(("lockup-5", ok))
tw, ok = swap_ph(tw, "treatweek/02-band.png",         1080,200,"treatweek/03-band",          1080,200); tw_ok.append(("02-band → 03-band", ok))
tw, ok = swap_ph(tw, "treatweek/system-logo.png",     1080,249,"treatweek/04-system-logo",   1080,239); tw_ok.append(("system-logo", ok))
tw, ok = swap_ph(tw, "treatweek/system-type.png",     1080,129,"treatweek/04-system-type",   1080,103); tw_ok.append(("system-type", ok))
tw, ok = swap_ph(tw, "treatweek/system-graphics.png", 1080,253,"treatweek/04-system-graphics",1080,253); tw_ok.append(("system-graphics", ok))
tw, ok = swap_ph(tw, "treatweek/system-color.png",    1080,474,"treatweek/04-system-color",  1080,474); tw_ok.append(("system-color", ok))
tw, ok = swap_ph(tw, "treatweek/03-applications.png", 1080,511,"treatweek/05-applications",  1080,511); tw_ok.append(("03-applications → 05", ok))
tw, ok = swap_ph(tw, "treatweek/04-email.png",         966,591,"treatweek/06-email",          966,591); tw_ok.append(("04-email → 06", ok))
tw, ok = swap_ph(tw, "treatweek/05-devices.png",      1080,500,"treatweek/07-devices",       1080,500); tw_ok.append(("05-devices → 07", ok))

for name, ok in tw_ok:
    if not ok: fail(f"treat-week: {name} — swap failed")
pending[tw_p] = tw
note(f"treat-week: {sum(ok for _,ok in tw_ok)}/{len(tw_ok)} swaps")

# ── RIPCO ─────────────────────────────────────────────────────────────────────
ri_p = REPO / "ripco/index.html"
ri = ri_p.read_text(); ri_ok = []

ri, ok = swap_portrait(ri, "ripco/hero.png", "ripco/hero"); ri_ok.append(("hero portrait", ok))
ri, ok = swap_ph(ri, "ripco/01-work.png", 1080, 1649, "ripco/01-work", 1080, 1649); ri_ok.append(("01-work", ok))

RIPCO_OLD = '<div class="cs-strip fade-up"><div class="ph" style="aspect-ratio:4175/540" data-asset="ripco/02-strip.png"></div></div>'
RIPCO_SLIDES = "\n        ".join(img_tag(f"ripco/02-slide-{i+1}", w, 540)
                                 for i, w in enumerate([842, 701, 703, 809, 960]))
RIPCO_NEW = f'<div class="cs-strip fade-up">\n        {RIPCO_SLIDES}\n      </div>'
if RIPCO_OLD in ri:
    ri = ri.replace(RIPCO_OLD, RIPCO_NEW, 1); ri_ok.append(("02-strip → 5 slides", True))
else:
    ri_ok.append(("02-strip", False)); fail("ripco: strip placeholder not found")

for name, ok in ri_ok:
    if not ok: fail(f"ripco: {name} — swap failed")
pending[ri_p] = ri
note(f"ripco: {sum(ok for _,ok in ri_ok)}/{len(ri_ok)} swaps (strip → 5 slides)")

# ── West Elm ──────────────────────────────────────────────────────────────────
we_p = REPO / "west-elm/index.html"
we = we_p.read_text(); we_ok = []

we, ok = swap_portrait(we, "westelm/hero.png", "westelm/hero"); we_ok.append(("hero portrait", ok))
we, ok = swap_ph(we, "westelm/01-devices.png", 1080, 810, "westelm/01-devices", 1080, 810); we_ok.append(("01-devices", ok))

WE_OLD = '<div class="cs-strip fade-up"><div class="ph" style="aspect-ratio:3891/639" data-asset="westelm/02-strip.png"></div></div>'
WE_SLIDES = "\n        ".join(img_tag(f"westelm/02-slide-{i+1}", w, 680)
                               for i, w in enumerate([655, 1187, 834, 568, 610]))
WE_NEW = f'<div class="cs-strip fade-up">\n        {WE_SLIDES}\n      </div>'
if WE_OLD in we:
    we = we.replace(WE_OLD, WE_NEW, 1); we_ok.append(("02-strip → 5 slides", True))
else:
    we_ok.append(("02-strip", False)); fail("west-elm: strip placeholder not found")

for name, ok in we_ok:
    if not ok: fail(f"west-elm: {name} — swap failed")
pending[we_p] = we
note(f"west-elm: {sum(ok for _,ok in we_ok)}/{len(we_ok)} swaps (strip → 5 slides)")

# ── Home ──────────────────────────────────────────────────────────────────────
home_p = REPO / "index.html"
home = home_p.read_text()
home, ok = swap_portrait(home, "home/portrait.png", "home/portrait")
if not ok: fail("index.html: home portrait swap failed")
else: note("index.html: home portrait swapped")
pending[home_p] = home

# ── About ─────────────────────────────────────────────────────────────────────
about_p = REPO / "about/index.html"
about = about_p.read_text()
about, ok = swap_portrait(about, "about/portrait.png", "about/portrait")
if not ok: fail("about/index.html: portrait swap failed")
else: note("about/index.html: portrait swapped")
pending[about_p] = about

# ── site.css ─────────────────────────────────────────────────────────────────
css_p = REPO / "css/site.css"
css = css_p.read_text()

PORTRAIT_IMG_RULE = """\n/* portrait images — circular crop after .ph is replaced */
.hero-portrait > img {
  display: block;
  width: 256px;
  height: 256px;
  object-fit: cover;
  border-radius: 50%;
}
"""
if ".hero-portrait > img" not in css:
    target = """.hero-portrait {
  width: 256px;
  height: auto;
  flex-shrink: 0;
}"""
    if target in css:
        css = css.replace(target, target + PORTRAIT_IMG_RULE, 1)
        note("site.css: .hero-portrait > img rule added")
    else:
        fail("site.css: .hero-portrait block not found for portrait-img insertion")

STRIP_OLD = '.cs-strip { overflow-x: auto; -webkit-overflow-scrolling: touch; padding-bottom: var(--space-8); }\n.cs-strip > .ph { min-width: 1600px; }'
STRIP_NEW = '.cs-strip { display: flex; gap: var(--space-4); overflow-x: auto; -webkit-overflow-scrolling: touch; align-items: flex-start; }\n.cs-strip > img { flex-shrink: 0; height: auto; }'
if STRIP_OLD in css:
    css = css.replace(STRIP_OLD, STRIP_NEW, 1)
    note("site.css: .cs-strip → flex row, .cs-strip > .ph rule removed")
elif STRIP_NEW not in css:
    fail("site.css: .cs-strip pattern not found — update manually")

pending[css_p] = css

# ── write ─────────────────────────────────────────────────────────────────────
print("\nPLAN"); [print("  + " + n) for n in notes]
if errors:
    print("\nABORTED — nothing written:"); [print("  x " + e) for e in errors]; sys.exit(1)

for p, content in pending.items():
    p.write_text(content)

print(f"\nWROTE {len(pending)} files")
[print("  " + str(p.relative_to(REPO))) for p in pending]

# ── remaining placeholder count ───────────────────────────────────────────────
import re
remaining = []
for f in sorted(REPO.rglob("*.html")):
    for i, line in enumerate(f.read_text().splitlines(), 1):
        if re.search(r'class="[^"]*\bph\b[^"]*"', line):
            remaining.append(f"{f.relative_to(REPO)}:{i}: {line.strip()[:70]}")

print(f"\nPlaceholders remaining: {len(remaining)}")
for r in remaining: print("  " + r)
if remaining:
    print("\n  (marly/portrait.png and workhuman/hero.png are expected — export those nodes to clear)")

print("\n  git add -A && git commit -m 'V3 swap: replace .ph placeholders with real images' && git push")
print("Undo:  git checkout .")
