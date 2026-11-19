"""Prove a page checker FIRES: apply one defect at a time to a copy of the page,
run the checker on the copy, and require it to fail AND to name the defect.

    py -X utf8 recaps/inject.py 7

Each case is (description, old, new, a phrase the failure message must carry).
The real page is never touched; copies go to the system temp directory.
"""

import pathlib
import subprocess
import sys
import tempfile

N = int(sys.argv[1])
ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "public" / f"week{N}.html"
CHECKER = ROOT / "recaps" / f"check_week{N}.py"

CASES = {
    7: [
        ("owner swapped on the board",
         '<tr><td>Sharonda Cox</td><td><span class="chip tovuto">Tovuto</span></td><td><span class="owner">Will</span></td></tr>',
         '<tr><td>Sharonda Cox</td><td><span class="chip tovuto">Tovuto</span></td><td><span class="owner">Mike</span></td></tr>',
         "Sharonda Cox owner cell"),
        ("Daron's votes off by one",
         '<div class="count vcount">25<small>', '<div class="count vcount">24<small>',
         "Daron votes 24"),
        ("finish order reversed",
         "Kristin stepped off, then Lewis dropped", "Lewis stepped off, then Kristin dropped",
         "orders the finish"),
        ("gendered pronoun",
         "Brady Booker went six", "He went six", "gendered pronouns"),
        ("unaired episode mentioned",
         "Twelve left, one tribe", "Episode 8 next. Twelve left, one tribe", "unaired"),
        ("castaway dropped from the merged card",
         "<li>Cristian Chavez<span>&mdash; undrafted</span></li>\n        <li>Sharonda",
         "<li>Sharonda", "merged card roster"),
        ("boot ordinal wrong",
         "the eighth castaway\n      voted out", "the ninth castaway\n      voted out",
         "eighth voted out"),
        ("a 4-4 tally in the story",
         "The vote went 9&ndash;4.", "The vote went 4&ndash;4, then 9&ndash;4.", "4-4"),
    ],
    8: [
        ("Will's last castaway given to Mike on the board",
         '<tr><td>Sharonda Cox</td><td><span class="chip tovuto">Tovuto</span></td><td><span class="owner">Will</span></td></tr>',
         '<tr><td>Sharonda Cox</td><td><span class="chip tovuto">Tovuto</span></td><td><span class="owner">Mike</span></td></tr>',
         "Sharonda Cox owner cell"),
        ("a pair credited to the wrong drafters",
         "Danny Kilby &amp; Kristin Flickinger<span>Will &amp; Cagney</span>",
         "Danny Kilby &amp; Kristin Flickinger<span>Will &amp; Daron</span>",
         "credited to"),
        ("individual ordinal for one of a pair",
         "Will. Voted out with Kristin on\n        a single ballot, the two of them the ninth and tenth castaways voted out",
         "Will. Voted out with Kristin on\n        a single ballot, the ninth castaway voted out",
         "shared ordinals"),
        ("contested extra-vote giver asserted",
         "saw that extra vote end up with Eric",
         "Cristian gave the extra vote to Eric, and saw it end up with Eric",
         "who handed over the extra vote"),
        ("Tethered Idol status invented",
         "and is still carrying the Tethered Idol",
         "and the Tethered Idol is now void, though Sharonda is still carrying the Tethered Idol",
         "Tethered Idol's status"),
        ("cancelled note dropped from the idol line",
         "Cagney &amp; Daron &mdash; all eight cancelled by Jelly's idol",
         "Cagney &amp; Daron &mdash; all eight read out", "cancelled ballots", "votes"),
        ("pair ballots changed",
         'Will &amp; Cagney &mdash; voted out</span></span><span class="v">1</span>',
         'Will &amp; Cagney &mdash; voted out</span></span><span class="v">2</span>',
         "reads 2", "votes"),
        ("ledger note drops the names count",
         "carried eighty-one names", "carried many names", "81 names", "votes"),
        ("fewest-votes claim unscoped",
         "One\n      ballot each, on the night they left;", "One each;", "scoped to the night"),
        ("Mike given four of six pairs",
         "has a castaway in three of the six pairs", "has a castaway in four of the six pairs",
         "in three of the six pairs"),
        ("half the cancelled ballots, wrongly widened",
         "half of the eight\n      ballots that idol cancelled", "half of the nine\n      ballots cancelled",
         "half of the eight"),
    ],
    9: [
        ("Lewis called voted out",
         "but not the eleventh voted out, because there was no vote",
         "and the eleventh voted out", "not negated"),
        ("coin-flip pip shown as a vote",
         'title="Lewis Kelly &mdash; lost the coin flip, episode 9">C<',
         'title="Lewis Kelly &mdash; lost the coin flip, episode 9">&times;<', "glyph"),
        ("gone box tag says voted out",
         '<p class="tag">Lost the coin flip &middot; Tovuto</p>',
         '<p class="tag">Voted out &middot; Tovuto</p>', "must not say voted out"),
        ("wrong juror number",
         "and the third\n      member of the jury.", "and the second\n      member of the jury.",
         "is juror 3"),
        ("first-round claim names the wrong survivor",
         "Carter is now the only one still in the game",
         "Carter and Lewis are now still in the game", "first-round"),
        ("fake idol handoff asserted",
         "planted it for someone else to find.",
         "planted it, and Maggie kept it.", "fake-idol handoff"),
        ("Daron given a castaway too many",
         '<div class="count">1<small>left</small></div>\n      <div class="count vcount">33',
         '<div class="count">2<small>left</small></div>\n      <div class="count vcount">33',
         "Daron count 2"),
        ("gendered pronoun",
         "Lewis took the coin, called", "He took the coin, called", "gendered pronouns"),
        ("unaired episode mentioned",
         "Nine left on one tribe.", "Nine left on one tribe before episode 10.", "unaired"),
        ("ledger note drops the no-card reason",
         "so it adds nothing and has no card\n    below.", "so it adds nothing.",
         "no tribal card"),
    ],
}

failed = 0
gaps = 0
for case in CASES[N]:
    desc, old, new, must = case[:4]
    target = case[4] if len(case) > 4 else "page"
    src = PAGE.read_text(encoding="utf-8")
    if src.count(old) != 1:
        print(f"  BAD CASE  {desc}: anchor found {src.count(old)} times")
        failed += 1
        continue
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                     encoding="utf-8") as f:
        f.write(src.replace(old, new))
        tmp = f.name
    cmd = ([sys.executable, "-X", "utf8", str(ROOT / "recaps" / "check_votes.py"),
            "--page", tmp, "--through", str(N)] if target == "votes"
           else [sys.executable, "-X", "utf8", str(CHECKER), tmp])
    r = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
    pathlib.Path(tmp).unlink()
    if must is None:
        # A KNOWN GAP, recorded rather than hidden: this prose claim is not
        # bound to the page text. Reported, never counted as caught.
        print(f"  GAP     {desc}  (rc={r.returncode}; not text-gated)")
        gaps += 1
        continue
    ok = r.returncode == 1 and must.lower() in r.stdout.lower()
    print(f"  {'FIRES' if ok else 'MISSED':6}  {desc}"
          + ("" if ok else f"  (rc={r.returncode}) {r.stdout.strip()[:300]} {r.stderr[-300:]}"))
    failed += not ok

print(f"{len(CASES[N]) - failed - gaps} of {len(CASES[N]) - gaps} injected defects caught"
      + (f"; {gaps} known gap(s) listed above" if gaps else ""))
sys.exit(1 if failed else 0)
