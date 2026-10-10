"""Map the Survivor 51 draft onto the state after episode 3. Read-only.

Roster is the draft as verified against the live app in week 1 (the draft is
complete, so it cannot change). Tribes, departures and the episode-3 tribe move
are from the Paramount+ episode recaps.
"""

DRAFT = {
    "Daron":  [(1, "Lewis Kelly"), (8, "Aaliyah Puglia"), (9, "Patt Cannaday"),
               (16, "Brady Booker"), (17, "Angelica Loblack")],
    "Will":   [(2, "Danny Kilby"), (7, "Jenna Doore"), (10, "Ori Jean-Charles"),
               (15, "Sharonda Cox"), (18, "Ana Sani")],
    "Cagney": [(3, "Alexis Levine"), (6, "Eric Macksoud"), (11, "Rob Antonson"),
               (14, "Kristin Flickinger"), (19, "Devin Way")],
    "Mike":   [(4, "Carter Krull"), (5, "Mike Pinsky"), (12, "Maggie Nestor"),
               (13, "Linnea Capobianco"), (20, "Thien An Nguyen")],
}
UNDRAFTED = ["Cristian Chavez"]

# Starting tribes, episode 1.
TOKA_START = ["Aaliyah Puglia", "Thien An Nguyen", "Angelica Loblack", "Brady Booker",
              "Danny Kilby", "Devin Way", "Jenna Doore", "Maggie Nestor", "Mike Pinsky",
              "Patt Cannaday", "Lewis Kelly"]
SAVU_START = ["Alexis Levine", "Ana Sani", "Carter Krull", "Cristian Chavez",
              "Eric Macksoud", "Kristin Flickinger", "Linnea Capobianco",
              "Ori Jean-Charles", "Rob Antonson", "Sharonda Cox"]

# Episode 3: Carter missed the boat back from his visit and joined Toka.
# Devin visited Savu, found an extra vote, and returned to Toka (no change).
MOVED = {"Carter Krull": ("Savu", "Toka")}

# How each departure happened, and which episode.
GONE = {
    "Aaliyah Puglia":  (1, "voted out"),
    "Ana Sani":        (2, "voted out"),
    "Rob Antonson":    (3, "quit"),
    "Patt Cannaday":   (3, "voted out"),
}
LOST_IMMUNITY = {1: "Toka", 2: "Savu", 3: "Toka"}

# Advantages known to be in play at the end of episode 3.
ADVANTAGES = {
    "Angelica Loblack": "hidden immunity idol (found ep 2)",
    "Carter Krull":     "hidden immunity idol (Rob's, never played)",
    "Maggie Nestor":    "advantage found in Carter's bag (shared with Brady Booker)",
    "Devin Way":        "secret extra vote (found on the Savu visit)",
}

tribe = {n: "Toka" for n in TOKA_START}
tribe.update({n: "Savu" for n in SAVU_START})

drafted = [n for picks in DRAFT.values() for _, n in picks]
everyone = drafted + UNDRAFTED
owner = {n: w for w, picks in DRAFT.items() for _, n in picks}
owner.update({n: "undrafted" for n in UNDRAFTED})

assert len(TOKA_START) == 11 and len(SAVU_START) == 10
assert not set(TOKA_START) & set(SAVU_START), "castaway on both tribes"
assert len(everyone) == 21 == len(set(everyone)), "roster is not 21 unique"
assert sorted(tribe) == sorted(everyone), "tribe lists do not match the cast"
assert set(GONE) <= set(everyone) and set(ADVANTAGES) <= set(everyone)

for n, (frm, to) in MOVED.items():
    assert tribe[n] == frm, f"{n} was not on {frm}"
    tribe[n] = to

# A voted-out castaway must have been on the tribe that LOST immunity that week.
# A quit is not bound by that, so it is exempt.
for n, (ep, how) in GONE.items():
    if how == "voted out":
        assert tribe[n] == LOST_IMMUNITY[ep], f"{n} voted out of the tribe that WON ep {ep}"

out = set(GONE)
alive = [n for n in everyone if n not in out]
assert len(alive) == 21 - len(out)

print(f"{'drafter':8} {'left':>4} {'Savu':>5} {'Toka':>5}   roster")
print("-" * 92)
for who, picks in DRAFT.items():
    liv = [n for _, n in picks if n not in out]
    print(f"{who:8} {len(liv):>4} "
          f"{sum(1 for n in liv if tribe[n]=='Savu'):>5} "
          f"{sum(1 for n in liv if tribe[n]=='Toka'):>5}   "
          + ", ".join(f"{n} ({'X' if n in out else tribe[n][0]})" for _, n in picks))

print()
for t in ("Savu", "Toka"):
    liv = sorted(n for n in alive if tribe[n] == t)
    print(f"{t} ({len(liv)}): " + ", ".join(f"{n}/{owner[n][:3]}" for n in liv))
print(f"\nstill in the game: {len(alive)}   (gone: {len(out)})")

print("\ndepartures:")
for n, (ep, how) in sorted(GONE.items(), key=lambda kv: kv[1][0]):
    print(f"  ep{ep}  {n:18} {how:10} ({owner[n]})")

print("\nadvantages in play:")
for n, what in ADVANTAGES.items():
    assert n not in out, f"{n} holds an advantage but is out of the game"
    print(f"  {owner[n]:9} {n:18} {what}")
by_owner = {}
for n in ADVANTAGES:
    by_owner[owner[n]] = by_owner.get(owner[n], 0) + 1
print("  by drafter: " + ", ".join(f"{w} {c}" for w, c in sorted(by_owner.items())))

untouched = [w for w, picks in DRAFT.items() if not any(n in out for _, n in picks)]
print(f"\ndrafters who have lost nobody: {untouched or 'none'}")
