export interface Player {
  id: number;
  name: string;
  tribe: string;
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

export const TRIBE_COLORS: Record<string, string> = {
  "Cila (Orange)": "#F97316",
  "Kalo (Teal)": "#14B8A6",
  "Vatu (Purple)": "#8B5CF6",
};

export const TOTAL_PLAYERS = 24;
export const TOTAL_DRAFTERS = 4;
export const TOTAL_ROUNDS = TOTAL_PLAYERS / TOTAL_DRAFTERS; // 6
