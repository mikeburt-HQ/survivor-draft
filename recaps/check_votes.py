"""Verify public/votes.html against recaps/vote_history.py.

Every number on the page is asserted AT ITS POSITION -- inside its own drafter
row, its own tribal card, its own table row -- never by appearing somewhere in
the document. A value present in the wrong place is the defect this is for.

Two traps this file is written around, both of which have produced false
failures on earlier checkers in this repo:

  * Parse the RAW page. Unescaping the whole document first turns a &quot;
    inside a title attribute into a real quote and breaks the attribute parse.
  * html.unescape() alone is not enough to compare text: &ldquo; yields a
    CURLY quote while the data holds a straight one. norm() straightens them.

Anchors are on element TAGS, never on a bare attribute, because a bare
attribute matches the CSS block first and runs to the wrong element.
"""

import html
import importlib.util
import io
import pathlib
import re
import sys
import contextlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "public" / "votes.html"

# Load vote_history as the single source of truth. Importing it re-runs all of
# its own asserts, so a broken model fails here too.
spec = importlib.util.spec_from_file_location(
    "vote_history", pathlib.Path(__file__).resolve().parent / "vote_history.py")
vh = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(vh)

raw = PAGE.read_text(encoding="utf8")

CURLY = {"“": '"', "”": '"', "‘": "'", "’": "'",
         "‑": "-", "–": "-", "—": "--", " ": " "}


def norm(s):
    """Compare-ready: unescape, straighten curly punctuation, collapse space."""
    s = html.unescape(s)
    for bad, good in CURLY.items():
        s = s.replace(bad, good)
    return re.sub(r"\s+", " ", s).strip()


def section(start, end=None):
    """Slice the raw page between two markers, so a table regex cannot stray."""
    i = raw.index(start)
    j = raw.index(end, i) if end else len(raw)
    return raw[i:j]


failures = []


def check(ok, msg):
    if not ok:
        failures.append(msg)


# --- rebuild the expected figures from the module -------------------------
received = {}
for t in vh.TRIBALS:
    for n, v in t["votes"].items():
        received[n] = received.get(n, 0) + v

owner = {n: d for d, picks in vh.DRAFT.items() for n in picks}
total = sum(received.values())

by_drafter = {d: 0 for d in vh.DRAFT}
for n, v in received.items():
    by_drafter[owner[n]] += v

out_names = {max(t["votes"], key=t["votes"].get) for t in vh.TRIBALS}
top = max(by_drafter.values())

# --- 1. headline and standfirst carry the real total ----------------------
NUMWORD = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
           6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
           11: "eleven", 12: "twelve", 17: "seventeen", 21: "twenty-one",
           34: "thirty-four"}


def says(text, n, unit):
    """True if text states n before unit, as either a digit or a word."""
    t = text.lower()
    return (f"{n} {unit.lower()}" in t
            or f"{NUMWORD.get(n, n)} {unit.lower()}" in t)


# Strip tags: the headline is broken across a <span> and a <br>, so a raw
# substring test can never match the sentence a reader actually sees.
head = norm(re.sub(r"<[^>]+>", " ", section("<header>", "</header>")))
check(NUMWORD[total] in head.lower(),
      f"headline should say {NUMWORD[total]} votes; header reads: {head[:90]}")
check(says(head, total, "ballots"),
      f"standfirst should name {total} ballots")
check(says(head, len(vh.TRIBALS), "Tribal Councils"),
      f"standfirst should name {len(vh.TRIBALS)} Tribal Councils")

zero = [d for d, v in by_drafter.items() if v == 0]
check(len(zero) == 1 and f"None of them {zero[0]}'s" in head,
      f"headline should name {zero} as the drafter with no votes")

# --- 2. one drafter row each, with count, share and bar width -------------
# Split rather than match: a row holds nested divs (the bar sits inside the
# track), so a non-greedy "...</div></div>" closes early and cuts off the
# count element -- which reads exactly like a page missing its counts.
stand = section('<div class="standings">', '<div class="kicker">')
rows = []
for chunk in stand.split('<div class="row r-')[1:]:
    rows.append((re.match(r'(\w+)">', chunk).group(1), chunk))

check(len(rows) == len(vh.DRAFT),
      f"expected {len(vh.DRAFT)} drafter rows, found {len(rows)}")

seen = {}
for who, body in rows:
    name = who.capitalize()
    seen[name] = True
    expected = by_drafter[name]

    m = re.search(r'<div class="count">(\d+)<small>(.*?)</small>', body, re.S)
    check(m is not None, f"{name} row has no count element")
    if not m:
        continue
    check(int(m.group(1)) == expected,
          f"{name} count reads {m.group(1)}, expected {expected}")

    share = round(100 * expected / total)
    check(f"{share}%" in norm(m.group(2)),
          f"{name} share reads '{norm(m.group(2))}', expected {share}%")

    fill = re.search(r'<div class="fill" style="width:([\d.]+)%"', body)
    if expected == 0:
        check(fill is None, f"{name} has 0 votes but the row draws a bar")
        check('class="none-yet"' in body,
              f"{name} has 0 votes and should carry the not-once label")
    else:
        check(fill is not None, f"{name} has {expected} votes but no bar")
        if fill:
            want = round(100 * expected / top, 1)
            check(abs(float(fill.group(1)) - want) < 0.15,
                  f"{name} bar is {fill.group(1)}%, expected {want}% "
                  f"({expected} of {top})")

check(set(seen) == set(vh.DRAFT),
      f"rows cover {sorted(seen)}, expected {sorted(vh.DRAFT)}")

# row order must be descending by votes, or the page argues with itself
order = [by_drafter[w.capitalize()] for w, _ in rows]
check(order == sorted(order, reverse=True),
      f"drafter rows are not ordered most-voted first: {order}")

# --- 3. the zero-votes kicker names that drafter's whole team -------------
kick = norm(section('<div class="kicker">', "</div>"))
for n in vh.DRAFT[zero[0]]:
    check(n in kick, f"kicker should name {n} among the never-voted-against")
check(f"{len(vh.DRAFT[zero[0]])} of those" in kick
      or f"five of those" in kick.lower(),
      "kicker should tie the clean team to the clean-castaway count")

clean_total = len([n for n in owner if not received.get(n)]) + len(vh.UNDRAFTED)
check(f"Fourteen of the 21" in kick,
      f"kicker should say Fourteen of the 21 (computed {clean_total})")
check(clean_total == 14,
      f"the page says fourteen are clean; the data says {clean_total}")

# --- 4. a tribal card per council, with its own tally --------------------
cards = re.findall(r'<div class="tc (savu|toka)">(.*?)</div>\s*(?=<div class="tc |</div>)',
                   raw, re.S)
check(len(cards) == len(vh.TRIBALS),
      f"expected {len(vh.TRIBALS)} tribal cards, found {len(cards)}")

for (chip, body), t in zip(cards, vh.TRIBALS):
    ep = t["ep"]
    check(chip == t["tribe"].lower(),
          f"ep {ep} card is styled {chip}, expected {t['tribe'].lower()}")
    check(f"<h3>Episode {ep}</h3>" in norm(body),
          f"ep {ep} card is mislabelled")

    attending = t["_attending"]
    cast_votes = sum(t["votes"].values())
    meta = norm(re.search(r'<p class="n">(.*?)</p>', body, re.S).group(1))
    check(t["tribe"] in meta, f"ep {ep} meta should name {t['tribe']}: {meta}")
    check(f"day {t['day']}" in meta, f"ep {ep} meta should say day {t['day']}")
    check(f"{attending} at tribal" in meta,
          f"ep {ep} meta reads '{meta}', expected {attending} at tribal")
    check(f"{cast_votes} votes" in meta,
          f"ep {ep} meta reads '{meta}', expected {cast_votes} votes")

    lis = re.findall(r'<li( class="boot")?><span class="nm">(.*?)<span>'
                     r'(.*?)</span></span><span class="v">(\d+)</span>', body, re.S)
    check(len(lis) == len(t["votes"]),
          f"ep {ep} card lists {len(lis)} names, tally has {len(t['votes'])}")

    listed = {}
    for boot, nm, note, v in lis:
        nm, note = norm(nm), norm(note)
        listed[nm] = int(v)
        check(nm in t["votes"], f"ep {ep} card lists {nm}, who took no votes")
        if nm in t["votes"]:
            check(int(v) == t["votes"][nm],
                  f"ep {ep}: {nm} reads {v} votes, expected {t['votes'][nm]}")
        check(owner[nm] in note,
              f"ep {ep}: {nm} credited to '{note}', expected {owner[nm]}")
        booted = nm == max(t["votes"], key=t["votes"].get)
        check(bool(boot) == booted,
              f"ep {ep}: {nm} boot styling is {bool(boot)}, expected {booted}")
        check(("voted out" in note) == booted,
              f"ep {ep}: {nm} note says voted out = {'voted out' in note}, "
              f"expected {booted}")

    check(listed == t["votes"],
          f"ep {ep} card tally {listed} does not match {t['votes']}")

    # names must be ordered most votes first within the card
    vals = [int(v) for *_, v in lis]
    check(vals == sorted(vals, reverse=True),
          f"ep {ep} card is not ordered most votes first: {vals}")

# --- 5. the by-castaway table, row by row --------------------------------
tbl = section("<h2>Votes received, by castaway</h2>", "<h2>Three things")
trs = re.findall(r"<tr><td(?: class=\"struck\")?>(.*?)</td>"
                 r"<td class=\"num\">(\d+)</td>"
                 r"<td><span class=\"owner\">(.*?)</span></td>"
                 r"<td><span class=\"owner\">(.*?)</span></td>"
                 r"<td><span class=\"chip (in|out)\">", tbl, re.S)
check(len(trs) == len(received),
      f"table has {len(trs)} rows, {len(received)} castaways took votes")

table_votes = {}
for nm, v, eps, own, status in trs:
    nm = norm(nm)
    table_votes[nm] = int(v)
    check(nm in received, f"table row {nm} never took a vote")
    if nm not in received:
        continue
    check(int(v) == received[nm],
          f"{nm} reads {v} votes, expected {received[nm]}")
    check(norm(own) == owner[nm],
          f"{nm} credited to {norm(own)}, expected {owner[nm]}")
    want_status = "out" if nm in out_names else "in"
    check(status == want_status,
          f"{nm} status chip is '{status}', expected '{want_status}'")
    want_eps = [t["ep"] for t in vh.TRIBALS if nm in t["votes"]]
    for e in want_eps:
        check(f"ep {e}" in norm(eps),
              f"{nm} tribals read '{norm(eps)}', missing ep {e}")
    check(len(re.findall(r"ep \d", norm(eps))) == len(want_eps),
          f"{nm} tribals read '{norm(eps)}', expected {len(want_eps)} entries")

check(table_votes == received,
      f"table totals {table_votes} do not match {received}")
check(f"Seven of the 21" in norm(tbl),
      f"section note should say Seven of the 21 (computed {len(received)})")
check(len(received) == 7,
      f"page says seven took votes; the data says {len(received)}")

# --- 6. the three claims in prose must be the real superlatives ----------
story = norm(section('<div class="story">', "<h2>Where these came from</h2>"))

survivors = {n: v for n, v in received.items() if n not in out_names}
most_survived = max(survivors, key=survivors.get)
check(most_survived in story,
      f"prose should name {most_survived} as having survived the most votes")
check(f"{survivors[most_survived]} of the eleven" in story
      or f"Five of the eleven" in story,
      "prose should state how many votes the survivor absorbed")

multi = [n for n in received
         if len([t for t in vh.TRIBALS if n in t["votes"]]) > 1]
check(len(multi) == 1, f"expected one twice-voted castaway, got {multi}")
check(multi and multi[0] in story,
      f"prose should name {multi} as the only castaway voted against twice")
check("only castaway" in story.lower() or "only" in story.lower(),
      "prose should state the twice-voted claim as a uniqueness claim")

# --- 7. pronoun gate ------------------------------------------------------
# No castaway's or drafter's pronouns are stated anywhere in our sources, and
# this page is read by other people. Daron is she/her; everyone else is
# they/them. Rewriting around the pronoun is cleaner than they/them, so the
# page carries none at all and this gate keeps it that way.
body_text = norm(re.sub(r"<[^>]+>", " ", section("<body>")))
banned = re.findall(
    r"\b(he|him|his|himself|she|her|hers|herself|man|woman|men|women)\b",
    body_text, re.I)
check(not banned,
      f"page uses gendered pronouns for people whose pronouns are not "
      f"stated: {sorted(set(w.lower() for w in banned))}")

# --- 8. footer links must all resolve to files that exist ----------------
foot = section("<footer>", "</footer>")
for href in re.findall(r'href="(/[^"]*)"', foot):
    if href == "/":
        continue
    check((ROOT / "public" / href.lstrip("/")).exists(),
          f"footer links {href}, which does not exist in public/")

# --- report ---------------------------------------------------------------
if failures:
    print(f"FAIL  {len(failures)} problem(s) in public/votes.html\n")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print(f"PASS  {len(rows)} drafter rows, {len(cards)} tribal cards, "
      f"{len(trs)} castaway rows, {total} votes reconciled, "
      f"no gendered pronouns")
