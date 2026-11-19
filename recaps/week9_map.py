"""Map the Survivor 51 draft onto the state after episode 9. Read-only except
for the SQL it writes.

Episode 9 ("Wilder Than a Cat in a Bathtub", aired 2026-11-18, Tribal on day
17): THE MILLION DOLLAR COIN FLIP. No vote was cast. Lewis Kelly volunteered to
flip, called fire, the coin landed water, and Lewis was eliminated -- the 12th
to leave, NOT a 11th voted out, and the third member of the jury.

Sources: Wikipedia's raw wikitext (episode table, summary, contestant table,
voting-history row reading "None", coin-flip footnote), Paramount+ (CBS's own
recap), Yahoo, and DK Network.

Agreed by every source that covers it:
  - reward teams of five: Mike, Devin, Eric, Lewis, Thien An (won) against
    Sharonda, Carter, Jelly, Maggie, Cristian (all four);
  - the reward: a helicopter ride over Fiji and a fried-chicken meal (all four);
  - Lewis won the slingshot stage for that team (Wikipedia, Paramount+, Yahoo);
  - immunity: an endurance hang over water; Carter and Lewis the last two,
    Carter the winner after more than half an hour (all four);
  - Devin made a FAKE idol from the parchment and wrapping of Jelly's played
    idol and planted it (Wikipedia, DK; Yahoo: it carried Jelly's real clues);
  - Cristian told Sharonda about Carter's idol (Wikipedia, Yahoo, DK);
  - at Tribal: Devin and Lewis were the two left considering the flip and Lewis
    took it; fire called, water landed; Lewis out, no votes cast (all four);
  - a correct call would have taken the prize to two million (all four); the
    unspent million rolls over to the next season (Paramount+, Yahoo).
  - Lewis is the third juror (Wikipedia, Paramount+).

Deliberately OMITTED:
  - how Devin's attempt to steer Maggie to the fake idol ended: Wikipedia (she
    missed it, Devin retrieved it), Paramount+ (Devin "found" it and failed to
    hand it over), Yahoo (Maggie kept it after taking it for a leaf) and DK
    (Maggie refused to hold it) are four different stories. So nobody is named
    as HOLDING the fake.
  - what a CORRECT call would have done for the flipper: three outlets say an
    idol and safety, Wikipedia words the win side differently.
  - Paramount+'s "11th castaway voted off": no ballot was cast; Wikipedia's
    contestant table says "Eliminated", and Paramount+ itself calls "voted" a
    stretch.
  - the order everyone else dropped in the immunity challenge.
  - Lewis's unplayed Shot in the Dark: one outlet only.
Deliberately EXCLUDED as unaired: episode 10 and every "next time" preview.

Names are the exact `players.name` spellings from supabase/seed.sql.
"""

import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEED = ROOT / "supabase" / "seed.sql"
RECAP = ROOT / "public" / "recap.html"

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

# --- independent control: recap.html's roster COLUMNS (never its <h2>s) ---
recap = RECAP.read_text(encoding="utf-8")
cols = re.findall(r'<div class="col s-(\w+)">(.*?)</ul>', recap, re.S)
assert len(cols) == 4, f"recap.html yielded {len(cols)} roster columns, expected 4"
for slug, body in cols:
    who = slug.capitalize()
    got = [(int(p), html.unescape(n)) for p, n in
           re.findall(r'<span class="pk">#(\d+)</span><b>([^<]+)</b>', body)]
    want = [(p, n.replace('Angelica "Jelly" Loblack', "Jelly Loblack"))
            for p, n in DRAFT[who]]
    assert got == want, f"{who}: recap.html reads {got}, DRAFT says {want}"

MERGED = "Tovuto (Blue)"
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
    "Lewis Kelly":        (9, "coin flip"),
}
JURY = ["Danny Kilby", "Kristin Flickinger", "Lewis Kelly"]   # Lewis is third
FLIPPER, CALLED, LANDED = "Lewis Kelly", "fire", "water"
CONSIDERED_FLIP = ["Devin Way", "Lewis Kelly"]                # the last two
IMMUNE = "Carter Krull"
IMMUNITY_LAST_TWO = ["Carter Krull", "Lewis Kelly"]
REWARD_WON = ["Mike Pinsky", "Devin Way", "Eric Macksoud", "Lewis Kelly",
              "Thien An Nguyen"]
REWARD_LOST = ["Sharonda Cox", "Carter Krull", 'Angelica "Jelly" Loblack',
               "Maggie Nestor", "Cristian Chavez"]
FAKE_IDOL_MAKER = "Devin Way"

ADVANTAGES = {
    "Carter Krull": "hidden immunity idol (Rob's, never played; Cristian "
                    "told Sharonda about it this week)",
    "Devin Way":    "secret extra vote (ep 3; no vote was held, so unplayed)",
    "Sharonda Cox": "Tethered Idol (handed over by Kristin in ep 7; not "
                    "mentioned since)",
}

# --- gates ----------------------------------------------------------------
seed_names = set(re.findall(r"^\(\d+,\s+'(.+?)',", SEED.read_text(), re.M))
drafted = [n for ps in DRAFT.values() for _, n in ps]
everyone = drafted + UNDRAFTED
owner = {n: w for w, ps in DRAFT.items() for _, n in ps}
owner.update({n: "undrafted" for n in UNDRAFTED})
assert len(set(everyone)) == 21 and set(everyone) == seed_names

out = set(GONE)
alive = [n for n in everyone if n not in out]
at_tribal = [n for n in everyone if GONE.get(n, (99,))[0] >= 9]
assert len(at_tribal) == 10 and len(alive) == 9, (len(at_tribal), len(alive))

teams = REWARD_WON + REWARD_LOST
assert len(teams) == len(set(teams)) == 10 and set(teams) == set(at_tribal), \
    "the two reward teams must partition the ten exactly"
assert len(REWARD_WON) == len(REWARD_LOST) == 5
assert IMMUNE in at_tribal and IMMUNE not in out
assert set(IMMUNITY_LAST_TWO) <= set(at_tribal) and IMMUNE in IMMUNITY_LAST_TWO
assert FLIPPER in CONSIDERED_FLIP and FLIPPER != IMMUNE
assert CALLED != LANDED, "the flipper went out, so the call must have missed"
assert {n for n, (e, _) in GONE.items() if e == 9} == {FLIPPER}
assert GONE[FLIPPER][1] != "voted out", "nobody voted; the flip eliminated Lewis"
for n in ADVANTAGES:
    assert n in alive, f"{n} holds an advantage but is out"
assert JURY[-1] == FLIPPER and all(GONE[n][0] >= 8 for n in JURY)

voted_out = [n for n, (e, how) in GONE.items() if how == "voted out"]
left = {w: len([n for _, n in ps if n not in out]) for w, ps in DRAFT.items()}

if __name__ == "__main__":
    print(f"{len(out)} gone ({len(voted_out)} voted out), {len(alive)} in")
    print("standings: " + ", ".join(f"{w} {c}" for w, c in
                                     sorted(left.items(), key=lambda kv: -kv[1])))
    for label, team in (("won reward", REWARD_WON), ("lost reward", REWARD_LOST)):
        print(f"  {label}: " + ", ".join(f"{n} ({owner[n]})" for n in team))
    print(f"flipper {FLIPPER} = {owner[FLIPPER]}'s pick "
          f"#{[p for p, n in DRAFT[owner[FLIPPER]] if n == FLIPPER][0]}; "
          f"considered: {[(n, owner[n]) for n in CONSIDERED_FLIP]}")
    print(f"immune: {IMMUNE} ({owner[IMMUNE]}); last two {IMMUNITY_LAST_TWO}")
    print("jury:", [(n, owner[n]) for n in JURY])

# --- SQL ------------------------------------------------------------------
names = ",\n  ".join("'" + n.replace("'", "''") + "'" for n in sorted(alive))
gone_names = ",\n  ".join("'" + n.replace("'", "''") + "'" for n in sorted(out))
sql = ["-- Tribe state after Survivor 51 episode 9 (Lewis Kelly eliminated by the coin flip).",
       "-- Generated by recaps/week9_map.py. Safe to re-run.",
       "-- SUPERSEDES every earlier tribes-after-ep*.sql: sets all 21 rows.",
       "-- Labels MUST carry the colour word or getTribeColor() falls back to grey.",
       "",
       f"UPDATE players SET tribe = '{MERGED}' WHERE name IN (\n  {names}\n);  -- {len(alive)} rows",
       "",
       "-- Out of the game: tribe cleared so the board shows them unassigned.",
       f"UPDATE players SET tribe = NULL WHERE name IN (\n  {gone_names}\n);  -- {len(out)} rows",
       ""]
assert len(alive) + len(out) == 21
(ROOT / "supabase" / "tribes-after-ep9.sql").write_text("\n".join(sql), encoding="utf-8")
