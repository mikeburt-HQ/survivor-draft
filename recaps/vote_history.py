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
]

# Non-vote exits and mid-game moves, so populations stay honest.
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

for t in TRIBALS:
    ep, tribe = t["ep"], t["tribe"]

    # mid-episode moves land before that episode's tribal
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

    if ep == 4:                      # the swap replaces the two-tribe model
        pop = {k: set(v) for k, v in SWAP.items()}

    # Snapshot: pop[tribe] is mutated below, and a live reference would make
    # every reported attendance one short of the truth.
    attending = frozenset(pop[tribe])
    eligible = len(attending) - len(t["no_vote"])
    cast_votes = sum(t["votes"].values())

    assert cast_votes == eligible, (
        f"ep {ep}: tally sums to {cast_votes} but {eligible} members could "
        f"vote ({len(attending)} at tribal, {len(t['no_vote'])} forfeited)"
    )
    for n in t["votes"]:
        assert n in attending, f"ep {ep}: {n} took votes but was not on {tribe}"

    booted = max(t["votes"], key=t["votes"].get)
    assert t["votes"][booted] > cast_votes / 2, \
        f"ep {ep}: {booted} left without a majority"
    pop[tribe].discard(booted)
    gone.append((ep, booted, "voted out"))

    tally = " / ".join(f"{n} {v}" for n, v in
                       sorted(t["votes"].items(), key=lambda kv: -kv[1]))
    print(f"\nEpisode {ep}, day {t['day']} -- {tribe}, "
          f"{len(attending)} at tribal, {cast_votes} votes cast")
    print(f"  {tally}")
    print(f"  out: {booted}")
    print(f"  {t['note']}")

still_in = sum(len(v) for v in pop.values()) + len(exile)
assert still_in == 16, f"16 should remain after ep 4; model says {still_in}"

# --- roll up ---------------------------------------------------------------
received = {}
for t in TRIBALS:
    for n, v in t["votes"].items():
        received[n] = received.get(n, 0) + v

owner = {n: d for d, picks in DRAFT.items() for n in picks}
for n in UNDRAFTED:
    owner[n] = "(undrafted)"

total_votes = sum(received.values())
assert total_votes == sum(sum(t["votes"].values()) for t in TRIBALS)

by_drafter = {d: 0 for d in DRAFT}
by_drafter["(undrafted)"] = 0
for n, v in received.items():
    by_drafter[owner[n]] += v
assert sum(by_drafter.values()) == total_votes, "roll-up lost votes"

print("\n" + "=" * 72)
print(f"Votes cast at the four tribals: {total_votes}")

print("\nVotes received, by drafter")
print("-" * 72)
for d, v in sorted(by_drafter.items(), key=lambda kv: -kv[1]):
    share = 100 * v / total_votes
    team = DRAFT.get(d, UNDRAFTED)
    hit = [n for n in team if received.get(n)]
    print(f"  {d:<12} {v:>3} votes  ({share:4.1f}%)  "
          f"{len(hit)} of {len(team)} castaways voted against")

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
    v, n = survivors_voted[0]
    print(f"Most votes survived: {n} ({owner[n]}) took {v} and stayed")

multi = {n: [t["ep"] for t in TRIBALS if n in t["votes"]]
         for n in received}
multi = {n: eps for n, eps in multi.items() if len(eps) > 1}
print(f"Voted against at more than one tribal: {multi}")
