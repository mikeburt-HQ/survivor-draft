"""Map the Survivor 51 draft onto the state after episode 8. Read-only except
for the SQL it writes.

Episode 8 ("Load the Ark, Two by Two", aired 2026-11-11, days 14-15): THE
DOUBLE DUO. The twelve paired up, competed in pairs, and were voted out in
pairs, although each castaway cast an individual ballot naming a pair.

Sources: Wikipedia's raw wikitext (episode table and footnotes, summary,
per-voter voting-history rows), Paramount+ (CBS's own recap), Yahoo, and DK
Network. Paramount+ and Wikipedia name the same eight voters against Devin and
Jelly, Jelly against Carter and Cristian, and Devin against Kilby and Kristin.

Agreed by every source that covers it:
  - the six pairs (all four sources);
  - Brady Booker, voted out in episode 7, asked to leave the game to look after
    an injured thumb and gave up the jury seat (Paramount+, Yahoo, DK; Wikipedia
    says "following an injury");
  - Kilby & Kristin and Mike & Maggie were the first two pairs out of the
    challenge (Paramount+, Yahoo; Wikipedia: "the first two to drop");
  - Carter & Cristian won the first stage; Lewis & Sharonda won immunity and
    the reward, and took Jelly and Kristin to it;
  - Cristian went on the journey, arrived without a vote, won it back and won
    an extra vote usable only that night (Wikipedia, Paramount+, Yahoo);
  - that extra vote ended up with Eric, who did not use it;
  - Kristin's Shot in the Dark came back Not Safe and Cristian's came back
    Safe; Jelly played an idol and cancelled the eight against her pair;
  - Kilby and Kristin went out on the single counted ballot, Devin's, and are
    the first two members of the jury (Wikipedia, Paramount+).

Deliberately OMITTED, because sources disagree or say nothing:
  - WHO handed Eric the extra vote: three sources say Cristian, DK says Carter.
  - WHICH winner picked which guest for the reward: one source only.
  - the challenge order after stage one: Paramount+ and DK place Carter &
    Cristian's and Devin & Jelly's exits in different stages.
  - the six-person alliance's NAME: three outlets, three names.
  - what became of the Tethered Idol: Sharonda has held it since episode 7 and
    no episode-8 source mentions it. It stays on the hardware list with that
    said, rather than being declared live or dead.
  - which of Kilby and Kristin is juror one and which is two.
Deliberately EXCLUDED as unaired: anything from episode 9 onward, including
Wikipedia's contestant-table placings for later boots and the episode-8
"next time" preview.

Names are the exact `players.name` spellings from supabase/seed.sql.
"""

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEED = ROOT / "supabase" / "seed.sql"

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

MERGED = "Tovuto (Blue)"
MERGE_ROSTER = ["Brady Booker", "Carter Krull", "Cristian Chavez", "Devin Way",
                "Eric Macksoud", 'Angelica "Jelly" Loblack', "Danny Kilby",
                "Kristin Flickinger", "Lewis Kelly", "Maggie Nestor",
                "Mike Pinsky", "Sharonda Cox", "Thien An Nguyen"]

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
    "Danny Kilby":        (8, "voted out"),
    "Kristin Flickinger": (8, "voted out"),
}
JURY = ["Danny Kilby", "Kristin Flickinger"]       # order between them omitted
LEFT_JURY = ["Brady Booker"]                       # withdrew, episode 8

# The six pairs, as the sources list them. Order within a pair is not meaningful.
PAIRS = [("Maggie Nestor", "Mike Pinsky"), ("Carter Krull", "Cristian Chavez"),
         ("Devin Way", 'Angelica "Jelly" Loblack'),
         ("Danny Kilby", "Kristin Flickinger"),
         ("Eric Macksoud", "Thien An Nguyen"), ("Lewis Kelly", "Sharonda Cox")]
IMMUNE_PAIR = ("Lewis Kelly", "Sharonda Cox")
FIRST_OUT_OF_CHALLENGE = [("Danny Kilby", "Kristin Flickinger"),
                          ("Maggie Nestor", "Mike Pinsky")]
STAGE_ONE_WINNERS = ("Carter Krull", "Cristian Chavez")
REWARD_GUESTS = ['Angelica "Jelly" Loblack', "Kristin Flickinger"]
JOURNEY = "Cristian Chavez"

# Who wrote which pair. Wikipedia's voter rows and Paramount+'s list agree.
DJ, KK, CC = PAIRS[2], PAIRS[3], PAIRS[1]
EP8_VOTERS = {
    "Carter Krull": DJ, "Eric Macksoud": DJ, "Lewis Kelly": DJ,
    "Maggie Nestor": DJ, "Mike Pinsky": DJ, "Sharonda Cox": DJ,
    "Thien An Nguyen": DJ, "Danny Kilby": DJ,
    'Angelica "Jelly" Loblack': CC,
    "Devin Way": KK,
}
SHOTS = {"Kristin Flickinger": "Not Safe", "Cristian Chavez": "Safe"}
IDOL_PLAYED = ('Angelica "Jelly" Loblack', DJ)     # who played it, whom it covered
EXTRA_VOTE_UNUSED = "Eric Macksoud"                # ended up with, did not cast

ADVANTAGES = {
    "Carter Krull": "hidden immunity idol (Rob's, never played; shown to "
                    "Cristian this week)",
    "Devin Way":    "secret extra vote (ep 3, still unplayed)",
    "Sharonda Cox": "Tethered Idol (handed over by Kristin in ep 7; not "
                    "mentioned this week)",
}
SPENT_THIS_WEEK = {
    'Angelica "Jelly" Loblack': "hidden immunity idol, played on the pair",
    "Cristian Chavez": "journey extra vote, valid only that night, ended up "
                       "with Eric unused",
}

# --- bind names, partition, and gate the tribal ---------------------------
seed_names = set(re.findall(r"^\(\d+,\s+'(.+?)',", SEED.read_text(), re.M))
assert len(seed_names) == 21
drafted = [n for ps in DRAFT.values() for _, n in ps]
everyone = drafted + UNDRAFTED
owner = {n: w for w, ps in DRAFT.items() for _, n in ps}
owner.update({n: "undrafted" for n in UNDRAFTED})
assert len(set(everyone)) == 21 and set(everyone) == seed_names

out = set(GONE)
alive = [n for n in everyone if n not in out]
before = [n for n in MERGE_ROSTER if GONE.get(n, (99,))[0] >= 8]   # at ep-8 tribal
assert len(before) == 12, f"{len(before)} at the episode-8 tribal, expected 12"
assert len(alive) == 10, f"{len(alive)} alive, expected 10"
assert set(alive) == set(before) - {"Danny Kilby", "Kristin Flickinger"}

paired = [n for p in PAIRS for n in p]
assert len(paired) == len(set(paired)) == 12 and set(paired) == set(before), \
    "the six pairs must partition the twelve exactly"
assert IMMUNE_PAIR in PAIRS and STAGE_ONE_WINNERS in PAIRS
assert all(p in PAIRS for p in FIRST_OUT_OF_CHALLENGE)
assert IMMUNE_PAIR not in FIRST_OUT_OF_CHALLENGE
assert not set(REWARD_GUESTS) & set(IMMUNE_PAIR)

# ballots = present - forfeits; every voter present, nobody votes own pair
assert set(EP8_VOTERS) == set(before) - set(SHOTS), \
    "voters must be everyone at tribal except the two who forfeited"
for v, pair in EP8_VOTERS.items():
    assert v not in pair, f"{v} voted for their own pair"
    assert pair != IMMUNE_PAIR, f"{v} voted for the immune pair"
cast = {}
for pair in EP8_VOTERS.values():
    cast[pair] = cast.get(pair, 0) + 1
negated = {DJ: cast[DJ], CC: cast[CC]}             # idol on DJ, Safe Shot on CC
counted = {p: cast[p] - negated.get(p, 0) for p in cast}
assert sum(cast.values()) == 10
assert counted == {DJ: 0, KK: 1, CC: 0}, counted
booted = max(counted, key=counted.get)
assert booted == KK and set(booted) == {n for n, (e, _) in GONE.items() if e == 8}
assert [v for v, p in EP8_VOTERS.items() if p == booted] == ["Devin Way"]
assert IDOL_PLAYED[1] == DJ and IDOL_PLAYED[0] in DJ
assert SHOTS["Cristian Chavez"] == "Safe" and "Cristian Chavez" in CC
assert SHOTS["Kristin Flickinger"] == "Not Safe" and "Kristin Flickinger" in KK
assert EXTRA_VOTE_UNUSED in EP8_VOTERS and EP8_VOTERS[EXTRA_VOTE_UNUSED] == DJ

for n in ADVANTAGES:
    assert n not in out, f"{n} holds an advantage but is out"
for n in JURY:
    assert GONE[n][0] >= 7, f"{n} is not a post-merge boot"
assert not set(JURY) & set(LEFT_JURY)

voted_out_order = [n for n, (ep, how) in sorted(GONE.items(), key=lambda kv: (kv[1][0], kv[0]))
                   if how == "voted out"]
place = {n: i + 1 for i, n in enumerate(voted_out_order)}
left = {w: len([n for _, n in ps if n not in out]) for w, ps in DRAFT.items()}

if __name__ == "__main__":
    print(f"{len(out)} gone, {len(alive)} in; standings "
          + ", ".join(f"{w} {c}" for w, c in sorted(left.items(), key=lambda kv: -kv[1])))
    print("pairs by owner:")
    for p in PAIRS:
        print(f"  {' & '.join(p):42} {' & '.join(owner[n] for n in p)}")
    print("ballots:")
    for v, p in EP8_VOTERS.items():
        same = [n for n in p if owner[n] == owner[v]]
        print(f"  {v:26} ({owner[v]:9}) -> {' & '.join(p)}"
              + (f"   (own drafter's {same})" if same else ""))
    print(f"counted: { {' & '.join(p): c for p, c in counted.items()} }")
    print(f"places: Kilby {place['Danny Kilby']}, Kristin {place['Kristin Flickinger']}")

# --- SQL ------------------------------------------------------------------
still_in = sorted(alive)
names = ",\n  ".join("'" + n.replace("'", "''") + "'" for n in still_in)
gone_names = ",\n  ".join("'" + n.replace("'", "''") + "'" for n in sorted(out))
sql = ["-- Tribe state after Survivor 51 episode 8 (Danny Kilby and Kristin Flickinger voted out).",
       "-- Generated by recaps/week8_map.py. Safe to re-run.",
       "-- SUPERSEDES every earlier tribes-after-ep*.sql, ep7 included: sets all 21 rows.",
       "-- Labels MUST carry the colour word or getTribeColor() falls back to grey.",
       "",
       f"UPDATE players SET tribe = '{MERGED}' WHERE name IN (\n  {names}\n);  -- {len(still_in)} rows",
       "",
       "-- Out of the game: tribe cleared so the board shows them unassigned.",
       f"UPDATE players SET tribe = NULL WHERE name IN (\n  {gone_names}\n);  -- {len(out)} rows",
       ""]
assert len(still_in) + len(out) == 21
(ROOT / "supabase" / "tribes-after-ep8.sql").write_text("\n".join(sql), encoding="utf-8")
