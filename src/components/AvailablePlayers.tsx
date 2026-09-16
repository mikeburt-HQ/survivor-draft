import { Player } from "@/lib/types";
import { PlayerCard } from "./PlayerCard";

interface AvailablePlayersProps {
  players: Player[];
  isMyTurn: boolean;
  onDraft: (playerId: number) => void;
}

/**
 * Groups castaways by starting tribe. Survivor 51's tribe split is not public
 * until the premiere, so while every `tribe` is null this renders one flat
 * list. Populate tribes in seed.sql and the grouped view appears on its own.
 */
function groupByTribe(players: Player[]): { tribe: string | null; members: Player[] }[] {
  const tribes = [...new Set(players.map((p) => p.tribe).filter(Boolean))] as string[];

  if (tribes.length === 0) {
    return [{ tribe: null, members: players }];
  }

  const groups = tribes.sort().map((tribe) => ({
    tribe: tribe as string | null,
    members: players.filter((p) => p.tribe === tribe),
  }));

  // Anyone still unassigned keeps a home at the bottom rather than vanishing.
  const unassigned = players.filter((p) => !p.tribe);
  if (unassigned.length > 0) {
    groups.push({ tribe: null, members: unassigned });
  }

  return groups;
}

export function AvailablePlayers({ players, isMyTurn, onDraft }: AvailablePlayersProps) {
  const grouped = groupByTribe(players);
  const showTribeHeadings = grouped.some(({ tribe }) => tribe !== null);

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold">Available Players</h2>
      {grouped.map(({ tribe, members }) => (
        <div key={tribe ?? "unassigned"}>
          {showTribeHeadings && (
            <h3 className="text-lg font-semibold mb-2">
              {tribe ? `${tribe} Tribe` : "Not yet assigned"}
            </h3>
          )}
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
