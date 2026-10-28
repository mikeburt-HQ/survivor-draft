"""Map the Survivor 51 draft onto the state after episode 4. Read-only.

Episode 4 ("That's the Magic of Survivor", aired 2026-10-14) split the two
starting tribes into THREE. Tribe rosters below are corroborated by three
independent sources (Paramount+, TVLine, Inside Survivor) which agree exactly.

Deliberately OMITTED, because sources disagree:
  - the vote count. TVLine says 4-1, Inside Survivor and Surviving Tribal say
    unanimous, Paramount+ says Jenna 3 / Alexis 1. Three answers, so no count.
Nothing is omitted on the idol front any more. SETTLED 2026-10-28 by Mike,
who watched it, after this file got it wrong TWICE:

  The baby-whale idol was SECOND PLACE'S IMMUNITY TOKEN. Three tribes and one
  Tribal Council, so the top two finishers were both safe. Dina took first (a
  coffee kit); Toka took second, and second place's immunity arrived as the
  baby-whale idol plus a pitcher of iced coffee. It meant Toka skipped that
  week's vote. It was spent on the night and nobody retained it, so it is NOT
  an advantage in play and must never appear in a holders table.

  Wrong version 1 (shipped, two weeks): "the mini-whale idol handed to the
  second-place tribe: only one source mentions it and does not confirm who
  received it" -- treated a spent tribe token as retained hardware with an
  unknown owner.
  Wrong version 2 (shipped for an hour): "the season's second hidden immunity
  idol ... nothing says where it is hidden or that anyone has found it" --
  read Yahoo's "the second immunity idol for the season is a baby whale" as
  the second HIDDEN idol, when it meant the idol for SECOND PLACE. Every
  source fits the right reading: Paramount+ calls it "a mini-whale idol
  introduced for the second-place winners", and one recap says second place
  won "iced coffee and safety from the upcoming vote".
Deliberately EXCLUDED as unaired: the "Blood Ring" teased for a later episode.

Names are the exact `players.name` spellings from supabase/seed.sql, so the
generated SQL cannot silently match zero rows.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEED = ROOT / "supabase" / "seed.sql"

# --- the draft (complete, verified against the live board in week 1) --------
DRAFT = {
    "Daron":  [(1, "Lewis Kelly"), (8, "Aaliyah Puglia"), (9, "Patt Cannaday"),
               (16, "Brady Booker"), (17, 'Angelica "Jelly" Loblack')],
    "Will":   [(2, "Danny Kilby"), (7, "Jenna Doore"), (10, "Ori Jean-Charles"),
               (15, "Sharonda Cox"), (18, "Ana Sani")],
    "Cagney": [(3, "Alexis Levine"), (6, "Eric Macksoud"), (11, "Rob Antonson"),
               (14, "Kristin Flickinger"), (19, "Devin Way")],
    "Mike":   [(4, "Carter Krull"), (5, "Mike Pinsky"), (12, "Maggie Nestor"),
               (13, "Linnea Capobianco"), (20, "Thien An Nguyen")],
}
UNDRAFTED = ["Cristian Chavez"]

# --- tribes AFTER the episode-4 swap ---------------------------------------
TRIBES = {
    "Toka (Yellow)": ["Mike Pinsky", "Carter Krull", "Brady Booker",
                      "Thien An Nguyen", "Maggie Nestor", "Kristin Flickinger"],
    "Savu (Purple)": ["Devin Way", 'Angelica "Jelly" Loblack', "Ori Jean-Charles",
                      "Alexis Levine", "Jenna Doore"],
    "Dina (Red)":    ["Danny Kilby", "Lewis Kelly", "Sharonda Cox",
                      "Eric Macksoud", "Linnea Capobianco", "Cristian Chavez"],
}

# Episode 4 challenge: Dina first, Toka second, Savu last -> tribal council.
LOST_IMMUNITY = {1: "Toka", 2: "Savu", 3: "Toka", 4: "Savu"}

GONE = {
    "Aaliyah Puglia":  (1, "voted out"),
    "Ana Sani":        (2, "voted out"),
    "Rob Antonson":    (3, "quit"),
    "Patt Cannaday":   (3, "voted out"),
    "Jenna Doore":     (4, "voted out"),
}

ADVANTAGES = {
    'Angelica "Jelly" Loblack': "hidden immunity idol (found ep 2, still unplayed)",
    "Carter Krull":             "hidden immunity idol (Rob's, never played)",
    "Maggie Nestor":            "advantage found in Carter's bag (shared with Brady Booker)",
    "Devin Way":                "secret extra vote (found on the Savu visit, ep 3)",
}

# --- bind every name to the database's own spelling ------------------------
seed_names = set(re.findall(r"^\(\d+,\s+'(.+?)',", SEED.read_text(), re.M))
assert len(seed_names) == 21, f"seed.sql yielded {len(seed_names)} names, expected 21"

drafted = [n for picks in DRAFT.values() for _, n in picks]
everyone = drafted + UNDRAFTED
owner = {n: w for w, picks in DRAFT.items() for _, n in picks}
owner.update({n: "undrafted" for n in UNDRAFTED})

assert len(everyone) == 21 == len(set(everyone)), "roster is not 21 unique"
unknown = sorted(set(everyone) - seed_names)
assert not unknown, f"names absent from seed.sql (would match 0 rows): {unknown}"

# --- the swap must partition exactly the survivors -------------------------
# TRIBES is the state AT the swap, which is BEFORE episode 4's tribal council,
# so it still contains Jenna. Two distinct moments, kept separate on purpose.
out = set(GONE)
gone_before_ep4 = {n for n, (ep, _) in GONE.items() if ep < 4}
at_swap = [n for n in everyone if n not in gone_before_ep4]
alive = [n for n in everyone if n not in out]
placed = [n for roster in TRIBES.values() for n in roster]

assert len(placed) == len(set(placed)), "a castaway appears on two tribes"
assert set(placed) == set(at_swap), (
    f"tribes do not partition the castaways in the game at the swap; "
    f"on a tribe but already out: {sorted(set(placed) & gone_before_ep4)}; "
    f"in the game but unplaced: {sorted(set(at_swap) - set(placed))}"
)
assert len(at_swap) == 17, f"{len(at_swap)} in the game at the swap, expected 17"
assert len(alive) == 21 - len(out) == 16

tribe = {n: t for t, roster in TRIBES.items() for n in roster}

# A voted-out castaway must have been on the tribe that LOST immunity. For
# episode 4 that is testable against the post-swap tribes; earlier episodes
# pre-date the swap, so only ep 4 is checked here. A quit is exempt.
for n, (ep, how) in GONE.items():
    if how == "voted out" and ep == 4:
        assert tribe.get(n, "").startswith(LOST_IMMUNITY[ep]), \
            f"{n} voted out of a tribe that did not lose immunity in ep {ep}"
assert "Jenna Doore" in out and "Jenna Doore" in TRIBES["Savu (Purple)"]

for n in ADVANTAGES:
    assert n not in out, f"{n} holds an advantage but is out of the game"

# Derived, never recalled: Rob quit, so "voted out" and "gone" differ by one.
voted_out = sum(1 for _, (_, how) in GONE.items() if how == "voted out")
print(f"Jenna Doore is the {voted_out}th person VOTED OUT "
      f"and the {len(out)}th to LEAVE (Rob quit).")

print(f"\n{'drafter':8} {'left':>4}  roster (T=Toka, S=Savu, D=Dina, X=out)")
print("-" * 100)
order = []
for who, picks in DRAFT.items():
    liv = [n for _, n in picks if n not in out]
    order.append((len(liv), who))
    cells = ", ".join(
        f"{n} ({'X' if n in out else tribe[n][0]})" for _, n in picks
    )
    print(f"{who:8} {len(liv):>4}  {cells}")

print("\nstandings: " + ", ".join(
    f"{w} {c}" for c, w in sorted(order, key=lambda cw: (-cw[0], cw[1]))
))

print()
for t, roster in TRIBES.items():
    liv = sorted(n for n in roster if n not in out)
    print(f"{t:14} ({len(liv)}): " + ", ".join(f"{n}/{owner[n][:3]}" for n in liv))

by_tribe_owner = {}
for t, roster in TRIBES.items():
    for n in roster:
        if n not in out:
            by_tribe_owner.setdefault(t, {}).setdefault(owner[n], 0)
            by_tribe_owner[t][owner[n]] += 1
print("\nwho owns each tribe:")
for t, counts in by_tribe_owner.items():
    print(f"  {t:14} " + ", ".join(
        f"{w} {c}" for w, c in sorted(counts.items(), key=lambda wc: -wc[1])
    ))

print("\ndepartures:")
for n, (ep, how) in sorted(GONE.items(), key=lambda kv: kv[1][0]):
    print(f"  ep{ep}  {n:26} {how:10} ({owner[n]})")

print("\nadvantages in play:")
for n, what in ADVANTAGES.items():
    print(f"  {owner[n]:9} {n:26} {what}")

untouched = [w for w, picks in DRAFT.items() if not any(n in out for _, n in picks)]
print(f"\ndrafters who have lost nobody: {untouched or 'none'}")

# --- SQL for the live board (idempotent, covers all 21) -------------------
sql = ["-- Tribe state after Survivor 51 episode 4 (three tribes).",
       "-- Generated by recaps/week4_map.py. Safe to re-run.",
       "-- Names are exact players.name spellings, asserted against seed.sql.",
       "-- Labels MUST carry the colour word or getTribeColor() falls back to grey.",
       ""]
touched = 0
for t, roster in TRIBES.items():
    still_in = sorted(n for n in roster if n not in out)
    names = ",\n  ".join("'" + n.replace("'", "''") + "'" for n in still_in)
    sql.append(f"UPDATE players SET tribe = '{t}' WHERE name IN (\n  {names}\n);"
               f"  -- {len(still_in)} rows")
    sql.append("")
    touched += len(still_in)
eliminated = sorted(out)
names = ",\n  ".join("'" + n.replace("'", "''") + "'" for n in eliminated)
sql.append("-- Out of the game: tribe cleared so the board shows them unassigned.")
sql.append(f"UPDATE players SET tribe = NULL WHERE name IN (\n  {names}\n);"
           f"  -- {len(eliminated)} rows")
sql.append("")

total = touched + len(eliminated)
assert touched == 16, f"SQL tribes {touched} rows, expected 16 survivors"
assert total == 21, f"SQL touches {total} rows, not 21"

(ROOT / "supabase" / "tribes-after-ep4.sql").write_text("\n".join(sql), encoding="utf-8")
print(f"\nwrote supabase/tribes-after-ep4.sql ({total} rows touched)")
