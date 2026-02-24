"use client";

import { useState } from "react";
import { useDraft } from "@/hooks/use-draft";
import { PreDraft } from "@/components/PreDraft";
import { DRAFTER_NAMES } from "@/lib/types";

export default function Home() {
  const { players, draftState, loading, randomizeDraftOrder, startDraft, makePick } = useDraft();
  const [myName, setMyName] = useState<string>("");

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

  // Placeholder for draft board — built in next tasks
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Draft in progress — pick {draftState.current_pick}</h1>
      <p>Board UI coming next...</p>
    </div>
  );
}
