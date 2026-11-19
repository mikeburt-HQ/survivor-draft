"""Every vote cast in Survivor 51 so far, rolled up by drafter.

Answers: how many votes has each drafter's team taken, cumulatively?

Each tribal's tally is recorded with the number of ELIGIBLE VOTERS derived
independently from tribe populations, and the script asserts the two agree.
That is the whole point: a tally that does not match the voter count is either
a bad source or a bad population model, and both have bitten this season.

Sources and the conflicts that were resolved, per tribal:

  ep 1  Aaliyah 6 / Jenna 2.  Wikipedia's vote table, TVLine and Inside
        Survivor agree, and the named voters corroborate it (only Devin and
        Jelly voted Jenna). Paramount+ printed 5-3; it is the outlier.
  ep 2  Ana 6 / Eric 4.  Wikipedia, the Fandom tribal table, Paramount+ and
        TVLine all agree. Rob tried to vote for HIMSELF; production stopped
        him (self-voting is not allowed) and he re-cast, reportedly for Eric.
        So Rob received nothing, and all ten Savu members voted.
  ep 3  Patt 6 / Kilby 5.  Wikipedia and Inside Survivor agree. Sunday
        Guardian printed 7-5, which cannot be right: Toka had 11.
  ep 4  Jenna 4 / Alexis 1.  Wikipedia's vote table, TVLine and Yahoo's
        results piece agree; Jenna's own vote was the one against Alexis.
        Paramount+ printed Jenna 3 / Alexis 1, which totals 4 of 5 votes, so
        it under-counts rather than disagreeing. Yahoo's LIVE blog called it
        unanimous; a live blog is the weakest source in the set.
  ep 5  TWO tribals -- Toka won immunity and both Savu and Dina voted.
        Savu: Alexis 3, plus ONE UNATTRIBUTED ballot. The 3-1 split is
        three-source (Wikipedia, Yahoo, Inside Survivor); only Yahoo names a
        recipient for the lone vote, so it is not credited to anyone here.
        Surviving Tribal calls it unanimous and is the lone dissenter, as it
        was on episode 4, where it was wrong.
        Dina: Linnea 4 / Lewis 4 from EIGHT ballots -- six members plus the two
        extra votes Maggie handed to Kilby and Lewis, both played on Linnea
        (Yahoo's per-person breakdown and DK Network agree, and it is the only
        reading that makes 4-4 arithmetically possible).
        Not recorded: the REVOTE. Yahoo and Surviving Tribal both print a
        second 4-4, which cannot happen -- a revote excludes the two tied
        castaways, leaving four voters, and extra votes do not carry into it.
        Not recorded either: the consensus round that followed, where Kilby
        held for Lewis and the other three came across to Linnea. No source
        gives a tally that is consistent with the stated unanimity rule, and
        no rocks were drawn.
  ep 6  Ori 2, from TWO ballots cast by THREE people. Ori played a Shot in the
        Dark, drew Not Safe, and forfeited that night's vote -- the same rule
        that made episode 1 eight ballots from ten. Wikipedia's episode table
        prints 2-0 and its summary says "unanimously"; both are correct and
        describe the same tally, differing only on whether the forfeited
        ballot is counted. TVLine, Yahoo, DK Network and Primetimer all name
        Jelly and Devin as the two voters, so the tally is fully attributed.

No tribal this season has produced a third vote recipient -- every tally is
two-way, so there are no stray votes hiding outside these numbers.

What the voter-count gate CANNOT do: episode 1's rival readings, 6-2 and 5-3,
both sum to the 8 votes available, so the gate accepts either. Proven by
injection -- feeding it 5-3 passes silently, while ep 3 as 7-5 and ep 4 as
Paramount+'s 3/1 both fail and name themselves. Episode 1's split therefore
rests on source agreement alone (Wikipedia's table, TVLine, and only Devin
and Jelly named as voting Jenna), never on arithmetic. If a better source
ever contradicts it, nothing here will object.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEED = ROOT / "supabase" / "seed.sql"

# --- the draft, as in week4_map.py -----------------------------------------
DRAFT = {
    "Daron":  ["Lewis Kelly", "Aaliyah Puglia", "Patt Cannaday",
               "Brady Booker", 'Angelica "Jelly" Loblack'],
    "Will":   ["Danny Kilby", "Jenna Doore", "Ori Jean-Charles",
               "Sharonda Cox", "Ana Sani"],
    "Cagney": ["Alexis Levine", "Eric Macksoud", "Rob Antonson",
               "Kristin Flickinger", "Devin Way"],
    "Mike":   ["Carter Krull", "Mike Pinsky", "Maggie Nestor",
               "Linnea Capobianco", "Thien An Nguyen"],
}
UNDRAFTED = ["Cristian Chavez"]

# --- starting tribes (Lewis began on Exile, joined Toka in ep 3) -----------
START_SAVU = ["Alexis Levine", "Ana Sani", "Carter Krull", "Cristian Chavez",
              "Eric Macksoud", "Kristin Flickinger", "Linnea Capobianco",
              "Ori Jean-Charles", "Rob Antonson", "Sharonda Cox"]
START_TOKA = ["Aaliyah Puglia", "Brady Booker", "Devin Way",
              'Angelica "Jelly" Loblack', "Jenna Doore", "Danny Kilby",
              "Maggie Nestor", "Mike Pinsky", "Patt Cannaday",
              "Thien An Nguyen"]
START_EXILE = ["Lewis Kelly"]

# --- every tribal council -------------------------------------------------
# votes: castaway -> votes received.  no_vote: at tribal but did not cast a
# ballot (a Shot in the Dark played and lost forfeits that night's vote).
TRIBALS = [
    {
        "ep": 1, "day": 3, "tribe": "Toka",
        "votes": {"Aaliyah Puglia": 6, "Jenna Doore": 2},
        "no_vote": ["Aaliyah Puglia", "Jenna Doore"],
        "note": "Aaliyah and Jenna both played a Shot in the Dark; both drew "
                "Not Safe, so both forfeited their vote.",
    },
    {
        "ep": 2, "day": 5, "tribe": "Savu",
        "votes": {"Ana Sani": 6, "Eric Macksoud": 4},
        "no_vote": [],
        "note": "Rob's self-vote was stopped by production and re-cast, so "
                "all ten Savu members voted and Rob received nothing.",
    },
    {
        "ep": 3, "day": 7, "tribe": "Toka",
        "votes": {"Patt Cannaday": 6, "Danny Kilby": 5},
        "no_vote": [],
        "note": "Lewis arrived from Exile and Carter mutinied over from Savu, "
                "making Toka 11. They were the swing votes.",
    },
    {
        "ep": 4, "day": 9, "tribe": "Savu",
        "votes": {"Jenna Doore": 4, "Alexis Levine": 1},
        "no_vote": [],
        "note": "Post-swap Savu, five strong. Jenna cast the lone vote "
                "against Alexis.",
    },
    # Episode 5 sent TWO tribes to Tribal Council. Optional keys appear from
    # here on: extra_votes adds ballots beyond the members present,
    # unattributed holds ballots whose recipient no source confirms, out names
    # the castaway who left (needed when the vote TIES), and tie says the
    # result was settled after the vote rather than by it.
    {
        "ep": 5, "day": None, "day_label": "days 9-10", "tribe": "Savu",
        "votes": {"Alexis Levine": 3}, "unattributed": 1,
        "no_vote": [], "out": "Alexis Levine",
        "note": "Three of Savu's four turned on Alexis. The fourth ballot's "
                "recipient is named by only one source, so it is left "
                "uncredited here.",
    },
    {
        "ep": 5, "day": None, "day_label": "days 9-10", "tribe": "Dina",
        "votes": {"Linnea Capobianco": 4, "Lewis Kelly": 4},
        "extra_votes": 2, "no_vote": [], "out": "Linnea Capobianco",
        "tie": True,
        "note": "Eight ballots from six people: Maggie's two extra votes went "
                "to Kilby and Lewis and both were played on Linnea. The 4-4 "
                "tie, a deadlocked revote and a refusal to budge took it to "
                "the brink of rocks before the tribe settled on Linnea.",
    },
    {
        "ep": 6, "day": None, "day_label": "days 10-12", "tribe": "Savu",
        "votes": {"Ori Jean-Charles": 2},
        "no_vote": ["Ori Jean-Charles"],
        "note": "Two ballots from three people: Ori played a Shot in the Dark, "
                "drew Not Safe, and forfeited the vote. Jelly and Devin both "
                "wrote Ori's name, so 2-0 and 'unanimous' are the same result.",
    },
    # Episode 7: the merge. Everyone left became Tovuto and all thirteen
    # voted; Mike Pinsky had individual immunity.
    {
        "ep": 7, "day": 14, "tribe": "Tovuto",
        "votes": {"Brady Booker": 9, "Eric Macksoud": 4},
        "no_vote": [],
        "note": "The first merged vote: thirteen people, thirteen ballots, "
                "no advantages played.",
    },
    # Episode 8: the DOUBLE DUO. Castaways played and were voted out in
    # pairs, so every ballot named a PAIR. `pairs` holds ballots per pair;
    # `negated` holds ballots that were cast and read but did not count
    # (Jelly's idol covered her pair, Cristian's Safe Shot in the Dark his).
    # `votes` is DERIVED below: one credit to each member of a named pair.
    {
        "ep": 8, "day": 15, "tribe": "Tovuto",
        "pairs": {
            ("Devin Way", 'Angelica "Jelly" Loblack'): 8,
            ("Danny Kilby", "Kristin Flickinger"): 1,
            ("Carter Krull", "Cristian Chavez"): 1,
        },
        "negated": {
            ("Devin Way", 'Angelica "Jelly" Loblack'): 8,
            ("Carter Krull", "Cristian Chavez"): 1,
        },
        "no_vote": ["Kristin Flickinger", "Cristian Chavez"],
        "out": ["Danny Kilby", "Kristin Flickinger"],
        "note": "Ten ballots from twelve people: Kristin and Cristian both "
                "played a Shot in the Dark and forfeited their votes. Jelly's "
                "idol cancelled the eight against Devin and Jelly, Cristian's "
                "Safe Shot cancelled the one against Carter and Cristian, and "
                "the only ballot left standing -- Devin's -- sent Kilby and "
                "Kristin home together.",
    },
]

# A pair ballot credits each member once, so a castaway's figure is "ballots
# that named them". Derived here, once, for every consumer.
for _t in TRIBALS:
    if "pairs" in _t:
        _t["votes"] = {}
        for _pair, _v in _t["pairs"].items():
            assert len(_pair) == 2 and _pair[0] != _pair[1], f"bad pair {_pair}"
            for _n in _pair:
                _t["votes"][_n] = _t["votes"].get(_n, 0) + _v


def ballots_of(t):
    """Ballots physically cast at a tribal (a pair ballot is ONE ballot)."""
    if "pairs" in t:
        return sum(t["pairs"].values())
    return sum(t["votes"].values()) + t.get("unattributed", 0)


def outs_of(t):
    """Everyone who left at this tribal, as a list."""
    o = t.get("out")
    if o is None:
        return [max(t["votes"], key=t["votes"].get)]
    return list(o) if isinstance(o, (list, tuple)) else [o]


def negated_of(t):
    """Per-castaway credits that were cast but cancelled."""
    neg = {}
    for pair, v in t.get("negated", {}).items():
        for n in pair:
            neg[n] = neg.get(n, 0) + v
    return neg

# Non-vote exits and mid-game moves, so populations stay honest.
MERGE_EP, MERGED = 7, "Tovuto"     # every tribe folds into one
QUIT = {"Rob Antonson": 3}            # quit on day 6, no vote cast
MUTINY = {"Carter Krull": 3}          # Savu -> Toka in ep 3
EXILE_JOINED = {"Lewis Kelly": 3}     # Exile -> Toka in ep 3

# Post-swap tribes, episode 4 (17 in the game at the swap).
SWAP = {
    "Toka": ["Mike Pinsky", "Carter Krull", "Brady Booker",
             "Thien An Nguyen", "Maggie Nestor", "Kristin Flickinger"],
    "Savu": ["Devin Way", 'Angelica "Jelly" Loblack', "Ori Jean-Charles",
             "Alexis Levine", "Jenna Doore"],
    "Dina": ["Danny Kilby", "Lewis Kelly", "Sharonda Cox", "Eric Macksoud",
             "Linnea Capobianco", "Cristian Chavez"],
}

# --- names must be the exact seed spellings -------------------------------
seed = SEED.read_text(encoding="utf8")
cast = set(re.findall(r"^\(\d+,\s+'(.+?)',", seed, re.M))
assert len(cast) == 21, f"expected 21 castaways in seed.sql, found {len(cast)}"

drafted = [n for picks in DRAFT.values() for n in picks]
assert len(drafted) == 20, f"draft should be 20 picks, got {len(drafted)}"
assert len(set(drafted)) == 20, "a castaway was drafted twice"
assert set(drafted) | set(UNDRAFTED) == cast, "draft does not cover the cast"

for label, group in (("Savu", START_SAVU), ("Toka", START_TOKA),
                     ("Exile", START_EXILE)):
    unknown = [n for n in group if n not in cast]
    assert not unknown, f"starting {label} has names not in seed.sql: {unknown}"
assert set(START_SAVU) | set(START_TOKA) | set(START_EXILE) == cast, \
    "starting tribes plus Exile do not account for all 21 castaways"

for t in TRIBALS:
    for n in list(t["votes"]) + t["no_vote"]:
        assert n in cast, f"ep {t['ep']}: '{n}' is not a seed.sql name"

for group in SWAP.values():
    for n in group:
        assert n in cast, f"post-swap tribes contain a non-seed name: {n}"
assert sum(len(g) for g in SWAP.values()) == 17, \
    "the swap should cover the 17 still in the game"

# --- walk the populations and gate every tally ----------------------------
pop = {"Savu": set(START_SAVU), "Toka": set(START_TOKA)}
exile = set(START_EXILE)
gone = []

print("Tribal councils, episode by episode")
print("=" * 72)

moves_done = set()      # an episode's moves fire ONCE, not once per tribal

for t in TRIBALS:
    ep, tribe = t["ep"], t["tribe"]

    # mid-episode moves land before that episode's tribal
    if ep not in moves_done:
        moves_done.add(ep)
        for name, e in QUIT.items():
            if e == ep:
                pop["Savu" if name in START_SAVU else "Toka"].discard(name)
                gone.append((ep, name, "quit"))
        for name, e in MUTINY.items():
            if e == ep:
                pop["Savu"].discard(name)
                pop["Toka"].add(name)
        for name, e in EXILE_JOINED.items():
            if e == ep:
                exile.discard(name)
                pop["Toka"].add(name)

        if ep == 4:                  # the swap replaces the two-tribe model
            pop = {k: set(v) for k, v in SWAP.items()}
        if ep == MERGE_EP:           # the merge folds every tribe into one
            pop = {MERGED: set().union(*pop.values())}

    # Snapshot: pop[tribe] is mutated below, and a live reference would make
    # every reported attendance one short of the truth.
    attending = frozenset(pop[tribe])
    extra = t.get("extra_votes", 0)
    unattributed = t.get("unattributed", 0)
    eligible = len(attending) - len(t["no_vote"]) + extra
    # Published on the page, so these are recorded here rather than recomputed
    # by any consumer: one derivation, one number.
    t["_attending"] = len(attending)
    t["_label"] = t.get("day_label") or f"day {t['day']}"
    cast_votes = ballots_of(t)

    assert cast_votes == eligible, (
        f"ep {ep} {tribe}: ballots account for {cast_votes} but {eligible} "
        f"were available ({len(attending)} at tribal, "
        f"{len(t['no_vote'])} forfeited, {extra} extra votes played)"
    )
    for n in t["votes"]:
        assert n in attending, f"ep {ep}: {n} took votes but was not on {tribe}"
    for n in t["no_vote"]:
        assert n in attending, f"ep {ep}: {n} forfeited but was not at tribal"

    if "pairs" in t:
        # A pair vote is decided on the ballots that COUNTED. Negated ballots
        # were cast and read, so they stay in `votes`, but they decide nothing.
        for pair, v in t.get("negated", {}).items():
            assert pair in t["pairs"] and 0 < v <= t["pairs"][pair], \
                f"ep {ep}: negated {pair} x{v} exceeds what it received"
        counted = {p: v - t.get("negated", {}).get(p, 0)
                   for p, v in t["pairs"].items()}
        live = sum(counted.values())
        top = max(counted.values())
        lead = [p for p, v in counted.items() if v == top]
        assert len(lead) == 1, f"ep {ep}: counted ballots tie between {lead}"
        assert top > live / 2, f"ep {ep}: {lead[0]} left without a majority"
        assert sorted(lead[0]) == sorted(t["out"]), (
            f"ep {ep}: {t['out']} declared out but {lead[0]} led the counted "
            f"ballots {counted}")
        t["_counted"] = counted
        for n in t["out"]:
            assert n in attending, f"ep {ep}: {n} was not on {tribe}"
            pop[tribe].discard(n)
            gone.append((ep, n, "voted out"))
        print(f"\nEpisode {ep}, {t['_label']} -- {tribe}, {len(attending)} at "
              f"tribal, {cast_votes} ballots against pairs")
        for p, v in t["pairs"].items():
            print(f"  {' & '.join(p)}: {v} cast, {counted[p]} counted")
        print(f"  out: {' & '.join(t['out'])}")
        print(f"  {t['note']}")
        continue

    # With a tie the vote alone does not name the boot, so it must be declared.
    top = max(t["votes"].values())
    tied = [n for n, v in t["votes"].items() if v == top]
    if t.get("tie"):
        assert len(tied) > 1, f"ep {ep} {tribe}: marked a tie but nobody tied"
        booted = t["out"]
        assert booted in tied, (
            f"ep {ep} {tribe}: {booted} left but was not among the tied "
            f"castaways {tied}"
        )
    else:
        assert len(tied) == 1, f"ep {ep} {tribe}: tied {tied} without a tie flag"
        booted = t.get("out", tied[0])
        assert booted == tied[0], \
            f"ep {ep} {tribe}: {booted} left but {tied[0]} had the most votes"
        assert t["votes"][booted] > cast_votes / 2, \
            f"ep {ep} {tribe}: {booted} left without a majority"

    assert booted in attending, f"ep {ep}: {booted} was not on {tribe}"
    pop[tribe].discard(booted)
    gone.append((ep, booted, "voted out"))

    tally = " / ".join(f"{n} {v}" for n, v in
                       sorted(t["votes"].items(), key=lambda kv: -kv[1]))
    if unattributed:
        tally += f" / {unattributed} unattributed"
    print(f"\nEpisode {ep}, {t['_label']} -- {tribe}, "
          f"{len(attending)} at tribal, {cast_votes} ballots"
          + (f" ({extra} from extra votes)" if extra else ""))
    print(f"  {tally}")
    print(f"  out: {booted}" + ("  (after a tie)" if t.get("tie") else ""))
    print(f"  {t['note']}")

LAST_EP = max(t["ep"] for t in TRIBALS)
EXPECTED_ALIVE = {4: 16, 5: 14, 6: 13, 7: 12, 8: 10}
still_in = sum(len(v) for v in pop.values()) + len(exile)
assert still_in == EXPECTED_ALIVE[LAST_EP], (
    f"{EXPECTED_ALIVE[LAST_EP]} should remain after ep {LAST_EP}; "
    f"model says {still_in}"
)

# --- roll up ---------------------------------------------------------------
received = {}
for t in TRIBALS:
    for n, v in t["votes"].items():
        received[n] = received.get(n, 0) + v

owner = {n: d for d, picks in DRAFT.items() for n in picks}
for n in UNDRAFTED:
    owner[n] = "(undrafted)"

# Attributed votes are those credited to a named castaway; UNATTRIBUTED are
# ballots that were cast but whose recipient no source confirms. Through
# episode 7 every ballot named one castaway, so credits and ballots are the
# same number. From episode 8 a pair ballot credits TWO castaways, so the
# credit total (TOTAL_CREDITS, the denominator for shares) runs ahead of the
# ballots physically cast (TOTAL_BALLOTS).
attributed = sum(received.values())
unattributed_total = sum(t.get("unattributed", 0) for t in TRIBALS)
TOTAL_CREDITS = attributed + unattributed_total
TOTAL_BALLOTS = sum(ballots_of(t) for t in TRIBALS)
assert attributed == sum(sum(t["votes"].values()) for t in TRIBALS)
assert TOTAL_CREDITS - TOTAL_BALLOTS == sum(
    sum(t["pairs"].values()) for t in TRIBALS if "pairs" in t), \
    "credits should exceed ballots by exactly one per pair ballot"
# A pair inside ONE roster would credit that drafter twice for one ballot.
# None exists yet; if one ever does, the roll-up must decide, not drift.
for t in TRIBALS:
    for pair in t.get("pairs", {}):
        assert len({owner[n] for n in pair}) == 2, \
            f"ep {t['ep']}: pair {pair} sits on one roster"

by_drafter = {d: 0 for d in DRAFT}
by_drafter["(undrafted)"] = 0
for n, v in received.items():
    by_drafter[owner[n]] += v
assert sum(by_drafter.values()) == attributed, "roll-up lost votes"
assert sum(by_drafter.values()) + unattributed_total == TOTAL_CREDITS

print("\n" + "=" * 72)
print(f"Ballots cast at the {len(TRIBALS)} tribals: {TOTAL_BALLOTS}; "
      f"credits {TOTAL_CREDITS} ({attributed} attributed, "
      f"{unattributed_total} unattributed)")

print("\nVotes received, by drafter")
print("-" * 72)
for d, v in sorted(by_drafter.items(), key=lambda kv: -kv[1]):
    share = 100 * v / TOTAL_CREDITS
    team = DRAFT.get(d, UNDRAFTED)
    hit = [n for n in team if received.get(n)]
    print(f"  {d:<12} {v:>3} votes  ({share:4.1f}%)  "
          f"{len(hit)} of {len(team)} castaways voted against")
if unattributed_total:
    print(f"  {'unattributed':<12} {unattributed_total:>3} votes  "
          f"({100 * unattributed_total / TOTAL_CREDITS:4.1f}%)")

print("\nVotes received, by castaway")
print("-" * 72)
out_names = {n for _, n, how in gone if how == "voted out"}
for n, v in sorted(received.items(), key=lambda kv: (-kv[1], kv[0])):
    eps = [t["ep"] for t in TRIBALS if n in t["votes"]]
    status = "voted out" if n in out_names else "still in"
    print(f"  {n:<28} {v:>2}  {owner[n]:<12} "
          f"ep {','.join(map(str, eps)):<6} {status}")

clean = [n for n in cast if not received.get(n)]
print(f"\nNever had a vote cast against them: {len(clean)} of 21")

# The two facts worth leading with, both derived rather than recalled.
zero = [d for d, v in by_drafter.items() if v == 0 and d != "(undrafted)"]
print(f"Drafters with ZERO votes against their team: {zero}")

survivors_voted = sorted(
    ((v, n) for n, v in received.items() if n not in out_names), reverse=True)
if survivors_voted:
    v = survivors_voted[0][0]
    tops = sorted(n for vv, n in survivors_voted if vv == v)
    print(f"Most votes survived ({v}): " + ", ".join(
        f"{n} ({owner[n]})" for n in tops))

multi = {n: [t["ep"] for t in TRIBALS if n in t["votes"]]
         for n in received}
multi = {n: eps for n, eps in multi.items() if len(eps) > 1}
print(f"Voted against at more than one tribal: {multi}")
