"""Map the Survivor 51 draft onto the state after episode 2. Read-only.

Extends week1_map.py. Roster is the draft as verified against the live app in
week 1 (the draft is complete, so it cannot change); tribes and eliminations are
from the Paramount+ episode recaps.
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

# Unchanged after episode 2 — no swap. Lewis Kelly returned from Exile to Toka.
TOKA = ["Aaliyah Puglia", "Thien An Nguyen", "Angelica Loblack", "Brady Booker",
        "Danny Kilby", "Devin Way", "Jenna Doore", "Maggie Nestor", "Mike Pinsky",
        "Patt Cannaday", "Lewis Kelly"]
SAVU = ["Alexis Levine", "Ana Sani", "Carter Krull", "Cristian Chavez",
        "Eric Macksoud", "Kristin Flickinger", "Linnea Capobianco",
        "Ori Jean-Charles", "Rob Antonson", "Sharonda Cox"]

VOTED_OUT = {"Aaliyah Puglia": 1, "Ana Sani": 2}   # name -> episode
LOST_IMMUNITY = {1: "Toka", 2: "Savu"}

tribe = {n: "Toka" for n in TOKA}
tribe.update({n: "Savu" for n in SAVU})

drafted = [n for picks in DRAFT.values() for _, n in picks]
everyone = drafted + UNDRAFTED

assert len(TOKA) == 11 and len(SAVU) == 10, (len(TOKA), len(SAVU))
assert not set(TOKA) & set(SAVU), "castaway on both tribes"
assert len(everyone) == 21 == len(set(everyone)), "roster is not 21 unique"
missing, extra = sorted(set(everyone) - set(tribe)), sorted(set(tribe) - set(everyone))
assert not missing and not extra, f"missing={missing} extra={extra}"
assert set(VOTED_OUT) <= set(everyone), "voted-out name not in the cast"
for n, ep in VOTED_OUT.items():
    assert tribe[n] == LOST_IMMUNITY[ep], f"{n} voted out of the tribe that WON ep {ep}"

out = set(VOTED_OUT)
print(f"{'drafter':8} {'left':>4} {'Savu':>5} {'Toka':>5}   roster (S/T, X = out)")
print("-" * 86)
for who, picks in DRAFT.items():
    alive = [n for _, n in picks if n not in out]
    print(f"{who:8} {len(alive):>4} "
          f"{sum(1 for n in alive if tribe[n] == 'Savu'):>5} "
          f"{sum(1 for n in alive if tribe[n] == 'Toka'):>5}   "
          + ", ".join(f"{n} ({'X' if n in out else tribe[n][0]})" for _, n in picks))

print()
for t in ("Savu", "Toka"):
    alive = [n for n in tribe if tribe[n] == t and n not in out]
    print(f"{t}: {len(alive)} left  (started {sum(1 for n in tribe if tribe[n]==t)})")
print(f"total still in the game: {21 - len(out)}")

print("\neliminations by drafter:")
for who, picks in DRAFT.items():
    gone = [(VOTED_OUT[n], n) for _, n in picks if n in out]
    print(f"  {who:8} {len(gone)}  " + (", ".join(f"ep{e} {n}" for e, n in sorted(gone)) or "-"))
un_out = [n for n in UNDRAFTED if n in out]
print(f"  {'undrafted':8} {len(un_out)}  " + (", ".join(un_out) or "-"))
