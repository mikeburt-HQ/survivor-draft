"use client";

import { useState } from "react";
import { DraftState, DRAFTER_NAMES } from "@/lib/types";

interface PreDraftProps {
  draftState: DraftState;
  onSelectName: (name: string) => void;
  onRandomize: () => void;
  onStart: () => void;
}

export function PreDraft({ draftState, onSelectName, onRandomize, onStart }: PreDraftProps) {
  const [selectedName, setSelectedName] = useState<string>("");
  const hasOrder = draftState.draft_order.length > 0;

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-8 p-8">
      <h1 className="text-4xl font-bold">Survivor 50 Fantasy Draft</h1>
      <p className="text-lg text-gray-600">Pick your name to join the draft</p>

      <div className="flex gap-3">
        {DRAFTER_NAMES.map((name) => (
          <button
            key={name}
            onClick={() => {
              setSelectedName(name);
              onSelectName(name);
            }}
            className={`px-6 py-3 rounded-lg text-lg font-semibold transition-all ${
              selectedName === name
                ? "bg-green-600 text-white scale-105"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            {name}
          </button>
        ))}
      </div>

      {hasOrder && (
        <div className="text-center">
          <p className="text-lg font-semibold mb-2">Draft Order:</p>
          <div className="flex gap-4">
            {draftState.draft_order.map((name, i) => (
              <span key={name} className="text-xl">
                {i + 1}. {name}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-4">
        <button
          onClick={onRandomize}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700"
        >
          Randomize Draft Order
        </button>
        <button
          onClick={onStart}
          disabled={!hasOrder || !selectedName}
          className="px-6 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Start Draft
        </button>
      </div>
    </div>
  );
}
