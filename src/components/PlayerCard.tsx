import { Player, TRIBE_COLORS } from "@/lib/types";

interface PlayerCardProps {
  player: Player;
  isMyTurn: boolean;
  onDraft: (playerId: number) => void;
}

export function PlayerCard({ player, isMyTurn, onDraft }: PlayerCardProps) {
  const isDrafted = player.drafted_by !== null;
  const tribeColor = TRIBE_COLORS[player.tribe] || "#6B7280";

  return (
    <button
      onClick={() => !isDrafted && isMyTurn && onDraft(player.id)}
      disabled={isDrafted || !isMyTurn}
      className={`w-full text-left p-3 rounded-lg border-2 transition-all ${
        isDrafted
          ? "opacity-50 cursor-default border-gray-300 bg-gray-100"
          : isMyTurn
          ? "cursor-pointer hover:scale-[1.02] hover:shadow-md border-gray-300 bg-white"
          : "cursor-default border-gray-200 bg-white"
      }`}
      style={{ borderLeftColor: tribeColor, borderLeftWidth: "4px" }}
    >
      <div className="font-semibold">{player.name}</div>
      <div className="text-sm text-gray-500">{player.tribe}</div>
      {isDrafted && (
        <div className="text-sm font-medium text-gray-600 mt-1">
          Drafted by {player.drafted_by} (#{player.draft_pick})
        </div>
      )}
    </button>
  );
}
