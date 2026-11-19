"""Verify public/week9.html against week9_map.py. Fails loudly on any mismatch.

Covers the recap's own content. The vote ledger at the bottom of the page is
checked separately by `check_votes.py --page week9.html --through 9`; both must
pass before the page ships.

Lessons carried from earlier checkers (each produced a FALSE result once):
anchor on element TAGS, never a bare attribute; parse the RAW page and
unescape only what is compared; straighten typographic quotes before any name
comparison; a missing section marker is a named failure, never a raise; and a
blanket WORD ban is the worst available gate, so omissions are scanned only
inside the sections that could state them.

Every comparison the prose makes ("the only first-round pick still in",
"twelfth to leave but not voted out", "one juror each from three drafters")
is RECOMPUTED here from the model, not just the numbers inside it.
"""

import html
import importlib.util
import io
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "public" / "week9.html"
THROUGH = 9          # this page is a frozen snapshot through episode 9


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


w9 = load("week9_map")
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
owner = w9.owner
out = w9.out
TRIBALS = [t for t in vh.TRIBALS if t["ep"] <= THROUGH]
received = {}
for t in TRIBALS:
    for n, v in t["votes"].items():
        received[n] = received.get(n, 0) + v
votes_by_drafter = {d: 0 for d in w9.DRAFT}
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
        ep, how = w9.GONE[name]
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
check(not (set(w9.everyone) - seen),
      f"castaways absent from the board: {sorted(set(w9.everyone) - seen)}")

# --- 2. standings rows ----------------------------------------------------
standings = section(">Standings<", ">The merged tribe<")
for who in w9.DRAFT:
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
    check(count == w9.left[who], f"{who} count {count}, expected {w9.left[who]}")
    check(vcount == votes_by_drafter[who],
          f"{who} votes {vcount}, expected {votes_by_drafter[who]}")
    for kind, raw_title, glyph in pips:
        nm = norm(raw_title).split("—")[0].strip()
        if nm not in owner:
            check(False, f"{who} pip titles unknown castaway {nm!r}")
            continue
        check(owner[nm] == who, f"{who}'s row shows {nm} ({owner[nm]}'s)")
        if kind == "gone":
            ep, how = w9.GONE.get(nm, (None, None))
            check(nm in out, f"{who}: {nm} shown gone but still in")
            check(norm(glyph) == {"quit": "Q", "coin flip": "C"}.get(how, "×"),
                  f"{who}: {nm} glyph {norm(glyph)!r}")
            check(f"episode {ep}" in norm(raw_title),
                  f"{who}: {nm} title does not name episode {ep}")
        else:
            check(nm not in out, f"{who}: {nm} shown on a tribe but is out")
            check(kind == CHIP and norm(glyph) == GLYPH and "Tovuto" in norm(raw_title),
                  f"{who}: {nm} pip reads {kind}/{norm(glyph)}/{norm(raw_title)}")
order = re.findall(r"<div class=\"row r-(\w+)\">", standings)
counts = [w9.left[w.capitalize()] for w in order]
check(counts == sorted(counts, reverse=True),
      f"standings not most-left-first: {list(zip(order, counts))}")

# --- 3. the one merged-tribe card ----------------------------------------
cards = section(">The merged tribe<", "<div class=\"story\">")
found = re.findall(r"<div class=\"tcard (\w+)\">(.*?)</ul>", cards, re.S)
check(len(found) == 1, f"found {len(found)} tribe cards, expected the 1 merged tribe")
alive_sorted = sorted(w9.alive)
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
    check(f"· {len(w9.alive)} ·" in meta, f"card count should read {len(w9.alive)}: {meta}")
    check(w9.IMMUNE in meta and "immun" in meta.lower(),
          f"card should name {w9.IMMUNE} as immune: {meta}")
    check("Blue" in meta, f"card should name the buff colour: {meta}")



# --- 4. hardware ----------------------------------------------------------
hardware = section(">Hardware watch<", "class=\"gone-box\"")
hw = re.findall(r"<tr><td>([^<]+)</td><td><span class=\"chip (\w+)\">", hardware)
holders = [norm(h) for h, _ in hw]
check(sorted(holders) == sorted(w9.ADVANTAGES),
      f"hardware holders\n   got  {sorted(holders)}\n   want {sorted(w9.ADVANTAGES)}")
for _, chip in hw:
    check(chip == CHIP, f"a hardware chip reads {chip!r}")
check("fake" in norm(hardware).lower() and "not on this list" in norm(hardware),
      "the hardware note must say the fake idol is not an advantage")
tether = re.search(r"<tr><td>Sharonda Cox</td>.*?</tr>", hardware, re.S)
check(tether is not None and "not known" in norm(tether.group(0)),
      "the Tethered Idol row must say its status is not known")
check(not any(t["ep"] == 9 for t in vh.TRIBALS),
      "page says there was no vote in episode 9; the model holds a tribal for it")

# --- 5. the gone box ------------------------------------------------------
gone = section("class=\"gone-box\"", ">Who owns whom<")
boxes = re.findall(r"<p class=\"tag\">([^<]+)</p>\s*<div class=\"nm\">([^<]+)</div>\s*<p>(.*?)</p>",
                   gone, re.S)
check([norm(b[1]) for b in boxes] == [w9.FLIPPER],
      f"gone box names {[norm(b[1]) for b in boxes]}, expected {[w9.FLIPPER]}")
ORD = ["zeroth", "first", "second", "third", "fourth", "fifth", "sixth", "seventh",
       "eighth", "ninth", "tenth", "eleventh", "twelfth", "thirteenth"]
pick_of = {n: p for ps in w9.DRAFT.values() for p, n in ps}
for tag, raw, body in boxes:
    nm, txt = norm(raw), norm(body)
    check("voted out" not in norm(tag).lower() and "coin" in norm(tag).lower(),
          f"the box tag must not say voted out: {norm(tag)!r}")
    check(f"drafted {pick_of[nm]}st by {owner[nm]}" in txt,
          f"{nm} box should read 'drafted {pick_of[nm]}st by {owner[nm]}'")
    check(f"{ORD[len(out)]} castaway to leave" in txt,
          f"{nm} was the {ORD[len(out)]} to leave: {txt[:140]}")
    check(f"{ORD[len(w9.JURY)]} member of the jury" in txt,
          f"{nm} is juror {len(w9.JURY)}: {txt[:160]}")
    check(not re.search(r"\b\w+ (castaway )?voted out\b", txt),
          f"the box gives Lewis a voted-out ordinal; nobody voted: {txt[:160]}")

# --- 6. headline and story claims, each recomputed -----------------------
story = strip_tags(section("<div class=\"story\">", ">Hardware watch<"))
header = strip_tags(section("<header>", "</header>"))
check(pick_of[w9.FLIPPER] == 1 and owner[w9.FLIPPER] == "Daron",
      "the headline needs Lewis to be the first pick of the draft, Daron's")
check(w9.GONE[w9.FLIPPER] == (9, "coin flip"), "Lewis must be a coin-flip exit")
check(w9.CALLED == "fire" and w9.LANDED == "water"
      and "called fire" in story and "water" in story,
      "the story must state the call (fire) and the landing (water)")
check(w9.CONSIDERED_FLIP == ["Devin Way", "Lewis Kelly"]
      and "Devin Way and Lewis Kelly were the last two" in story,
      "the story should name Devin and Lewis as the last two weighing the flip")
check("not the eleventh voted out" in story and f"{ORD[len(out)]} castaway to leave" in story,
      "the story must reconcile 'twelfth to leave' with 'not voted out'")
check(len(w9.voted_out) == 10,
      f"page implies ten voted out so far (Lewis would have been eleventh): {len(w9.voted_out)}")

firsts = {w: min(ps)[1] for w, ps in w9.DRAFT.items()}
still = [w for w, n in firsts.items() if n not in out]
check(still == ["Mike"] and firsts["Mike"] == "Carter Krull",
      f"page claims Mike's Carter is the only first-round pick still in: {firsts}, {still}")
for w, n in firsts.items():
    check(n in story, f"the first-round paragraph should name {w}'s {n}")
# Bind the claim to the TEXT: the sentence must name the model's sole survivor.
if len(still) == 1:
    want = f"{firsts[still[0]].split()[0]} is now the only one still in the game"
    check(want in story, f"the first-round sentence should read {want!r}")
check(w9.IMMUNE == "Carter Krull" and w9.IMMUNITY_LAST_TWO == ["Carter Krull", "Lewis Kelly"],
      "page claims Carter beat Lewis for immunity")
check(w9.left == {"Mike": 4, "Cagney": 2, "Daron": 1, "Will": 1},
      f"standings changed: {w9.left}")
check([n for _, n in w9.DRAFT["Daron"] if n not in out] == ['Angelica "Jelly" Loblack']
      and [n for _, n in w9.DRAFT["Will"] if n not in out] == ["Sharonda Cox"],
      "page names Jelly and Sharonda as Daron's and Will's last")
check(sorted(owner[n] for n in w9.JURY) == ["Cagney", "Daron", "Will"],
      f"page claims the jury is one each from Will, Cagney and Daron: {w9.JURY}")
mike_losses = sorted(w9.GONE[n][0] for _, n in w9.DRAFT["Mike"] if n in out)
check(mike_losses == [5], f"page claims Mike has lost nobody since ep 5: {mike_losses}")

won = {}
for n in w9.REWARD_WON:
    won.setdefault(owner[n], []).append(n)
lost = {}
for n in w9.REWARD_LOST:
    lost.setdefault(owner[n], []).append(n)
check(len(won.get("Cagney", [])) == 2 and "Cagney" not in lost,
      f"page claims both of Cagney's won the reward: {won}, {lost}")
check(len(won.get("Mike", [])) == 2 and len(lost.get("Mike", [])) == 2,
      f"page claims Mike's four split two and two: {won}, {lost}")
check(len(won.get("Daron", [])) == 1 and len(lost.get("Daron", [])) == 1,
      "page claims Daron's two were split")
check(lost.get("Will") == ["Sharonda Cox"] and lost.get("undrafted") == ["Cristian Chavez"],
      "page puts Sharonda and Cristian on the losing side")
for n in w9.REWARD_WON:
    check(n in story, f"the reward paragraph should name winner {n}")
check(w9.FAKE_IDOL_MAKER == "Devin Way", "page says Devin built the fake idol")
drafted_out = len([n for n in out if owner[n] != "undrafted"])
check(drafted_out == 12, f"footer claims Cristian has outlasted twelve: {drafted_out}")

# --- 7. the ledger's own prose claims ------------------------------------
check(received.get("Lewis Kelly") == 4
      and [t["ep"] for t in TRIBALS if "Lewis Kelly" in t["votes"]] == [5],
      "page says Lewis was written down four times, all in episode 5")
t5 = [t for t in TRIBALS if t["ep"] == 5 and "Lewis Kelly" in t["votes"]]
check(len(t5) == 1 and t5[0]["tribe"] == "Dina" and t5[0].get("tie"),
      "page says Lewis's four came in the episode-5 tie at Dina")
multi = sorted(n for n in received if sum(n in t["votes"] for t in TRIBALS) > 1)
check(multi == ["Alexis Levine", "Danny Kilby", "Eric Macksoud", "Jenna Doore"],
      f"page names four twice-voted castaways: {multi}")
ledger_note = strip_tags(section("<h2 id=\"votes\">", "<div class=\"standings\">"))
check("no vote" in ledger_note and "no card" in ledger_note,
      "the ledger note must explain why episode 9 has no tribal card")

# --- 8. unaired material and omissions -----------------------------------
flat = strip_tags(page)
for banned in (r"\bepisode 10\b", r"thanksgiving", r"\bday 1[89]\b", r"\bday 2\d\b"):
    check(not re.search(banned, flat, re.I), f"page refers to unaired material: {banned}")
# "eleventh voted out" is legitimate only as the NEGATION that reconciles the
# count; any un-negated use is the outlet's false count leaking in.
for m in re.finditer(r"eleventh (castaway )?voted (out|off)", flat, re.I):
    before = flat[max(0, m.start() - 40):m.start()].lower()
    check("not the" in before or "calls lewis the" in before,
          f"'eleventh voted out' asserted, not negated: ...{flat[max(0, m.start() - 60):m.end() + 20]}...")
check("not the eleventh voted out" in flat, "the reconciling sentence is missing")
# Who holds the fake idol, and what a WIN would have earned the flipper, are
# contested. Scan the story only; the left-out note names the readings.
for banned, why in ((r"maggie (has|holds|kept|took|refused|missed)", "how the fake-idol handoff ended"),
                    (r"(flipper|winner) (would|gets|earns)[^.]{0,40}idol", "the win-side reward"),
                    (r"shot in the dark[^.]{0,60}lewis|lewis[^.]{0,60}shot in the dark",
                     "Lewis's single-source Shot in the Dark")):
    check(not re.search(banned, story, re.I), f"the story asserts {why}")
kick = strip_tags(section(">What is left out, and why<", "<footer>"))
for must in ("fake idol", "eleventh", "immunity challenge", "Tethered Idol", "correct call"):
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
print(f"PASS  {len(rows)} board rows, {len(w9.DRAFT)} standings rows, "
      f"{len(found)} merged card, {len(holders)} advantages, {len(boxes)} gone box, "
      f"{len(w9.alive)} alive, coin-flip and first-round claims recomputed, "
      f"omissions held, no unaired material, no stray pronouns")
