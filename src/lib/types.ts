export interface Player {
  id: number;
  name: string;
  hometown: string;
  /**
   * Starting tribe, e.g. "Purple". Null until CBS reveals the tribe split at
   * the premiere — see TRIBE_COLORS. The UI groups by tribe automatically
   * once these are populated.
   */
  tribe: string | null;
  drafted_by: string | null;
  draft_pick: number | null;
}

export interface DraftState {
  id: number;
  draft_order: string[];
  current_pick: number;
  status: "not_started" | "in_progress" | "complete";
}

export const DRAFTER_NAMES = ["Mike", "Daron", "Will", "Cagney"] as const;
export type DrafterName = (typeof DRAFTER_NAMES)[number];

/**
 * Survivor 51 started with two tribes — Savu (Purple) and Toka (Yellow) — and
 * episode 4 split them into three by adding Dina (Red).
 *
 * Keys are COLOR words, not tribe names, so a label must carry its color:
 * write "Dina (Red)", not "Dina". getTribeColor matches the color word
 * anywhere in the string, case-insensitively; a label with no known color
 * word falls back to NO_TRIBE_COLOR, which is the same gray as "no tribe at
 * all" and therefore reads as missing data rather than as a new tribe.
 */
export const TRIBE_COLORS: Record<string, string> = {
  Purple: "#8B5CF6",
  Yellow: "#EAB308",
  Red: "#DC2626",
};

/** Neutral gray for a castaway with no tribe, or a tribe we have no color for. */
export const NO_TRIBE_COLOR = "#6B7280";

/**
 * Resolves a tribe label to its display color. Tolerant on purpose: an exact
 * key match wins, otherwise any color word appearing in the label wins, so a
 * real tribe name does not silently render gray.
 */
export function getTribeColor(tribe: string | null | undefined): string {
  if (!tribe) return NO_TRIBE_COLOR;

  const exact = Object.keys(TRIBE_COLORS).find(
    (key) => key.toLowerCase() === tribe.toLowerCase()
  );
  if (exact) return TRIBE_COLORS[exact];

  const contained = Object.keys(TRIBE_COLORS).find((key) =>
    new RegExp(`\\b${key}\\b`, "i").test(tribe)
  );
  return contained ? TRIBE_COLORS[contained] : NO_TRIBE_COLOR;
}

/** The 21 castaways on the board. */
export const TOTAL_PLAYERS = 21;

export const TOTAL_DRAFTERS = 4;

/**
 * 21 castaways do not divide evenly among 4 drafters, so the draft runs a
 * fixed 5 rounds and one castaway goes undrafted. TOTAL_ROUNDS is therefore
 * declared, NOT derived from TOTAL_PLAYERS / TOTAL_DRAFTERS.
 */
export const TOTAL_ROUNDS = 5;

/** Picks actually made: 20. Use this for completion, never TOTAL_PLAYERS. */
export const TOTAL_PICKS = TOTAL_ROUNDS * TOTAL_DRAFTERS;
