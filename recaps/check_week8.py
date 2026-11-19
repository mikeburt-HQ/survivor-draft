"""Verify public/week8.html against week8_map.py. Fails loudly on any mismatch.

Covers the recap's own content. The vote ledger at the bottom of the page is
checked separately by `check_votes.py --page week8.html --through 8`; both must
pass before the page ships.

Lessons carried from earlier checkers (each produced a FALSE result once):
anchor on element TAGS, never a bare attribute; parse the RAW page and
unescape only what is compared; straighten typographic quotes before any name
comparison; a missing section marker is a named failure, never a raise; and a
blanket WORD ban is the worst available gate, so omissions are scanned only
inside the sections that could state them.

Every comparison the prose makes ("the only ballot that counted", "half of
the eight", "the fewest votes of anyone voted out", "three share the record")
is RECOMPUTED here from the model, not just the numbers inside it.
"""

import html
import importlib.util
import io
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "public" / "week8.html"
THROUGH = 8          # this page is a frozen snapshot through episode 8


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


w8 = load("week8_map")
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
owner = w8.owner
out = w8.out
TRIBALS = [t for t in vh.TRIBALS if t["ep"] <= THROUGH]
received = {}
for t in TRIBALS:
    for n, v in t["votes"].items():
        received[n] = received.get(n, 0) + v
votes_by_drafter = {d: 0 for d in w8.DRAFT}
votes_by_drafter["undrafted"] = 0     # Cristian took a first vote in ep 8
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
        ep, how = w8.GONE[name]
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
check(not (set(w8.everyone) - seen),
      f"castaways absent from the board: {sorted(set(w8.everyone) - seen)}")

# --- 2. standings rows ----------------------------------------------------
standings = section(">Standings<", ">The merged tribe<")
for who in w8.DRAFT:
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
    check(count == w8.left[who], f"{who} count {count}, expected {w8.left[who]}")
    check(vcount == votes_by_drafter[who],
          f"{who} votes {vcount}, expected {votes_by_drafter[who]}")
    for kind, raw_title, glyph in pips:
        nm = norm(raw_title).split("—")[0].strip()
        if nm not in owner:
            check(False, f"{who} pip titles unknown castaway {nm!r}")
            continue
        check(owner[nm] == who, f"{who}'s row shows {nm} ({owner[nm]}'s)")
        if kind == "gone":
            ep, how = w8.GONE.get(nm, (None, None))
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
counts = [w8.left[w.capitalize()] for w in order]
check(counts == sorted(counts, reverse=True),
      f"standings not most-left-first: {list(zip(order, counts))}")

# --- 3. the one merged-tribe card ----------------------------------------
cards = section(">The merged tribe<", "<div class=\"story\">")
found = re.findall(r"<div class=\"tcard (\w+)\">(.*?)</ul>", cards, re.S)
check(len(found) == 1, f"found {len(found)} tribe cards, expected the 1 merged tribe")
alive_sorted = sorted(w8.alive)
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
    check(f"· {len(w8.alive)} ·" in meta, f"card count should read {len(w8.alive)}: {meta}")
    check(all(n in meta for n in w8.IMMUNE_PAIR) and "immun" in meta.lower(),
          f"card should name {w8.IMMUNE_PAIR} as immune: {meta}")
    check("Blue" in meta, f"card should name the buff colour: {meta}")


# --- 4. hardware ----------------------------------------------------------
hardware = section(">Hardware watch<", "class=\"gone-pair\"")
hw = re.findall(r"<tr><td>([^<]+)</td><td><span class=\"chip (\w+)\">", hardware)
holders = [norm(h) for h, _ in hw]
check(sorted(holders) == sorted(w8.ADVANTAGES),
      f"hardware holders\n   got  {sorted(holders)}\n   want {sorted(w8.ADVANTAGES)}")
for _, chip in hw:
    check(chip == CHIP, f"a hardware chip reads {chip!r}")
hw_txt = norm(hardware)
for nm in w8.SPENT_THIS_WEEK:
    check(nm not in holders, f"{nm} spent an advantage this week but is still listed")
    short = nm.split('"')[1] if '"' in nm else nm.split()[0]
    check(short in hw_txt and "Spent this week" in hw_txt,
          f"{nm}'s spent advantage should be noted under the table")
tether = re.search(r"<tr><td>Sharonda Cox</td>.*?</tr>", hardware, re.S)
check(tether is not None and "not mentioned this week" in norm(tether.group(0)),
      "the Tethered Idol row must say this week's sources do not mention it")
check(not re.search(r"tethered idol[^.]{0,80}\b(is|was) (now )?(void|gone|dead|"
                    r"worthless|an ordinary|a normal|untethered)", strip_tags(page), re.I),
      "page declares the Tethered Idol's status, which no source reports")
# "ten ballots from ten voters" is the page's evidence Devin's extra vote is
# unplayed, so the model must agree.
t8 = next(t for t in TRIBALS if t["ep"] == 8)
check(vh.ballots_of(t8) == t8["_attending"] - len(t8["no_vote"]) and not t8.get("extra_votes"),
      "page says no extra vote was played; the ballot arithmetic disagrees")

# --- 5. two gone boxes ----------------------------------------------------
gone = section("class=\"gone-pair\"", ">Who owns whom<")
boxes = re.findall(r"<div class=\"nm\">([^<]+)</div>\s*<p>(.*?)</p>", gone, re.S)
boots = sorted(n for n, (ep, _) in w8.GONE.items() if ep == THROUGH)
check(sorted(norm(b[0]) for b in boxes) == boots,
      f"gone boxes name {[norm(b[0]) for b in boxes]}, expected {boots}")
pick_of = {n: p for ps in w8.DRAFT.values() for p, n in ps}
ORD = ["zeroth", "first", "second", "third", "fourth", "fifth", "sixth",
       "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth"]
places = sorted(w8.place[n] for n in boots)
for raw, body in boxes:
    nm, txt = norm(raw), norm(body)
    other = next(b for b in boots if b != nm)
    sfx = {1: "st", 2: "nd", 3: "rd"}.get(pick_of[nm], "th")
    check(f"drafted {pick_of[nm]}{sfx} by {owner[nm]}" in txt,
          f"{nm} box should read 'drafted {pick_of[nm]}{sfx} by {owner[nm]}': {txt[:90]}")
    # The two left on ONE ballot, so neither may be given its own ordinal.
    check(f"{ORD[places[0]]} and {ORD[places[1]]} castaways voted out" in txt,
          f"{nm} box should give the shared ordinals {places}: {txt[:160]}")
    check(f"{ORD[len(out) - 1]} and {ORD[len(out)]} to leave" in txt,
          f"{nm} box should say {ORD[len(out) - 1]} and {ORD[len(out)]} to leave")
    check(other.split()[-1] in txt or other.split()[0] in txt,
          f"{nm} box should name the partner {other}")
    check("jury" in txt.lower(), f"{nm} box should say {nm} is on the jury")
    check(nm in w8.JURY, f"{nm} is not on the model's jury")
    check(not re.search(rf"\b{ORD[w8.place[nm]]} (castaway )?voted out\b", txt.replace(
        f"{ORD[places[0]]} and {ORD[places[1]]}", "")),
          f"{nm} box assigns an individual ordinal; the pair left on one ballot")

# --- 6. headline and story claims, each recomputed -----------------------
story = strip_tags(section("<div class=\"story\">", ">Hardware watch<"))
header = strip_tags(section("<header>", "</header>"))
V = w8.EP8_VOTERS
counted_by = [v for v, p in V.items() if w8.counted[p] > 0]
check(counted_by == ["Devin Way"],
      f"page claims Devin cast the only counted ballot: {counted_by}")
check(owner["Devin Way"] == "Cagney" == owner["Kristin Flickinger"],
      "headline needs Devin and Kristin both to be Cagney's")
check(owner["Danny Kilby"] == "Will" and pick_of["Danny Kilby"] == 2
      and min(p for p, _ in w8.DRAFT["Will"]) == 2,
      "page calls Kilby Will's very first pick")
check(pick_of["Devin Way"] == 19 and pick_of["Kristin Flickinger"] == 14,
      "page gives Devin as Cagney's 19th and Kristin as 14th")
check("Devin" in header and "Kristin" in header and "Cagney" in header,
      "the standfirst should carry the Devin-Kristin-Cagney headline")
check(sum(w8.negated.values()) == 9 and sum(w8.cast.values()) == 10
      and sum(w8.counted.values()) == 1,
      f"page claims ten cast, nine cancelled, one counted: {w8.cast} {w8.negated}")
check(w8.cast[w8.DJ] == 8 and w8.negated[w8.DJ] == 8,
      "page claims eight against Devin & Jelly, all cancelled")
check([v for v, p in V.items() if p == w8.CC] == ['Angelica "Jelly" Loblack'],
      "page claims Jelly's own ballot went against Carter & Cristian")
check(len(w8.before) == 12 and len(w8.SHOTS) == 2,
      "page claims twelve at Tribal and two forfeits")
check("1–0–0" in strip_tags(page) or "1-0-0" in strip_tags(page),
      "the tribal card should state the 1-0-0 result")

same = {v: [n for n in p if owner[n] == owner[v]] for v, p in V.items()}
own_goals = sorted(v for v, s in same.items() if s)
check(own_goals == ["Devin Way", "Eric Macksoud", "Lewis Kelly"],
      f"page names Devin, Eric and Lewis as writing down a teammate: {own_goals}")
check(same["Eric Macksoud"] == ["Devin Way"]
      and same["Lewis Kelly"] == ['Angelica "Jelly" Loblack'],
      "page says Eric wrote Devin and Lewis wrote Jelly")
mike_voters = [v for v in V if owner[v] == "Mike"]
check(len(mike_voters) == 4 and all(V[v] == w8.DJ for v in mike_voters),
      f"page claims all four of Mike's voted Devin & Jelly: {mike_voters}")
check(2 * len(mike_voters) == w8.negated[w8.DJ],
      "page claims Mike's four are half of the eight the idol cancelled")

pair_owners = {p: tuple(owner[n] for n in p) for p in w8.PAIRS}
single = [p for p, o in pair_owners.items() if o[0] == o[1]]
check(single == [("Maggie Nestor", "Mike Pinsky")] and pair_owners[single[0]][0] == "Mike",
      f"page claims Maggie & Mike were the only one-drafter pair, Mike's: {single}")
mike_pairs = [p for p, o in pair_owners.items() if "Mike" in o]
check(len(mike_pairs) == 3, f"page claims Mike is in three of six pairs: {len(mike_pairs)}")

# Bind each counted claim to the TEXT, with the number word derived from the
# model -- a model-side check alone passes while the sentence says "four".
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve"]
for phrase in (f"in {WORDS[len(mike_pairs)]} of the {WORDS[len(w8.PAIRS)]} pairs",
               f"half of the {WORDS[w8.negated[w8.DJ]]}",
               f"{WORDS[sum(len(t['no_vote']) for t in TRIBALS)].capitalize()} Shots in the Dark",
               f"outlasted {WORDS[len([n for n in out if owner[n] != 'undrafted'])]} drafted",
               f"{WORDS[len(w8.before)].capitalize()} people went to Tribal Council and "
               f"{WORDS[sum(w8.cast.values())]} ballots"):
    check(phrase in story, f"the story should say {phrase!r} (derived from the model)")
pairs_box = section("class=\"pairs\"", "</ul>")
listed = re.findall(r"<li>(.*?)<span>(.*?)</span></li>", pairs_box, re.S)
check(len(listed) == 6, f"the pairs callout lists {len(listed)}, expected 6")
for raw_names, raw_owners in listed:
    members = tuple(x.strip() for x in norm(raw_names).split(" & "))
    match = next((p for p in w8.PAIRS if sorted(p) == sorted(members)), None)
    check(match is not None, f"pairs callout lists {members}, not a real pair")
    if match:
        want = sorted(owner[n] for n in match)
        got = sorted(x.strip() for x in norm(raw_owners).split(" & "))
        check(got == want, f"pair {members} credited to {got}, expected {want}")
check(w8.FIRST_OUT_OF_CHALLENGE == [w8.KK, ("Maggie Nestor", "Mike Pinsky")],
      "page names Kilby & Kristin and Maggie & Mike as the first two pairs out")
check(w8.REWARD_GUESTS == ['Angelica "Jelly" Loblack', "Kristin Flickinger"],
      "page says the reward guests were Jelly and Kristin")

shots_all = sum(len(t["no_vote"]) for t in TRIBALS)
check(shots_all == 5, f"page claims five Shots in the Dark this season: {shots_all}")
safe = [n for n, r in w8.SHOTS.items() if r == "Safe"]
check(safe == ["Cristian Chavez"],
      f"page claims Cristian's is the only Safe Shot ever: {safe}")

check(w8.left == {"Mike": 4, "Cagney": 2, "Daron": 2, "Will": 1},
      f"standings changed: {w8.left}")
will_alive = [n for _, n in w8.DRAFT["Will"] if n not in out]
check(will_alive == ["Sharonda Cox"] and not received.get("Sharonda Cox"),
      "page claims Sharonda is Will's last and has never been written down")
check("Sharonda Cox" in w8.IMMUNE_PAIR, "page says Sharonda held immunity")
kilby_by_ep = {t["ep"]: t["votes"]["Danny Kilby"] for t in TRIBALS if "Danny Kilby" in t["votes"]}
check(kilby_by_ep == {3: 5, 8: 1}, f"page says Kilby survived five then left on one: {kilby_by_ep}")
check(w8.LEFT_JURY == ["Brady Booker"] and sorted(owner[n] for n in w8.JURY) == ["Cagney", "Will"],
      "page says Brady left the jury and the jury is one of Will's and one of Cagney's")
drafted_out = len([n for n in out if owner[n] != "undrafted"])
check(drafted_out == 11 and "Cristian Chavez" in w8.alive,
      f"page claims Cristian has outlasted eleven drafted castaways: {drafted_out}")
cr = [t["ep"] for t in TRIBALS if "Cristian Chavez" in t["votes"]]
check(cr == [8] and "Cristian Chavez" in w8.CC,
      f"page calls Cristian's ep-8 vote a first-ever, cancelled: {cr}")
check(w8.STAGE_ONE_WINNERS == w8.CC and w8.JOURNEY == "Cristian Chavez",
      "page says Cristian won stage one with Carter and went on the journey")

# --- 7. the ledger's own prose claims ------------------------------------
surv = {n: v for n, v in received.items() if n not in out}
top = max(surv.values())
check(sorted(n for n, v in surv.items() if v == top)
      == ['Angelica "Jelly" Loblack', "Devin Way", "Eric Macksoud"] and top == 8,
      f"page says three share the record at eight: {surv}")
# The claim is about the NIGHT each boot left, not season totals: Kilby's
# season total is six (a first draft compared totals and was wrong).
night_of = {}
for t in TRIBALS:
    for n in vh.outs_of(t):
        night_of[n] = t["votes"][n]
low = min(night_of.values())
check(low == 1 and sorted(n for n, v in night_of.items() if v == low)
      == ["Danny Kilby", "Kristin Flickinger"],
      f"page says Kilby and Kristin went out on the fewest votes: {night_of}")
prev_low = min(v for n, v in night_of.items() if w8.GONE[n][0] < THROUGH)
check(prev_low == 2 and night_of["Ori Jean-Charles"] == 2
      and sum(1 for n, v in night_of.items() if v == 2) == 1,
      f"page says the previous boot-night low was Ori's two: {night_of}")
check(received["Danny Kilby"] == 6 and kilby_by_ep[3] == 5,
      "page says Kilby has been written down six times, five in episode 3")
check("on the night they left" in strip_tags(page),
      "the fewest-votes claim must be scoped to the night they left")
multi = sorted(n for n in received if sum(n in t["votes"] for t in TRIBALS) > 1)
check(multi == ["Alexis Levine", "Danny Kilby", "Eric Macksoud", "Jenna Doore"],
      f"page says Kilby is the fourth twice-voted castaway: {multi}")
clean = sorted(n for n in w8.everyone if not received.get(n))
check(clean == ["Maggie Nestor", "Mike Pinsky", "Rob Antonson", "Sharonda Cox",
                "Thien An Nguyen"],
      f"kicker names five never written down: {clean}")
check([t["ep"] for t in TRIBALS if "Carter Krull" in t["votes"]] == [8],
      "kicker says Carter's first vote came this week")

# --- 8. unaired material and omissions -----------------------------------
flat = strip_tags(page)
for banned in (r"\bepisode 9\b", r"tropical storm", r"\bcoin\b", r"11th voted out",
               r"eleventh (castaway )?voted out", r"\bday 1[6-9]\b"):
    check(not re.search(banned, flat, re.I), f"page refers to unaired material: {banned}")
# Contested details must not be asserted. Scan the story only; the kicker
# legitimately names the competing readings in order to set them aside.
for banned, why in (
        (r"\b(Cristian|Carter) (gave|handed|passed) (the |an |that |his |their )?extra vote",
         "who handed over the extra vote"),
        (r"\bsalt\b", "the alliance's disputed name"),
        (r"(Sharonda|Lewis) (chose|picked) (Jelly|Kristin)", "who picked which guest"),
        (r"juror (number )?(one|two|#?1|#?2)\b|\b(first|second) juror\b", "jury order")):
    check(not re.search(banned, story, re.I), f"the story asserts {why}")
kick = strip_tags(section(">What is left out, and why<", "<footer>"))
for must in ("extra vote", "reward guest", "alliance", "juror", "Tethered Idol"):
    check(must.lower() in kick.lower(), f"the left-out note should explain the {must} omission")

# --- 9. no gendered pronouns anywhere ------------------------------------
slips = re.findall(r"\b(he|him|his|himself|she|her|hers|herself|man|woman|men|women)\b",
                   strip_tags(section("<body>")), re.I)
check(not slips, f"page uses gendered pronouns: {sorted(set(s.lower() for s in slips))}")

if fail:
    print(f"FAIL ({len(fail)})")
    for f in fail:
        print(f" - {f}")
    sys.exit(1)
print(f"PASS  {len(rows)} board rows, {len(w8.DRAFT)} standings rows, "
      f"{len(found)} merged card, {len(holders)} advantages, {len(boxes)} gone boxes, "
      f"{len(listed)} pairs, {len(w8.alive)} alive, pair-vote and superlative "
      f"claims recomputed, omissions held, no unaired material, no stray pronouns")
