"""Print every vote-ledger figure a recap page quotes, cut off at one episode.

    py -X utf8 recaps/ledger_figures.py 7

Read-only. The page is written from this output, never from memory, and the
week's checker recomputes the same figures independently from vote_history.
"""

import contextlib
import importlib.util
import io
import pathlib
import sys

THROUGH = int(sys.argv[1])
spec = importlib.util.spec_from_file_location(
    "vote_history", pathlib.Path(__file__).resolve().parent / "vote_history.py")
vh = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(vh)

T = [t for t in vh.TRIBALS if t["ep"] <= THROUGH]
owner = {n: d for d, ps in vh.DRAFT.items() for n in ps}
owner.update({n: "Undrafted" for n in vh.UNDRAFTED})
rec = {}
for t in T:
    for n, v in t["votes"].items():
        rec[n] = rec.get(n, 0) + v
unatt = sum(t.get("unattributed", 0) for t in T)
credits = sum(rec.values()) + unatt
ballots = sum(vh.ballots_of(t) for t in T)
by = {}
for n, v in rec.items():
    by[owner[n]] = by.get(owner[n], 0) + v
if unatt:
    by["unattributed"] = unatt
top = max(by.values())
print(f"through ep {THROUGH}: {len(T)} tribals, {ballots} ballots, {credits} names")
for d, v in sorted(by.items(), key=lambda kv: -kv[1]):
    print(f"  {d:12} {v:3}  {round(100 * v / credits)}%  bar {round(100 * v / top, 1)}%")
outs = {n for t in T for n in vh.outs_of(t)}
print(f"written down: {len(rec)} of 21; never: {21 - len(rec)}")
for n, v in sorted(rec.items(), key=lambda kv: (-kv[1], kv[0])):
    eps = ", ".join(f"ep {t['ep']}" for t in T if n in t["votes"])
    print(f"  {n:28} {v:2}  {eps:12} {owner[n]:10} {'out' if n in outs else 'in'}")
surv = {n: v for n, v in rec.items() if n not in outs}
b = max(surv.values())
print(f"most survived ({b}): {sorted(n for n, v in surv.items() if v == b)}")
print("multi-tribal:", sorted(n for n in rec if sum(n in t['votes'] for t in T) > 1))
single = max((v, t["ep"], n) for t in T for n, v in t["votes"].items())
print(f"most in one night: {single}")
print("shots in the dark (forfeits):", sum(len(t["no_vote"]) for t in T))
