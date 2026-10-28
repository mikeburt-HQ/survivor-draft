"""Verify public/week5.html against week5_map.py. Fails loudly on any mismatch.

Covers the recap's own content. The vote ledger at the bottom of the page is
checked separately by `check_votes.py --page week5.html --through 5`; both must
pass before the page ships.

Three lessons are baked in here, each of which has produced a FALSE FAILURE on
an earlier checker in this repo:

1. Regexes anchor on ELEMENT TAGS, never a bare attribute - a bare attribute
   match hits the CSS block first.
2. Parse the RAW page, and html.unescape() only the strings you COMPARE.
   Unescaping the whole document first turns `title="... &quot;Jelly&quot; ..."`
   into a real quote and silently breaks the attribute parse.
3. unescape() is not enough: `&ldquo;Jelly&rdquo;` becomes CURLY quotes while
   the database spelling uses STRAIGHT ones. Normalise typographic quotes
   before any name comparison.

And one from the week-4 pass: a MISSING section marker is reported as a named
failure, never raised. A traceback exits non-zero without evaluating a single
check, so it reads like a broken tool rather than a page defect.
"""

import html
import importlib.util
import io
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "public" / "week5.html"


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, pathlib.Path(__file__).parent / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    stdout, sys.stdout = sys.stdout, io.StringIO()
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.stdout = stdout
    return mod


w5 = load("week5_map")
vh = load("vote_history")

page = PAGE.read_text(encoding="utf-8")
fail = []

QUOTES = {"“": '"', "”": '"', "‘": "'", "’": "'"}


def norm(s):
    """Unescape entities, straighten typographic quotes, collapse whitespace."""
    s = html.unescape(s)
    for bad, good in QUOTES.items():
        s = s.replace(bad, good)
    return re.sub(r"\s+", " ", s).strip()


def check(cond, msg):
    if not cond:
        fail.append(msg)


def section(start, end=None):
    """Slice between two markers; a missing marker is a FAILURE, not a raise."""
    if start not in page:
        check(False, f"page is missing the section marker {start!r}")
        return ""
    i = page.index(start)
    if end is not None and end not in page:
        check(False, f"page is missing the section marker {end!r}; "
                     f"slicing {start!r} to the end of the file instead")
        return page[i:]
    j = page.index(end, i) if end else len(page)
    return page[i:j]


SHORT = {"Toka (Yellow)": "toka", "Savu (Purple)": "savu", "Dina (Red)": "dina"}
LETTER = {"toka": "T", "savu": "S", "dina": "D"}
alive_tribe = {n: t for t, roster in w5.TRIBES.items()
               for n in roster if n not in w5.out}

# --- 1. the "who owns whom" table: tribe chip + owner for all 21 -----------
board = section(">Who owns whom<", ">Vote ledger<")
rows = re.findall(
    r"<tr><td(?P<cls>[^>]*)>(?P<name>[^<]+)</td>"
    r"<td><span class=\"chip (?P<chip>\w+)\">[^<]*</span></td>"
    r"<td><span class=\"owner\">(?P<owner>[^<]*)</span></td></tr>",
    board,
)
check(len(rows) == 21, f"board table has {len(rows)} rows, expected 21")

seen = set()
for cls, raw_name, chip, raw_owner in rows:
    name, owner_txt = norm(raw_name), norm(raw_owner)
    seen.add(name)
    check(name in w5.owner, f"board row names unknown castaway {name!r}")
    if name not in w5.owner:
        continue
    want_owner = w5.owner[name]
    if name in w5.out:
        ep = w5.GONE[name][0]
        check(chip == "none", f"{name} is out but chip is {chip!r}, expected none")
        check("struck" in cls, f"{name} is out but the row is not struck through")
        check(want_owner.lower() in owner_txt.lower(),
              f"{name} owner cell {owner_txt!r} does not name {want_owner}")
        check(f"ep {ep}" in owner_txt,
              f"{name} left in ep {ep}; cell reads {owner_txt!r}")
        how = w5.GONE[name][1]
        word = "quit" if how == "quit" else "out"
        check(word in owner_txt.lower(),
              f"{name} {how} in ep {ep}; cell reads {owner_txt!r}")
    else:
        want_chip = SHORT[alive_tribe[name]]
        check(chip == want_chip,
              f"{name} chip is {chip!r}, expected {want_chip!r} "
              f"({alive_tribe[name]})")
        check("struck" not in cls, f"{name} is alive but the row is struck through")
        if want_owner == "undrafted":
            check("undrafted" in owner_txt.lower(),
                  f"{name} should read undrafted, got {owner_txt!r}")
        else:
            check(owner_txt == want_owner,
                  f"{name} owner cell {owner_txt!r}, expected {want_owner!r}")

missing = sorted(set(w5.everyone) - seen)
check(not missing, f"castaways absent from the board table: {missing}")

# --- 2. standings rows: pips, tribe letters, owner, left count, votes ------
received = {}
for t in vh.TRIBALS:
    if t["ep"] <= 5:
        for n, v in t["votes"].items():
            received[n] = received.get(n, 0) + v
votes_by_drafter = {d: 0 for d in w5.DRAFT}
for n, v in received.items():
    votes_by_drafter[w5.owner[n]] += v

standings = section(">Standings<", ">The three tribes<")
for who in w5.DRAFT:
    block = re.search(
        r"<div class=\"row r-" + who.lower() + r"\">(.*?)"
        r"<div class=\"count\">(\d+)<small>left</small></div>\s*"
        r"<div class=\"count vcount\">(\d+)<small>votes</small>",
        standings, re.S,
    )
    check(block is not None, f"no standings row for {who}")
    if not block:
        continue
    body, count, vcount = block.group(1), int(block.group(2)), int(block.group(3))

    pips = re.findall(
        r"<span class=\"pip (\w+)\" title=\"([^\"]*)\">(.*?)</span>", body)
    check(len(pips) == 5, f"{who} has {len(pips)} pips, expected 5 picks")

    want_alive = [n for _, n in w5.DRAFT[who] if n not in w5.out]
    live_pips = [p for p in pips if p[0] != "gone"]
    check(len(live_pips) == len(want_alive),
          f"{who}: {len(live_pips)} live pips vs {len(want_alive)} live picks")
    check(count == len(want_alive),
          f"{who} count reads {count}, expected {len(want_alive)}")
    check(vcount == votes_by_drafter[who],
          f"{who} votes-taken reads {vcount}, expected {votes_by_drafter[who]}")

    for kind, raw_title, raw_glyph in pips:
        nm = norm(raw_title).split("—")[0].strip()
        check(nm in w5.owner, f"{who} pip titles unknown castaway {nm!r}")
        if nm not in w5.owner:
            continue
        check(w5.owner[nm] == who,
              f"{who}'s row shows {nm}, who belongs to {w5.owner[nm]}")
        if kind == "gone":
            check(nm in w5.out, f"{who}: {nm} shown as gone but is still in")
            how = w5.GONE[nm][1]
            want_glyph = "Q" if how == "quit" else "×"
            check(norm(raw_glyph) == want_glyph,
                  f"{who}: {nm} {how} but the pip glyph is "
                  f"{norm(raw_glyph)!r}, expected {want_glyph!r}")
            check(f"episode {w5.GONE[nm][0]}" in norm(raw_title),
                  f"{who}: {nm} pip title does not name episode "
                  f"{w5.GONE[nm][0]}")
        else:
            check(nm not in w5.out, f"{who}: {nm} shown on a tribe but is out")
            want_chip = SHORT[alive_tribe[nm]]
            check(kind == want_chip,
                  f"{who}: {nm} pip is {kind!r}, expected {want_chip!r}")
            check(norm(raw_glyph) == LETTER[kind],
                  f"{who}: {nm} pip glyph {norm(raw_glyph)!r} does not match {kind}")
            check(alive_tribe[nm].split(" ")[0] in norm(raw_title),
                  f"{who}: {nm} pip title does not name {alive_tribe[nm]}")

# rows must run most-castaways-first, or the page argues with itself
row_order = [w for w in re.findall(r"<div class=\"row r-(\w+)\">", standings)]
counts_in_order = [len([n for _, n in w5.DRAFT[w.capitalize()]
                        if n not in w5.out]) for w in row_order]
check(counts_in_order == sorted(counts_in_order, reverse=True),
      f"standings rows are not ordered most-left-first: "
      f"{list(zip(row_order, counts_in_order))}")

# --- 3. tribe cards: each roster is exactly that tribe's survivors ---------
cards = section(">The three tribes<", "<div class=\"story\">")
found_cards = re.findall(r"<div class=\"tcard (\w+)\">(.*?)</ul>", cards, re.S)
check(len(found_cards) == 3, f"found {len(found_cards)} tribe cards, expected 3")
for short, body in found_cards:
    tribe_name = next(t for t, s in SHORT.items() if s == short)
    want = sorted(n for n in w5.TRIBES[tribe_name] if n not in w5.out)
    got = sorted(norm(m) for m in re.findall(r"<li>([^<]+)<span>", body))
    check(got == want, f"{tribe_name} card roster\n   got  {got}\n   want {want}")

    names = [norm(m) for m in re.findall(r"<li>([^<]+)<span>", body)]
    owners = [norm(m) for m in re.findall(r"<span>([^<]+)</span>", body)]
    for nm, ow in zip(names, owners):
        if nm in w5.owner:
            want_ow = w5.owner[nm]
            check(want_ow in ow or (want_ow == "undrafted"
                                    and "undrafted" in ow.lower()),
                  f"{tribe_name} card: {nm} credited to {ow!r}, "
                  f"expected {want_ow!r}")

    n = re.search(r"·\s*(\d+)\s*·", norm(body))
    check(n is not None and int(n.group(1)) == len(want),
          f"{tribe_name} card count should read {len(want)}")

# --- 4. hardware table == the advantages still in play ---------------------
hardware = section(">Hardware watch<", "class=\"gone-pair\"")
hw = re.findall(
    r"<tr><td>([^<]+)</td><td><span class=\"chip (\w+)\">", hardware)
holders = [norm(h) for h, _ in hw]
check(sorted(holders) == sorted(w5.ADVANTAGES),
      f"hardware holders\n   got  {sorted(holders)}\n"
      f"   want {sorted(w5.ADVANTAGES)}")
for raw_h, chip in hw:
    nm = norm(raw_h)
    if nm in alive_tribe:
        check(chip == SHORT[alive_tribe[nm]],
              f"hardware: {nm} chip {chip!r}, "
              f"expected {SHORT[alive_tribe[nm]]!r}")
# An advantage SPENT this week must not still be listed as in play.
for nm in w5.SPENT:
    check(nm not in holders,
          f"{nm} spent their advantage in episode 5 but is still in the "
          f"hardware table")
    check(nm in norm(hardware),
          f"{nm}'s spent advantage should be noted under the table")

# --- 5. one gone box per episode-5 boot, with pick number and drafter ------
gone_pair = section("class=\"gone-pair\"", ">Who owns whom<")
boxes = re.findall(r"<div class=\"nm\">([^<]+)</div>\s*<p>(.*?)</p>",
                   gone_pair, re.S)
ep5 = sorted(n for n, (ep, _) in w5.GONE.items() if ep == 5)
check(sorted(norm(b[0]) for b in boxes) == ep5,
      f"gone boxes name {sorted(norm(b[0]) for b in boxes)}, expected {ep5}")

pick_of = {n: p for picks in w5.DRAFT.values() for p, n in picks}
place = {n: i + 1 for i, n in enumerate(
    [m for m, (ep, how) in sorted(w5.GONE.items(), key=lambda kv: (kv[1][0], kv[0]))
     if how == "voted out"])}
ORD = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
       6: "sixth", 7: "seventh"}
for raw_nm, body in boxes:
    nm, txt = norm(raw_nm), norm(body)
    if nm not in w5.owner:
        continue
    check(f"{pick_of[nm]}" in txt,
          f"{nm} box should give the pick number {pick_of[nm]}; reads: {txt[:90]}")
    check(w5.owner[nm] in txt, f"{nm} box should name {w5.owner[nm]}")
    check(ORD[place[nm]] in txt.lower(),
          f"{nm} was the {ORD[place[nm]]} voted out; box reads: {txt[:110]}")

# --- 6. omissions actually stayed omitted ---------------------------------
# The ep-4 tally came OFF this list once it was settled. These three are still
# genuinely unsettled or unaired, and each says in one line why it is benign
# to suppress: the whale idol's holder is named by nobody, the revote tally is
# arithmetically impossible, and "unanimous" was simply wrong when printed.
flat = norm(page)
OMISSIONS = [
    (r"\bwhale\b", "the mini-whale idol by name (holder still unconfirmed)"),
    (r"\bunanimous\b", "the word unanimous (printed wrongly twice this season)"),
    (r"revote[^.]{0,40}4\s*[-–]\s*4",
     "a 4-4 revote tally, which cannot happen with four voters"),
]
for banned, why in OMISSIONS:
    check(not re.search(banned, flat, re.I), f"page mentions {why}")

# Episode 6 airs the evening this page ships, so nothing from it may appear.
for banned in [r"\bepisode 6\b", r"\bI Love Crying\b"]:
    check(not re.search(banned, flat, re.I),
          f"page refers to unaired material: {banned}")

# --- 7. headline claims must be derivable from the data -------------------
untouched = [w for w, picks in w5.DRAFT.items()
             if not any(n in w5.out for _, n in picks)]
check(untouched == [],
      f"page claims nobody has a clean sheet; these drafters do: {untouched}")

left = {w: len([n for _, n in picks if n not in w5.out])
        for w, picks in w5.DRAFT.items()}
check(left == {"Mike": 4, "Cagney": 3, "Daron": 3, "Will": 3},
      f"standings changed: {left}")

mike_toka = sum(1 for n in w5.TRIBES["Toka (Yellow)"]
                if n not in w5.out and w5.owner[n] == "Mike")
toka_live = len([n for n in w5.TRIBES["Toka (Yellow)"] if n not in w5.out])
check(mike_toka == 4 and toka_live == 6,
      f"page claims Mike holds four of Toka's six; actual {mike_toka} of {toka_live}")

savu_owners = sorted(w5.owner[n] for n in w5.TRIBES["Savu (Purple)"]
                     if n not in w5.out)
check(savu_owners == ["Cagney", "Daron", "Will"],
      f"page claims Savu is one castaway each from Cagney, Daron and Will; "
      f"actual {savu_owners}")
check("Mike" not in savu_owners, "page claims Mike has nobody on Savu")

check(len(w5.alive) == 14, f"page claims fourteen left; actual {len(w5.alive)}")
check(len(w5.out) == 7, f"page claims seven are out; actual {len(w5.out)}")
check(w5.owner["Cristian Chavez"] == "undrafted"
      and "Cristian Chavez" in w5.TRIBES["Dina (Red)"]
      and "Cristian Chavez" not in w5.out,
      "page claims undrafted Cristian is still in, on Dina")

# The headline: Maggie and Linnea share a drafter, and Linnea is that drafter's
# first loss. Both halves are asserted, because either alone is not the story.
check(w5.owner["Maggie Nestor"] == w5.owner["Linnea Capobianco"] == "Mike",
      "the headline needs Maggie and Linnea to both be Mike's")
mike_losses = [n for _, n in w5.DRAFT["Mike"] if n in w5.out]
check(mike_losses == ["Linnea Capobianco"],
      f"page claims Linnea is Mike's only loss; actual {mike_losses}")

story = section("<div class=\"story\">", ">Hardware watch<")
for nm in ["Maggie Nestor", "Linnea Capobianco", "Danny Kilby", "Lewis Kelly",
           "Cristian Chavez", "Alexis Levine"]:
    check(nm in norm(story), f"the story section should name {nm}")

# Lewis survived the tie, so he must NOT be shown as out anywhere.
check("Lewis Kelly" not in w5.out, "Lewis Kelly survived episode 5")

# --- 8. no gendered pronouns except Daron's, and only about Daron ---------
def strip_tags(chunk):
    return norm(re.sub(r"<[^>]+>", " ", chunk))


prose = strip_tags(section("<body>"))
slips = re.findall(r"\b(he|him|his|himself|man|woman|men|women)\b", prose, re.I)
check(not slips,
      f"page uses gendered pronouns for people whose pronouns are not "
      f"stated: {sorted(set(w.lower() for w in slips))}")

# Daron is she/her. Nobody else here has stated pronouns, so a she/her must sit
# inside a Daron section or not appear at all.
FEM = r"\b(she|her|hers|herself)\b"
here = re.findall(FEM, prose, re.I)
daron_secs = [">Daron came within one refusal of losing Lewis<"]
allowed = []
for marker in daron_secs:
    if marker in page:
        allowed += re.findall(FEM, strip_tags(section(marker, "<h2")), re.I)
check(len(here) == len(allowed),
      f"page has {len(here)} she/her, {len(allowed)} of them inside a Daron "
      f"section; every one must be about Daron")

# --- report ----------------------------------------------------------------
if fail:
    print(f"FAIL ({len(fail)})")
    for f in fail:
        print(f" - {f}")
    sys.exit(1)

print(f"PASS  {len(rows)} board rows, {len(w5.DRAFT)} standings rows, "
      f"{len(found_cards)} tribe cards, {len(holders)} advantages, "
      f"{len(boxes)} gone boxes, {len(w5.alive)} alive, "
      f"{len(OMISSIONS)} omissions held, no stray pronouns")
