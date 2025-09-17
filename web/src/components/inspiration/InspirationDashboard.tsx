import { Grid3X3, Image as ImageIcon, MessageSquare, Plus, Sparkles } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/lib/supabase";
import BoardCreator from "./BoardCreator";
import BoardView from "./BoardView";
import FloatingIrisChat from "../unified/FloatingIrisChat";
import { useIris } from "@/contexts/IrisContext";
import PotentialBidCardsInspiration from "./PotentialBidCardsInspiration";

export interface InspirationBoard {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  room_type?: string;
  status: "collecting" | "organizing" | "refining" | "ready";
  cover_image_id?: string;
  ai_insights?: any;
  created_at: string;
  updated_at: string;
  image_count?: number;
}

const InspirationDashboard: React.FC = () => {
  const { user } = useAuth();
  const { setBoardContext, clearContext } = useIris();
  const [boards, setBoards] = useState<InspirationBoard[]>([]);
  const [loading, setLoading] = useState(true);
  const [showBoardCreator, setShowBoardCreator] = useState(false);
  const [selectedBoard, setSelectedBoard] = useState<InspirationBoard | null>(null);

  const loadBoards = async () => {
    try {
      setLoading(true);

      // Load boards with image count
      const { data: boardsData, error: boardsError } = await supabase
        .from("inspiration_boards")
        .select(`
          *,
          inspiration_images(count)
        `)
        .eq("user_id", user?.id)
        .order("created_at", { ascending: false });

      if (boardsError) throw boardsError;

      // Transform the data to include image count
      const boardsWithCount =
        boardsData?.map((board) => ({
          ...board,
          image_count: board.inspiration_images?.[0]?.count || 0,
        })) || [];

      setBoards(boardsWithCount);
    } catch (error) {
      console.error("Error loading boards:", error);
      toast.error("Failed to load inspiration boards");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      loadBoards();
    } else {
      // Stop loading if no user
      setLoading(false);
    }
  }, [user]);

  const handleCreateBoard = async (boardData: Partial<InspirationBoard>) => {
    try {
      if (!user) {
        toast.error("Please sign in to create boards");
        return;
      }

      // For authenticated users, use direct Supabase access
      const { data, error } = await supabase
        .from("inspiration_boards")
        .insert({
          ...boardData,
          user_id: user.id,
          status: "collecting",
        })
        .select()
        .single();

      if (error) throw error;

      toast.success("Board created successfully!");
      setBoards([data, ...boards]);
      setShowBoardCreator(false);
    } catch (error) {
      console.error("Error creating board:", error);
      toast.error("Failed to create board");
    }
  };

  const handleBoardClick = (board: InspirationBoard) => {
    setSelectedBoard(board);
    // Set board context for IRIS when viewing a specific board
    setBoardContext(board.id);
  };

  const getStatusColor = (status: InspirationBoard["status"]) => {
    switch (status) {
      case "collecting":
        return "bg-blue-100 text-blue-800";
      case "organizing":
        return "bg-yellow-100 text-yellow-800";
      case "refining":
        return "bg-purple-100 text-purple-800";
      case "ready":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusLabel = (status: InspirationBoard["status"]) => {
    switch (status) {
      case "collecting":
        return "🌱 Collecting Ideas";
      case "organizing":
        return "🏗️ Organizing";
      case "refining":
        return "🎯 Refining Vision";
      case "ready":
        return "🚀 Ready for Bids";
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-2xl mx-auto py-12">
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Please Sign In
          </h2>
          <p className="text-gray-600 mb-6">
            You need to be signed in to view your inspiration boards.
          </p>
          <a
            href="/login"
            className="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors"
          >
            Sign In
          </a>
        </div>
      </div>
    );
  }

  if (selectedBoard) {
    return (
      <>
        <BoardView
          board={selectedBoard}
          onBack={() => {
            setSelectedBoard(null);
            // Clear board context when leaving board view
            clearContext();
          }}
          onBoardUpdate={(updatedBoard) => {
            setBoards((prev) => prev.map((b) => (b.id === updatedBoard.id ? updatedBoard : b)));
            setSelectedBoard(updatedBoard);
          }}
        />

        {/* Floating IRIS Chat - automatically available with board context */}
        <FloatingIrisChat
          boardId={selectedBoard.id}
          initialContext="inspiration"
        />
      </>
    );
  }

  return (
    <div className="relative">
      {/* Header */}
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">My Inspiration Boards</h1>
          <p className="text-gray-600">Collect and organize your home improvement ideas</p>
        </div>
        <div className="flex gap-4">
          <button
            type="button"
            onClick={() => setShowBoardCreator(true)}
            className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            New Board
          </button>
        </div>
      </div>

      {/* Potential Bid Cards Section */}
      <div className="mb-8">
        <PotentialBidCardsInspiration userId={user?.id} />
      </div>

      {/* Empty State */}
      {boards.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="mx-auto w-24 h-24 bg-primary-100 rounded-full flex items-center justify-center mb-6">
            <Sparkles className="w-12 h-12 text-primary-600" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Start Your First Inspiration Board
          </h2>
          <p className="text-gray-600 mb-6 max-w-md mx-auto">
            Collect images from anywhere, organize your ideas, and turn your dream into reality with
            AI assistance.
          </p>
          <button
            type="button"
            onClick={() => setShowBoardCreator(true)}
            className="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Create Your First Board
          </button>
        </div>
      ) : (
        /* Board Grid */
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {boards.map((board) => (
            <div
              key={board.id}
              onClick={() => handleBoardClick(board)}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer overflow-hidden group"
            >
              {/* Cover Image or Placeholder */}
              <div className="aspect-video bg-gray-100 relative overflow-hidden">
                {board.cover_image_id ? (
                  <img
                    src={`/api/placeholder/400/225`}
                    alt={board.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Grid3X3 className="w-12 h-12 text-gray-400" />
                  </div>
                )}

                {/* Status Badge */}
                <div className="absolute top-2 right-2">
                  <span
                    className={`text-xs px-2 py-1 rounded-full ${getStatusColor(board.status)}`}
                  >
                    {getStatusLabel(board.status)}
                  </span>
                </div>

                {/* Image Count */}
                {board.image_count > 0 && (
                  <div className="absolute bottom-2 left-2 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
                    <ImageIcon className="w-3 h-3" />
                    {board.image_count}
                  </div>
                )}
              </div>

              {/* Board Info */}
              <div className="p-4">
                <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-primary-600 transition-colors">
                  {board.title}
                </h3>
                {board.description && (
                  <p className="text-sm text-gray-600 line-clamp-2">{board.description}</p>
                )}
                {board.room_type && (
                  <div className="mt-2">
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {board.room_type}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Board Creator Modal */}
      {showBoardCreator && (
        <BoardCreator onClose={() => setShowBoardCreator(false)} onCreate={handleCreateBoard} />
      )}

      {/* Floating IRIS Chat - available on main dashboard */}
      <FloatingIrisChat initialContext="inspiration" />
    </div>
  );
};

export default InspirationDashboard;
