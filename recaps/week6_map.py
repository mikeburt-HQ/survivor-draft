"""Map the Survivor 51 draft onto the state after episode 6. Read-only except
for the SQL it writes.

Episode 6 ("I Love Crying", aired 2026-10-28, days 10-12): Toka and Dina both
won immunity, Savu lost its third challenge in a row and went to its third
Tribal Council. Ori Jean-Charles was voted out, the 7th voted out and the 8th
to leave. Savu is down to TWO people.

No swap, merge or tribe dissolution, so the rosters are the episode-4 post-swap
tribes minus the four eliminated since.

Corroborated by Wikipedia's episode table and summary, TVLine, Yahoo's results
piece, DK Network and Primetimer.

THE VOTE, and why 2-0 and "unanimous" are the same claim:
  Three people attended (Devin, Jelly, Ori) and only TWO ballots were cast,
  because Ori played a Shot in the Dark, drew Not Safe, and forfeited that
  night's vote. Both ballots carried Ori's name. So Wikipedia's episode table
  (2-0) and its summary text ("unanimously") are both right and describe the
  same tally -- the apparent conflict is an artifact of counting the forfeited
  ballot or not. The forfeit rule is the same one that made episode 1 eight
  ballots from ten people, and it is gated below on ballot arithmetic.

THE TETHERED IDOL, the episode's new advantage. Three sources agree (TVLine,
Yahoo, DK Network) on all four clauses:
  - Kristin Flickinger holds it, won by volunteering for Exile at the summit.
  - Only Kristin may play it.
  - It may be played only ON Ori Jean-Charles or Sharonda Cox -- never on
    Kristin.
  - If BOTH of those two are voted out while it is still in play, it becomes a
    normal hidden immunity idol playable on anybody, Kristin included.

Pronouns: no castaway's pronouns have been stated to us, so every castaway is
they/them here and on the page, and the Tethered Idol's rules are written
around the pronoun rather than with one. Published recaps use she/her for
Kristin; third-party press is not a statement of pronouns, and this repo has
already shipped a gendered-pronoun error publicly once.
  Ori went out the same night, so one of the two beneficiaries is already gone
  and Sharonda is the only person alive Kristin can spend it on.

Deliberately OMITTED, because sources disagree or cannot be settled:
  - WHICH of Toka and Dina placed first. Wikipedia's season summary says Dina
    first and Toka second; its episode table names Toka the immunity winner;
    another outlet has Toka first and Dina second. Three readings, so the page
    says both were safe and does not rank them.
  - any REWARD for finishing. Wikipedia's episode table prints "None" while its
    general season description has a standing coffee kit for first and iced
    coffee for second. Unresolved for this episode, so no reward is claimed.
  - a DEADLINE on the Tethered Idol. One source alone adds that Kristin must
    use it by the final five; the other three state no deadline. Single-source,
    so it is not reported.
Deliberately EXCLUDED as unaired: anything from episode 7.

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

# --- tribes: the episode-4 swap rosters, unchanged in episodes 5 and 6 -----
# TRIBES is MEMBERSHIP, not survivors, so the eliminated are still listed.
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
                  5: ["Savu", "Dina"], 6: ["Savu"]}

GONE = {
    "Aaliyah Puglia":     (1, "voted out"),
    "Ana Sani":           (2, "voted out"),
    "Rob Antonson":       (3, "quit"),
    "Patt Cannaday":      (3, "voted out"),
    "Jenna Doore":        (4, "voted out"),
    "Alexis Levine":      (5, "voted out"),
    "Linnea Capobianco":  (5, "voted out"),
    "Ori Jean-Charles":   (6, "voted out"),
}

# Episode 6's single tribal. `members` is who attended; `no_vote` names those
# who attended but cast no ballot, so ballots = members - no_vote + extra.
EP6_TRIBAL = {
    "tribe": "Savu (Purple)", "members": 3, "extra_votes": 0,
    "no_vote": ["Ori Jean-Charles"],
    "votes": {"Ori Jean-Charles": 2}, "unattributed": 0,
    "out": "Ori Jean-Charles",
}

# The Tethered Idol's only legal beneficiaries, in source order.
TETHERED_HOLDER = "Kristin Flickinger"
TETHERED_ON = ["Ori Jean-Charles", "Sharonda Cox"]

# Advantages still in play AFTER episode 6.
ADVANTAGES = {
    'Angelica "Jelly" Loblack': "hidden immunity idol (found ep 2; revealed it at "
                                "the ep-6 vote but did not play it)",
    "Carter Krull":             "hidden immunity idol (Rob's, never played)",
    "Devin Way":                "secret extra vote (found on the Savu visit, ep 3, "
                                "still unplayed)",
    TETHERED_HOLDER:            "Tethered Idol (ep 6; playable only on "
                                "Sharonda Cox, never on Kristin)",
}

# Advantages SPENT in episode 5, kept so the page cannot keep listing them.
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
assert len(alive) == 21 - len(out) == 13, f"{len(alive)} alive, expected 13"

tribe = {n: t for t, roster in TRIBES.items() for n in roster}

# A voted-out castaway must have been on a tribe that WENT to Tribal that week.
# Only episodes 4-6 are testable against the post-swap rosters; earlier
# episodes pre-date the swap. A quit is exempt.
for n, (ep, how) in GONE.items():
    if how == "voted out" and ep >= 4:
        assert any(tribe.get(n, "").startswith(t) for t in WENT_TO_TRIBAL[ep]), \
            f"{n} voted out in ep {ep} from a tribe that did not go to Tribal"

for n in ADVANTAGES:
    assert n not in out, f"{n} holds an advantage but is out of the game"
for n in SPENT:
    assert n in everyone, f"{n} is not on the roster"

# --- gate episode 6's tribal on its own ballot arithmetic -----------------
t = EP6_TRIBAL
ballots = t["members"] - len(t["no_vote"]) + t["extra_votes"]
counted = sum(t["votes"].values()) + t["unattributed"]
assert counted == ballots, (
    f"{t['tribe']}: tally accounts for {counted} ballots but {t['members']} "
    f"members - {len(t['no_vote'])} forfeited + {t['extra_votes']} extra "
    f"= {ballots}"
)
# The attendance figure must match the tribe's actual surviving population
# going into the vote, or the arithmetic above is gated against a guess.
savu_before = [n for n in TRIBES["Savu (Purple)"]
               if n not in out or GONE[n][0] == 6]
assert len(savu_before) == t["members"], (
    f"Savu had {len(savu_before)} alive going into the ep-6 vote "
    f"({sorted(savu_before)}), but the tribal says {t['members']}"
)
for n in list(t["votes"]) + t["no_vote"]:
    assert n in TRIBES[t["tribe"]], f"{n} was not on {t['tribe']}"
booted = t["out"]
assert booted in t["votes"], f"{booted} left but took no votes"
top = max(t["votes"].values())
assert t["votes"][booted] == top, f"{booted} left without the most votes"
assert t["votes"][booted] > counted / 2, f"{booted} left without a majority"
assert GONE[booted] == (6, "voted out"), f"{booted} is not an ep-6 boot"
assert {n for n, (ep, how) in GONE.items() if ep == 6} == {booted}, \
    "the ep-6 tribal and the GONE list disagree on who left"
assert any(t["tribe"].startswith(x) for x in WENT_TO_TRIBAL[6])

# Savu played no extra vote, so Devin's is still in hand.
assert t["extra_votes"] == 0, "Savu played an extra vote"
assert "Devin Way" in ADVANTAGES, "Devin's extra vote should still be in play"
# Jelly revealed an idol but did not play it, so it is still listed.
assert 'Angelica "Jelly" Loblack' in ADVANTAGES, "Jelly's idol should still be in play"

# --- the Tethered Idol, gated rather than described ----------------------
assert TETHERED_HOLDER not in TETHERED_ON, \
    "the holder cannot be her own beneficiary -- that is the whole restriction"
for n in TETHERED_ON:
    assert n in everyone, f"{n} is not on the roster"
tethered_live = [n for n in TETHERED_ON if n not in out]
tethered_dead = [n for n in TETHERED_ON if n in out]
assert tethered_dead == ["Ori Jean-Charles"], \
    f"expected Ori alone to be the gone beneficiary, got {tethered_dead}"
assert tethered_live == ["Sharonda Cox"], \
    f"expected Sharonda alone to remain playable, got {tethered_live}"
# It untethers only when EVERY beneficiary is out. One is, so it has not.
assert tethered_live, "both beneficiaries are out -- the idol has untethered"

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


print(f"{len(out)} of 21 are now gone, {len(alive)} still in.")
print(f"  {booted:22} ({owner[booted]:6}) -- {ordinal(place[booted])} voted out, "
      f"{ordinal(len(out))} to leave")
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
last = standings[-1][0]
alone_at_bottom = [w for c, w in standings if c == last]
print(f"leader(s): {tied_at_top} on {lead}; "
      f"bottom: {alone_at_bottom} on {last}")

print()
for t_name, roster in TRIBES.items():
    liv = sorted(n for n in roster if n not in out)
    print(f"{t_name:14} ({len(liv)}): " + ", ".join(f"{n}/{owner[n][:3]}" for n in liv))

print("\nwho owns each tribe:")
for t_name, roster in TRIBES.items():
    counts = {}
    for n in roster:
        if n not in out:
            counts[owner[n]] = counts.get(owner[n], 0) + 1
    print(f"  {t_name:14} " + ", ".join(
        f"{w} {c}" for w, c in sorted(counts.items(), key=lambda wc: (-wc[1], wc[0]))))

print("\nepisode 6 tribal:")
tally = " / ".join(f"{n} {v}" for n, v in
                   sorted(t["votes"].items(), key=lambda kv: -kv[1]))
print(f"  {EP6_TRIBAL['tribe']:14} {EP6_TRIBAL['members']} at tribal, "
      f"{len(EP6_TRIBAL['no_vote'])} forfeited = {ballots} ballots -> {tally}")
print(f"  {'':14} out: {booted} ({owner[booted]})")

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

# --- the headline claim, derived rather than asserted --------------------
# Kristin is Cagney's. Both people she is allowed to spend the idol on are
# Will's. That is the week's find, so it is gated, not trusted.
tethered_owners = {owner[n] for n in TETHERED_ON}
assert len(tethered_owners) == 1, (
    f"the headline needs both beneficiaries on ONE roster, got {tethered_owners}"
)
beneficiary_owner = tethered_owners.pop()
assert owner[TETHERED_HOLDER] != beneficiary_owner, (
    "the headline needs the holder and the beneficiaries on DIFFERENT rosters"
)
print(f"\nheadline check: {TETHERED_HOLDER} is {owner[TETHERED_HOLDER]}'s, and both "
      f"castaways she may play the Tethered Idol on "
      f"({', '.join(TETHERED_ON)}) are {beneficiary_owner}'s.")
print(f"  {tethered_dead[0]} went out the same night, so only "
      f"{tethered_live[0]} ({beneficiary_owner}'s) is left to spend it on.")

# Savu is two people, and they belong to two different drafters.
savu_alive = sorted(n for n in TRIBES["Savu (Purple)"] if n not in out)
assert len(savu_alive) == 2, f"Savu should be 2, got {savu_alive}"
assert len({owner[n] for n in savu_alive}) == 2, \
    "Savu's last two should belong to different drafters"
print(f"Savu is down to {len(savu_alive)}: " + ", ".join(
    f"{n} ({owner[n]})" for n in savu_alive))

# The summit sent one castaway per tribe; two of the three were Will's.
summit = [TETHERED_HOLDER] + TETHERED_ON
assert len({tribe[n] for n in summit}) == 3, \
    "the summit should have drawn one castaway from each of the three tribes"
print("summit: " + ", ".join(f"{n} ({owner[n]}, {tribe[n].split()[0]})" for n in summit))

undrafted_alive = [n for n in UNDRAFTED if n not in out]
print(f"undrafted still in: {undrafted_alive}; "
      f"they have now outlasted {len(out)} drafted castaways.")

# --- SQL for the live board (idempotent, covers all 21) -------------------
sql = ["-- Tribe state after Survivor 51 episode 6 (Ori Jean-Charles voted out).",
       "-- Generated by recaps/week6_map.py. Safe to re-run.",
       "-- SUPERSEDES tribes-after-ep3/ep4/ep5.sql: this file sets all 21 rows,",
       "-- so it is correct whether or not any of those ever ran.",
       "-- Names are exact players.name spellings, asserted against seed.sql.",
       "-- Labels MUST carry the colour word or getTribeColor() falls back to grey.",
       ""]
touched = 0
for t_name, roster in TRIBES.items():
    still_in = sorted(n for n in roster if n not in out)
    names = ",\n  ".join("'" + n.replace("'", "''") + "'" for n in still_in)
    sql.append(f"UPDATE players SET tribe = '{t_name}' WHERE name IN (\n  {names}\n);"
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
assert touched == len(alive) == 13, f"SQL tribes {touched} rows, expected 13"
assert total == 21, f"SQL touches {total} rows, not 21"

(ROOT / "supabase" / "tribes-after-ep6.sql").write_text("\n".join(sql), encoding="utf-8")
print(f"\nwrote supabase/tribes-after-ep6.sql ({total} rows touched)")
