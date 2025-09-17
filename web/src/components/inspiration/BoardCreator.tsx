import { Sparkles, X } from "lucide-react";
import type React from "react";
import { useState } from "react";
import type { InspirationBoard } from "./InspirationDashboard";

interface BoardCreatorProps {
  onClose: () => void;
  onCreate: (boardData: Partial<InspirationBoard>) => void;
}

const ROOM_TYPES = [
  { value: "kitchen", label: "Kitchen", icon: "🍳" },
  { value: "bathroom", label: "Bathroom", icon: "🚿" },
  { value: "bedroom", label: "Bedroom", icon: "🛏️" },
  { value: "living_room", label: "Living Room", icon: "🛋️" },
  { value: "dining_room", label: "Dining Room", icon: "🍽️" },
  { value: "outdoor", label: "Outdoor", icon: "🌳" },
  { value: "office", label: "Home Office", icon: "💼" },
  { value: "basement", label: "Basement", icon: "🏠" },
  { value: "garage", label: "Garage", icon: "🚗" },
  { value: "other", label: "Other", icon: "✨" },
];

const BoardCreator: React.FC<BoardCreatorProps> = ({ onClose, onCreate }) => {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [roomType, setRoomType] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) return;

    setIsSubmitting(true);

    const boardData: Partial<InspirationBoard> = {
      title: title.trim(),
      description: description.trim() || undefined,
      room_type: roomType || undefined,
      status: "collecting",
    };

    await onCreate(boardData);
    setIsSubmitting(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Create New Board</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Title Input */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
              Board Name *
            </label>
            <input
              type="text"
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Kitchen Renovation Ideas"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              required
            />
          </div>

          {/* Description Input */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description (optional)
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What's your vision for this space?"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
            />
          </div>

          {/* Room Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Room Type (optional)
            </label>
            <div className="grid grid-cols-3 gap-2">
              {ROOM_TYPES.map((room) => (
                <button
                  key={room.value}
                  type="button"
                  onClick={() => setRoomType(room.value)}
                  className={`
                    flex flex-col items-center p-3 border rounded-lg transition-all
                    ${
                      roomType === room.value
                        ? "border-primary-500 bg-primary-50 text-primary-700"
                        : "border-gray-300 hover:border-gray-400 text-gray-700"
                    }
                  `}
                >
                  <span className="text-2xl mb-1">{room.icon}</span>
                  <span className="text-xs">{room.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-blue-800">
                <strong>Tip:</strong> Give your board a descriptive name to help you stay organized.
                You can always add more details later!
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={!title.trim() || isSubmitting}
            >
              {isSubmitting ? "Creating..." : "Create Board"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BoardCreator;
