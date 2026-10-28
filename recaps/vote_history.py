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
    cast_votes = sum(t["votes"].values()) + unattributed

    assert cast_votes == eligible, (
        f"ep {ep} {tribe}: ballots account for {cast_votes} but {eligible} "
        f"were available ({len(attending)} at tribal, "
        f"{len(t['no_vote'])} forfeited, {extra} extra votes played)"
    )
    for n in t["votes"]:
        assert n in attending, f"ep {ep}: {n} took votes but was not on {tribe}"

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
EXPECTED_ALIVE = {4: 16, 5: 14}
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
# ballots that were cast but whose recipient no source confirms. Both are real
# ballots, so TOTAL_BALLOTS is the denominator and the two must reconcile to it.
attributed = sum(received.values())
unattributed_total = sum(t.get("unattributed", 0) for t in TRIBALS)
TOTAL_BALLOTS = attributed + unattributed_total
assert attributed == sum(sum(t["votes"].values()) for t in TRIBALS)

by_drafter = {d: 0 for d in DRAFT}
by_drafter["(undrafted)"] = 0
for n, v in received.items():
    by_drafter[owner[n]] += v
assert sum(by_drafter.values()) == attributed, "roll-up lost votes"
assert sum(by_drafter.values()) + unattributed_total == TOTAL_BALLOTS

print("\n" + "=" * 72)
print(f"Ballots cast at the {len(TRIBALS)} tribals: {TOTAL_BALLOTS} "
      f"({attributed} attributed, {unattributed_total} unattributed)")

print("\nVotes received, by drafter")
print("-" * 72)
for d, v in sorted(by_drafter.items(), key=lambda kv: -kv[1]):
    share = 100 * v / TOTAL_BALLOTS
    team = DRAFT.get(d, UNDRAFTED)
    hit = [n for n in team if received.get(n)]
    print(f"  {d:<12} {v:>3} votes  ({share:4.1f}%)  "
          f"{len(hit)} of {len(team)} castaways voted against")
if unattributed_total:
    print(f"  {'unattributed':<12} {unattributed_total:>3} votes  "
          f"({100 * unattributed_total / TOTAL_BALLOTS:4.1f}%)")

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
