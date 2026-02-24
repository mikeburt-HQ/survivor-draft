"use client";

import { useEffect, useState, useCallback } from "react";
import { supabase } from "@/lib/supabase";
import { Player, DraftState, TOTAL_PLAYERS } from "@/lib/types";
import { getActiveDrafter } from "@/lib/draft-logic";

export function useDraft() {
  const [players, setPlayers] = useState<Player[]>([]);
  const [draftState, setDraftState] = useState<DraftState | null>(null);
  const [loading, setLoading] = useState(true);

  // Initial fetch
  useEffect(() => {
    async function fetchAll() {
      const [playersRes, stateRes] = await Promise.all([
        supabase.from("players").select("*").order("id"),
        supabase.from("draft_state").select("*").eq("id", 1).single(),
      ]);
      if (playersRes.data) setPlayers(playersRes.data);
      if (stateRes.data) setDraftState(stateRes.data);
      setLoading(false);
    }
    fetchAll();
  }, []);

  // Real-time subscriptions
  useEffect(() => {
    const playersChannel = supabase
      .channel("players-changes")
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "players" },
        (payload) => {
          setPlayers((prev) =>
            prev.map((p) => (p.id === payload.new.id ? (payload.new as Player) : p))
          );
        }
      )
      .subscribe();

    const stateChannel = supabase
      .channel("draft-state-changes")
      .on(
        "postgres_changes",
        { event: "UPDATE", schema: "public", table: "draft_state" },
        (payload) => {
          setDraftState(payload.new as DraftState);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(playersChannel);
      supabase.removeChannel(stateChannel);
    };
  }, []);

  const randomizeDraftOrder = useCallback(async (names: string[]) => {
    const shuffled = [...names].sort(() => Math.random() - 0.5);
    await supabase
      .from("draft_state")
      .update({ draft_order: shuffled })
      .eq("id", 1);
  }, []);

  const startDraft = useCallback(async () => {
    await supabase
      .from("draft_state")
      .update({ status: "in_progress", current_pick: 1 })
      .eq("id", 1);
  }, []);

  const makePick = useCallback(
    async (playerId: number, drafterName: string) => {
      if (!draftState) return;

      const expectedDrafter = getActiveDrafter(
        draftState.current_pick,
        draftState.draft_order
      );
      if (drafterName !== expectedDrafter) return;

      const nextPick = draftState.current_pick + 1;
      const isComplete = draftState.current_pick >= TOTAL_PLAYERS;

      await supabase
        .from("players")
        .update({
          drafted_by: drafterName,
          draft_pick: draftState.current_pick,
        })
        .eq("id", playerId)
        .is("drafted_by", null);

      await supabase
        .from("draft_state")
        .update({
          current_pick: isComplete ? draftState.current_pick : nextPick,
          status: isComplete ? "complete" : "in_progress",
        })
        .eq("id", 1)
        .eq("current_pick", draftState.current_pick); // optimistic lock
    },
    [draftState]
  );

  const resetDraft = useCallback(async () => {
    await supabase
      .from("players")
      .update({ drafted_by: null, draft_pick: null })
      .neq("id", 0);
    await supabase
      .from("draft_state")
      .update({ status: "not_started", current_pick: 0, draft_order: [] })
      .eq("id", 1);
  }, []);

  return {
    players,
    draftState,
    loading,
    randomizeDraftOrder,
    startDraft,
    makePick,
    resetDraft,
  };
}
