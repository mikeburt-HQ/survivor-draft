"""Compose public/week7.html = week8_page.html with the SHARED <style> block
spliced in verbatim from week7.html.

The style block is MOVED, never retyped: retyping is how a design token
silently drifts between weeks. The splice is asserted both ways -- the block
must be found in the source, and the result must contain it byte-for-byte --
and week six's own rules (the tether callout) must NOT come across.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "public" / "week7.html"
TPL = pathlib.Path(__file__).parent / "week8_page.html"
OUT = ROOT / "public" / "week8.html"
SENTINEL = "<!--BASE-STYLE-->"

src = SRC.read_text(encoding="utf-8")
tpl = TPL.read_text(encoding="utf-8")

start = src.index("<style>")
end = src.index("</style>", start) + len("</style>")
base = src[start:end]

assert src.count("<style>") == 2, (
    f"week7.html has {src.count('<style>')} style blocks, expected 2 "
    "(shared + week-seven-only)")
for leak in (".tether", "--c:var(--out)", "--tovuto", ".tribe-cards.one"):
    assert leak not in base, f"the shared block picked up week-only {leak}"
for token in ("--f-disp", "--f-body", ".pip", ".standings", ".tcard",
              ".gone-box", ".kicker", ".tribals", "prefers-color-scheme"):
    assert token in base, f"shared style block is missing {token}"
assert len(base) > 6000, f"shared style block is only {len(base)} bytes"

assert tpl.count(SENTINEL) == 1, f"expected exactly one {SENTINEL} in the template"
out = tpl.replace(SENTINEL, base)

assert base in out, "the spliced block is not byte-identical in the result"
assert SENTINEL not in out, "the sentinel survived the splice"
assert out.count("<style>") == 2, "the result should carry two style blocks"
assert ".tether" not in out, "week six's tether rules leaked into week eight"
assert out.count("--tovuto:#1F5FBF") == 1, "the Tovuto tokens should appear exactly once"

# Every custom property the page USES must be DEFINED on it. An undefined
# var() fails silently in the browser (week six's tether callout lost its
# border, background and heading font to --line/--card/--f-disp this way).
import re
used = set(re.findall(r"var\((--[\w-]+)", out))
defined = set(re.findall(r"(--[\w-]+)\s*:", out))
assert not used - defined, f"undefined CSS custom properties: {sorted(used - defined)}"

OUT.write_text(out, encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)} ({len(out):,} bytes; "
      f"{len(base):,} of them the shared style block)")
