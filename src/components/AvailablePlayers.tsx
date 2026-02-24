import { Player } from "@/lib/types";
import { PlayerCard } from "./PlayerCard";

interface AvailablePlayersProps {
  players: Player[];
  isMyTurn: boolean;
  onDraft: (playerId: number) => void;
}

const TRIBE_ORDER = ["Cila (Orange)", "Kalo (Teal)", "Vatu (Purple)"];

export function AvailablePlayers({ players, isMyTurn, onDraft }: AvailablePlayersProps) {
  const grouped = TRIBE_ORDER.map((tribe) => ({
    tribe,
    members: players.filter((p) => p.tribe === tribe),
  }));

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Available Players</h2>
      {grouped.map(({ tribe, members }) => (
        <div key={tribe}>
          <h3 className="text-lg font-semibold mb-2">{tribe}</h3>
          <div className="grid gap-2">
            {members.map((player) => (
              <PlayerCard
                key={player.id}
                player={player}
                isMyTurn={isMyTurn}
                onDraft={onDraft}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
