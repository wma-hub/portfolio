#!/usr/bin/env python3
# export_figma_assets.py - pull all 38 named assets straight from Figma into /assets/.
#
# Needs a Figma personal access token with file_content:read scope:
#   figma.com -> Settings -> Security -> Personal access tokens -> Generate
# Then, in the same shell (the token is never stored in this file):
#   export FIGMA_TOKEN='figd_...'
#   python3 export_figma_assets.py
#
# Node IDs were read from the file, so names and placement are already correct.
# Downloads at 2x, writes to /assets/<path>.png, verifies PNG magic bytes and
# reports actual pixel dimensions against expected.

import os, sys, json, time, struct, pathlib, urllib.parse, urllib.request

TOKEN    = os.environ.get("FIGMA_TOKEN", "").strip()
FILE_KEY = "yL4hnNAJKHlEWVLT5OUhvx"
REPO     = pathlib.Path("/Users/wma/Desktop/portfolio")
ASSETS   = REPO / "assets"
SCALE    = 2
BATCH    = 15

# node id -> (asset path, expected 1x size)
ASSETS_MAP = [
    ("3968:16273", "about/portrait",              (341, 317)),
    ("3968:15616", "home/portrait",               (284, 261)),
    ("3968:17063", "ge-terminal/hero",            (380, 291)),
    ("3968:16465", "ge-terminal/01-problem",      (708, 349)),
    ("3968:16471", "ge-terminal/02-engine",      (1079, 544)),
    ("3968:16551", "ge-terminal/02-callout",      (480, 131)),
    ("3968:16559", "ge-terminal/03-override",    (1080, 446)),
    ("3968:16564", "ge-terminal/04-daily",       (1080, 470)),
    ("3968:16573", "ge-terminal/05-origin",       (591, 408)),
    ("3968:15111", "treatweek/hero",              (380, 242)),
    ("3968:15113", "treatweek/01-campaign",      (1080, 479)),
    ("3971:17109", "treatweek/02-lockup-1",       (160, 160)),
    ("3971:17121", "treatweek/02-lockup-2",       (160, 160)),
    ("3971:17136", "treatweek/02-lockup-3",       (160, 160)),
    ("3971:17148", "treatweek/02-lockup-4",       (160, 160)),
    ("3971:17159", "treatweek/02-lockup-5",       (160, 160)),
    ("3968:15114", "treatweek/03-band",          (1080, 200)),
    ("3968:15117", "treatweek/04-system-logo",   (1080, 239)),
    ("3968:15199", "treatweek/04-system-type",   (1080, 103)),
    ("3968:15225", "treatweek/04-system-graphics",(1080, 253)),
    ("3968:15259", "treatweek/04-system-color",  (1080, 474)),
    ("3968:15354", "treatweek/05-applications",  (1080, 511)),
    ("3968:15444", "treatweek/06-email",          (966, 591)),
    ("3968:15467", "treatweek/07-devices",       (1080, 500)),
    ("3968:15687", "ripco/hero",                  (380, 307)),
    ("3968:14957", "ripco/01-work",              (1080, 1649)),
    ("3968:14963", "ripco/02-slide-1",            (842, 540)),
    ("3968:14964", "ripco/02-slide-2",            (701, 540)),
    ("3968:14965", "ripco/02-slide-3",            (703, 540)),
    ("3968:14966", "ripco/02-slide-4",            (809, 540)),
    ("3968:14967", "ripco/02-slide-5",            (960, 540)),
    ("3968:16140", "westelm/hero",                (379, 473)),
    ("3968:16185", "westelm/01-devices",         (1080, 810)),
    ("3968:16211", "westelm/02-slide-1",          (655, 680)),
    ("3968:16214", "westelm/02-slide-2",         (1187, 680)),
    ("3968:16222", "westelm/02-slide-3",          (834, 680)),
    ("3968:16226", "westelm/02-slide-4",          (568, 680)),
    ("3978:17223", "westelm/02-slide-5",          (610, 680)),
]

if not TOKEN:
    print("ABORTED: FIGMA_TOKEN not set in this shell.")
    print("  figma.com -> Settings -> Security -> Personal access tokens")
    print("  export FIGMA_TOKEN='figd_...'   then re-run")
    sys.exit(1)
if not REPO.exists():
    print("ABORTED: repo not found at %s" % REPO); sys.exit(1)

def api(url):
    req = urllib.request.Request(url, headers={"X-Figma-Token": TOKEN})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)

def png_size(b):
    if b[:8] != b"\x89PNG\r\n\x1a\n": return None
    w, h = struct.unpack(">II", b[16:24])
    return (w, h)

by_id = {i: (p, s) for i, p, s in ASSETS_MAP}
ids = [i for i, _, _ in ASSETS_MAP]

print("=" * 66)
print("RENDERING %d assets at %dx" % (len(ids), SCALE))
print("=" * 66)

urls = {}
for n in range(0, len(ids), BATCH):
    chunk = ids[n:n + BATCH]
    q = urllib.parse.urlencode({"ids": ",".join(chunk), "format": "png", "scale": SCALE})
    print("  batch %d/%d ..." % (n // BATCH + 1, (len(ids) + BATCH - 1) // BATCH), end=" ", flush=True)
    try:
        data = api("https://api.figma.com/v1/images/%s?%s" % (FILE_KEY, q))
    except Exception as e:
        print("FAILED: %s" % e); sys.exit(1)
    if data.get("err"):
        print("FAILED: %s" % data["err"]); sys.exit(1)
    got = {k: v for k, v in (data.get("images") or {}).items() if v}
    urls.update(got)
    print("%d urls" % len(got))
    time.sleep(0.5)

missing = [by_id[i][0] for i in ids if i not in urls]
if missing:
    print("\nWARNING: no render URL returned for:")
    for m in missing: print("   - " + m)

print("\n" + "=" * 66)
print("DOWNLOADING")
print("=" * 66)
ok, bad = [], []
for nid, url in urls.items():
    path, (ew, eh) = by_id[nid]
    dest = ASSETS / (path + ".png")
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=180) as r:
            blob = r.read()
    except Exception as e:
        bad.append("%s  download failed: %s" % (path, e)); continue
    dim = png_size(blob)
    if dim is None:
        bad.append("%s  not a PNG (%d bytes)" % (path, len(blob))); continue
    dest.write_bytes(blob)
    want = (ew * SCALE, eh * SCALE)
    flag = "" if abs(dim[0] - want[0]) <= 2 and abs(dim[1] - want[1]) <= 2 else \
           "  <-- expected %dx%d" % want
    ok.append("%-32s %5dx%-5d %6.0f KB%s" % (path + ".png", dim[0], dim[1], len(blob) / 1024, flag))

for line in sorted(ok): print("  " + line)
if bad:
    print("\nFAILURES:")
    for b in bad: print("   x " + b)

total = sum((ASSETS / (p + ".png")).stat().st_size for _, p, _ in ASSETS_MAP
            if (ASSETS / (p + ".png")).exists())
print("\n" + "=" * 66)
print("%d of %d written  |  %.1f MB total" % (len(ok), len(ASSETS_MAP), total / 1048576))
print("=" * 66)
print("\nNext: send this listing back and I'll write the HTML swap.")
print("  find assets -name '*.png' -newermt '-10 minutes' | sort")
