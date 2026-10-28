"""Map the Survivor 51 draft onto the state after episode 5. Read-only except
for the SQL it writes.

Episode 5 ("Not Here to Get a Pedicure", aired 2026-10-21, days 9-10) was a
DOUBLE elimination: Toka won immunity, and both Savu and Dina went to Tribal
Council. Alexis Levine left Savu and Linnea Capobianco left Dina.

No swap, merge or tribe dissolution happened, so the rosters are the episode-4
post-swap tribes minus the two eliminated.

Corroborated by Wikipedia's episode table and summary, Yahoo's recap, Inside
Survivor, Surviving Tribal and DK Network.

Deliberately OMITTED, because sources disagree or cannot be settled:
  - WHO took the single vote at Savu. Yahoo alone says Alexis voted for Devin;
    no other source names a recipient, so it is carried as unattributed. The
    3-1 SPLIT itself is three-source (Wikipedia, Yahoo, Inside Survivor).
    Surviving Tribal calls the Savu vote unanimous -- it is the lone dissenter,
    exactly as it was on episode 4, where it was wrong.
  - the REVOTE tally at Dina. Yahoo and Surviving Tribal both print a second
    4-4 tie, which cannot be right: a revote excludes the two tied castaways,
    leaving four voters, and extra votes do not carry into it. So the revote is
    reported as a deadlock with no number.
  - the final consensus round's tally. Every source agrees Kilby held for Lewis
    while Eric, Sharonda and Cristian came across to Linnea, and that no rocks
    were drawn -- but a rule requiring unanimity cannot produce a 3-1, so the
    mechanism is described without a count.
Deliberately EXCLUDED as unaired: anything from episode 6, which airs tonight.

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

# --- tribes: the episode-4 swap rosters, unchanged in episode 5 ------------
# Jenna Doore (out ep 4), Alexis Levine and Linnea Capobianco (both out ep 5)
# are still listed here because TRIBES is the membership, not the survivors.
TRIBES = {
    "Toka (Yellow)": ["Mike Pinsky", "Carter Krull", "Brady Booker",
                      "Thien An Nguyen", "Maggie Nestor", "Kristin Flickinger"],
    "Savu (Purple)": ["Devin Way", 'Angelica "Jelly" Loblack', "Ori Jean-Charles",
                      "Alexis Levine", "Jenna Doore"],
    "Dina (Red)":    ["Danny Kilby", "Lewis Kelly", "Sharonda Cox",
                      "Eric Macksoud", "Linnea Capobianco", "Cristian Chavez"],
}

# Tribes that went to Tribal Council, per episode. Episode 5 sent TWO.
WENT_TO_TRIBAL = {1: ["Toka"], 2: ["Savu"], 3: ["Toka"], 4: ["Savu"],
                  5: ["Savu", "Dina"]}

GONE = {
    "Aaliyah Puglia":     (1, "voted out"),
    "Ana Sani":           (2, "voted out"),
    "Rob Antonson":       (3, "quit"),
    "Patt Cannaday":      (3, "voted out"),
    "Jenna Doore":        (4, "voted out"),
    "Alexis Levine":      (5, "voted out"),
    "Linnea Capobianco":  (5, "voted out"),
}

# Episode 5's two tribals. `members` is who attended; `extra_votes` is the
# number of ADDITIONAL ballots played, so ballots = members + extra_votes.
EP5_TRIBALS = [
    {"tribe": "Savu (Purple)", "members": 4, "extra_votes": 0,
     "votes": {"Alexis Levine": 3}, "unattributed": 1,
     "out": "Alexis Levine"},
    {"tribe": "Dina (Red)", "members": 6, "extra_votes": 2,
     "votes": {"Linnea Capobianco": 4, "Lewis Kelly": 4}, "unattributed": 0,
     "out": "Linnea Capobianco"},
]

# Advantages still in play AFTER episode 5.
ADVANTAGES = {
    'Angelica "Jelly" Loblack': "hidden immunity idol (found ep 2, carried through "
                                "two Tribals unplayed)",
    "Carter Krull":             "hidden immunity idol (Rob's, never played)",
    "Devin Way":                "secret extra vote (found on the Savu visit, ep 3, "
                                "still unplayed)",
}

# Advantages SPENT in episode 5, tracked so the page cannot keep listing them.
SPENT = {
    "Maggie Nestor": "gave both of her extra votes away on the journey to Dina, "
                     "to Danny Kilby and Lewis Kelly, naming Linnea Capobianco "
                     "as the target",
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

# --- the tribes must partition everyone still in at the episode-4 swap -----
out = set(GONE)
gone_before_swap = {n for n, (ep, _) in GONE.items() if ep < 4}
at_swap = [n for n in everyone if n not in gone_before_swap]
alive = [n for n in everyone if n not in out]
placed = [n for roster in TRIBES.values() for n in roster]

assert len(placed) == len(set(placed)), "a castaway appears on two tribes"
assert set(placed) == set(at_swap), (
    f"tribes do not partition the castaways in the game at the swap; "
    f"on a tribe but already out: {sorted(set(placed) & gone_before_swap)}; "
    f"in the game but unplaced: {sorted(set(at_swap) - set(placed))}"
)
assert len(at_swap) == 17, f"{len(at_swap)} in the game at the swap, expected 17"
assert len(alive) == 21 - len(out) == 14, f"{len(alive)} alive, expected 14"

tribe = {n: t for t, roster in TRIBES.items() for n in roster}

# A voted-out castaway must have been on a tribe that WENT to Tribal that week.
# Only episodes 4 and 5 are testable against the post-swap rosters; earlier
# episodes pre-date the swap. A quit is exempt.
for n, (ep, how) in GONE.items():
    if how == "voted out" and ep >= 4:
        assert any(tribe.get(n, "").startswith(t) for t in WENT_TO_TRIBAL[ep]), \
            f"{n} voted out in ep {ep} from a tribe that did not go to Tribal"

for n in ADVANTAGES:
    assert n not in out, f"{n} holds an advantage but is out of the game"
for n in SPENT:
    assert n in everyone, f"{n} is not on the roster"

# --- gate episode 5's two tribals on their own ballot arithmetic -----------
ep5_out = set()
for t in EP5_TRIBALS:
    ballots = t["members"] + t["extra_votes"]
    counted = sum(t["votes"].values()) + t["unattributed"]
    assert counted == ballots, (
        f"{t['tribe']}: tally accounts for {counted} ballots but "
        f"{t['members']} members + {t['extra_votes']} extra votes = {ballots}"
    )
    for n in t["votes"]:
        assert n in TRIBES[t["tribe"]], f"{n} took votes but was not on {t['tribe']}"
    booted = t["out"]
    assert booted in t["votes"], f"{booted} left but took no votes"
    top = max(t["votes"].values())
    assert t["votes"][booted] == top, f"{booted} left without the most votes"
    assert GONE[booted] == (5, "voted out"), f"{booted} is not an ep-5 boot"
    ep5_out.add(booted)
    # The tribe that lost someone must be one that went to Tribal.
    assert any(t["tribe"].startswith(x) for x in WENT_TO_TRIBAL[5])

assert ep5_out == {n for n, (ep, how) in GONE.items() if ep == 5}, \
    "the ep-5 tribals and the GONE list disagree on who left"
assert len(ep5_out) == 2, f"episode 5 was a double elimination, got {len(ep5_out)}"

# Savu played no extra vote, which is what proves Devin's is still in hand.
savu = next(t for t in EP5_TRIBALS if t["tribe"].startswith("Savu"))
assert savu["extra_votes"] == 0, "Savu played an extra vote"
assert "Devin Way" in ADVANTAGES, "Devin's extra vote should still be in play"

# --- derived, never recalled ----------------------------------------------
voted_out_order = [n for n, (ep, how) in sorted(
    GONE.items(), key=lambda kv: (kv[1][0], kv[0])) if how == "voted out"]
place = {n: i + 1 for i, n in enumerate(voted_out_order)}

def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


# Which of the two left FIRST is an on-screen sequencing claim, not a fact the
# data carries, so it is not stated here or on the page.
print(f"Episode 5 was a double elimination: "
      f"{len(out)} of 21 are now gone, {len(alive)} still in.")
for n in sorted(ep5_out, key=lambda n: place[n]):
    print(f"  {n:22} ({owner[n]:6}) -- {ordinal(place[n])} voted out")
quits = [n for n, (_, how) in GONE.items() if how == "quit"]
print(f"  voted out: {len(voted_out_order)}   quit: {len(quits)}   "
      f"total gone: {len(out)}")

print(f"\n{'drafter':8} {'left':>4}  roster (T=Toka, S=Savu, D=Dina, X=out)")
print("-" * 104)
order = []
for who, picks in DRAFT.items():
    liv = [n for _, n in picks if n not in out]
    order.append((len(liv), who))
    cells = ", ".join(
        f"{n} ({'X' if n in out else tribe[n][0]})" for _, n in picks)
    print(f"{who:8} {len(liv):>4}  {cells}")

standings = sorted(order, key=lambda cw: (-cw[0], cw[1]))
print("\nstandings: " + ", ".join(f"{w} {c}" for c, w in standings))

lead = standings[0][0]
tied_at_top = [w for c, w in standings if c == lead]
chasing = sorted({c for c, _ in standings if c != lead})
print(f"leader(s): {tied_at_top} on {lead}; "
      f"everyone else on {chasing}")

print()
for t, roster in TRIBES.items():
    liv = sorted(n for n in roster if n not in out)
    print(f"{t:14} ({len(liv)}): " + ", ".join(f"{n}/{owner[n][:3]}" for n in liv))

print("\nwho owns each tribe:")
for t, roster in TRIBES.items():
    counts = {}
    for n in roster:
        if n not in out:
            counts[owner[n]] = counts.get(owner[n], 0) + 1
    print(f"  {t:14} " + ", ".join(
        f"{w} {c}" for w, c in sorted(counts.items(), key=lambda wc: (-wc[1], wc[0]))))

print("\nepisode 5 tribals:")
for t in EP5_TRIBALS:
    ballots = t["members"] + t["extra_votes"]
    tally = " / ".join(f"{n} {v}" for n, v in
                       sorted(t["votes"].items(), key=lambda kv: -kv[1]))
    if t["unattributed"]:
        tally += f" / {t['unattributed']} unattributed"
    print(f"  {t['tribe']:14} {t['members']} members + {t['extra_votes']} extra "
          f"= {ballots} ballots -> {tally}")
    print(f"  {'':14} out: {t['out']} ({owner[t['out']]})")

print("\ndepartures:")
for n, (ep, how) in sorted(GONE.items(), key=lambda kv: (kv[1][0], kv[0])):
    tag = f"{ordinal(place[n])} voted out" if how == "voted out" else "quit"
    print(f"  ep{ep}  {n:22} {tag:16} ({owner[n]})")

print("\nadvantages still in play:")
for n, what in ADVANTAGES.items():
    print(f"  {owner[n]:9} {n:26} {what}")
print("spent in episode 5:")
for n, what in SPENT.items():
    print(f"  {owner[n]:9} {n:26} {what}")

untouched = [w for w, picks in DRAFT.items() if not any(n in out for _, n in picks)]
print(f"\ndrafters who have lost nobody: {untouched or 'none'}")

# The headline claim, derived rather than asserted: Maggie and Linnea share an
# owner, so one drafter's castaway armed the vote that took out their own.
maggie, linnea = "Maggie Nestor", "Linnea Capobianco"
assert owner[maggie] == owner[linnea], \
    "the headline needs Maggie and Linnea to share a drafter"
print(f"\nheadline check: {maggie} and {linnea} are both {owner[maggie]}'s, "
      f"and {linnea} is {owner[linnea]}'s first loss in five episodes.")

undrafted_alive = [n for n in UNDRAFTED if n not in out]
print(f"undrafted still in: {undrafted_alive}; "
      f"they have now outlasted {len(out)} drafted castaways.")

# --- SQL for the live board (idempotent, covers all 21) -------------------
sql = ["-- Tribe state after Survivor 51 episode 5 (double elimination).",
       "-- Generated by recaps/week5_map.py. Safe to re-run.",
       "-- SUPERSEDES tribes-after-ep3.sql and tribes-after-ep4.sql: this file",
       "-- sets all 21 rows, so it is correct whether or not those ever ran.",
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
assert touched == len(alive) == 14, f"SQL tribes {touched} rows, expected 14"
assert total == 21, f"SQL touches {total} rows, not 21"

(ROOT / "supabase" / "tribes-after-ep5.sql").write_text("\n".join(sql), encoding="utf-8")
print(f"\nwrote supabase/tribes-after-ep5.sql ({total} rows touched)")
