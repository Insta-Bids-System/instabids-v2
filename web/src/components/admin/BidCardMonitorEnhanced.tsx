import { Download, Filter, RefreshCw } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { useWebSocketContext } from "../../context/WebSocketContext";
import { AdminBidCardEnhanced } from "./AdminBidCardEnhanced";

export interface EnhancedBidCard {
  id: string;
  bid_card_number: string;
  project_type: string;
  status: string;

  // All the enhanced fields
  homeowner_name?: string;
  homeowner_email?: string;
  homeowner_phone?: string;
  urgency_level?: string;
  complexity_score?: number;
  budget_min?: number;
  budget_max?: number;
  timeline_weeks?: number;
  location_city?: string;
  location_state?: string;
  location_zip?: string;
  contractor_count_needed?: number;
  bid_count?: number;
  interested_contractors?: number;
  bids_target_met?: boolean;

  campaign?: {
    max_contractors?: number;
    contractors_targeted?: number;
    contractors_responded?: number;
    status?: string;
  };

  outreach?: {
    email_sent?: number;
    forms_sent?: number;
    sms_sent?: number;
    total_attempts?: number;
    successful_deliveries?: number;
  };

  views_count?: number;
  last_viewed?: string;
  created_at?: string;
  updated_at?: string;
  next_checkin?: string;
}

const BidCardMonitorEnhanced: React.FC = () => {
  const [bidCards, setBidCards] = useState<EnhancedBidCard[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "active" | "completed">("all");
  const [sortBy, setSortBy] = useState<"recent" | "urgency" | "progress">("recent");

  const { lastMessage, subscribe } = useWebSocketContext();

  // Load enhanced bid cards data
  useEffect(() => {
    const loadBidCards = async () => {
      try {
        const response = await fetch(
          "/api/admin/bid-cards-enhanced?limit=50",
          {
            headers: {
              Authorization: `Bearer ${localStorage.getItem("admin_session_id")}`,
            },
          }
        );

        if (response.ok) {
          const data = await response.json();
          setBidCards(data.bid_cards || []);
        } else {
          console.error("Failed to load enhanced bid cards");
        }
      } catch (error) {
        console.error("Error loading enhanced bid cards:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadBidCards();

    // Polling disabled for performance - use manual refresh instead
    // const interval = setInterval(loadBidCards, 30000);
    // return () => clearInterval(interval);
  }, []);

  // Handle WebSocket updates
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === "bid_card_update") {
      const updatedCard = lastMessage.data;
      setBidCards((prev) =>
        prev.map((card) => (card.id === updatedCard.id ? { ...card, ...updatedCard } : card))
      );
    } else if (lastMessage.type === "new_bid_card") {
      setBidCards((prev) => [lastMessage.data, ...prev]);
    }
  }, [lastMessage]);

  // Filter and sort cards
  const filteredAndSortedCards = bidCards
    .filter((card) => {
      if (filter === "all") return true;
      if (filter === "active")
        return ["active", "discovery", "collecting_bids"].includes(card.status);
      if (filter === "completed")
        return ["completed", "awarded", "cancelled"].includes(card.status);
      return true;
    })
    .sort((a, b) => {
      if (sortBy === "recent") {
        return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
      }
      if (sortBy === "urgency") {
        const urgencyScore = (card: EnhancedBidCard) => {
          if (card.urgency_level === "week") return 3;
          if (card.urgency_level === "month") return 2;
          return 1;
        };
        return urgencyScore(b) - urgencyScore(a);
      }
      if (sortBy === "progress") {
        const progress = (card: EnhancedBidCard) =>
          (card.bid_count || 0) / Math.max(card.contractor_count_needed || 1, 1);
        return progress(b) - progress(a);
      }
      return 0;
    });

  const handleExport = () => {
    // Export bid cards data as CSV
    const csv = [
      ["Bid Card", "Status", "Homeowner", "Project Type", "Budget", "Progress", "Created"],
      ...filteredAndSortedCards.map((card) => [
        card.bid_card_number,
        card.status,
        card.homeowner_name || "Unknown",
        card.project_type,
        `$${card.budget_min}-${card.budget_max}`,
        `${card.bid_count}/${card.contractor_count_needed}`,
        new Date(card.created_at || "").toLocaleDateString(),
      ]),
    ]
      .map((row) => row.join(","))
      .join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `bid-cards-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Enhanced Bid Card Monitor</h3>
        <div className="animate-pulse space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">📊 Enhanced Bid Card Dashboard</h3>
            <p className="text-sm text-gray-500 mt-1">
              Complete lifecycle tracking with real-time updates
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="p-2 text-gray-400 hover:text-gray-600"
              title="Refresh"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
            <button
              type="button"
              onClick={handleExport}
              className="p-2 text-gray-400 hover:text-gray-600"
              title="Export CSV"
            >
              <Download className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Filters and Sorting */}
      <div className="px-6 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as any)}
                className="text-sm border-gray-300 rounded-md"
              >
                <option value="all">All Bid Cards</option>
                <option value="active">Active Only</option>
                <option value="completed">Completed</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">Sort by:</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="text-sm border-gray-300 rounded-md"
              >
                <option value="recent">Most Recent</option>
                <option value="urgency">Urgency</option>
                <option value="progress">Progress</option>
              </select>
            </div>
          </div>
          <div className="text-sm text-gray-500">{filteredAndSortedCards.length} bid cards</div>
        </div>
      </div>

      <div className="p-6">
        {filteredAndSortedCards.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-4xl mb-4">📋</div>
            <p className="text-gray-500">No bid cards match your filters</p>
            <button
              type="button"
              onClick={() => setFilter("all")}
              className="text-sm text-blue-600 hover:text-blue-700 mt-2"
            >
              Clear filters
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredAndSortedCards.map((card) => (
              <AdminBidCardEnhanced
                key={card.id}
                bidCard={card}
                onStatusChange={(id, status) => {
                  // Handle status changes
                  console.log(`Status change: ${id} -> ${status}`);
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default BidCardMonitorEnhanced;
