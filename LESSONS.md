# WMA.NYC — Build Lessons

## 2026-07-07
**Run the full §6 gate and paste raw output before posting any preview URL or §8 review.**

§6 gate check 1 (`find . -name "index.html" | sort`) would have failed with only one route built. The gate is a completion signal, not a formality — posting a preview URL or §8 review before all routes exist and all checks pass defeats its purpose. Output or it didn't happen.

## 2026-07-08

**Per-directory export scale map: `assets/marly → ÷2`, `assets/treatweek → ÷1` (@1x exports, display width = intrinsic width).**

`setwidths.js` now takes a page argument (`node qa/setwidths.js marly` or `treat-week`) and applies the correct divisor per directory. The SCALE map lives in the PAGES config object at the top of the script. When onboarding a new page: add its entry to PAGES with `html`, `re` (filename pattern), and `scale`. Never hardcode a divisor inline.

**Mapping checkpoint is mandatory on every new page before building.**

Before writing any HTML for a new case study or portfolio page, complete STEP 1: copy exports to `/assets/{page}/`, run `ls`, post a filename→section mapping table (flag ambiguous assignments with `?`), and hard-stop for wma sign-off. Building before the checkpoint resolved two ambiguities on treat-week (03-1.png scope, 04-x ordering) that would have required a full section rebuild if discovered after. The mapping table is the contract; the build executes it.

## 2026-09-13

**`/work/tumblerware/` shipped without the twelve `c-*.svg` type files — the 160x600 unit has been rendering with broken images since the `/units/ -> /work/` migration.**

Commit 2343556 renamed the 160x600 type SVGs to the `c-f*` prefix; e2ffc92 (the adblock-bypass move to `/work/`) then copied only the `a-*` and `b-*` sets. `c.html` swaps `data-ls -> src` at runtime, so the misses never show up in a static grep for `src="` — they only surface when the unit actually plays. Restored from `marly-work/tumblerware/media/svg/type/`. When relocating unit directories, diff the full referenced-asset list (`data-ls` attributes included) against what landed on disk, per unit, not per brand.

**A live-ad panel inside `.cs-level` needs its own height branch.**

`computeH()` reads the first `<img>` width/height attributes; a panel built from live iframes returns 0 and the frame collapses. The `.cs-live` wrapper also needs an explicit pixel height set by the same function — with `overflow:hidden` and a 0-height wrapper, the absolutely-positioned stage is clipped to nothing and the panel renders empty with no error anywhere.

**A bare `sandbox="allow-scripts"` iframe silently loses cookies behind any auth layer — protected previews are the only place it shows up.**

Step 06 and the §03 trio (ghia/graza/gorjana) rendered styled units with every image broken on the Vercel preview. The frame's opaque origin makes its subresource requests third-party, so the `_vercel_jwt` protection cookie is withheld: each image went 302 -> vercel.com/sso-api -> 307 -> /login and failed, while top-document requests on the same deployment (posters included) returned 200. It was misdiagnosed as an ad blocker and chased through four localhost repro runs, none of which could fail — localhost has no protection layer. Fix: `allow-scripts allow-same-origin`, matching the rail loader, which never showed the bug. That pair effectively neuters the sandbox; acceptable because the units are first-party content in this repo. Before theorising about a broken embed, read the failed request's status and redirect chain in DevTools on the environment where it broke.

