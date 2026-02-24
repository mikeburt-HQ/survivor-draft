import { Player, DraftState, TOTAL_ROUNDS, TOTAL_DRAFTERS, TRIBE_COLORS } from "@/lib/types";
import { getSnakeIndex } from "@/lib/draft-logic";

interface DraftBoardProps {
  players: Player[];
  draftState: DraftState;
}

export function DraftBoard({ players, draftState }: DraftBoardProps) {
  const { draft_order } = draftState;

  const grid: (Player | null)[][] = [];
  for (let round = 0; round < TOTAL_ROUNDS; round++) {
    const row: (Player | null)[] = [];
    for (let col = 0; col < TOTAL_DRAFTERS; col++) {
      const pickNumber = round * TOTAL_DRAFTERS + col + 1;
      const snakeCol = getSnakeIndex(pickNumber);
      const player = players.find((p) => p.draft_pick === pickNumber) || null;
      row[snakeCol] = player;
    }
    grid.push(row);
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Draft Board</h2>
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="p-2 text-sm text-gray-500">Round</th>
              {draft_order.map((name) => (
                <th key={name} className="p-2 text-center font-bold">
                  {name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {grid.map((row, roundIdx) => (
              <tr key={roundIdx} className="border-t">
                <td className="p-2 text-sm text-gray-500 text-center">{roundIdx + 1}</td>
                {row.map((player, colIdx) => {
                  const tribeColor = player ? TRIBE_COLORS[player.tribe] : undefined;
                  return (
                    <td
                      key={colIdx}
                      className="p-2 text-center border"
                      style={tribeColor ? { backgroundColor: `${tribeColor}20` } : {}}
                    >
                      {player ? (
                        <div>
                          <div className="font-semibold text-sm">{player.name}</div>
                          <div className="text-xs text-gray-500">#{player.draft_pick}</div>
                        </div>
                      ) : (
                        <div className="text-gray-300 text-sm">—</div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
