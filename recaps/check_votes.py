"""Verify a recap page's vote ledger SECTION against vote_history.py.

Each weekly recap carries the ledger as it stood AFTER that episode, so the
page and the cutoff go together:

    py -X utf8 recaps/check_votes.py                        # week5, through ep 5
    py -X utf8 recaps/check_votes.py --page week4.html --through 4

Both must pass before either page ships. week4.html is a frozen snapshot: its
ledger stops at episode 4 and must keep reconciling against the first four
tribals even as later episodes are added to the model.

Everything is scoped to the slice between the "Vote ledger" heading and the
footer, and every number is asserted AT ITS POSITION -- inside its own drafter
row, its own tribal card, its own table row -- never by appearing somewhere in
the document. A value present in the wrong place is the defect this is for.

Traps this file is written around, each of which has produced a false result
on an earlier checker in this repo:

  * Parse the RAW page. Unescaping the whole document first turns a &quot;
    inside a title attribute into a real quote and breaks the attribute parse.
  * html.unescape() alone is not enough to compare text: &ldquo; yields a
    CURLY quote while the data holds a straight one. norm() straightens them.
  * Anchor on element TAGS, never a bare attribute -- a bare attribute matches
    the CSS block first and runs to the wrong element.
  * Find the drafter rows by SPLITTING, not matching: a row holds nested divs
    and a non-greedy "...</div></div>" closes early, silently cutting off the
    count element.
  * Claims whose shape depends on the data (a drafter on zero votes, a single
    twice-voted castaway) are checked in BRANCHES, and the branch that ran is
    printed -- a conditional check that quietly matches nothing is a check that
    cannot fail.
"""

import argparse
import contextlib
import html
import importlib.util
import io
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

ap = argparse.ArgumentParser(allow_abbrev=False)
ap.add_argument("--page", default="week5.html")
ap.add_argument("--through", type=int, default=5,
                help="highest episode the page's ledger covers")
args = ap.parse_args()

PAGE = ROOT / "public" / args.page

spec = importlib.util.spec_from_file_location(
    "vote_history", pathlib.Path(__file__).resolve().parent / "vote_history.py")
vh = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(vh)

TRIBALS = [t for t in vh.TRIBALS if t["ep"] <= args.through]
assert TRIBALS, f"no tribals at or before episode {args.through}"

page = PAGE.read_text(encoding="utf8")

CURLY = {"“": '"', "”": '"', "‘": "'", "’": "'",
         "‑": "-", "–": "-", "—": "--", " ": " "}
NUMWORD = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
           6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
           11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
           16: "sixteen", 17: "seventeen", 21: "twenty-one",
           34: "thirty-four", 45: "forty-five", 46: "forty-six"}


def norm(s):
    """Compare-ready: unescape, straighten curly punctuation, collapse space."""
    s = html.unescape(s)
    for bad, good in CURLY.items():
        s = s.replace(bad, good)
    return re.sub(r"\s+", " ", s).strip()


def strip_tags(chunk):
    return norm(re.sub(r"<[^>]+>", " ", chunk))


def says(text, n, unit):
    """True if text states n before unit, as either a digit or a word."""
    t = text.lower()
    return (f"{n} {unit.lower()}" in t
            or f"{NUMWORD.get(n, n)} {unit.lower()}" in t)


failures = []
branches = []


def check(ok, msg):
    if not ok:
        failures.append(msg)


# --- scope to the ledger slice -------------------------------------------
START = '<h2 id="votes">Vote ledger</h2>'
check(page.count(START) == 1, "page should carry exactly one vote ledger heading")
if START not in page:
    print(f"FAIL  the vote ledger section is missing from public/{args.page}")
    sys.exit(1)

ledger = page[page.index(START):page.index("<footer>")]


def section(start, end=None):
    i = ledger.index(start)
    j = ledger.index(end, i) if end else len(ledger)
    return ledger[i:j]


# --- rebuild the expected figures from the module -------------------------
received = {}
for t in TRIBALS:
    for n, v in t["votes"].items():
        received[n] = received.get(n, 0) + v

owner = {n: d for d, picks in vh.DRAFT.items() for n in picks}
attributed = sum(received.values())
unattributed = sum(t.get("unattributed", 0) for t in TRIBALS)
total = attributed + unattributed

by_drafter = {d: 0 for d in vh.DRAFT}
for n, v in received.items():
    by_drafter[owner[n]] += v
assert sum(by_drafter.values()) + unattributed == total

out_names = {t.get("out") or max(t["votes"], key=t["votes"].get)
             for t in TRIBALS}
top = max(list(by_drafter.values()) + [unattributed])
zero = [d for d, v in by_drafter.items() if v == 0]
clean_total = len([n for n in owner if not received.get(n)]) + len(vh.UNDRAFTED)

# --- 1. the section note carries the real totals --------------------------
note = strip_tags(section(START, '<div class="standings">'))
check(says(note, total, "ballots") or says(note, total, "votes"),
      f"ledger note should name {total} ballots; reads: {note[:120]}")
check(says(note, len(TRIBALS), "Tribal Councils"),
      f"ledger note should name {len(TRIBALS)} Tribal Councils")

worst = max(by_drafter, key=by_drafter.get)
check(worst in note,
      f"ledger note should name {worst}, who has taken the most votes")

# --- 2. one drafter row each, with count, share and bar width -------------
stand = section('<div class="standings">', '<div class="kicker">')
rows = []
for chunk in stand.split('<div class="row vrow r-')[1:]:
    rows.append((re.match(r'([\w-]+)">', chunk).group(1), chunk))

expect_rows = dict(by_drafter)
if unattributed:
    expect_rows["unattributed"] = unattributed
check(len(rows) == len(expect_rows),
      f"expected {len(expect_rows)} ledger rows, found {len(rows)}")

seen = {}
for who, body in rows:
    name = "unattributed" if who == "unattributed" else who.capitalize()
    seen[name] = True
    check(name in expect_rows, f"ledger row '{name}' is not a known row")
    if name not in expect_rows:
        continue
    expected = expect_rows[name]

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

check(set(seen) == set(expect_rows),
      f"rows cover {sorted(seen)}, expected {sorted(expect_rows)}")
order = [expect_rows.get("unattributed" if w == "unattributed"
                         else w.capitalize(), -1) for w, _ in rows]
check(order == sorted(order, reverse=True),
      f"ledger rows are not ordered most-voted first: {order}")

# --- 3. the kicker's claims, by branch -----------------------------------
kick = strip_tags(section('<div class="kicker">', '<div class="tribals">'))
check(says(kick, clean_total, "of the 21"),
      f"kicker should say {NUMWORD[clean_total]} of the 21; reads: {kick[:110]}")

if zero:
    branches.append(f"clean-sheet ({zero})")
    check(len(zero) == 1, f"expected at most one drafter on zero, got {zero}")
    for n in vh.DRAFT[zero[0]]:
        check(n in kick, f"kicker should name {n} among the never-voted-against")
    check(says(kick, len(vh.DRAFT[zero[0]]), "of those"),
          f"kicker should tie {len(vh.DRAFT[zero[0]])} of those to the roster")
else:
    branches.append("no-clean-sheet")
    # Every drafter has now been voted against, so the page must not leave a
    # clean-sheet claim standing from a previous week.
    for d in vh.DRAFT:
        check(not re.search(rf"\b{d}\b[^.]*\b(not once|never)\b", kick, re.I),
              f"kicker still claims {d} has never been voted against")
    check(re.search(r"\ball four\b|\bevery drafter\b", kick, re.I) is not None,
          "with no drafter on zero, the kicker should say all four are on the "
          f"board; reads: {kick[:110]}")

# --- 4. a tribal card per council, with its own tally --------------------
cards = re.findall(
    r'<div class="tc (savu|toka|dina)">(.*?)</div>\s*(?=<div class="tc |</div>)',
    section('<div class="tribals">'), re.S)
check(len(cards) == len(TRIBALS),
      f"expected {len(TRIBALS)} tribal cards, found {len(cards)}")

for (chip, body), t in zip(cards, TRIBALS):
    ep, tribe = t["ep"], t["tribe"]
    where = f"ep {ep} {tribe}"
    check(chip == tribe.lower(),
          f"{where} card is styled {chip}, expected {tribe.lower()}")
    check(f"<h3>Episode {ep}</h3>" in norm(body),
          f"{where} card is mislabelled")

    ballots = sum(t["votes"].values()) + t.get("unattributed", 0)
    meta = norm(re.search(r'<p class="n">(.*?)</p>', body, re.S).group(1))
    check(tribe in meta, f"{where} meta should name {tribe}: {meta}")
    check(t["_label"] in meta,
          f"{where} meta reads '{meta}', expected '{t['_label']}'")
    check(f"{t['_attending']} at tribal" in meta,
          f"{where} meta reads '{meta}', expected {t['_attending']} at tribal")
    check(f"{ballots} ballots" in meta or f"{ballots} votes" in meta,
          f"{where} meta reads '{meta}', expected {ballots} ballots")
    if t.get("extra_votes"):
        check(says(meta, t["extra_votes"], "extra"),
              f"{where} meta should disclose {t['extra_votes']} extra votes")

    lis = re.findall(r'<li( class="boot")?><span class="nm">(.*?)<span>'
                     r'(.*?)</span></span><span class="v">(\d+)</span>', body, re.S)
    want_lines = len(t["votes"]) + (1 if t.get("unattributed") else 0)
    check(len(lis) == want_lines,
          f"{where} card lists {len(lis)} lines, expected {want_lines}")

    booted = t.get("out") or max(t["votes"], key=t["votes"].get)
    listed = {}
    for boot, nm, note_txt, v in lis:
        nm, note_txt = norm(nm), norm(note_txt)
        if nm.lower().startswith("unattributed") or "unattributed" in nm.lower():
            check(int(v) == t.get("unattributed", 0),
                  f"{where}: unattributed line reads {v}, "
                  f"expected {t.get('unattributed', 0)}")
            check(not boot, f"{where}: the unattributed line is styled as a boot")
            continue
        listed[nm] = int(v)
        check(nm in t["votes"], f"{where} card lists {nm}, who took no votes")
        if nm in t["votes"]:
            check(int(v) == t["votes"][nm],
                  f"{where}: {nm} reads {v} votes, expected {t['votes'][nm]}")
        check(owner[nm] in note_txt,
              f"{where}: {nm} credited to '{note_txt}', expected {owner[nm]}")
        check(bool(boot) == (nm == booted),
              f"{where}: {nm} boot styling is {bool(boot)}, "
              f"expected {nm == booted}")
        check(("voted out" in note_txt) == (nm == booted),
              f"{where}: {nm} note says voted out = "
              f"{'voted out' in note_txt}, expected {nm == booted}")

    check(listed == t["votes"],
          f"{where} card tally {listed} does not match {t['votes']}")
    vals = [v for v in listed.values()]
    check(vals == sorted(vals, reverse=True),
          f"{where} card is not ordered most votes first: {vals}")

    # A tie must be disclosed, or the card implies the vote decided it.
    if t.get("tie"):
        check(re.search(r"\btie\b|\btied\b", strip_tags(body), re.I) is not None,
              f"{where} ended in a tie and the card must say so")

# --- 5. the by-castaway table, row by row --------------------------------
tbl = section('<div class="tbl-scroll">', '<div class="story">')
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
    want_eps = [t["ep"] for t in TRIBALS if nm in t["votes"]]
    for e in want_eps:
        check(f"ep {e}" in norm(eps),
              f"{nm} tribals read '{norm(eps)}', missing ep {e}")
    check(len(re.findall(r"ep \d", norm(eps))) == len(want_eps),
          f"{nm} tribals read '{norm(eps)}', expected {len(want_eps)} entries")

check(table_votes == received,
      f"table totals {table_votes} do not match {received}")

TABLE_NOTE = '<p class="sec-note" style="margin-top:22px">'
check(ledger.count(TABLE_NOTE) == 1,
      "the castaway table should be introduced by exactly one note")
intro = strip_tags(section(TABLE_NOTE, '<div class="tbl-scroll">'))
check(says(intro, len(received), "of the 21"),
      f"the table note should say {NUMWORD[len(received)]} of the 21; "
      f"reads: {intro[:100]}")

# --- 6. the prose claims must be the real superlatives -------------------
check(ledger.count('<div class="story">') == 1,
      "the ledger should carry exactly one prose block")
story = strip_tags(section('<div class="story">', '<div class="kicker">'))

survivors = {n: v for n, v in received.items() if n not in out_names}
most_survived = max(survivors, key=survivors.get)
check(most_survived in story,
      f"prose should name {most_survived} as having survived the most votes")

multi = [n for n in received
         if len([t for t in TRIBALS if n in t["votes"]]) > 1]
if len(multi) == 1:
    branches.append("one-twice-voted")
    check(multi[0] in story,
          f"prose should name {multi[0]} as the only castaway voted twice")
    check("only castaway" in story.lower(),
          "prose should state the twice-voted claim as a uniqueness claim")
else:
    branches.append(f"several-twice-voted ({len(multi)})")
    for n in multi:
        check(n in story, f"prose should name {n} among the twice-voted")
    check("only castaway" not in story.lower(),
          f"{len(multi)} castaways have now been voted against twice "
          f"({multi}); the page must not call one of them the only")

# --- 7. pronoun gate over the ledger's own prose -------------------------
banned = re.findall(
    r"\b(he|him|his|himself|she|her|hers|herself|man|woman|men|women)\b",
    strip_tags(ledger), re.I)
check(not banned,
      f"ledger uses gendered pronouns for people whose pronouns are not "
      f"stated: {sorted(set(w.lower() for w in banned))}")

# --- report ---------------------------------------------------------------
if failures:
    print(f"FAIL  {len(failures)} problem(s) in {args.page}'s vote ledger "
          f"(through ep {args.through})\n")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print(f"PASS  {args.page} ledger through ep {args.through}: {len(rows)} rows, "
      f"{len(cards)} tribal cards, {len(trs)} castaway rows, "
      f"{total} ballots reconciled ({attributed} attributed, "
      f"{unattributed} not), branches: {', '.join(branches)}, "
      f"no gendered pronouns")
