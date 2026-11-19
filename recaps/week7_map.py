"""Map the Survivor 51 draft onto the state after episode 7. Read-only except
for the SQL it writes.

Episode 7 ("The Girl at the Prom", aired 2026-11-04, days 12-14): THE MERGE.
All thirteen castaways still in the game became one tribe, Tovuto, on day 13.
Mike Pinsky won the season's first individual immunity. Brady Booker was voted
out 9-4 over Eric Macksoud, the 8th voted out and the 9th to leave, and the
first member of the jury as of this episode.

Sources: Wikipedia's raw wikitext (episode table, contestant table and the
per-voter voting-history rows), Paramount+ (CBS's own recap), Yahoo, and DK
Network. Paramount+ and Wikipedia's voting history name the same nine voters
for Brady and the same four for Eric; that pairing is what EP7_VOTERS encodes.

The merged tribe's NAME is Wikipedia's ("Tovuto", in its episode table and
voting history) and Paramount+'s episode-8 recap ("the Tovuto Tribe (Blue)").
The buff COLOUR is from Paramount+ alone; no source disagrees with it, and the
live board needs a colour word in the label.

Merge feast: the first ten to eat two grubs ate; Kristin, Cristian and
Sharonda did not make it (Paramount+, DK, and Wikipedia's ten-name reward
list, which is the other ten). HOW each of the three missed differs between
outlets, so the page says only that they missed it.

Immunity: Mike Pinsky, Kristin and Lewis were the last three; Kristin dropped,
then Lewis. Paramount+, Yahoo and DK agree.

The Tethered Idol: Kristin handed it to Sharonda (Paramount+, Yahoo, DK).
What that handover changed about who may PLAY it is worded differently by each
outlet ("complete control", "if Sharonda were eliminated it would become an
idol Kristin could play"), so the page reports the handover and nothing about
the new rules.

Deliberately OMITTED:
  - the DK Network line "4-4 after eight votes": that is the reading order,
    not a tally, and printing it beside 9-4 would read as a conflict.
  - the episode-title quote, which only one outlet prints.
  - Paramount+'s "ninth person voted out": the same article also says eighth,
    and Rob's quit is what separates the two counts. Both are derived below.
Deliberately EXCLUDED as unaired: anything from episode 8 onward, including
Brady's later withdrawal from the jury.

Names are the exact `players.name` spellings from supabase/seed.sql, so the
generated SQL cannot silently match zero rows.
"""

import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEED = ROOT / "supabase" / "seed.sql"
RECAP = ROOT / "public" / "recap.html"

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

# --- independent control: recap.html's roster COLUMNS ----------------------
# seed.sql carries no drafter, so the draft-night page is the only on-disk
# second source. Anchor on the column div, never on the <h2>s: the rosters sit
# in a <details> block after all four headings, and an h2-keyed parse hands
# every pick to the last drafter.
recap = RECAP.read_text(encoding="utf-8")
cols = re.findall(r'<div class="col s-(\w+)">(.*?)</ul>', recap, re.S)
assert len(cols) == 4, f"recap.html yielded {len(cols)} roster columns, expected 4"
for slug, body in cols:
    who = slug.capitalize()
    assert who in DRAFT, f"recap.html has a column for unknown drafter {who}"
    got = [(int(p), html.unescape(n)) for p, n in
           re.findall(r'<span class="pk">#(\d+)</span><b>([^<]+)</b>', body)]
    want = [(p, n.replace('Angelica "Jelly" Loblack', "Jelly Loblack"))
            for p, n in DRAFT[who]]
    assert got == want, f"{who}: recap.html reads {got}, DRAFT says {want}"

# --- tribes: one merged tribe from episode 7 -------------------------------
# TRIBES is MEMBERSHIP at the merge, so Brady is still listed.
MERGED = "Tovuto (Blue)"
TRIBES = {
    MERGED: ["Brady Booker", "Carter Krull", "Cristian Chavez", "Devin Way",
             "Eric Macksoud", 'Angelica "Jelly" Loblack', "Danny Kilby",
             "Kristin Flickinger", "Lewis Kelly", "Maggie Nestor",
             "Mike Pinsky", "Sharonda Cox", "Thien An Nguyen"],
}

# Tribes that went to Tribal Council, per episode. Episode 5 sent TWO.
WENT_TO_TRIBAL = {1: ["Toka"], 2: ["Savu"], 3: ["Toka"], 4: ["Savu"],
                  5: ["Savu", "Dina"], 6: ["Savu"], 7: ["Tovuto"]}

GONE = {
    "Aaliyah Puglia":     (1, "voted out"),
    "Ana Sani":           (2, "voted out"),
    "Rob Antonson":       (3, "quit"),
    "Patt Cannaday":      (3, "voted out"),
    "Jenna Doore":        (4, "voted out"),
    "Alexis Levine":      (5, "voted out"),
    "Linnea Capobianco":  (5, "voted out"),
    "Ori Jean-Charles":   (6, "voted out"),
    "Brady Booker":       (7, "voted out"),
}

IMMUNE = ["Mike Pinsky"]                     # individual immunity, episode 7
# The last three on the beam, in the order they finished (winner first).
FINAL_THREE = ["Mike Pinsky", "Lewis Kelly", "Kristin Flickinger"]
assert FINAL_THREE[0] == IMMUNE[0]
MISSED_FEAST = ["Cristian Chavez", "Kristin Flickinger", "Sharonda Cox"]

# Who wrote whose name. Wikipedia's voting-history rows and Paramount+'s
# named list agree on all thirteen.
EP7_VOTERS = {
    "Cristian Chavez": "Brady Booker", "Devin Way": "Brady Booker",
    "Eric Macksoud": "Brady Booker", 'Angelica "Jelly" Loblack': "Brady Booker",
    "Maggie Nestor": "Brady Booker", "Mike Pinsky": "Brady Booker",
    "Sharonda Cox": "Brady Booker", "Danny Kilby": "Brady Booker",
    "Kristin Flickinger": "Brady Booker",
    "Carter Krull": "Eric Macksoud", "Lewis Kelly": "Eric Macksoud",
    "Thien An Nguyen": "Eric Macksoud", "Brady Booker": "Eric Macksoud",
}

# Episode 7's tribal. `members` is who attended; `no_vote` names those who
# attended but cast no ballot, so ballots = members - no_vote + extra.
EP7_TRIBAL = {
    "tribe": MERGED, "members": 13, "extra_votes": 0, "no_vote": [],
    "votes": {"Brady Booker": 9, "Eric Macksoud": 4}, "unattributed": 0,
    "out": "Brady Booker",
}

# Advantages still in play AFTER episode 7.
ADVANTAGES = {
    'Angelica "Jelly" Loblack': "hidden immunity idol (found ep 2, unplayed)",
    "Carter Krull":             "hidden immunity idol (Rob's, never played)",
    "Devin Way":                "secret extra vote (ep 3, still unplayed)",
    "Sharonda Cox":             "Tethered Idol (won by Kristin in ep 6, "
                                "handed to Sharonda in ep 7)",
}
SPENT = {
    "Maggie Nestor": "gave both of her extra votes away on the journey to Dina, "
                     "to Danny Kilby and Lewis Kelly, naming Linnea Capobianco "
                     "as the target",
}
TETHERED_FROM = "Kristin Flickinger"       # won it in ep 6, gave it away in ep 7

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

# --- the merged tribe must be exactly everyone still in after episode 6 ----
out = set(GONE)
gone_before_merge = {n for n, (ep, _) in GONE.items() if ep < 7}
at_merge = [n for n in everyone if n not in gone_before_merge]
alive = [n for n in everyone if n not in out]
placed = [n for roster in TRIBES.values() for n in roster]

assert len(placed) == len(set(placed)), "a castaway appears twice in the merge"
assert set(placed) == set(at_merge), (
    f"the merged tribe is not everyone left after episode 6; "
    f"listed but already out: {sorted(set(placed) & gone_before_merge)}; "
    f"in the game but missing: {sorted(set(at_merge) - set(placed))}"
)
assert len(at_merge) == 13, f"{len(at_merge)} at the merge, expected 13"
assert len(alive) == 21 - len(out) == 12, f"{len(alive)} alive, expected 12"

tribe = {n: t for t, roster in TRIBES.items() for n in roster}

for n in ADVANTAGES:
    assert n not in out, f"{n} holds an advantage but is out of the game"
for n in IMMUNE + MISSED_FEAST:
    assert n in at_merge, f"{n} was not at the merge"
assert len(at_merge) - len(MISSED_FEAST) == 10, "the feast took ten"

# --- gate episode 7's tribal on its own ballot arithmetic -----------------
t = EP7_TRIBAL
ballots = t["members"] - len(t["no_vote"]) + t["extra_votes"]
counted = sum(t["votes"].values()) + t["unattributed"]
assert counted == ballots, (
    f"tally accounts for {counted} ballots but {t['members']} members - "
    f"{len(t['no_vote'])} forfeited + {t['extra_votes']} extra = {ballots}")
assert t["members"] == len(at_merge), \
    f"{t['members']} at tribal but {len(at_merge)} merged"

# The per-voter rows must reproduce the tally, voter for voter.
assert set(EP7_VOTERS) == set(at_merge), \
    f"voters {sorted(set(at_merge) ^ set(EP7_VOTERS))} differ from the tribe"
from_voters = {}
for v, target in EP7_VOTERS.items():
    assert v != target, f"{v} voted for themself"
    from_voters[target] = from_voters.get(target, 0) + 1
assert from_voters == t["votes"], f"voter rows {from_voters} != tally {t['votes']}"
for n in IMMUNE:
    assert n not in t["votes"], f"{n} was immune but took votes"

booted = t["out"]
assert t["votes"][booted] == max(t["votes"].values())
assert t["votes"][booted] > counted / 2, f"{booted} left without a majority"
assert {n for n, (ep, _) in GONE.items() if ep == 7} == {booted}

# --- derived, never recalled ----------------------------------------------
voted_out_order = [n for n, (ep, how) in sorted(
    GONE.items(), key=lambda kv: (kv[1][0], kv[0])) if how == "voted out"]
place = {n: i + 1 for i, n in enumerate(voted_out_order)}
left_order = [n for n, _ in sorted(GONE.items(), key=lambda kv: (kv[1][0], kv[0]))]


def ordinal(n):
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


left = {w: len([n for _, n in picks if n not in out]) for w, picks in DRAFT.items()}

if __name__ == "__main__":
    print(f"{len(out)} of 21 are now gone, {len(alive)} still in.")
    print(f"  {booted} ({owner[booted]}) -- {ordinal(place[booted])} voted out, "
          f"{ordinal(len(out))} to leave")
    print("\nstandings: " + ", ".join(
        f"{w} {c}" for w, c in sorted(left.items(), key=lambda kv: (-kv[1], kv[0]))))
    print("\nvotes by voter's drafter:")
    for target in t["votes"]:
        by = {}
        for v, tg in EP7_VOTERS.items():
            if tg == target:
                by.setdefault(owner[v], []).append(v)
        print(f"  {target} ({owner[target]}): " + "; ".join(
            f"{d}: {', '.join(vs)}" for d, vs in sorted(by.items())))
    print("\nMike's roster at the vote:")
    for _, n in DRAFT["Mike"]:
        if n in EP7_VOTERS:
            print(f"  {n:18} -> {EP7_VOTERS[n]}")
    print(f"\nimmune: {IMMUNE} ({owner[IMMUNE[0]]})")
    print(f"missed the feast: {[(n, owner[n]) for n in MISSED_FEAST]}")
    print("\nadvantages:")
    for n, what in ADVANTAGES.items():
        print(f"  {owner[n]:9} {n:26} {what}")

# --- SQL for the live board (idempotent, covers all 21) -------------------
sql = ["-- Tribe state after Survivor 51 episode 7 (the merge; Brady Booker voted out).",
       "-- Generated by recaps/week7_map.py. Safe to re-run.",
       "-- SUPERSEDES every earlier tribes-after-ep*.sql: sets all 21 rows.",
       "-- Names are exact players.name spellings, asserted against seed.sql.",
       "-- Labels MUST carry the colour word or getTribeColor() falls back to grey.",
       ""]
still_in = sorted(n for n in TRIBES[MERGED] if n not in out)
names = ",\n  ".join("'" + n.replace("'", "''") + "'" for n in still_in)
sql += [f"UPDATE players SET tribe = '{MERGED}' WHERE name IN (\n  {names}\n);"
        f"  -- {len(still_in)} rows", ""]
eliminated = sorted(out)
names = ",\n  ".join("'" + n.replace("'", "''") + "'" for n in eliminated)
sql += ["-- Out of the game: tribe cleared so the board shows them unassigned.",
        f"UPDATE players SET tribe = NULL WHERE name IN (\n  {names}\n);"
        f"  -- {len(eliminated)} rows", ""]
assert len(still_in) + len(eliminated) == 21, "SQL does not touch all 21 rows"
assert "(Blue)" in MERGED, "the label must carry the colour word"
(ROOT / "supabase" / "tribes-after-ep7.sql").write_text("\n".join(sql), encoding="utf-8")
if __name__ == "__main__":
    print(f"\nwrote supabase/tribes-after-ep7.sql ({len(still_in) + len(eliminated)} rows)")
