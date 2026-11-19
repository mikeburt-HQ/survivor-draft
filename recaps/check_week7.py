"""Verify public/week7.html against week7_map.py. Fails loudly on any mismatch.

Covers the recap's own content. The vote ledger at the bottom of the page is
checked separately by `check_votes.py --page week7.html --through 7`; both must
pass before the page ships.

Lessons carried from earlier checkers (each produced a FALSE result once):
anchor on element TAGS, never a bare attribute; parse the RAW page and
unescape only what is compared; straighten typographic quotes before any name
comparison; a missing section marker is a named failure, never a raise; and a
blanket WORD ban is the worst available gate, so omissions are scanned only
inside the sections that could state them.

Every comparison the prose makes ("the most votes in a single night", "past
Will", "split down the middle") is RECOMPUTED here from the model, not just
the numbers inside it.
"""

import html
import importlib.util
import io
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "public" / "week7.html"
THROUGH = 7          # this page is a frozen snapshot through episode 7


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


w7 = load("week7_map")
vh = load("vote_history")

page = PAGE.read_text(encoding="utf-8")
fail = []
QUOTES = {"“": '"', "”": '"', "‘": "'", "’": "'"}


def norm(s):
    s = html.unescape(s)
    for bad, good in QUOTES.items():
        s = s.replace(bad, good)
    return re.sub(r"\s+", " ", s).strip()


def strip_tags(chunk):
    return norm(re.sub(r"<[^>]+>", " ", chunk))


def check(cond, msg):
    if not cond:
        fail.append(msg)


def section(start, end=None):
    if start not in page:
        check(False, f"page is missing the section marker {start!r}")
        return ""
    i = page.index(start)
    if end is not None and end not in page:
        check(False, f"page is missing the section marker {end!r}")
        return page[i:]
    j = page.index(end, i) if end else len(page)
    return page[i:j]


CHIP = "tovuto"
GLYPH = "T"
owner = w7.owner
out = w7.out
TRIBALS = [t for t in vh.TRIBALS if t["ep"] <= THROUGH]
received = {}
for t in TRIBALS:
    for n, v in t["votes"].items():
        received[n] = received.get(n, 0) + v
votes_by_drafter = {d: 0 for d in w7.DRAFT}
for n, v in received.items():
    votes_by_drafter[owner[n]] += v
ballots = sum(vh.ballots_of(t) for t in TRIBALS)

# --- 1. who owns whom: 21 rows, chip + owner + struck state ---------------
board = section(">Who owns whom<", ">Vote ledger<")
rows = re.findall(
    r"<tr><td(?P<cls>[^>]*)>(?P<name>[^<]+)</td>"
    r"<td><span class=\"chip (?P<chip>\w+)\">[^<]*</span></td>"
    r"<td><span class=\"owner\">(?P<owner>[^<]*)</span></td></tr>", board)
check(len(rows) == 21, f"board table has {len(rows)} rows, expected 21")
seen = set()
for cls, raw_name, chip, raw_owner in rows:
    name, own = norm(raw_name), norm(raw_owner)
    seen.add(name)
    if name not in owner:
        check(False, f"board row names unknown castaway {name!r}")
        continue
    if name in out:
        ep, how = w7.GONE[name]
        check(chip == "none", f"{name} is out but chip is {chip!r}")
        check("struck" in cls, f"{name} is out but not struck through")
        check(owner[name] in own and f"ep {ep}" in own
              and ("quit" if how == "quit" else "out") in own.lower(),
              f"{name} owner cell reads {own!r}")
    else:
        check(chip == CHIP, f"{name} chip is {chip!r}, expected {CHIP!r}")
        check("struck" not in cls, f"{name} is alive but struck through")
        want = owner[name]
        check(own == want or (want == "undrafted" and "undrafted" in own.lower()),
              f"{name} owner cell {own!r}, expected {want!r}")
check(not (set(w7.everyone) - seen),
      f"castaways absent from the board: {sorted(set(w7.everyone) - seen)}")

# --- 2. standings rows ----------------------------------------------------
standings = section(">Standings<", ">The merged tribe<")
for who in w7.DRAFT:
    m = re.search(
        r"<div class=\"row r-" + who.lower() + r"\">(.*?)"
        r"<div class=\"count\">(\d+)<small>left</small></div>\s*"
        r"<div class=\"count vcount\">(\d+)<small>votes</small>",
        standings, re.S)
    check(m is not None, f"no standings row for {who}")
    if not m:
        continue
    body, count, vcount = m.group(1), int(m.group(2)), int(m.group(3))
    pips = re.findall(r"<span class=\"pip (\w+)\" title=\"([^\"]*)\">(.*?)</span>", body)
    check(len(pips) == 5, f"{who} has {len(pips)} pips, expected 5")
    check(count == w7.left[who], f"{who} count {count}, expected {w7.left[who]}")
    check(vcount == votes_by_drafter[who],
          f"{who} votes {vcount}, expected {votes_by_drafter[who]}")
    for kind, raw_title, glyph in pips:
        nm = norm(raw_title).split("—")[0].strip()
        if nm not in owner:
            check(False, f"{who} pip titles unknown castaway {nm!r}")
            continue
        check(owner[nm] == who, f"{who}'s row shows {nm} ({owner[nm]}'s)")
        if kind == "gone":
            ep, how = w7.GONE.get(nm, (None, None))
            check(nm in out, f"{who}: {nm} shown gone but still in")
            check(norm(glyph) == ("Q" if how == "quit" else "×"),
                  f"{who}: {nm} glyph {norm(glyph)!r}")
            check(f"episode {ep}" in norm(raw_title),
                  f"{who}: {nm} title does not name episode {ep}")
        else:
            check(nm not in out, f"{who}: {nm} shown on a tribe but is out")
            check(kind == CHIP and norm(glyph) == GLYPH and "Tovuto" in norm(raw_title),
                  f"{who}: {nm} pip reads {kind}/{norm(glyph)}/{norm(raw_title)}")
order = re.findall(r"<div class=\"row r-(\w+)\">", standings)
counts = [w7.left[w.capitalize()] for w in order]
check(counts == sorted(counts, reverse=True),
      f"standings not most-left-first: {list(zip(order, counts))}")

# --- 3. the one merged-tribe card ----------------------------------------
cards = section(">The merged tribe<", "<div class=\"story\">")
found = re.findall(r"<div class=\"tcard (\w+)\">(.*?)</ul>", cards, re.S)
check(len(found) == 1, f"found {len(found)} tribe cards, expected the 1 merged tribe")
alive_sorted = sorted(w7.alive)
for short, body in found:
    check(short == CHIP, f"merged card is styled {short!r}")
    names = [norm(x) for x in re.findall(r"<li>([^<]+)<span>", body)]
    owns = [norm(x) for x in re.findall(r"<span>([^<]+)</span>", body)]
    check(sorted(names) == alive_sorted,
          f"merged card roster\n   got  {sorted(names)}\n   want {alive_sorted}")
    for nm, ow in zip(names, owns):
        if nm in owner:
            want = owner[nm]
            check(want in ow or (want == "undrafted" and "undrafted" in ow.lower()),
                  f"card credits {nm} to {ow!r}, expected {want!r}")
    meta = norm(re.search(r"<p class=\"n\">(.*?)</p>", body, re.S).group(1))
    check(f"· {len(w7.alive)} ·" in meta, f"card count should read {len(w7.alive)}: {meta}")
    check(w7.IMMUNE[0] in meta and "immun" in meta.lower(),
          f"card should name {w7.IMMUNE[0]} as immune: {meta}")
    check("Blue" in meta, f"card should name the buff colour: {meta}")

# --- 4. hardware ----------------------------------------------------------
hardware = section(">Hardware watch<", "class=\"gone-box\"")
hw = re.findall(r"<tr><td>([^<]+)</td><td><span class=\"chip (\w+)\">", hardware)
holders = [norm(h) for h, _ in hw]
check(sorted(holders) == sorted(w7.ADVANTAGES),
      f"hardware holders\n   got  {sorted(holders)}\n   want {sorted(w7.ADVANTAGES)}")
for _, chip in hw:
    check(chip == CHIP, f"a hardware chip reads {chip!r}")
for nm in w7.SPENT:
    check(nm not in holders, f"{nm} spent an advantage but is still listed")
    check(nm in norm(hardware), f"{nm}'s spent advantage should be noted")
tether_row = re.search(r"<tr><td>Sharonda Cox</td>.*?</tr>", hardware, re.S)
check(tether_row is not None and w7.TETHERED_FROM in norm(tether_row.group(0))
      and "Tethered" in norm(tether_row.group(0)),
      "the Tethered Idol row must say it came from Kristin Flickinger")
# The handover's NEW terms are omitted on purpose (no two outlets agree).
check(not re.search(r"complete control|could play (it|herself)|only (Sharonda|Kristin) may",
                    strip_tags(page), re.I),
      "page states new Tethered Idol terms that the sources do not agree on")
# Ballot arithmetic is the page's evidence that no extra vote or Shot was
# played, so it must actually hold.
t7 = next(t for t in TRIBALS if t["ep"] == 7)
check(vh.ballots_of(t7) == t7["_attending"] and not t7["no_vote"]
      and not t7.get("extra_votes"),
      "page says thirteen people cast thirteen ballots; the model disagrees")

# --- 5. gone box ----------------------------------------------------------
gone = section("class=\"gone-box\"", ">Who owns whom<")
boxes = re.findall(r"<div class=\"nm\">([^<]+)</div>\s*<p>(.*?)</p>", gone, re.S)
boots = sorted(n for n, (ep, _) in w7.GONE.items() if ep == THROUGH)
check(sorted(norm(b[0]) for b in boxes) == boots,
      f"gone boxes name {[norm(b[0]) for b in boxes]}, expected {boots}")
pick_of = {n: p for ps in w7.DRAFT.values() for p, n in ps}
ORD = ["zeroth", "first", "second", "third", "fourth", "fifth", "sixth",
       "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth"]
for raw, body in boxes:
    nm, txt = norm(raw), norm(body)
    check(f"{pick_of[nm]}th" in txt or f"{pick_of[nm]}" in txt,
          f"{nm} box should give pick {pick_of[nm]}")
    check(owner[nm] in txt, f"{nm} box should name {owner[nm]}")
    check(f"{ORD[w7.place[nm]]} castaway voted out" in txt.lower(),
          f"{nm} was the {ORD[w7.place[nm]]} voted out: {txt[:120]}")
    check(f"{ORD[len(out)]} to leave" in txt.lower(),
          f"{nm} was the {ORD[len(out)]} to leave: {txt[:120]}")
    check("first member of the jury" in txt.lower(),
          f"{nm} box should say first juror (as of episode 7)")
    check(f"{t7['votes'][nm]} of {vh.ballots_of(t7)}".replace("9 of 13", "nine of thirteen")
          in txt.lower() or f"{t7['votes'][nm]} of {vh.ballots_of(t7)}" in txt,
          f"{nm} box should give the tally, nine of thirteen")

# --- 6. headline and story claims, each recomputed -----------------------
story = strip_tags(section("<div class=\"story\">", ">Hardware watch<"))
header = strip_tags(section("<header>", "</header>"))

imm = w7.IMMUNE[0]
check(owner[imm] == "Mike" and imm.split()[0] == "Mike",
      f"the headline needs the immune castaway to be Mike's and named Mike: {imm}")
check(imm in header, "the standfirst should name the immunity winner")
check(len({owner[n] for n in w7.FINAL_THREE}) == 3,
      f"page claims the final three were three drafters' castaways: "
      f"{[(n, owner[n]) for n in w7.FINAL_THREE]}")
for n in w7.FINAL_THREE:
    check(n in story, f"the immunity paragraph should name {n}")
# Finishing order as written: Kristin stepped off, THEN Lewis.
check(story.find("Kristin stepped off") < story.find("then Lewis dropped") != -1,
      "the page orders the finish Kristin then Lewis")
check(w7.FINAL_THREE[1:] == ["Lewis Kelly", "Kristin Flickinger"],
      "the model's finishing order no longer matches the page's")

mike_alive = [n for _, n in w7.DRAFT["Mike"] if n not in out]
check(len(mike_alive) == 4 and 3 * len(mike_alive) == len(w7.alive),
      f"page claims Mike has four of twelve, a third: {len(mike_alive)} of {len(w7.alive)}")
mike_losses = sorted(w7.GONE[n][0] for _, n in w7.DRAFT["Mike"] if n in out)
check(mike_losses == [5], f"page claims Mike has lost nobody since ep 5: {mike_losses}")

# Nine is a season high for one castaway at one tribal; the old high was six.
singles = sorted(((v, t["ep"], n) for t in TRIBALS for n, v in t["votes"].items()),
                 reverse=True)
check(singles[0][2] == "Brady Booker" and singles[0][0] == 9,
      f"page claims Brady's nine is the season high: {singles[:2]}")
prior = max(v for v, ep, _ in singles if ep < THROUGH)
check(prior == 6 and singles[1][0] < 9,
      f"page claims the previous high was six and nine stands alone: {singles[:3]}")
check("9–4" in story or "9-4" in story, "the story should state the 9-4 tally")

V = w7.EP7_VOTERS
by_owner = {}
for voter, target in V.items():
    by_owner.setdefault(owner[voter], {}).setdefault(target, []).append(voter)
check(set(by_owner["Cagney"]) == {"Brady Booker"} and len(by_owner["Cagney"]["Brady Booker"]) == 3,
      f"page claims all three of Cagney's wrote Brady: {by_owner['Cagney']}")
check("Eric Macksoud" in by_owner["Cagney"]["Brady Booker"],
      "page claims Eric wrote Brady")
mike_split = {tg: sorted(vs) for tg, vs in by_owner["Mike"].items()}
check(mike_split == {"Brady Booker": ["Maggie Nestor", "Mike Pinsky"],
                     "Eric Macksoud": ["Carter Krull", "Thien An Nguyen"]},
      f"page claims Mike's four split two and two as named: {mike_split}")
daron_split = {tg: sorted(vs) for tg, vs in by_owner["Daron"].items()}
check(daron_split == {"Eric Macksoud": ["Brady Booker", "Lewis Kelly"],
                      "Brady Booker": ['Angelica "Jelly" Loblack']},
      f"page claims Brady and Lewis wrote Eric, Jelly wrote Brady: {daron_split}")
check(set(by_owner["Will"]) == {"Brady Booker"} and len(by_owner["Will"]["Brady Booker"]) == 2,
      f"page claims both of Will's wrote Brady: {by_owner['Will']}")
check(by_owner["undrafted"] == {"Brady Booker": ["Cristian Chavez"]},
      "page claims Cristian wrote Brady")

missed_owners = sorted(owner[n] for n in w7.MISSED_FEAST)
check(missed_owners == ["Cagney", "Will", "undrafted"],
      f"page claims the three who missed the feast were Cagney's, Will's and "
      f"the undrafted one: {missed_owners}")
at_merge_md = [n for n in w7.at_merge if owner[n] in ("Mike", "Daron")]
check(not set(at_merge_md) & set(w7.MISSED_FEAST),
      "page claims every Mike and Daron castaway at the merge ate")
for n in w7.MISSED_FEAST:
    check(n in story, f"the feast paragraph should name {n}")

check(votes_by_drafter["Daron"] == 25 and ballots == 61
      and votes_by_drafter["Daron"] > votes_by_drafter["Will"] == 19,
      f"page claims Daron 25 of 61, past Will's 19: {votes_by_drafter}, {ballots}")
prev = {d: 0 for d in w7.DRAFT}
for t in TRIBALS:
    if t["ep"] < THROUGH:
        for n, v in t["votes"].items():
            prev[owner[n]] += v
check(max(prev, key=prev.get) == "Will",
      f"page says Daron took over the top spot FROM Will: before ep 7 {prev}")
daron_hit = [n for _, n in w7.DRAFT["Daron"] if received.get(n)]
daron_clean = [n for _, n in w7.DRAFT["Daron"] if not received.get(n)]
check(len(daron_hit) == 4 and daron_clean == ['Angelica "Jelly" Loblack'],
      f"page claims four of Daron's five written down, only Jelly never: {daron_clean}")

drafted_out = len([n for n in out if owner[n] != "undrafted"])
check(drafted_out == 9 and "Cristian Chavez" in w7.alive,
      f"page claims Cristian has outlasted nine drafted castaways: {drafted_out}")
check("Cristian Chavez" in w7.EP7_VOTERS
      and w7.EP7_VOTERS["Cristian Chavez"] == w7.EP7_TRIBAL["out"],
      "page claims Cristian voted with the majority")

# --- 7. the ledger's own prose claims ------------------------------------
ledger_story = strip_tags(section("<h2 id=\"votes\">", "<footer>"))
surv = {n: v for n, v in received.items() if n not in out}
check(max(surv, key=surv.get) == "Eric Macksoud" and surv["Eric Macksoud"] == 8
      and sorted(surv.values())[-2] == 5 and surv.get("Danny Kilby") == 5,
      f"page claims Eric's eight passes Kilby's five: {surv}")
multi = sorted(n for n in received if sum(n in t["votes"] for t in TRIBALS) > 1)
check(multi == ["Alexis Levine", "Eric Macksoud", "Jenna Doore"],
      f"page claims Eric is the third twice-voted castaway: {multi}")
check([n for n in multi if n not in out] == ["Eric Macksoud"],
      "page claims Eric is the only twice-voted castaway still in")
mike_votes = {n: v for n, v in received.items() if owner[n] == "Mike"}
check(mike_votes == {"Linnea Capobianco": 4},
      f"page claims Mike's four votes all landed on Linnea: {mike_votes}")
clean = [n for n in w7.everyone if not received.get(n)]
check(len(clean) == 10 and {"Sharonda Cox", "Cristian Chavez"} <= set(clean)
      and set(mike_alive) <= set(clean),
      f"kicker claims ten clean incl. Sharonda, Cristian and Mike's four: {clean}")
prior_eps = [t["ep"] for t in TRIBALS if "Brady Booker" in t["votes"]]
check(prior_eps == [7], f"kicker claims Brady was first written down in ep 7: {prior_eps}")
check(len(received) == 11, f"kicker claims Brady is the eleventh written down: {len(received)}")

# --- 8. unaired material and omissions -----------------------------------
flat = strip_tags(page)
for banned in (r"\bepisode 8\b", r"\bthumb\b", r"withdr[ae]w", r"double duo",
               r"\bspaghetti\b", r"tree ?mail", r"\bsalt\b"):
    check(not re.search(banned, flat, re.I),
          f"page refers to unaired material: {banned}")
# The DK reading-order figure must not appear as a TALLY in the story.
check(not re.search(r"\b4\s*[–-]\s*4\b", story),
      "the story states a 4-4 figure for episode 7; the tally was 9-4")

# --- 9. no gendered pronouns anywhere ------------------------------------
slips = re.findall(r"\b(he|him|his|himself|she|her|hers|herself|man|woman|men|women)\b",
                   strip_tags(section("<body>")), re.I)
check(not slips, f"page uses gendered pronouns: {sorted(set(s.lower() for s in slips))}")

if fail:
    print(f"FAIL ({len(fail)})")
    for f in fail:
        print(f" - {f}")
    sys.exit(1)
print(f"PASS  {len(rows)} board rows, {len(w7.DRAFT)} standings rows, "
      f"{len(found)} merged card, {len(holders)} advantages, {len(boxes)} gone box, "
      f"{len(w7.alive)} alive, vote-split and superlative claims recomputed, "
      f"no unaired material, no stray pronouns")
