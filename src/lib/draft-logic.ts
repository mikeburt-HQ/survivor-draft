import { TOTAL_DRAFTERS } from "./types";

/**
 * Given a 1-based pick number, returns the 0-based index into the draft order
 * using snake draft logic (odd rounds forward, even rounds reversed).
 */
export function getSnakeIndex(pick: number): number {
  const zeroIndexed = pick - 1;
  const round = Math.floor(zeroIndexed / TOTAL_DRAFTERS);
  const positionInRound = zeroIndexed % TOTAL_DRAFTERS;
  return round % 2 === 0
    ? positionInRound
    : TOTAL_DRAFTERS - 1 - positionInRound;
}

/**
 * Returns the name of the drafter whose turn it is for a given pick number.
 */
export function getActiveDrafter(
  pick: number,
  draftOrder: string[]
): string {
  return draftOrder[getSnakeIndex(pick)];
}

/**
 * Returns the 1-based round number for a given pick number.
 */
export function getRound(pick: number): number {
  return Math.floor((pick - 1) / TOTAL_DRAFTERS) + 1;
}
