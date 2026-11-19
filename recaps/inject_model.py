"""Prove vote_history.py's episode-8 pair gates fire. Each case edits the
source IN MEMORY (the file is never written), executes it, and requires an
AssertionError that names the defect.

    py -X utf8 recaps/inject_model.py
"""

import contextlib
import io
import pathlib

SRC = pathlib.Path(__file__).resolve().parent / "vote_history.py"
CASES = [
    ("idol not recorded, so Devin & Jelly would have gone",
     '''        "negated": {
            ("Devin Way", 'Angelica "Jelly" Loblack'): 8,''',
     '''        "negated": {''',
     "declared out but"),
    ("a forfeit dropped, so the ballot count no longer reconciles",
     '"no_vote": ["Kristin Flickinger", "Cristian Chavez"],',
     '"no_vote": ["Kristin Flickinger"],',
     "ballots account for 10 but 11"),
    ("more negated than were cast",
     '''            ("Carter Krull", "Cristian Chavez"): 1,
        },
        "no_vote"''',
     '''            ("Carter Krull", "Cristian Chavez"): 2,
        },
        "no_vote"''',
     "exceeds what it received"),
]
bad = 0
for desc, old, new, must in CASES:
    src = SRC.read_text(encoding="utf-8")
    if src.count(old) != 1:
        print(f"  BAD CASE  {desc}: anchor found {src.count(old)} times")
        bad += 1
        continue
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(src.replace(old, new), str(SRC), "exec"),
                 {"__file__": str(SRC), "__name__": "inject"})
        print(f"  MISSED  {desc}  (no assertion)")
        bad += 1
    except AssertionError as e:
        ok = must in str(e)
        print(f"  {'FIRES' if ok else 'WRONG':6}  {desc}" + ("" if ok else f"  -> {e}"))
        bad += not ok
print(f"{len(CASES) - bad} of {len(CASES)} model defects caught")
raise SystemExit(1 if bad else 0)
