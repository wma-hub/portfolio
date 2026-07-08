# WMA.NYC — Build Lessons

## 2026-07-07
**Run the full §6 gate and paste raw output before posting any preview URL or §8 review.**

§6 gate check 1 (`find . -name "index.html" | sort`) would have failed with only one route built. The gate is a completion signal, not a formality — posting a preview URL or §8 review before all routes exist and all checks pass defeats its purpose. Output or it didn't happen.

## 2026-07-08

**Per-directory export scale map: `assets/marly → ÷2`, `assets/treatweek → ÷1` (@1x exports, display width = intrinsic width).**

`setwidths.js` now takes a page argument (`node qa/setwidths.js marly` or `treat-week`) and applies the correct divisor per directory. The SCALE map lives in the PAGES config object at the top of the script. When onboarding a new page: add its entry to PAGES with `html`, `re` (filename pattern), and `scale`. Never hardcode a divisor inline.

**Mapping checkpoint is mandatory on every new page before building.**

Before writing any HTML for a new case study or portfolio page, complete STEP 1: copy exports to `/assets/{page}/`, run `ls`, post a filename→section mapping table (flag ambiguous assignments with `?`), and hard-stop for wma sign-off. Building before the checkpoint resolved two ambiguities on treat-week (03-1.png scope, 04-x ordering) that would have required a full section rebuild if discovered after. The mapping table is the contract; the build executes it.
