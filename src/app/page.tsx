"use client";

import { useState } from "react";
import { useDraft } from "@/hooks/use-draft";
import { PreDraft } from "@/components/PreDraft";
import { AvailablePlayers } from "@/components/AvailablePlayers";
import { DraftBoard } from "@/components/DraftBoard";
import { ConfirmModal } from "@/components/ConfirmModal";
import { DRAFTER_NAMES, Player } from "@/lib/types";
import { getActiveDrafter, getRound } from "@/lib/draft-logic";

export default function Home() {
  const { players, draftState, loading, randomizeDraftOrder, startDraft, makePick, resetDraft } = useDraft();
  const [myName, setMyName] = useState<string>("");
  const [pendingPick, setPendingPick] = useState<Player | null>(null);

  if (loading || !draftState) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-xl">Loading draft...</p>
      </div>
    );
  }

  if (draftState.status === "not_started") {
    return (
      <PreDraft
        draftState={draftState}
        onSelectName={setMyName}
        onRandomize={() => randomizeDraftOrder([...DRAFTER_NAMES])}
        onStart={startDraft}
      />
    );
  }

  const activeDrafter =
    draftState.status === "in_progress"
      ? getActiveDrafter(draftState.current_pick, draftState.draft_order)
      : null;
  const isMyTurn = activeDrafter === myName;
  const round = draftState.status === "in_progress" ? getRound(draftState.current_pick) : null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Bar */}
      <header className="bg-white shadow-sm p-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold">Survivor 50 Fantasy Draft</h1>
            {myName === "Mike" && (
              <button
                onClick={() => {
                  if (window.confirm("Reset the entire draft? This clears all picks.")) {
                    resetDraft();
                  }
                }}
                className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
              >
                Reset Draft
              </button>
            )}
          </div>
          {draftState.status === "in_progress" ? (
            <div className="text-right">
              <div className="text-2xl font-bold">
                {isMyTurn ? "Your Pick!" : `${activeDrafter}'s Pick`}
              </div>
              <div className="text-sm text-gray-500">
                Round {round} of 6 — Pick #{draftState.current_pick}
              </div>
            </div>
          ) : (
            <div className="text-2xl font-bold text-green-600">Draft Complete!</div>
          )}
        </div>
      </header>

      {/* Name selector if not yet chosen */}
      {!myName && draftState.status === "in_progress" && (
        <div className="bg-yellow-50 border-b border-yellow-200 p-4">
          <div className="max-w-7xl mx-auto flex items-center gap-4">
            <span className="font-semibold">Who are you?</span>
            {draftState.draft_order.map((name) => (
              <button
                key={name}
                onClick={() => setMyName(name)}
                className="px-4 py-2 bg-white border rounded-lg hover:bg-gray-50"
              >
                {name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="max-w-7xl mx-auto p-4 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <AvailablePlayers
            players={players}
            isMyTurn={isMyTurn}
            onDraft={(id) => {
              const player = players.find((p) => p.id === id);
              if (player) setPendingPick(player);
            }}
          />
        </div>
        <div>
          <DraftBoard players={players} draftState={draftState} />
        </div>
      </div>

      {/* Confirmation Modal */}
      {pendingPick && (
        <ConfirmModal
          player={pendingPick}
          onConfirm={() => {
            makePick(pendingPick.id, myName);
            setPendingPick(null);
          }}
          onCancel={() => setPendingPick(null)}
        />
      )}
    </div>
  );
}
