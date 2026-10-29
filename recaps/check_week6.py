"""Verify public/week6.html against week6_map.py. Fails loudly on any mismatch.

Covers the recap's own content. The vote ledger at the bottom of the page is
checked separately by `check_votes.py --page week6.html --through 6`; both must
pass before the page ships.

Lessons baked in from earlier checkers in this repo, each of which has produced
a FALSE FAILURE here before:

1. Regexes anchor on ELEMENT TAGS, never a bare attribute - a bare attribute
   match hits the CSS block first.
2. Parse the RAW page, and html.unescape() only the strings you COMPARE.
3. unescape() is not enough: `&ldquo;Jelly&rdquo;` becomes CURLY quotes while
   the database spelling uses STRAIGHT ones. Normalise typographic quotes
   before any name comparison.
4. A MISSING section marker is reported as a named failure, never raised.

And the big one, from the baby-whale episode: a BLANKET WORD BAN is the worst
available gate. Banning "whale" let a wrong description live for two weeks and
would have failed the correct one. So the whale is guarded STRUCTURALLY below,
and so is the word "unanimous" - week 5's checker banned it outright, which
week 6 legitimately needs in order to explain why 2-0 and unanimous are the
SAME tally. The gate now demands the explanation, rather than the silence.
"""

import html
import importlib.util
import io
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "public" / "week6.html"
THROUGH = 6          # this page is a frozen snapshot through episode 6


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


w6 = load("week6_map")
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
alive_tribe = {n: t for t, roster in w6.TRIBES.items()
               for n in roster if n not in w6.out}

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
    check(name in w6.owner, f"board row names unknown castaway {name!r}")
    if name not in w6.owner:
        continue
    want_owner = w6.owner[name]
    if name in w6.out:
        ep = w6.GONE[name][0]
        check(chip == "none", f"{name} is out but chip is {chip!r}, expected none")
        check("struck" in cls, f"{name} is out but the row is not struck through")
        check(want_owner.lower() in owner_txt.lower(),
              f"{name} owner cell {owner_txt!r} does not name {want_owner}")
        check(f"ep {ep}" in owner_txt,
              f"{name} left in ep {ep}; cell reads {owner_txt!r}")
        how = w6.GONE[name][1]
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

missing = sorted(set(w6.everyone) - seen)
check(not missing, f"castaways absent from the board table: {missing}")

# --- 2. standings rows: pips, tribe letters, owner, left count, votes ------
# Votes are counted ONLY through this page's episode, so a later episode
# cannot make this frozen page read as wrong.
received = {}
for t in vh.TRIBALS:
    if t["ep"] <= THROUGH:
        for n, v in t["votes"].items():
            received[n] = received.get(n, 0) + v
votes_by_drafter = {d: 0 for d in w6.DRAFT}
for n, v in received.items():
    votes_by_drafter[w6.owner[n]] += v

standings = section(">Standings<", ">The three tribes<")
for who in w6.DRAFT:
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

    want_alive = [n for _, n in w6.DRAFT[who] if n not in w6.out]
    live_pips = [p for p in pips if p[0] != "gone"]
    check(len(live_pips) == len(want_alive),
          f"{who}: {len(live_pips)} live pips vs {len(want_alive)} live picks")
    check(count == len(want_alive),
          f"{who} count reads {count}, expected {len(want_alive)}")
    check(vcount == votes_by_drafter[who],
          f"{who} votes-taken reads {vcount}, expected {votes_by_drafter[who]}")

    for kind, raw_title, raw_glyph in pips:
        nm = norm(raw_title).split("—")[0].strip()
        check(nm in w6.owner, f"{who} pip titles unknown castaway {nm!r}")
        if nm not in w6.owner:
            continue
        check(w6.owner[nm] == who,
              f"{who}'s row shows {nm}, who belongs to {w6.owner[nm]}")
        if kind == "gone":
            check(nm in w6.out, f"{who}: {nm} shown as gone but is still in")
            how = w6.GONE[nm][1]
            want_glyph = "Q" if how == "quit" else "×"
            check(norm(raw_glyph) == want_glyph,
                  f"{who}: {nm} {how} but the pip glyph is "
                  f"{norm(raw_glyph)!r}, expected {want_glyph!r}")
            check(f"episode {w6.GONE[nm][0]}" in norm(raw_title),
                  f"{who}: {nm} pip title does not name episode "
                  f"{w6.GONE[nm][0]}")
        else:
            check(nm not in w6.out, f"{who}: {nm} shown on a tribe but is out")
            want_chip = SHORT[alive_tribe[nm]]
            check(kind == want_chip,
                  f"{who}: {nm} pip is {kind!r}, expected {want_chip!r}")
            check(norm(raw_glyph) == LETTER[kind],
                  f"{who}: {nm} pip glyph {norm(raw_glyph)!r} does not match {kind}")
            check(alive_tribe[nm].split(" ")[0] in norm(raw_title),
                  f"{who}: {nm} pip title does not name {alive_tribe[nm]}")

# rows must run most-castaways-first, or the page argues with itself
row_order = [w for w in re.findall(r"<div class=\"row r-(\w+)\">", standings)]
counts_in_order = [len([n for _, n in w6.DRAFT[w.capitalize()]
                        if n not in w6.out]) for w in row_order]
check(counts_in_order == sorted(counts_in_order, reverse=True),
      f"standings rows are not ordered most-left-first: "
      f"{list(zip(row_order, counts_in_order))}")

# --- 3. tribe cards: each roster is exactly that tribe's survivors ---------
cards = section(">The three tribes<", "<div class=\"story\">")
found_cards = re.findall(r"<div class=\"tcard (\w+)\">(.*?)</ul>", cards, re.S)
check(len(found_cards) == 3, f"found {len(found_cards)} tribe cards, expected 3")
for short, body in found_cards:
    tribe_name = next(t for t, s in SHORT.items() if s == short)
    want = sorted(n for n in w6.TRIBES[tribe_name] if n not in w6.out)
    got = sorted(norm(m) for m in re.findall(r"<li>([^<]+)<span>", body))
    check(got == want, f"{tribe_name} card roster\n   got  {got}\n   want {want}")

    names = [norm(m) for m in re.findall(r"<li>([^<]+)<span>", body)]
    owners = [norm(m) for m in re.findall(r"<span>([^<]+)</span>", body)]
    for nm, ow in zip(names, owners):
        if nm in w6.owner:
            want_ow = w6.owner[nm]
            check(want_ow in ow or (want_ow == "undrafted"
                                    and "undrafted" in ow.lower()),
                  f"{tribe_name} card: {nm} credited to {ow!r}, "
                  f"expected {want_ow!r}")

    n = re.search(r"·\s*(\d+)\s*·", norm(body))
    check(n is not None and int(n.group(1)) == len(want),
          f"{tribe_name} card count should read {len(want)}")

# Savu went to Tribal and lost Ori; the other two won immunity. The cards say
# so, and WENT_TO_TRIBAL is the source of truth for which.
for short, body in found_cards:
    tribe_name = next(t for t, s in SHORT.items() if s == short)
    sub = norm(body).lower()
    went = any(tribe_name.startswith(x) for x in w6.WENT_TO_TRIBAL[THROUGH])
    if went:
        check("lost" in sub,
              f"{tribe_name} went to Tribal in ep {THROUGH}; card reads {sub[:80]!r}")
    else:
        check("immunity" in sub,
              f"{tribe_name} won immunity in ep {THROUGH}; card reads {sub[:80]!r}")

# --- 4. hardware table == the advantages still in play ---------------------
hardware = section(">Hardware watch<", "class=\"gone-box\"")
hw = re.findall(
    r"<tr><td>([^<]+)</td><td><span class=\"chip (\w+)\">", hardware)
holders = [norm(h) for h, _ in hw]
check(sorted(holders) == sorted(w6.ADVANTAGES),
      f"hardware holders\n   got  {sorted(holders)}\n"
      f"   want {sorted(w6.ADVANTAGES)}")
for raw_h, chip in hw:
    nm = norm(raw_h)
    if nm in alive_tribe:
        check(chip == SHORT[alive_tribe[nm]],
              f"hardware: {nm} chip {chip!r}, "
              f"expected {SHORT[alive_tribe[nm]]!r}")
# An advantage spent in an EARLIER episode must not be listed as in play.
for nm in w6.SPENT:
    check(nm not in holders,
          f"{nm} spent their advantage already but is still in the "
          f"hardware table")
    check(nm in norm(hardware),
          f"{nm}'s spent advantage should be noted under the table")

# --- 5. one gone box for the episode-6 boot, with pick number and drafter --
gone = section("class=\"gone-box\"", ">Who owns whom<")
boxes = re.findall(r"<div class=\"nm\">([^<]+)</div>\s*<p>(.*?)</p>",
                   gone, re.S)
ep_boots = sorted(n for n, (ep, _) in w6.GONE.items() if ep == THROUGH)
check(sorted(norm(b[0]) for b in boxes) == ep_boots,
      f"gone boxes name {sorted(norm(b[0]) for b in boxes)}, expected {ep_boots}")

pick_of = {n: p for picks in w6.DRAFT.values() for p, n in picks}
place = {n: i + 1 for i, n in enumerate(
    [m for m, (ep, how) in sorted(w6.GONE.items(), key=lambda kv: (kv[1][0], kv[0]))
     if how == "voted out"])}
ORD = {1: "first", 2: "second", 3: "third", 4: "fourth", 5: "fifth",
       6: "sixth", 7: "seventh", 8: "eighth", 9: "ninth", 10: "tenth"}
for raw_nm, body in boxes:
    nm, txt = norm(raw_nm), norm(body)
    if nm not in w6.owner:
        continue
    check(f"{pick_of[nm]}" in txt,
          f"{nm} box should give the pick number {pick_of[nm]}; reads: {txt[:90]}")
    check(w6.owner[nm] in txt, f"{nm} box should name {w6.owner[nm]}")
    check(ORD[place[nm]] in txt.lower(),
          f"{nm} was the {ORD[place[nm]]} voted out; box reads: {txt[:110]}")
    # Ori was the 7th voted out but the 8th to LEAVE, because Rob quit. Both
    # numbers are on the page, so both are gated.
    check(ORD[len(w6.out)] in txt.lower(),
          f"{nm} was the {ORD[len(w6.out)]} to leave; box reads: {txt[:110]}")

# --- 6. omissions actually stayed omitted ---------------------------------
flat = norm(page)
OMISSIONS = [
    (r"revote[^.]{0,40}4\s*[-–]\s*4",
     "a 4-4 revote tally, which cannot happen with four voters"),
    (r"\bfinal five\b(?![^.]{0,200}corroborat)",
     "the Tethered Idol's final-five deadline, which is single-source"),
]
for banned, why in OMISSIONS:
    check(not re.search(banned, flat, re.I), f"page mentions {why}")

# Placement between Toka and Dina is unresolved, so the page must not rank
# them. Two passages legitimately use placement words and are cut out first:
# the hardware note (about episode 4's SECOND-PLACE whale token) and the
# omissions kicker (which names the competing readings in order to reject
# them). A blanket ban over the whole page fails both -- the baby-whale
# lesson, in a new costume.
placement_scan = flat
for cut_start, cut_end in ((">Hardware watch<", "class=\"gone-box\""),
                           (">What is left out, and why<", "<footer>")):
    if cut_start in page and cut_end in page:
        placement_scan = placement_scan.replace(
            norm(section(cut_start, cut_end)), " ")
check(placement_scan != flat, "the placement scan cut nothing; markers moved")
BANNED_PLACEMENT = r"\b(first|second) place\b|\b(placed|finished|came in) (first|second)\b"
hit = re.search(BANNED_PLACEMENT, placement_scan, re.I)
check(hit is None,
      f"page ranks the two immune tribes, but three sources disagree on the "
      f"order: {hit.group(0) if hit else ''!r}")
# And the disclaimer must actually be there, or the silence is just an omission
# nobody told the reader about.
check(re.search(r"whether toka or dina finished first is not reported",
                flat, re.I),
      "the page must SAY the placement is unresolved, not merely omit it")

# "unanimous" is NOT banned this week - the page needs it to reconcile the
# 2-0 tally with the sources' wording. But every use must sit beside the
# explanation, or it becomes the bare wrong claim week 5 was guarding against.
RECONCILE = ("forfeit", "shot in the dark", "2–0", "2-0", "same result",
             "same tally")
for m in re.finditer(r"\bunanimous", flat, re.I):
    window = flat[max(0, m.start() - 450):m.end() + 450].lower()
    check(any(w in window for w in RECONCILE),
          f"'unanimous' appears with no reconciliation nearby; a bare "
          f"unanimous claim was wrong twice this season. Context: "
          f"...{flat[max(0, m.start() - 90):m.end() + 90]}...")

# The baby whale was SECOND PLACE'S IMMUNITY TOKEN in episode 4: Toka's for
# one night, spent when Toka skipped the vote. Two wrong descriptions shipped
# (see week4_map.py), so these guard the STRUCTURE, never a word.
check("<div class=\"tbl-scroll\">" in hardware,
      "the hardware section should contain a holders table")
if "<div class=\"tbl-scroll\">" in hardware:
    cut = hardware.index("<div class=\"tbl-scroll\">")
    hw_note, hw_table = norm(hardware[:cut]), norm(hardware[cut:])
    check("whale" in hw_note.lower(),
          "the hardware note should account for the baby-whale idol")
    check("whale" not in hw_table.lower(),
          "the baby whale is in the holders table; it was a spent tribe "
          "token and was never held by anyone")
    check("second place" in hw_note.lower(),
          "the note must tie the whale to SECOND PLACE, or it reads as a "
          "hidden idol again")
    NOT_KEPT = ("nobody kept", "covered one", "one night", "spent")
    check(any(w in hw_note.lower() for w in NOT_KEPT),
          f"the note must say the whale was not retained; expected one of "
          f"{NOT_KEPT} in: {hw_note[:150]}")

# Model-level guard: no advantage may ever BE the whale.
for src, label in ((w6.ADVANTAGES, "ADVANTAGES"), (w6.SPENT, "SPENT")):
    check(not any("whale" in str(v).lower() for v in src.values()),
          f"an entry in {label} describes the whale, which was never held")

# Nothing from an unaired episode.
for banned in [r"\bepisode 7\b", r"\bweek seven recap\b"]:
    check(not re.search(banned, flat, re.I),
          f"page refers to unaired material: {banned}")

# --- 7. the Tethered Idol, checked structurally against the model ---------
tether = section("class=\"tether\"", "</div>")
tether_txt = norm(tether)
check(w6.TETHERED_HOLDER in tether_txt,
      f"the tether callout must name the holder {w6.TETHERED_HOLDER}")
for n in w6.TETHERED_ON:
    check(n in tether_txt,
          f"the tether callout must name {n} as a permitted beneficiary")
rules = re.findall(r"<li>(.*?)</li>", tether, re.S)
check(len(rules) == 4,
      f"the tether callout lists {len(rules)} rules, expected the 4 that every "
      f"source agrees on")
# The gone beneficiary must be struck through, and the live one must not be.
for n in w6.tethered_dead:
    hit = re.search(r"<span class=\"dead\">" + re.escape(n) + r"</span>", tether)
    check(hit is not None,
          f"{n} is out, so the tether callout should strike that name through")
for n in w6.tethered_live:
    check(not re.search(r"<span class=\"dead\">" + re.escape(n) + r"</span>",
                        tether),
          f"{n} is still in, so that name must NOT be struck through")
# It has NOT untethered, so the page must not say it is a normal idol now.
check(not re.search(r"(is|has) now (an?|become) (ordinary|normal|regular|full)",
                    flat, re.I),
      "the idol has not untethered: one beneficiary is still in the game")

# --- 8. headline claims must be derivable from the data -------------------
# Both beneficiaries belong to ONE rival drafter. That IS the headline.
ben_owners = sorted({w6.owner[n] for n in w6.TETHERED_ON})
check(ben_owners == ["Will"],
      f"the headline needs both tethered beneficiaries to be Will's; "
      f"actual {ben_owners}")
check(w6.owner[w6.TETHERED_HOLDER] == "Cagney",
      f"the headline needs the holder to be Cagney's; actual "
      f"{w6.owner[w6.TETHERED_HOLDER]}")
check(w6.tethered_live == ["Sharonda Cox"],
      f"the page claims only Sharonda is left to spend it on; actual "
      f"{w6.tethered_live}")

left = {w: len([n for _, n in picks if n not in w6.out])
        for w, picks in w6.DRAFT.items()}
check(left == {"Mike": 4, "Cagney": 3, "Daron": 3, "Will": 2},
      f"standings changed: {left}")

savu_alive = sorted(n for n in w6.TRIBES["Savu (Purple)"] if n not in w6.out)
savu_owners = sorted(w6.owner[n] for n in savu_alive)
check(savu_owners == ["Cagney", "Daron"],
      f"page claims Savu's last two are Cagney's and Daron's; "
      f"actual {savu_owners}")
check(len(savu_alive) == 2, f"page claims Savu is two people; got {savu_alive}")

mike_toka = sum(1 for n in w6.TRIBES["Toka (Yellow)"]
                if n not in w6.out and w6.owner[n] == "Mike")
toka_live = len([n for n in w6.TRIBES["Toka (Yellow)"] if n not in w6.out])
check(mike_toka == 4 and toka_live == 6,
      f"page claims Mike holds four of Toka's six; actual {mike_toka} of {toka_live}")

# Toka last voted in episode 3 - the page says so explicitly.
toka_tribals = [e for e, ts in w6.WENT_TO_TRIBAL.items() if "Toka" in ts]
check(max(toka_tribals) == 3,
      f"page claims Toka has not voted since episode 3; actual {toka_tribals}")

# Mike's only loss is Linnea, and Mike has nobody on Dina where it happened.
mike_losses = [n for _, n in w6.DRAFT["Mike"] if n in w6.out]
check(mike_losses == ["Linnea Capobianco"],
      f"page claims Linnea is Mike's only loss; actual {mike_losses}")
mike_dina = [n for n in w6.TRIBES["Dina (Red)"]
             if n not in w6.out and w6.owner[n] == "Mike"]
check(mike_dina == [],
      f"page claims Mike has nobody on Dina; actual {mike_dina}")

# Will: four of five written down, only Sharonda never.
will_clean = [n for _, n in w6.DRAFT["Will"] if not received.get(n)]
check(will_clean == ["Sharonda Cox"],
      f"page claims only Sharonda of Will's five has never been written down; "
      f"actual {will_clean}")
check(votes_by_drafter["Will"] == 19,
      f"page claims Will carries 19 votes; actual {votes_by_drafter['Will']}")
other = votes_by_drafter["Cagney"] + votes_by_drafter["Mike"]
check(votes_by_drafter["Will"] > other,
      f"page claims Will carries more than Cagney and Mike put together "
      f"({votes_by_drafter['Will']} vs {other})")
ratio = votes_by_drafter["Will"] / votes_by_drafter["Mike"]
check(4.5 <= ratio < 5.0,
      f"page claims Will's total is nearly five times Mike's; actual "
      f"ratio {ratio:.2f}")

check(len(w6.alive) == 13, f"page claims thirteen left; actual {len(w6.alive)}")
check(len(w6.out) == 8, f"page claims eight are out; actual {len(w6.out)}")
check(len(w6.ADVANTAGES) == 4,
      f"page claims four known advantages; actual {len(w6.ADVANTAGES)}")
check(w6.owner["Cristian Chavez"] == "undrafted"
      and "Cristian Chavez" in w6.TRIBES["Dina (Red)"]
      and "Cristian Chavez" not in w6.out,
      "page claims undrafted Cristian is still in, on Dina")

# Three Shots in the Dark, all Not Safe: eps 1 (two) and 6 (one).
shots = sum(len(t["no_vote"]) for t in vh.TRIBALS if t["ep"] <= THROUGH)
check(shots == 3,
      f"page claims three Shots in the Dark have been played; model says {shots}")

# Two superlatives the page states about Ori's 2-0, both derived here rather
# than trusted: the highest SHARE of a night's ballots any boot has taken, and
# the FEWEST votes of anyone ever written down.
shares = []
for t in vh.TRIBALS:
    if t["ep"] > THROUGH:
        continue
    ballots = sum(t["votes"].values()) + t.get("unattributed", 0)
    booted = t.get("out") or max(t["votes"], key=t["votes"].get)
    shares.append((t["votes"][booted] / ballots, t["ep"], booted))
best = max(shares)
check(best[2] == "Ori Jean-Charles" and best[0] == 1.0,
      f"page claims Ori took the highest share of a night's ballots; "
      f"actual leader {best}")
fewest = min(received.values())
check(received["Ori Jean-Charles"] == fewest
      and sum(1 for v in received.values() if v == fewest) == 1,
      f"page claims Ori has the fewest votes of anyone written down; "
      f"actual minimum {fewest}, Ori has {received['Ori Jean-Charles']}")

# Danny Kilby still survived the most votes of anyone still in.
survived = sorted(((v, n) for n, v in received.items() if n not in w6.out),
                  reverse=True)
check(survived and survived[0][1] == "Danny Kilby",
      f"page claims Kilby has survived the most votes; actual {survived[:2]}")

story = section("<div class=\"story\">", ">Hardware watch<")
for nm in ["Kristin Flickinger", "Sharonda Cox", "Ori Jean-Charles",
           "Devin Way", "Danny Kilby", "Cristian Chavez"]:
    check(nm in norm(story), f"the story section should name {nm}")

# --- 9. no gendered pronouns anywhere ------------------------------------
# Daron is she/her; every other drafter and every castaway is they/them,
# because nobody else's pronouns have been stated to us. This page talks
# about no drafter in the third person singular, so the correct count of
# gendered pronouns is ZERO. Published recaps use she/her for Kristin;
# third-party press is not a statement of pronouns.
def strip_tags(chunk):
    return norm(re.sub(r"<[^>]+>", " ", chunk))


prose = strip_tags(section("<body>"))
slips = re.findall(
    r"\b(he|him|his|himself|she|her|hers|herself|man|woman|men|women)\b",
    prose, re.I)
check(not slips,
      f"page uses gendered pronouns for people whose pronouns are not "
      f"stated: {sorted(set(w.lower() for w in slips))}")

# --- report ----------------------------------------------------------------
if fail:
    print(f"FAIL ({len(fail)})")
    for f in fail:
        print(f" - {f}")
    sys.exit(1)

print(f"PASS  {len(rows)} board rows, {len(w6.DRAFT)} standings rows, "
      f"{len(found_cards)} tribe cards, {len(holders)} advantages, "
      f"{len(boxes)} gone box, {len(rules)} tether rules, "
      f"{len(w6.alive)} alive, {len(OMISSIONS)} omissions held, "
      f"no stray pronouns")
