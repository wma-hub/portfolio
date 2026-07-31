#!/usr/bin/env python3
"""
apply_v3_workhuman.py — the last page.

  1. CHROME : Workhuman never received the shared swap. V3 nav + footer,
              Google Fonts link removed, Switzer preload added.
  2. TOKENS : property-aware hex substitution across the 392-line inline
              <style> block and 163 inline style= attributes. Text darks ->
              --color-ink, light fills -> --color-background-acc, dark wells
              stay dark (they carry white text), borders -> --color-rule.
              #f18bff is left alone: intentional annotation styling.
  3. CS-HERO: retokenized in site.css. Workhuman is now its only consumer.
              The legacy .cs-nav-outer responsive overrides go with it.

All-or-nothing. Undo: git checkout .
"""
import re, sys, subprocess, pathlib

REPO   = pathlib.Path("/Users/wma/Desktop/portfolio")
BRANCH = "v3-restyle"
WH     = REPO / "workhuman" / "index.html"
CSHERO = """/* ── CS Hero — Workhuman only (all other pages rebuilt) ──── */
.cs-hero-outer {
  background: var(--bg);
  padding: var(--space-80) var(--px-outer);
}
.cs-hero-feature {
  background: var(--color-background-acc);
  border: 1px solid var(--color-rule);
  border-radius: var(--radius-md);
  padding: var(--space-80);
  max-width: var(--content-width);
  margin-inline: auto;
}
.cs-hero-copy { display: flex; flex-direction: column; gap: var(--space-40); }
.cs-hero-text { display: flex; flex-direction: column; gap: var(--space-16); }
.cs-hero-title {
  font-size: var(--type-hero);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-normal);
  color: var(--color-ink);
}
.cs-hero-subtitle {
  font-size: var(--type-subhead);
  font-weight: var(--font-weight-medium);
  letter-spacing: var(--tracking-snug);
  color: var(--color-ink);
}
.cs-hero-body {
  font-size: var(--type-body);
  font-weight: var(--font-weight-regular);
  letter-spacing: var(--tracking-snug);
  line-height: var(--leading-normal);
  color: var(--color-ink-muted);
}
.cs-hero-cards { display: flex; gap: var(--space-24); }
.cs-hero-card {
  flex: 1;
  background: var(--color-surface);
  border: 1px solid var(--color-rule);
  border-radius: var(--radius-sm);
  padding: var(--space-14);
  display: flex;
  flex-direction: column;
  gap: var(--space-8);
}
.cs-hero-card-label {
  font-size: var(--type-body);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--tracking-tight);
  color: var(--color-ink);
}
.cs-hero-card-value {
  font-size: var(--type-caption);
  font-weight: var(--font-weight-regular);
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-normal);
  color: var(--color-ink-muted);
}

@media (max-width: 900px) {
  .cs-hero-feature { padding: var(--space-40); }
  .cs-hero-text { gap: var(--space-12); }
}
@media (max-width: 700px) {
  .cs-hero-outer { padding: var(--space-24) var(--px-outer); }
  .cs-hero-feature { padding: var(--space-24); }
  .cs-hero-cards { flex-wrap: wrap; }
  .cs-hero-card { flex: 1 0 calc(50% - 12px); }
}
"""

errors, notes = [], []
def fail(m): errors.append(m)
def note(m): notes.append(m)
def git(*a): return subprocess.run(["git","-C",str(REPO)]+list(a),
                                   capture_output=True, text=True).stdout.strip()

print("=" * 62); print("PRECONDITIONS"); print("=" * 62)
if not REPO.exists(): fail(f"repo not found: {REPO}")
else:
    b, d = git("rev-parse","--abbrev-ref","HEAD"), git("status","--porcelain")
    print(f"  branch : {b}\n  tree   : {'clean' if not d else 'DIRTY'}")
    if b != BRANCH: fail(f"expected branch {BRANCH}, found {b}")
    if d: fail("uncommitted changes - commit or stash first")
if not WH.exists(): fail("workhuman/index.html missing")
css_path = REPO / "css" / "site.css"
if not css_path.exists(): fail("css/site.css missing")
if errors:
    print("\nABORTED:"); [print("  x "+e) for e in errors]; sys.exit(1)

src = WH.read_text(); css = css_path.read_text()

# ------------------------------------------------------ property-aware tokens
TEXT_INK    = {"#1e293b","#203f5b","#212744","#333e6a","#f1ece7","#0e1f45","#1a3570"}
TEXT_MUTED  = {"#a5b1b5","#474747","#6b7a9a","#4e6b88"}
BG_LIGHT    = {"#f1f4f8","#f4f5f7","#eef3f9","#f5f5f5","#cbd5e1","#d9d9d9"}
BG_DARK     = {"#15191f","#0e1f45","#1a3570"}      # keep dark: white text sits on these
BG_ACCENT   = {"#5b63e4","#7c5cfc","#295ce6"}
BORDERS     = {"#cbd5e1","#9bc0e4","#d9d9d9","#b8c4d6"}
WHITE       = {"#fff","#ffffff"}
LEAVE       = {"#f18bff","#ffebdd"}                # annotation + one-off peach

counts = {}
def bump(k): counts[k] = counts.get(k, 0) + 1

def sub_value(prop, value):
    def repl(m):
        h = m.group(0).lower()
        if h in LEAVE: return m.group(0)
        if prop.startswith("border"):
            if h in BORDERS: bump("border->rule"); return "var(--color-rule)"
            if h in BG_ACCENT: bump("border->accent"); return "var(--color-accent)"
        elif prop.startswith("background"):
            if h in BG_DARK: bump("bg->ink"); return "var(--color-ink)"
            if h in BG_ACCENT: bump("bg->accent"); return "var(--color-accent)"
            if h in BG_LIGHT: bump("bg->bg-acc"); return "var(--color-background-acc)"
            if h in WHITE: bump("bg->surface"); return "var(--color-surface)"
        elif prop == "color":
            if h in TEXT_INK: bump("text->ink"); return "var(--color-ink)"
            if h in TEXT_MUTED: bump("text->ink-muted"); return "var(--color-ink-muted)"
            if h in BG_ACCENT: bump("text->accent"); return "var(--color-accent)"
            if h in WHITE: bump("text->surface"); return "var(--color-surface)"
        bump("UNMAPPED " + h)
        return m.group(0)
    return re.sub(r"#[0-9a-fA-F]{3,8}", repl, value)

def tokenize(text):
    return re.sub(
        r"((?:^|[;{\s\"])(?:color|background[a-z-]*|border[a-z-]*))(\s*:\s*)([^;{}\"]*)",
        lambda m: m.group(1) + m.group(2) + sub_value(
            m.group(1).lstrip(';{ \n\t"\''), m.group(3)),
        text)

out = tokenize(src)

# ----------------------------------------------------------------- chrome
NAV = '''  <nav class="site-nav" role="navigation" aria-label="Main navigation">
    <a href="/" class="nav-wordmark">wilson ma</a>
    <div class="nav-links">
      <a href="/#work" class="ui-nav" aria-current="page">projects</a>
      <a href="/about" class="ui-nav">about</a>
    </div>
  </nav>'''
FOOTER = '''  <footer class="site-footer" role="contentinfo">
    <div class="footer-inner">
      <div class="footer-mark">
        <span class="heading-wordmark">wma.nyc</span>
        <p class="footer-copy meta-small">&#169; 2026 Wilson Ma</p>
      </div>
      <nav class="footer-links" aria-label="Footer navigation">
        <a href="/#work" class="ui-nav">projects</a>
        <a href="/about" class="ui-nav">about</a>
        <a href="https://www.linkedin.com/in/wilsonxma/" target="_blank" rel="noopener noreferrer" class="ui-nav">linkedin</a>
        <a href="mailto:ny.wilson.ma@gmail.com" class="ui-nav">email</a>
      </nav>
    </div>
  </footer>'''

out, n = re.subn(r'<nav class="nav".*?</nav>', NAV.strip(), out, flags=re.S)
note(f"nav swapped ({n})");  n == 1 or fail(f"expected 1 nav, got {n}")
out, n = re.subn(r'<footer class="footer".*?</footer>', FOOTER.strip(), out, flags=re.S)
note(f"footer swapped ({n})"); n == 1 or fail(f"expected 1 footer, got {n}")

out, ng = re.subn(r'[ \t]*<link rel="preconnect" href="https://fonts\.[^>]*>\n|[ \t]*<link href="https://fonts\.googleapis\.com[^>]*>\n', "", out)
note(f"google fonts links removed ({ng})")
# strip orphaned CSS rules for classes that lived only in the old chrome
out, nd = re.subn(r'\s*\.nav-cta\s*\{[^}]*\}|\s*\.footer-tagline\s*\{[^}]*\}', "", out)
note(f"orphaned chrome CSS rules stripped ({nd})")
if "Switzer-Variable.woff2" not in out:
    out = out.replace('  <link rel="stylesheet" href="/css/site.css">',
        '  <link rel="preload" href="/assets/fonts/Switzer-Variable.woff2" as="font" type="font/woff2" crossorigin>\n  <link rel="stylesheet" href="/css/site.css">', 1)
    note("switzer preload added")

# -------------------------------------------------------------- site.css
new_css = css
blk = re.search(r'/\* .. CS Hero ─+.*?\n(?=/\* .. CS Nav)', css, re.S)
if blk:
    new_css = new_css.replace(blk.group(0), CSHERO.rstrip() + "\n\n", 1)
    note("cs-hero retokenized")
else:
    fail("cs-hero block not found in site.css")

resp = re.search(r'/\* .. CS Hero responsive .*?\Z', new_css, re.S)
if resp:
    new_css = new_css.replace(resp.group(0), "", 1)
    note("legacy CS Hero responsive block removed (takes the .cs-nav-outer overrides with it)")

# ---------------------------------------------------------------- verify
for bad in ("fonts.googleapis.com", "footer-brand", "footer-tagline", "nav-cta"):
    if bad in out: fail(f"V2 remnant survived: {bad}")
if "#f18bff" not in out: fail("annotation magenta was stripped - it is intentional")

print("\n" + "=" * 62); print("TOKEN SUBSTITUTIONS"); print("=" * 62)
for k in sorted(counts, key=lambda x: -counts[x]):
    flag = "  <-- REVIEW" if k.startswith("UNMAPPED") else ""
    print(f"  {counts[k]:>4}  {k}{flag}")
print("\nPLAN"); [print("  - " + n) for n in notes]
if errors:
    print("\nABORTED - nothing written:"); [print("  x "+e) for e in errors]; sys.exit(1)

WH.write_text(out); css_path.write_text(new_css)
print("\nWROTE  workhuman/index.html, css/site.css")
print("  git add -A && git commit -m 'V3 Workhuman: chrome swap + token pass' && git push")
print("Undo:  git checkout .")
