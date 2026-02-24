import { Player, TRIBE_COLORS } from "@/lib/types";

interface ConfirmModalProps {
  player: Player;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmModal({ player, onConfirm, onCancel }: ConfirmModalProps) {
  const tribeColor = TRIBE_COLORS[player.tribe] || "#6B7280";

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-8 max-w-sm w-full mx-4 shadow-2xl">
        <h2 className="text-xl font-bold mb-2">Confirm Pick</h2>
        <p className="text-lg mb-1">
          Draft <span className="font-bold">{player.name}</span>?
        </p>
        <p className="text-sm mb-6" style={{ color: tribeColor }}>
          {player.tribe}
        </p>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-3 bg-gray-200 rounded-lg font-semibold hover:bg-gray-300"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-3 bg-green-600 text-white rounded-lg font-semibold hover:bg-green-700"
          >
            Draft!
          </button>
        </div>
      </div>
    </div>
  );
}
