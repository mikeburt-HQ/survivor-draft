"""Map the Survivor 51 draft onto the episode-1 tribe split. Read-only."""

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

# Paramount+ episode-1 recap (CBS-owned) + Wikipedia for Lewis Kelly, who was
# exiled before the tribe assignments were announced on screen.
TOKA = ["Aaliyah Puglia", "Thien An Nguyen", "Angelica Loblack", "Brady Booker",
        "Danny Kilby", "Devin Way", "Jenna Doore", "Maggie Nestor", "Mike Pinsky",
        "Patt Cannaday", "Lewis Kelly"]
SAVU = ["Alexis Levine", "Ana Sani", "Carter Krull", "Cristian Chavez",
        "Eric Macksoud", "Kristin Flickinger", "Linnea Capobianco",
        "Ori Jean-Charles", "Rob Antonson", "Sharonda Cox"]

VOTED_OUT = ["Aaliyah Puglia"]

tribe = {n: "Toka" for n in TOKA}
tribe.update({n: "Savu" for n in SAVU})

drafted = [n for picks in DRAFT.values() for _, n in picks]
everyone = drafted + UNDRAFTED

assert len(TOKA) == 11 and len(SAVU) == 10, (len(TOKA), len(SAVU))
assert len(set(TOKA) & set(SAVU)) == 0, "castaway on both tribes"
assert len(everyone) == 21 and len(set(everyone)) == 21, "roster is not 21 unique"
missing = sorted(set(everyone) - set(tribe))
extra = sorted(set(tribe) - set(everyone))
assert not missing and not extra, f"missing={missing} extra={extra}"

print(f"{'drafter':8} {'Savu':>5} {'Toka':>5}  {'left':>4}  roster")
print("-" * 72)
for who, picks in DRAFT.items():
    t = [tribe[n] for _, n in picks]
    out = [n for _, n in picks if n in VOTED_OUT]
    print(f"{who:8} {t.count('Savu'):>5} {t.count('Toka'):>5}  "
          f"{len(picks) - len(out):>4}  "
          + ", ".join(f"{n} ({tribe[n][0]})" for _, n in picks))
    if out:
        print(f"{'':8} {'':5} {'':5}  {'':4}  OUT: {', '.join(out)}")

print()
for t in ("Savu", "Toka"):
    by = {w: sum(1 for _, n in p if tribe[n] == t) for w, p in DRAFT.items()}
    un = sum(1 for n in UNDRAFTED if tribe[n] == t)
    total = sum(by.values()) + un
    print(f"{t}: " + ", ".join(f"{w} {c}" for w, c in by.items())
          + f", undrafted {un}  = {total}")

sweeps = [w for w, p in DRAFT.items() if len({tribe[n] for _, n in p}) == 1]
print(f"\nrosters entirely on ONE tribe: {sweeps or 'none'}")
for w in sweeps:
    print(f"  {w}: all 5 on {tribe[DRAFT[w][0][1]]}")
