import { readFileSync } from "fs";
import { join } from "path";
import {
  getSnakeIndex,
  getActiveDrafter,
  getRound,
  isFinalPick,
} from "../draft-logic";
import {
  TOTAL_PICKS,
  TOTAL_ROUNDS,
  TOTAL_PLAYERS,
  TOTAL_DRAFTERS,
  getTribeColor,
  NO_TRIBE_COLOR,
  TRIBE_COLORS,
} from "../types";

const order = ["Mike", "Joe", "Sarah", "Dan"];

describe("draft shape", () => {
  // Relational, not literal: these fail if the constants stop agreeing with
  // each other, which is the thing that actually breaks the draft.
  test("picks divide evenly among drafters", () => {
    expect(TOTAL_PICKS % TOTAL_DRAFTERS).toBe(0);
  });
  test("rounds x drafters = picks", () => {
    expect(TOTAL_ROUNDS * TOTAL_DRAFTERS).toBe(TOTAL_PICKS);
  });
  test("the roster is large enough for every pick", () => {
    expect(TOTAL_PLAYERS).toBeGreaterThanOrEqual(TOTAL_PICKS);
  });
  test("exactly one castaway goes undrafted", () => {
    expect(TOTAL_PLAYERS - TOTAL_PICKS).toBe(1);
  });
});

describe("seed data matches the declared roster size", () => {
  // Binds TOTAL_PLAYERS to the actual cast list rather than to itself, so
  // adding or dropping a castaway without updating the constant fails here.
  const seed = readFileSync(
    join(__dirname, "..", "..", "..", "supabase", "seed.sql"),
    "utf8"
  );
  const rows = seed.match(/^\(\d+,\s+'/gm) ?? [];

  test(`seed.sql contains ${TOTAL_PLAYERS} castaways`, () => {
    expect(rows.length).toBe(TOTAL_PLAYERS);
  });
  test("seed ids are 1..TOTAL_PLAYERS with no gaps or duplicates", () => {
    const ids = rows
      .map((r) => parseInt(r.slice(1), 10))
      .sort((a, b) => a - b);
    expect(ids).toEqual(
      Array.from({ length: TOTAL_PLAYERS }, (_, i) => i + 1)
    );
  });
});

describe("getSnakeIndex", () => {
  // Round 1 (picks 1-4): forward 0,1,2,3
  test("pick 1 → index 0", () => expect(getSnakeIndex(1)).toBe(0));
  test("pick 4 → index 3", () => expect(getSnakeIndex(4)).toBe(3));
  // Round 2 (picks 5-8): reverse 3,2,1,0
  test("pick 5 → index 3", () => expect(getSnakeIndex(5)).toBe(3));
  test("pick 8 → index 0", () => expect(getSnakeIndex(8)).toBe(0));
  // Round 3 (picks 9-12): forward again
  test("pick 9 → index 0", () => expect(getSnakeIndex(9)).toBe(0));
  test("pick 12 → index 3", () => expect(getSnakeIndex(12)).toBe(3));
  // Round 5 (picks 17-20) is odd-numbered, so forward — the final pick of the
  // draft lands on the last drafter in the order.
  test("pick 17 → index 0", () => expect(getSnakeIndex(17)).toBe(0));
  test("pick 20 → index 3", () => expect(getSnakeIndex(20)).toBe(3));
  test("every pick maps inside the draft order", () => {
    for (let pick = 1; pick <= TOTAL_PICKS; pick++) {
      const idx = getSnakeIndex(pick);
      expect(idx).toBeGreaterThanOrEqual(0);
      expect(idx).toBeLessThan(TOTAL_DRAFTERS);
    }
  });
});

describe("isFinalPick", () => {
  // Guards the completion boundary in use-draft.ts. Substituting TOTAL_PLAYERS
  // (21) for TOTAL_PICKS (20) turns the pick-20 case red.
  test("pick 19 is not final", () => expect(isFinalPick(19)).toBe(false));
  test("pick 20 IS final", () => expect(isFinalPick(20)).toBe(true));
  test("the draft never reaches pick 21", () => {
    expect(isFinalPick(TOTAL_PLAYERS)).toBe(true);
  });
  test("no pick before the last is final", () => {
    for (let pick = 1; pick < TOTAL_PICKS; pick++) {
      expect(isFinalPick(pick)).toBe(false);
    }
  });
});

describe("getActiveDrafter", () => {
  test("pick 1 → first in order", () => {
    expect(getActiveDrafter(1, order)).toBe("Mike");
  });
  test("pick 5 → last in order (snake)", () => {
    expect(getActiveDrafter(5, order)).toBe("Dan");
  });
  test("pick 8 → first in order (snake back)", () => {
    expect(getActiveDrafter(8, order)).toBe("Mike");
  });
  test("final pick 20 → last in order", () => {
    expect(getActiveDrafter(TOTAL_PICKS, order)).toBe("Dan");
  });
});

describe("getRound", () => {
  test("pick 1 → round 1", () => expect(getRound(1)).toBe(1));
  test("pick 4 → round 1", () => expect(getRound(4)).toBe(1));
  test("pick 5 → round 2", () => expect(getRound(5)).toBe(2));
  test("pick 20 → round 5", () => expect(getRound(20)).toBe(5));
  test("final pick is in the final round", () => {
    expect(getRound(TOTAL_PICKS)).toBe(TOTAL_ROUNDS);
  });
  test("no pick falls outside the rendered board", () => {
    for (let pick = 1; pick <= TOTAL_PICKS; pick++) {
      expect(getRound(pick)).toBeLessThanOrEqual(TOTAL_ROUNDS);
    }
  });
});

describe("every drafter gets an equal share", () => {
  test("each of the 4 drafters picks exactly 5 times", () => {
    const counts: Record<string, number> = {};
    for (let pick = 1; pick <= TOTAL_PICKS; pick++) {
      const drafter = getActiveDrafter(pick, order);
      counts[drafter] = (counts[drafter] ?? 0) + 1;
    }
    expect(Object.keys(counts).sort()).toEqual([...order].sort());
    expect(Object.values(counts)).toEqual([5, 5, 5, 5]);
  });
});

describe("getTribeColor", () => {
  test("null tribe → neutral gray", () => {
    expect(getTribeColor(null)).toBe(NO_TRIBE_COLOR);
  });
  test("empty tribe → neutral gray", () => {
    expect(getTribeColor("")).toBe(NO_TRIBE_COLOR);
  });
  test("exact key match", () => {
    expect(getTribeColor("Purple")).toBe(TRIBE_COLORS.Purple);
  });
  test("case-insensitive", () => {
    expect(getTribeColor("purple")).toBe(TRIBE_COLORS.Purple);
    expect(getTribeColor("YELLOW")).toBe(TRIBE_COLORS.Yellow);
  });
  test("real tribe name carrying the color still resolves", () => {
    // Survivor 50 used this shape, e.g. "Vatu (Purple)".
    expect(getTribeColor("Vatu (Purple)")).toBe(TRIBE_COLORS.Purple);
  });
  test("unknown tribe → neutral gray, not a crash", () => {
    expect(getTribeColor("Lagi")).toBe(NO_TRIBE_COLOR);
  });
});
