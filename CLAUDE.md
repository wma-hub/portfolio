# WMA.NYC V2 — Build Spec

## 0. Context
Personal portfolio for Wilson Ma. Static site on Vercel project "portfolio"
(framework: null, no build step). Production domains: wma.nyc, www.wma.nyc.
This build fully replaces V1. Work on branch `v2` only — NEVER commit to main.

## 1. Source of truth
Figma file `yL4hnNAJKHlEWVLT5OUhvx`, page "WMA.NYC — V2" (canvas 3259:2117).
Read every frame with `get_design_context` and execute 1:1. Never build from
`get_metadata` (it silently drops rotations, gradient directions, image
transforms). Home and About were restructured this week — always pull fresh
design context at build time; never reuse cached exports.
Mid-build compositional questions surface inline as questions. Do not
improvise composition and do not "fix" the design.

### Phase 1 routes (this build)
| Route      | Figma node  | Notes |
|------------|-------------|-------|
| /          | 3531:1134   | Home — chip rows, two-tone hero, gradient panel |
| /about     | 3531:1222   | About — 360px column sections |
| /marly     | 3295:4421   | Heaviest page; live ad embeds (§3) |
| /runeberg  | 3366:3316   | Magenta annotations are intentional (§2) |
| nav        | 3533:1134   | Component; sticky, all pages |
| footer     | 3533:1179   | Component; all pages. Links: Work, About, LinkedIn, Email. NO resume link anywhere on the site. |

### Phase 2 (do NOT build yet)
workhuman 3295:4590 (+ tab viewer 3394:933) · treat-week 3296:4719 ·
selected-works 3298:4728

## 2. Stack & conventions
- Plain HTML/CSS/vanilla JS. One folder per route with `index.html`.
  Shared `/css/site.css`, `/js/site.js`, `/assets/{page}/`.
- Fonts: Inter + Space Mono via Google Fonts. Frames reference
  "Font Awesome 6 Pro" chevrons — do NOT add Font Awesome; replace every
  icon with inline SVG.
- Design width 1440. Breakpoints 900 and 700, fluid type via clamp().
  wma designs desktop-only; you own the full responsive translation.
- Scroll animations: IntersectionObserver fade/translate, matching the
  marly.cc case-study template behavior.
- Assets: download Figma image assets to `/assets/` at build time. NEVER
  commit a figma.com CDN URL — they expire in ~7 days. Verify with grep (§6).
- Magenta elements (#f0e strokes, rgba(255,0,238,x) fills, dashed magenta
  borders) are INTENTIONAL annotation/callout styling on this site.
  Reproduce them exactly. Do not remove or "clean up."
- Content edits on files containing HTML entities: python str.replace(),
  never sed.

## 3. Live ad embeds (/marly)
Source of truth for available units is the local marly repo:
`/Users/wma/Desktop/marly/website/review/{client}/{campaign}/ads/`.
Enumerate with ls before writing any embed path — never guess slugs.
Embed via iframe pointing at the deployed files:
`https://www.marly.cc/review/{client}/{campaign}/ads/{unit}/index.html`
(adjust to actual file layout found on disk).

- Step 6 "DELIVERED" slot: Tumblerware Father's Day **300x250** unit
  (campaign at /review/tumblerware/fathers-day). Static, no rotation.
- Brand Range section: the mock slots become ROTATING SHOWCASES. Each slot
  keeps its Figma size and position and cycles through all seven brands'
  units at that slot's size (Tumblerware, Graza, Ghia, Ritual, Levi's,
  Byredo, Magic Spoon; most recent campaign per brand, enumerated on disk).
  Rotation rules:
  - Interval randomized 3–5s per slot so slots never swap in sync; expose
    the interval range as one JS const (`ROTATE_MS`) for tuning at preview.
  - Double-buffered crossfade: preload the next unit's iframe hidden, fade
    ~400ms, then remove the previous. Never hard-swap a visible iframe src
    (causes white flash + reflow). Max two live iframes per slot at any
    time so stacked GSAP loops don't pile up CPU.
  - A brand enters a slot's rotation only if it has a unit at that exact
    size on disk. Missing sizes are skipped silently and listed in the §8
    review, not padded with wrong-size units.
  - Lazy-init: no iframes load until the section approaches the viewport;
    pause all rotation while offscreen (IntersectionObserver).
  - prefers-reduced-motion: rotation disabled, each slot shows its first
    unit statically.

Iframes at exact IAB pixel dimensions, descriptive `title` attrs.
STAGE 1 CHECK: `curl -sI https://www.marly.cc/review/tumblerware/fathers-day`
and inspect X-Frame-Options / CSP frame-ancestors. If framing from wma.nyc is
blocked, fallback is copying unit files into this repo under `/ads/` — flag
before executing the fallback.

## 4. Links (all resolved — wire exactly these)
- Nav: wordmark → `/` · Work → `/#work` (anchor on the Selected Projects
  section; give that section `id="work"`) · About → `/about` ·
  "Get in touch" → `mailto:ny.wilson.ma@gmail.com`
- Footer: Work → `/#work` · About → `/about` ·
  LinkedIn → `https://www.linkedin.com/in/wilsonxma/` (new tab, rel noopener)
  · Email → `mailto:ny.wilson.ma@gmail.com`
- There is NO resume link on this site. Do not add one. Resume is shared
  upon request only.
- No dead `#` hrefs anywhere at gate time.

## 5. Deployment
Branch `v2` → push → Vercel preview URL → wma reviews → wma merges.
Never merge yourself. Do not touch Vercel project settings, domains, or DNS.
V1: DELETE all V1 site files in this branch (`git rm`), same PR as the V2
build, so the merge atomically replaces the live site. Preserve repo-level
non-site files (README, LICENSE, .gitignore, vercel.json if present — read
vercel.json before modifying anything in it). Git history retains V1;
rollback is one revert.

## 6. Verification gate (run before requesting review; paste raw output)
1. `find . -name "index.html" | sort` — four routes present
2. `grep -rn "figma.com" --include="*.html" --include="*.css" .` — empty
3. `grep -rni "fontawesome\|font awesome" .` — empty
4. `grep -rni "lorem\|OPEN ITEM\|TODO" --include="*.html" .` — empty
5. `grep -rn 'href="#"' --include="*.html" .` — empty
6. `grep -rni "resume" --include="*.html" .` — empty
7. Per-route weight < 2.5 MB excluding ad iframes (`du -sh` per folder)
No self-reported "Stage complete" — output or it didn't happen.
