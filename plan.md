# plan.md — WMA.NYC V2, Phase 1

## §1 Brief synthesis
Replace V1 wma.nyc with V2 Phase 1: four routes (/, /about, /marly,
/runeberg) plus shared sticky nav and footer, built 1:1 from Figma page
"WMA.NYC — V2", deployed via v2 branch → Vercel preview → wma merge.
Deadline pressure: live before a recruiter call. Phase 2 (workhuman,
treat-week, selected-works) follows the first deploy.

## §2 Source inventory
Nodes per CLAUDE.md §1. All four Phase 1 frames verified present and current
as of 2026-07-07. Home/About restructured by wma this week — re-pull design
context immediately before building each page.

## §3 Gap audit
All wma-owned rows resolved 2026-07-07 (see §7). Remaining unknowns are
Code-verifiable: marly.cc framing headers (row 9), actual ad unit paths
(enumerate on disk per CLAUDE.md §3), V1 file inventory (ls on clone).

## §4 Diff vs deployed
Deployed state is V1 (last production deploy ~March 2026). Full replacement:
V1 site files are git rm'd in this branch. Preserve repo-level non-site
files. Read vercel.json (if present) before modifying.

## §5 Build order
1. Scaffold: /css/site.css tokens (palette, type scale, breakpoints from
   Figma), nav + footer as shared partials/includes; V1 file inventory +
   git rm
2. Home  3. About  4. Runeberg  5. Marly (asset-heaviest, ad iframes last)
6. Responsive pass, all routes, 900/700
7. Verification gate (CLAUDE.md §6)
8. Push v2 → post preview URL for wma review

## §6 Risks
- Asset volume on /marly and /runeberg: batch export, compress to WebP where
  safe; never recompress ad creative files
- Cross-origin embed blocked by marly.cc headers: fallback documented
  (CLAUDE.md §3), requires flag before executing
- Brand Range rotation CPU/network load (multiple slots preloading iframes):
  mitigated by lazy-init, offscreen pause, and the two-iframe buffer cap
  per slot (CLAUDE.md §3)
- Rotation interval (3–5s) is shorter than most units' animation loops, so
  loops cut mid-animation: known tradeoff, wma tunes ROTATE_MS at preview
- Emoji in Home headline (👋) renders per-OS: acceptable, no image swap

## §7 Coverage table — resolved 2026-07-07
| # | Item                                | Resolution |
|---|-------------------------------------|------------|
| 1 | Repo URL + local path               | github.com/wma-hub/portfolio → ~/Desktop/portfolio |
| 2 | Nav "Work" target                   | /#work anchor on Selected Projects section |
| 3 | mailto address                      | ny.wilson.ma@gmail.com |
| 4 | LinkedIn URL                        | linkedin.com/in/wilsonxma/ |
| 5 | Resume                              | RESOLVED: no resume on site; upon request only. Gate check 6 enforces. |
| 6 | Brand Range ad units                | Rotating showcase: each slot cycles all seven brands (Tumblerware, Graza, Ghia, Ritual, Levi's, Byredo, Magic Spoon) at that slot's size, 3–5s randomized, double-buffered crossfade (CLAUDE.md §3) |
| 7 | Tumblerware DELIVERED unit          | fathers-day 300x250 |
| 8 | V1 files                            | DELETE in this PR (git history retains; rollback = revert) |
| 9 | marly.cc frame-ancestors            | OPEN — Code verifies Stage 1 via curl -sI |

## §8 Post-execution review
After wma approves the preview: record any Code missteps as dated H3 lessons
in LESSONS.md in this repo (same format as marly lessons.md). Phase 2 plan.md
authored fresh after Phase 1 merges.
