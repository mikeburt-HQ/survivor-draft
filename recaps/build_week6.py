"""Compose public/week6.html = week6_page.html with the SHARED <style> block
spliced in verbatim from week5.html.

The style block is MOVED, never retyped: retyping is how a design token
silently drifts between weeks. The splice is asserted both ways -- the block
must be found in the source, and the result must contain it byte-for-byte.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "public" / "week5.html"
TPL = pathlib.Path(__file__).parent / "week6_page.html"
OUT = ROOT / "public" / "week6.html"
SENTINEL = "<!--BASE-STYLE-->"

src = SRC.read_text(encoding="utf-8")
tpl = TPL.read_text(encoding="utf-8")

# The shared block is the FIRST <style>...</style> in week5.html; the second is
# that week's own additions, which must NOT come across.
start = src.index("<style>")
end = src.index("</style>", start) + len("</style>")
base = src[start:end]

assert src.count("<style>") == 2, (
    f"week5.html has {src.count('<style>')} style blocks, expected 2 "
    "(shared + week-five-only)")
assert "--c:var(--out)" not in base, \
    "the shared block picked up the week-five-only rules"
for token in ("--f-disp", "--f-body", ".pip", ".standings", ".tcard",
              ".gone-box", ".kicker", ".tribals", "prefers-color-scheme"):
    assert token in base, f"shared style block is missing {token}"
assert len(base) > 6000, f"shared style block is only {len(base)} bytes"

assert tpl.count(SENTINEL) == 1, f"expected exactly one {SENTINEL} in the template"
out = tpl.replace(SENTINEL, base)

assert base in out, "the spliced block is not byte-identical in the result"
assert SENTINEL not in out, "the sentinel survived the splice"
assert out.count("<style>") == 2, "the result should carry two style blocks"
assert out.count(".gone-pair") == 0, \
    "the week-five-only .gone-pair rules leaked in; week 6 has a single boot"

OUT.write_text(out, encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)} ({len(out):,} bytes; "
      f"{len(base):,} of them the shared style block)")
