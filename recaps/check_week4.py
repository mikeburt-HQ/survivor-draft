"""Verify public/week4.html against week4_map.py. Fails loudly on any mismatch.

Three lessons are baked in here, each of which has produced a FALSE FAILURE
before:

1. Regexes anchor on ELEMENT TAGS, never a bare attribute - a bare attribute
   match hits the CSS block first.
2. Parse the RAW page, and html.unescape() only the strings you COMPARE.
   Unescaping the whole document first turns `title="... &quot;Jelly&quot; ..."`
   into a real quote mid-attribute and silently breaks the attribute parse.
3. unescape() is not enough: `&ldquo;Jelly&rdquo;` becomes CURLY quotes while
   the database spelling uses STRAIGHT ones. Normalise typographic quotes
   before any name comparison.
"""

import html
import importlib.util
import io
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "public" / "week4.html"

spec = importlib.util.spec_from_file_location(
    "w4", pathlib.Path(__file__).parent / "week4_map.py")
w4 = importlib.util.module_from_spec(spec)
_stdout, sys.stdout = sys.stdout, io.StringIO()
try:
    spec.loader.exec_module(w4)
finally:
    sys.stdout = _stdout

page = PAGE.read_text(encoding="utf-8")
fail = []

# This page is a FROZEN snapshot: its figures stop at episode 4 and must keep
# reconciling as later episodes are added to vote_history. Comparing against
# the whole model makes a correct page read as wrong.
THROUGH = 4

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


SHORT = {"Toka (Yellow)": "toka", "Savu (Purple)": "savu", "Dina (Red)": "dina"}
LETTER = {"toka": "T", "savu": "S", "dina": "D"}
alive_tribe = {n: t for t, roster in w4.TRIBES.items()
               for n in roster if n not in w4.out}


def section(start, end=None):
    """Slice the raw page between two headings so sibling tables can't collide.

    A MISSING marker is reported as a named failure, not raised: a traceback
    exits non-zero without evaluating any check, so it reads like a broken
    tool rather than a page defect. Removing the vote ledger heading used to
    crash this file at the board-table slice.
    """
    if start not in page:
        check(False, f"page is missing the section marker {start!r}")
        return ""
    i = page.index(start)
    if end is not None and end not in page:
        check(False, f"page is missing the section marker {end!r}; "
                     f"slicing {start!r} to the end of the file instead")
        return page[i:]
    j = page.index(end, i) if end else len(page)
    assert i < j, f"{start!r} does not precede {end!r}"
    return page[i:j]


# --- 1. the "who owns whom" table: tribe chip + owner for all 21 -----------
# Bounded at the vote ledger: that section carries its own table, and an
# unbounded slice to EOF would put both tables in front of one regex.
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
    check(name in w4.owner, f"board row names unknown castaway {name!r}")
    if name not in w4.owner:
        continue
    want_owner = w4.owner[name]
    if name in w4.out:
        check(chip == "none", f"{name} is out but chip is {chip!r}, expected none")
        check("struck" in cls, f"{name} is out but row is not struck through")
        check(want_owner.lower() in owner_txt.lower(),
              f"{name} owner cell {owner_txt!r} does not name {want_owner}")
    else:
        want_chip = SHORT[alive_tribe[name]]
        check(chip == want_chip,
              f"{name} chip is {chip!r}, expected {want_chip!r} ({alive_tribe[name]})")
        check("struck" not in cls, f"{name} is alive but row is struck through")
        if want_owner == "undrafted":
            check("undrafted" in owner_txt.lower(),
                  f"{name} should read undrafted, got {owner_txt!r}")
        else:
            check(owner_txt == want_owner,
                  f"{name} owner cell {owner_txt!r}, expected {want_owner!r}")

missing = sorted(set(w4.everyone) - seen)
check(not missing, f"castaways absent from the board table: {missing}")

# --- 2. standings rows: pip count, tribe letters, owner, and the total -----
standings = section(">Standings<", ">The new tribes<")
for who in w4.DRAFT:
    block = re.search(
        r"<div class=\"row r-" + who.lower() + r"\">(.*?)<div class=\"count\">(\d+)<small>",
        standings, re.S,
    )
    check(block is not None, f"no standings row for {who}")
    if not block:
        continue
    body, count = block.group(1), int(block.group(2))

    pips = re.findall(
        r"<span class=\"pip (\w+)\" title=\"([^\"]*)\">(.*?)</span>", body)
    check(len(pips) == 5, f"{who} has {len(pips)} pips, expected 5 picks")

    want_alive = [n for _, n in w4.DRAFT[who] if n not in w4.out]
    live_pips = [p for p in pips if p[0] != "gone"]
    check(len(live_pips) == len(want_alive),
          f"{who}: {len(live_pips)} live pips vs {len(want_alive)} live picks")
    check(count == len(want_alive),
          f"{who} count reads {count}, expected {len(want_alive)}")

    for kind, raw_title, raw_glyph in pips:
        nm = norm(raw_title).split("—")[0].strip()
        check(nm in w4.owner, f"{who} pip titles unknown castaway {nm!r}")
        if nm not in w4.owner:
            continue
        check(w4.owner[nm] == who,
              f"{who}'s row shows {nm}, who belongs to {w4.owner[nm]}")
        if kind == "gone":
            check(nm in w4.out, f"{who}: {nm} shown as gone but is still in the game")
        else:
            check(nm not in w4.out, f"{who}: {nm} shown on a tribe but is out")
            want_chip = SHORT[alive_tribe[nm]]
            check(kind == want_chip,
                  f"{who}: {nm} pip is {kind!r}, expected {want_chip!r}")
            check(norm(raw_glyph) == LETTER[kind],
                  f"{who}: {nm} pip glyph {norm(raw_glyph)!r} does not match {kind}")
            # the title must also name the right tribe, not just carry the class
            check(alive_tribe[nm].split(" ")[0] in norm(raw_title),
                  f"{who}: {nm} pip title does not name {alive_tribe[nm]}")

# --- 3. tribe cards: each roster is exactly that tribe's survivors ---------
cards = section(">The new tribes<", "<div class=\"story\">")
found_cards = re.findall(r"<div class=\"tcard (\w+)\">(.*?)</ul>", cards, re.S)
check(len(found_cards) == 3, f"found {len(found_cards)} tribe cards, expected 3")
for short, body in found_cards:
    tribe_name = next(t for t, s in SHORT.items() if s == short)
    want = sorted(n for n in w4.TRIBES[tribe_name] if n not in w4.out)
    got = sorted(norm(m) for m in re.findall(r"<li>([^<]+)<span>", body))
    check(got == want, f"{tribe_name} card roster\n   got  {got}\n   want {want}")

    owners = [norm(m) for m in re.findall(r"<span>([^<]+)</span>", body)]
    names = [norm(m) for m in re.findall(r"<li>([^<]+)<span>", body)]
    for nm, ow in zip(names, owners):
        if nm in w4.owner:
            want_ow = w4.owner[nm]
            check(want_ow in ow or (want_ow == "undrafted" and "undrafted" in ow.lower()),
                  f"{tribe_name} card: {nm} credited to {ow!r}, expected {want_ow!r}")

    n = re.search(r"·\s*(\d+)\s*·", norm(body))
    check(n is not None and int(n.group(1)) == len(want),
          f"{tribe_name} card count should read {len(want)}")

# --- 4. hardware table holders == ADVANTAGES, with the right tribe ---------
hardware = section(">Hardware watch<", "class=\"gone-box\"")
hw = re.findall(
    r"<tr><td>([^<]+)</td><td><span class=\"chip (\w+)\">", hardware)
holders = [norm(h) for h, _ in hw]
check(sorted(holders) == sorted(w4.ADVANTAGES),
      f"hardware holders\n   got  {sorted(holders)}\n   want {sorted(w4.ADVANTAGES)}")
for raw_h, chip in hw:
    nm = norm(raw_h)
    if nm in alive_tribe:
        check(chip == SHORT[alive_tribe[nm]],
              f"hardware: {nm} chip {chip!r}, expected {SHORT[alive_tribe[nm]]!r}")

# --- 5. omissions actually stayed omitted ---------------------------------
# The 4-1 tally WAS on this list and has come off: it is now carried by
# Wikipedia's vote table, TVLine and Yahoo's results piece, and it reconciles
# against the five people who could vote. See recaps/vote_history.py. The
# live-blog "unanimous" stays banned, because it was simply wrong.
flat = norm(page)
OMISSIONS = [
    (r"\bunanimous\b", "the word unanimous (a live blog got this wrong)"),
    (r"blood\s*ring", "the Blood Ring, which is teased for a LATER episode"),
]

# The baby whale is the design of the season's SECOND hidden immunity idol,
# shown at the episode-4 challenge. Naming it is fine and now correct; what
# must never happen is ATTRIBUTING it to a holder. So it belongs in the note
# above the table and must stay out of the holders table itself. A blanket ban
# on the word used to stand here, which is why the page carried a wrong
# description of it for two weeks instead of the right one.
check("<div class=\"tbl-scroll\">" in hardware,
      "the hardware section should contain a holders table")
if "<div class=\"tbl-scroll\">" in hardware:
    cut = hardware.index("<div class=\"tbl-scroll\">")
    hw_note, hw_table = norm(hardware[:cut]), norm(hardware[cut:])
    check("whale" in hw_note.lower(),
          "the hardware note should say the second idol is a baby whale")
    check("whale" not in hw_table.lower(),
          "the baby whale appears in the holders table, which attributes an "
          "idol nobody is known to hold")
    check("iced coffee" in hw_note.lower(),
          "the note should say second place won iced coffee, not an idol")
for banned, why in OMISSIONS:
    check(not re.search(banned, flat, re.I), f"page mentions {why}")

# --- 5b. the tally is now STATED, and in the right place ------------------
spec_vh = importlib.util.spec_from_file_location(
    "vote_history", pathlib.Path(__file__).parent / "vote_history.py")
vh = importlib.util.module_from_spec(spec_vh)
_stdout, sys.stdout = sys.stdout, io.StringIO()
try:
    spec_vh.loader.exec_module(vh)
finally:
    sys.stdout = _stdout

ep4 = next(t for t in vh.TRIBALS if t["ep"] == THROUGH and t["tribe"] == "Savu")
boot = max(ep4["votes"], key=ep4["votes"].get)
runner = min(ep4["votes"], key=ep4["votes"].get)
want_tally = f"{ep4['votes'][boot]}-{ep4['votes'][runner]}"

gone_box = norm(section("class=\"gone-box\"", ">Who owns whom<"))
check(boot in gone_box, f"the gone box should name {boot}")
# Dash-tolerant: the page sets the tally with an &ndash;, and norm() here
# deliberately does NOT fold dashes, because name parsing splits on em dash.
check(re.search(rf"{ep4['votes'][boot]}\s*[-–—]\s*{ep4['votes'][runner]}",
                gone_box),
      f"gone box should state the tally as {want_tally}; reads: {gone_box[-170:]}")
check(runner in gone_box,
      f"gone box should name {runner} as taking the other vote")
check(ep4["votes"][runner] == 1 and "single vote" in gone_box,
      "gone box should describe one vote on the other side")

# --- 5c. votes-taken column matches the ledger ----------------------------
received = {}
for t in vh.TRIBALS:
    if t["ep"] <= THROUGH:
        for n, v in t["votes"].items():
            received[n] = received.get(n, 0) + v
vh_owner = {n: d for d, picks in vh.DRAFT.items() for n in picks}
votes_by_drafter = {d: 0 for d in vh.DRAFT}
for n, v in received.items():
    votes_by_drafter[vh_owner[n]] += v

for who in w4.DRAFT:
    m = re.search(
        r"<div class=\"row r-" + who.lower() + r"\">.*?"
        r"<div class=\"count vcount\">(\d+)<small>votes</small>",
        standings, re.S)
    check(m is not None, f"{who} standings row has no votes-taken cell")
    if m:
        check(int(m.group(1)) == votes_by_drafter[who],
              f"{who} votes-taken reads {m.group(1)}, "
              f"expected {votes_by_drafter[who]}")

# The ledger lives in this page now, not at /votes.html, so the standings
# note points at the in-page anchor and nothing may link the deleted page.
check('<h2 id="votes">' in page, "the vote ledger section is missing")
check('href="#votes"' in standings,
      "the standings note should link down to the ledger")
check("/votes.html" not in page,
      "page still links /votes.html, which no longer exists")
check(not (ROOT / "public" / "votes.html").exists(),
      "public/votes.html still exists; the ledger was moved into this page")

# --- 5d. no gendered pronouns for anyone whose pronouns are unstated ------
# Daron is she/her; no castaway's pronouns have been stated anywhere, and
# this page is read by three other people. "one undrafted man" shipped live
# about Cristian Chavez before this gate existed.
def strip_tags(chunk):
    return norm(re.sub(r"<[^>]+>", " ", chunk))


prose = strip_tags(section("<body>"))
slips = re.findall(r"\b(he|him|his|himself|man|woman|men|women)\b", prose, re.I)
check(not slips,
      f"page uses gendered pronouns for people whose pronouns are not "
      f"stated: {sorted(set(w.lower() for w in slips))}")

# Daron is she/her, so she/her is not banned outright -- but it must appear
# ONLY inside Daron's own section. A "she" anywhere else is a castaway or
# another drafter being assigned pronouns nobody has stated.
FEM = r"\b(she|her|hers|herself)\b"
daron_sec = strip_tags(section(">Daron drew one of each<", "<h2>Will lost"))
here, allowed = re.findall(FEM, prose, re.I), re.findall(FEM, daron_sec, re.I)
check(len(here) == len(allowed) and allowed,
      f"page has {len(here)} she/her, {len(allowed)} of them in Daron's "
      f"section; every one must be about Daron")

# --- 6. headline claims must be derivable from the data -------------------
untouched = [w for w, picks in w4.DRAFT.items()
             if not any(n in w4.out for _, n in picks)]
check(untouched == ["Mike"],
      f"page claims only Mike has lost nobody; actual: {untouched}")
daron_tribes = {alive_tribe[n] for _, n in w4.DRAFT["Daron"] if n not in w4.out}
check(len(daron_tribes) == 3,
      f"page claims Daron has one on each tribe; hers span {sorted(daron_tribes)}")
mike_toka = sum(1 for n in w4.TRIBES["Toka (Yellow)"] if w4.owner[n] == "Mike")
check(mike_toka == 4 and len(w4.TRIBES["Toka (Yellow)"]) == 6,
      f"page claims Mike owns 4 of Toka's 6; actual {mike_toka} of "
      f"{len(w4.TRIBES['Toka (Yellow)'])}")
check(len(w4.alive) == 16, f"page claims sixteen left; actual {len(w4.alive)}")
check(len(w4.out) == 5,
      f"page claims Cristian outlasted five drafted players; actual {len(w4.out)}")
check(w4.owner["Cristian Chavez"] == "undrafted" and
      "Cristian Chavez" in w4.TRIBES["Dina (Red)"],
      "page claims undrafted Cristian landed on Dina")
voted = sum(1 for _, (_, how) in w4.GONE.items() if how == "voted out")
check(voted == 4, f"page calls Jenna the fourth voted out; actual {voted}")
check(len([n for _, n in w4.DRAFT["Will"] if n not in w4.out]) ==
      len([n for _, n in w4.DRAFT["Daron"] if n not in w4.out]) == 3,
      "page claims Will is level with Daron on three")

# --- report ----------------------------------------------------------------
if fail:
    print(f"FAIL ({len(fail)})")
    for f in fail:
        print(f" - {f}")
    sys.exit(1)

print(f"PASS  {len(rows)} board rows, {len(w4.DRAFT)} standings rows, "
      f"{len(found_cards)} tribe cards, {len(holders)} advantages, "
      f"{len(w4.alive)} alive, {len(OMISSIONS)} omissions held, "
      f"tally {want_tally} stated, no stray pronouns")
