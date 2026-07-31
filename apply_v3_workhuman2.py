#!/usr/bin/env python3
"""
apply_v3_workhuman2.py — make Workhuman match the rest of the site.

The first pass did colours only, so the page still rendered at V2's type
scale and rhythm. This maps the remaining hardcoded values:

  font-size  -> --type-*      (9/10 -> micro, 11/12 -> meta, 13/14 -> caption,
                               15/16 -> body-sm, 18 -> body, 20 -> section,
                               22/24/28 -> subhead, 48 -> display)
  padding/margin/gap -> --space-*   (nearest step on the scale)
  border-radius      -> --radius-*  (V3 has only 4 and 6)

Structural, to match the V3 design (which has neither):
  - .cs-hero-feature card wrapper becomes a pass-through
  - the nine .stat-card blocks are hidden

clamp() declarations, width/height, and the annotation magenta are untouched.
All-or-nothing. Undo: git checkout .
"""
import re, sys, subprocess, pathlib

REPO   = pathlib.Path("/Users/wma/Desktop/portfolio")
WH     = REPO / "workhuman" / "index.html"
CSS    = REPO / "css" / "site.css"

FONT = {9:"micro",10:"micro",11:"meta",12:"meta",13:"caption",14:"caption",
        15:"body-sm",16:"body-sm",18:"body",20:"section",22:"subhead",
        24:"subhead",28:"subhead",48:"display",56:"hero"}
SPACE_STEPS = [2,4,6,8,10,12,14,16,20,24,32,40,60,80,120,160]
SPACE_PROPS = {"padding","margin","gap","row-gap","column-gap",
               "padding-top","padding-bottom","padding-left","padding-right",
               "margin-top","margin-bottom","margin-left","margin-right"}

errors, notes = [], []
counts = {}
def bump(k): counts[k] = counts.get(k,0)+1
def fail(m): errors.append(m)
def git(*a): return subprocess.run(["git","-C",str(REPO)]+list(a),
                                   capture_output=True, text=True).stdout.strip()

print("="*62); print("PRECONDITIONS"); print("="*62)
b, d = git("rev-parse","--abbrev-ref","HEAD"), git("status","--porcelain")
print(f"  branch : {b}\n  tree   : {'clean' if not d else 'DIRTY'}")
if d: fail("uncommitted changes - commit or stash first")
if not WH.exists(): fail("workhuman/index.html missing")
if not CSS.exists(): fail("css/site.css missing")
if errors:
    print("\nABORTED:"); [print("  x "+e) for e in errors]; sys.exit(1)

src, css = WH.read_text(), CSS.read_text()

def nearest(v):
    return min(SPACE_STEPS, key=lambda s: (abs(s-v), s))

def fix_decl(m):
    prop, sep, val = m.group(1), m.group(2), m.group(3)
    p = prop.strip().lstrip(';{ \n\t"\'')
    if "clamp(" in val or "var(" in val:
        return m.group(0)
    if p == "font-size":
        def r(mm):
            v = float(mm.group(1))
            key = int(round(v))
            if key in FONT:
                bump(f"font {key}px -> --type-{FONT[key]}")
                return f"var(--type-{FONT[key]})"
            bump(f"font UNMAPPED {key}px"); return mm.group(0)
        return prop + sep + re.sub(r"(\d+(?:\.\d+)?)px", r, val)
    if p in SPACE_PROPS:
        def r(mm):
            v = float(mm.group(1))
            if v > 200: bump(f"space kept {int(v)}px"); return mm.group(0)
            n = nearest(v)
            bump(f"space {int(v)}px -> --space-{n}" if v != n else f"space {n}px -> --space-{n}")
            return f"var(--space-{n})"
        return prop + sep + re.sub(r"(\d+(?:\.\d+)?)px", r, val)
    if p == "border-radius":
        def r(mm):
            v = float(mm.group(1))
            t = "sm" if v <= 5 else "md"
            bump(f"radius {int(v)}px -> --radius-{t}")
            return f"var(--radius-{t})"
        return prop + sep + re.sub(r"(\d+(?:\.\d+)?)px", r, val)
    return m.group(0)

PATTERN = r"((?:^|[;{\s\"])(?:font-size|border-radius|padding[a-z-]*|margin[a-z-]*|[a-z-]*gap))(\s*:\s*)([^;{}\"]*)"
out = re.sub(PATTERN, fix_decl, src, flags=re.M)

# structural: hero card wrapper + stat cards
EXTRA = """
/* V3 alignment: the design has no hero card and no stat cards */
.cs-hero-feature { background: none; border: 0; padding: 0; border-radius: 0; }
.stat-card { display: none; }
"""
if ".cs-hero-feature { background: none" not in out:
    out = out.replace("</style>", EXTRA + "  </style>", 1)
    notes.append("hero card neutralised, stat cards hidden")

for bad in ("font-size: 72px", "font-size: 13px", "font-size: 48px"):
    if bad in out: fail(f"unmapped declaration survived: {bad}")

print("\n"+"="*62); print("SUBSTITUTIONS"); print("="*62)
for k in sorted(counts, key=lambda x: (-counts[x], x)):
    flag = "   <-- REVIEW" if "UNMAPPED" in k else ""
    print(f"  {counts[k]:>4}  {k}{flag}")
[print("  - "+n) for n in notes]
if errors:
    print("\nABORTED - nothing written:"); [print("  x "+e) for e in errors]; sys.exit(1)

WH.write_text(out)
print("\nWROTE  workhuman/index.html")
print("  git add -A && git commit -m 'Workhuman: map type, spacing and radius to tokens' && git push")
print("Undo:  git checkout .")
