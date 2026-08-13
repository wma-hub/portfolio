#!/usr/bin/env python3
"""
figma_assets.py — verify Figma PNG exports and swap placeholders into <img> tags.

Two subcommands:

    python figma_assets.py verify  manifest.json --dir assets/
    python figma_assets.py swap    manifest.json --html-root .

`verify` reads real pixel dimensions straight from the PNG header (no Pillow
dependency), compares to 2x the manifest values, and classifies any mismatch.
`swap` replaces <div class="ph" data-asset="KEY"> with a real <img>.

Nothing is rescaled or "fixed" silently. Anomalies are reported and the exit
code is non-zero so a build step can fail on them.
"""

import argparse
import json
import re
import struct
import sys
from pathlib import Path

SCALE = 2  # all exports are 2x


# ---------------------------------------------------------------- PNG header

def png_size(path: Path):
    """(width, height) from the IHDR chunk. Returns None if not a valid PNG."""
    with path.open("rb") as fh:
        head = fh.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def classify(exp_w, exp_h, act_w, act_h):
    """Explain a dimension mismatch. Returns (severity, message)."""
    dw, dh = act_w - exp_w, act_h - exp_h
    if dw == 0 and dh == 0:
        return "ok", "exact"

    # Fractional node heights round up at 2x — harmless.
    if 0 <= dw <= 1 and 0 <= dh <= 1:
        return "ok", f"+{dw}W +{dh}H — fractional rounding, use export dims as attrs"

    # Uniform-ish growth on both axes = layer blur or shadow.
    if dw > 1 and dh > 1 and abs(dw - dh) <= 2:
        return "warn", f"+{dw}px both axes — blur/shadow, ~{dw / 2:.0f}px per side"

    # One axis grows, the other is stable = offset shadow or unclipped overflow.
    if dw >= 0 and dh >= 0 and (dw <= 1 or dh <= 1):
        return "warn", f"+{dw}W +{dh}H — offset shadow or unclipped child"

    # Negative delta means the render is smaller than the node. Stale cache.
    if dw < 0 or dh < 0:
        return "fail", (f"expected {exp_w}×{exp_h}, got {act_w}×{act_h} — render "
                        "smaller than node; stale cache, duplicate the frame "
                        "(Cmd+D, delete original) and re-export")

    # Non-uniform positive growth — frame has unclipped overflow or wrong bounds.
    return "fail", (f"expected {exp_w}×{exp_h}, got {act_w}×{act_h} — "
                    f"+{dw}W +{dh}H non-uniform; check for unclipped overflow or wrong frame bounds")


def cmd_verify(args):
    manifest = json.loads(Path(args.manifest).read_text())
    root = Path(args.dir)
    ok = warn = fail = missing = 0
    rows = []

    for key, a in manifest["assets"].items():
        path = root / a["file"]
        if not path.exists():
            rows.append(("MISSING", key, a["file"], "not on disk"))
            missing += 1
            continue

        size = path.stat().st_size
        dims = png_size(path)
        if dims is None:
            rows.append(("FAIL", key, a["file"], "not a valid PNG"))
            fail += 1
            continue
        if size < 1024:
            rows.append(("FAIL", key, a["file"],
                         f"{size} bytes — blank or transparent frame, re-export"))
            fail += 1
            continue

        act_w, act_h = dims
        exp_w, exp_h = a["w"] * SCALE, a["h"] * SCALE
        sev, msg = classify(exp_w, exp_h, act_w, act_h)
        rows.append((sev.upper(), key, f"{act_w}×{act_h}", msg))
        {"ok": "ok", "warn": "warn", "fail": "fail"}[sev]
        if sev == "ok":
            ok += 1
        elif sev == "warn":
            warn += 1
        else:
            fail += 1

        # Record real dims so `swap` writes truthful width/height attributes.
        a["actual_w"], a["actual_h"] = act_w // SCALE, act_h // SCALE

    w = max((len(r[1]) for r in rows), default=10)
    for sev, key, dims, msg in rows:
        print(f"  {sev:<8} {key:<{w}}  {dims:<12} {msg}")

    print(f"\n  {ok} exact · {warn} shadow/rounding · {fail} failed · {missing} missing")

    if args.write_back and not (fail or missing):
        Path(args.manifest).write_text(json.dumps(manifest, indent=2))
        print(f"  wrote measured dimensions back to {args.manifest}")

    return 1 if (fail or missing) else 0


# ---------------------------------------------------------------- swap

PH = r'<div\s+class="[^"]*\bph\b[^"]*"[^>]*data-asset="{key}"[^>]*>\s*</div>'


def cmd_swap(args):
    manifest = json.loads(Path(args.manifest).read_text())
    root = Path(args.html_root)
    by_page = {}
    for key, a in manifest["assets"].items():
        by_page.setdefault(a["page"], []).append((key, a))

    total = skipped = 0
    for page, entries in sorted(by_page.items()):
        html_path = root / manifest["pages"][page]
        if not html_path.exists():
            print(f"  SKIP  {page}: {html_path} not found")
            continue

        html = html_path.read_text()
        before = html
        for key, a in entries:
            w = a.get("actual_w", a["w"])
            h = a.get("actual_h", a["h"])
            eager = a.get("eager", False)
            img = (f'<img src="/{manifest["asset_dir"]}/{a["file"]}" '
                   f'width="{w}" height="{h}" alt="{a.get("alt", "")}" '
                   f'loading="{"eager" if eager else "lazy"}">')
            html, n = re.subn(PH.format(key=re.escape(key)), img, html, count=1)
            if n:
                total += 1
            else:
                skipped += 1
                print(f"  MISS  {page}: no placeholder for data-asset=\"{key}\"")

        if html != before:
            html_path.write_text(html)
            print(f"  OK    {page}: {len(entries) - 0} processed")

    print(f"\n  {total} swapped · {skipped} placeholders not found")

    leftovers = 0
    for page, rel in manifest["pages"].items():
        p = root / rel
        if p.exists():
            n = len(re.findall(r'class="[^"]*\bph\b', p.read_text()))
            if n:
                print(f"  {n} .ph remaining in {rel}")
                leftovers += n
    if not leftovers:
        print("  no .ph placeholders remaining")
    return 0


# ---------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("verify", help="check exported PNG dimensions")
    v.add_argument("manifest")
    v.add_argument("--dir", default="assets")
    v.add_argument("--write-back", action="store_true",
                   help="record measured dimensions into the manifest")
    v.set_defaults(fn=cmd_verify)

    s = sub.add_parser("swap", help="replace .ph placeholders with <img> tags")
    s.add_argument("manifest")
    s.add_argument("--html-root", default=".")
    s.set_defaults(fn=cmd_swap)

    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
