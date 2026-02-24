import { getSnakeIndex, getActiveDrafter, getRound } from "../draft-logic";

const order = ["Mike", "Joe", "Sarah", "Dan"];

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
  // Round 6 (picks 21-24): reverse
  test("pick 24 → index 0", () => expect(getSnakeIndex(24)).toBe(0));
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
});

describe("getRound", () => {
  test("pick 1 → round 1", () => expect(getRound(1)).toBe(1));
  test("pick 4 → round 1", () => expect(getRound(4)).toBe(1));
  test("pick 5 → round 2", () => expect(getRound(5)).toBe(2));
  test("pick 24 → round 6", () => expect(getRound(24)).toBe(6));
});
