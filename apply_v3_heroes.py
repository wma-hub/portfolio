#!/usr/bin/env python3
# apply_v3_heroes.py - final hero pass.
#
#  1. Swap Workhuman's last .ph for assets/workhuman/hero.png (verified first).
#  2. Size every hero visual to its design width instead of the 256px circle
#     left over from the placeholder system:
#         Home 284 | About 341 | case studies 380
#  3. Drop border-radius from hero images. The circular crop and the arcs are
#     baked into the exported PNGs - every hero group in Figma carries 2-3
#     ellipses - so a CSS circle crops an already-round image a second time.
#
# Self-inspecting: prints the markup it finds before touching it.
# All-or-nothing. Undo: git checkout .

import re, sys, struct, subprocess, pathlib

REPO = pathlib.Path("/Users/wma/Desktop/portfolio")
CSS  = REPO / "css" / "site.css"

WIDTHS = {
    "index.html":            ("home",  284),
    "about/index.html":      ("about", 341),
    "marly/index.html":      (None,    None),   # hero is the ad slot
    "workhuman/index.html":  ("cs",    380),
    "treat-week/index.html": ("cs",    380),
    "ge-terminal/index.html":("cs",    380),
    "ripco/index.html":      ("cs",    380),
    "west-elm/index.html":   ("cs",    380),
}

HERO_CSS = """.hero-portrait {
  flex-shrink: 0;
  width: 380px;
}
.hero-portrait--home  { width: 284px; }
.hero-portrait--about { width: 341px; }
.hero-portrait img {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 0;
}
"""

errors, notes = [], []
def fail(m): errors.append(m)
def git(*a): return subprocess.run(["git","-C",str(REPO)]+list(a),
                                   capture_output=True, text=True).stdout.strip()

print("=" * 66); print("PRECONDITIONS"); print("=" * 66)
b = git("rev-parse", "--abbrev-ref", "HEAD")
d = [l for l in git("status", "--porcelain").splitlines() if not l.startswith("??")]
print("  branch          : " + b)
print("  tracked changes : " + (str(len(d)) if d else "none"))
if d: fail("tracked files modified - commit or stash first")

wh_img = REPO / "assets" / "workhuman" / "hero.png"
if not wh_img.exists():
    fail("assets/workhuman/hero.png not found")
else:
    blob = wh_img.read_bytes()
    if blob[:8] != b"\x89PNG\r\n\x1a\n":
        fail("assets/workhuman/hero.png is not a valid PNG")
    else:
        w, h = struct.unpack(">II", blob[16:24])
        print("  workhuman/hero  : %dx%d, %.0f KB" % (w, h, len(blob) / 1024))

if errors:
    print("\nABORTED:"); [print("  x " + e) for e in errors]; sys.exit(1)

print("\n" + "=" * 66); print("CURRENT HERO MARKUP"); print("=" * 66)
pending = {}
HERO_RE = re.compile(r'<div class="hero-portrait[^"]*"[^>]*>(?:\s*<img[^>]*>\s*)?</div>|'
                     r'<div class="hero-portrait[^"]*"[^>]*/?>', re.S)

for rel, (kind, width) in WIDTHS.items():
    p = REPO / rel
    if not p.exists(): fail("missing page: " + rel); continue
    src = p.read_text()
    m = HERO_RE.search(src)
    if kind is None:
        print("  %-24s (ad slot, skipped)" % rel); continue
    if not m:
        print("  %-24s NO HERO DIV FOUND" % rel)
        if rel != "marly/index.html": fail(rel + ": hero div not found")
        continue
    print("  %-24s %s" % (rel, m.group(0)[:96].replace("\n", " ")))

    mod = {"home": " hero-portrait--home", "about": " hero-portrait--about"}.get(kind, "")
    if rel == "workhuman/index.html" and "<img" not in m.group(0):
        new = ('<div class="hero-portrait fade-up">\n'
               '          <img src="/assets/workhuman/hero.png" alt="" '
               'loading="eager" decoding="async">\n        </div>')
        notes.append("workhuman: placeholder -> img")
    else:
        img = re.search(r'<img[^>]*>', m.group(0))
        if not img: fail(rel + ": no <img> inside hero div"); continue
        new = ('<div class="hero-portrait%s fade-up">\n          %s\n        </div>' % (mod, img.group(0)))
        notes.append("%s: class -> hero-portrait%s" % (rel, mod or " (case study, 380px)"))
    pending[p] = src.replace(m.group(0), new, 1)

# ---- css ----
css = CSS.read_text()
old = re.search(r'\.hero-portrait \{.*?\n\}\n(?:\.hero-portrait[^\n]*\{[^}]*\}\n)*', css, re.S)
if old:
    css = css.replace(old.group(0), HERO_CSS, 1)
    notes.append("hero CSS replaced (widths per page, no border-radius)")
else:
    fail("could not locate .hero-portrait rules in site.css")
css = re.sub(r'\.hero-portrait\.ph \{[^}]*\}\n', '', css)
pending[CSS] = css

print("\n" + "=" * 66); print("PLAN"); print("=" * 66)
[print("  - " + n) for n in notes]
if errors:
    print("\nABORTED - nothing written:"); [print("  x " + e) for e in errors]; sys.exit(1)

for path, content in pending.items(): path.write_text(content)

left = subprocess.run(["grep","-rlo",'class="[^"]*\\bph\\b',"--include=*.html","."],
                      cwd=str(REPO), capture_output=True, text=True).stdout.strip()
print("\n" + "=" * 66)
print("WROTE %d FILES" % len(pending))
print("placeholders remaining: " + (left if left else "0  <-- merge gate clear"))
print("=" * 66)
print("\n  git add -A && git commit -m 'Hero sizing per design; Workhuman hero image' && git push")
print("Undo:  git checkout .")
