import type React from "react";
import { useEffect, useState } from "react";
import { useWebSocketContext } from "../../context/WebSocketContext";
import BidCardLifecycleView from "./BidCardLifecycleView";

interface BidCard {
  id: string;
  bid_card_number: string;
  status: "generated" | "collecting_bids" | "bids_complete" | "expired" | "active";
  project_type: string;
  contractor_count_needed?: number;
  bids_received?: number;
  progress_percentage?: number;
  // Legacy field names from old API
  progress?: number;
  target_bids?: number;
  created_at: string;
  updated_at: string;
  location: string;
  urgency_level?: string;
  last_activity: string;
  // Service complexity classification
  service_complexity?: "single-trade" | "multi-trade" | "complex-coordination";
  trade_count?: number;
  primary_trade?: string;
  secondary_trades?: string[];
  // Homeowner information
  user_id?: string;
  homeowner_name?: string;
  homeowner_email?: string;
  homeowner_phone?: string;
}

const BidCardMonitor: React.FC = () => {
  const [bidCards, setBidCards] = useState<BidCard[]>([]);
  const [filteredCards, setFilteredCards] = useState<BidCard[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedCard, setSelectedCard] = useState<string | null>(null);
  const [lifecycleViewCard, setLifecycleViewCard] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Filter states
  const [activeTab, setActiveTab] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [timelineFilter, setTimelineFilter] = useState<string>("all");
  const [outreachFilter, setOutreachFilter] = useState<string>("all");

  const { lastMessage, subscribe } = useWebSocketContext();

  // Update current time every minute for live countdown
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  // Load initial bid cards data
  useEffect(() => {
    const loadBidCards = async () => {
      try {
        const response = await fetch("/api/admin/bid-cards-enhanced", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("admin_session_id")}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setBidCards(data.bid_cards || []);
          setFilteredCards(data.bid_cards || []);
        } else {
          console.error("Failed to load bid cards");
        }
      } catch (error) {
        console.error("Error loading bid cards:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadBidCards();

    // Subscribe to bid card updates
    const unsubscribe = subscribe("bid_cards", () => {});

    return () => {
      if (typeof unsubscribe === 'function') {
        unsubscribe();
      }
    };
  }, [subscribe]);

  // Handle WebSocket updates
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === "bid_card_update") {
      const { bid_card_id, status, progress, additional_data } = lastMessage.data;

      setBidCards((prev) =>
        prev.map((card) =>
          card.id === bid_card_id
            ? {
                ...card,
                status: status,
                bids_received: progress.current,
                progress_percentage: progress.percentage,
                updated_at: new Date().toISOString(),
                last_activity: "Real-time update",
                ...additional_data,
              }
            : card
        )
      );
    }
  }, [lastMessage]);

  // Filtering effect
  useEffect(() => {
    let filtered = [...bidCards];

    // Filter by status tab
    if (activeTab !== "all") {
      if (activeTab === "needs_action") {
        // Show cards that need manual intervention
        filtered = filtered.filter(
          (card) =>
            card.status === "generated" ||
            (card.status === "collecting_bids" && isCardBehindSchedule(card))
        );
      } else if (activeTab === "outreach_active") {
        // Show cards with active contractor outreach
        filtered = filtered.filter(
          (card) => card.status === "collecting_bids" || card.status === "active"
        );
      } else if (activeTab === "timeline_issues") {
        // Show cards behind schedule
        filtered = filtered.filter((card) => isCardBehindSchedule(card));
      } else {
        // Filter by specific status
        filtered = filtered.filter((card) => card.status === activeTab);
      }
    }

    // Filter by search term
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (card) =>
          card.bid_card_number.toLowerCase().includes(search) ||
          card.project_type.toLowerCase().includes(search) ||
          card.id.toLowerCase().includes(search)
      );
    }

    // Filter by timeline performance
    if (timelineFilter !== "all") {
      filtered = filtered.filter((card) => {
        const performance = getTimelinePerformance(card);
        return performance === timelineFilter;
      });
    }

    // Filter by outreach status
    if (outreachFilter !== "all") {
      filtered = filtered.filter((card) => {
        const hasOutreach = hasActiveOutreach(card);
        if (outreachFilter === "with_outreach") return hasOutreach;
        if (outreachFilter === "no_outreach") return !hasOutreach;
        return true;
      });
    }

    setFilteredCards(filtered);
  }, [bidCards, activeTab, searchTerm, timelineFilter, outreachFilter, currentTime]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "generated":
        return "bg-blue-100 text-blue-800";
      case "collecting_bids":
        return "bg-yellow-100 text-yellow-800";
      case "bids_complete":
        return "bg-green-100 text-green-800";
      case "expired":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case "emergency":
        return "text-red-600";
      case "urgent":
        return "text-orange-600";
      case "standard":
        return "text-blue-600";
      case "flexible":
        return "text-green-600";
      default:
        return "text-gray-600";
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));

    if (diffInMinutes < 1) return "Just now";
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  const formatFullTimestamp = (timestamp: string) => {
    const time = new Date(timestamp);
    const now = currentTime; // Use live updated time
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    let runningTime = "";
    if (diffInDays > 0) {
      runningTime = `${diffInDays}d ${diffInHours % 24}h ${diffInMinutes % 60}m`;
    } else if (diffInHours > 0) {
      runningTime = `${diffInHours}h ${diffInMinutes % 60}m`;
    } else {
      runningTime = `${diffInMinutes}m`;
    }

    return {
      absolute: time.toLocaleString(),
      running: runningTime,
      relative: diffInMinutes < 1 ? "Just now" : formatTimeAgo(timestamp),
    };
  };

  const getUrgencyLabel = (urgency: string | null) => {
    if (!urgency) return "Standard";
    switch (urgency.toLowerCase()) {
      case "emergency":
        return "Emergency";
      case "urgent":
        return "Urgent";
      case "week":
        return "This Week";
      case "month":
        return "This Month";
      case "flexible":
        return "Flexible";
      default:
        return urgency.charAt(0).toUpperCase() + urgency.slice(1);
    }
  };

  const getContractorStrategy = (card: BidCard) => {
    // Handle both old and new field names
    const needed = card.contractor_count_needed || card.target_bids || 4;
    const urgency = card.urgency_level || "week";

    // InstaBids contractor outreach timing system (separate from project urgency)
    // This is how fast InstaBids collects bids, not when customer wants work done
    let timeframe = "TBD";
    let strategy = "Standard Outreach";
    let method = "Multi-tier Outreach";

    switch (urgency.toLowerCase()) {
      case "emergency":
        // < 1 hour: Emergency lockout/plumbing situations
        timeframe = "< 1 hour";
        strategy = `${needed} bids via pre-loaded contractors`;
        method = "Phone calls + SMS blast";
        break;
      case "urgent":
        // 1-12 hours: Same day collection (most common)
        timeframe = "1-12 hours";
        strategy = `${needed} bids same day`;
        method = "Tier 1 immediate + Tier 2 escalation";
        break;
      case "week":
        // 12-72 hours: 3-day max collection (standard business)
        timeframe = "12-72 hours";
        strategy = `${needed} bids within 3 days max`;
        method = "All tiers + quality filtering";
        break;
      case "month":
        // 72-120 hours: 5-day max (group bidding)
        timeframe = "72-120 hours";
        strategy = `${needed} bids within 5 days (group opportunities)`;
        method = "Group bidding + premium contractors";
        break;
      case "flexible":
        // 120+ hours: 5+ days absolute maximum
        timeframe = "5+ days max";
        strategy = `${needed} bids extended timeline`;
        method = "Comprehensive outreach + specialization";
        break;
      default:
        // Default to standard 3-day collection
        timeframe = "72 hours (default)";
        strategy = `${needed} bids within 3 days`;
        method = "Standard multi-tier approach";
    }

    return { timeframe, strategy, method };
  };

  const getBidDeadline = (card: BidCard) => {
    const createdAt = new Date(card.created_at);
    const urgency = card.urgency_level || "week";

    // InstaBids contractor outreach deadlines (business speed, not project timeline)
    let deadlineHours = 0;
    switch (urgency.toLowerCase()) {
      case "emergency":
        deadlineHours = 1; // < 1 hour for emergencies
        break;
      case "urgent":
        deadlineHours = 12; // 12 hours max for same-day collection
        break;
      case "week":
        deadlineHours = 72; // 72 hours (3 days) for standard collection
        break;
      case "month":
        deadlineHours = 120; // 120 hours (5 days) for group bidding
        break;
      case "flexible":
        deadlineHours = 168; // 168 hours (7 days) absolute maximum
        break;
      default:
        deadlineHours = 72; // Default to 3-day standard collection
    }

    const deadline = new Date(createdAt.getTime() + deadlineHours * 60 * 60 * 1000);
    return deadline;
  };

  const formatCountdown = (card: BidCard) => {
    const deadline = getBidDeadline(card);
    const now = currentTime;
    const timeLeft = deadline.getTime() - now.getTime();

    if (timeLeft <= 0) {
      return { text: "DEADLINE PASSED", isOverdue: true, percentage: 100 };
    }

    const totalTime = deadline.getTime() - new Date(card.created_at).getTime();
    const elapsed = now.getTime() - new Date(card.created_at).getTime();
    const percentage = Math.min((elapsed / totalTime) * 100, 100);

    const hoursLeft = Math.floor(timeLeft / (1000 * 60 * 60));
    const minutesLeft = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
    const daysLeft = Math.floor(hoursLeft / 24);

    let text = "";
    if (daysLeft > 0) {
      text = `${daysLeft}d ${hoursLeft % 24}h left`;
    } else if (hoursLeft > 0) {
      text = `${hoursLeft}h ${minutesLeft}m left`;
    } else {
      text = `${minutesLeft}m left`;
    }

    return { text, isOverdue: false, percentage };
  };

  const getProgressBarColor = (card: BidCard) => {
    const { isOverdue, percentage } = formatCountdown(card);

    if (card.status === "bids_complete") {
      return "bg-green-500";
    }

    if (isOverdue) {
      return "bg-red-600";
    }

    if (percentage > 85) {
      return "bg-red-500"; // Urgent - less than 15% time left
    } else if (percentage > 60) {
      return "bg-yellow-500"; // Warning - less than 40% time left
    } else {
      return "bg-blue-500"; // Good - plenty of time
    }
  };

  // Helper functions for filtering
  const isCardBehindSchedule = (card: BidCard): boolean => {
    const { percentage } = formatCountdown(card);
    const progressPercentage =
      ((card.bids_received || 0) / (card.contractor_count_needed || 1)) * 100;

    // Behind if time progress is ahead of bid progress by more than 25%
    return percentage > progressPercentage + 25 && card.status !== "bids_complete";
  };

  const getTimelinePerformance = (card: BidCard): string => {
    if (card.status === "bids_complete") return "completed";

    const { percentage, isOverdue } = formatCountdown(card);
    const progressPercentage =
      ((card.bids_received || 0) / (card.contractor_count_needed || 1)) * 100;

    if (isOverdue) return "behind";
    if (progressPercentage >= percentage + 10) return "ahead";
    if (progressPercentage >= percentage - 15) return "on_time";
    return "behind";
  };

  const hasActiveOutreach = (card: BidCard): boolean => {
    // This is a simplified check - in reality we'd check the campaigns table
    // For now, assume collecting_bids and active status means outreach is happening
    return card.status === "collecting_bids" || card.status === "active";
  };

  // Get status counts for tabs
  const getStatusCounts = () => {
    const counts = {
      all: bidCards.length,
      generated: bidCards.filter((c) => c.status === "generated").length,
      collecting_bids: bidCards.filter((c) => c.status === "collecting_bids").length,
      active: bidCards.filter((c) => c.status === "active").length,
      bids_complete: bidCards.filter((c) => c.status === "bids_complete").length,
      expired: bidCards.filter((c) => c.status === "expired").length,
      needs_action: bidCards.filter(
        (c) =>
          c.status === "generated" || (c.status === "collecting_bids" && isCardBehindSchedule(c))
      ).length,
      outreach_active: bidCards.filter(
        (c) => c.status === "collecting_bids" || c.status === "active"
      ).length,
      timeline_issues: bidCards.filter((c) => isCardBehindSchedule(c)).length,
    };
    return counts;
  };

  // Get critical alerts for cards that need immediate attention
  const getCriticalAlerts = () => {
    const alerts = [];

    bidCards.forEach((card) => {
      const { isOverdue, percentage } = formatCountdown(card);
      const performance = getTimelinePerformance(card);

      // Critical: Deadline passed
      if (isOverdue && card.status !== "bids_complete") {
        alerts.push({
          id: card.id,
          type: "overdue",
          severity: "critical",
          message: `${card.project_type} (${card.bid_card_number}) deadline has passed`,
          card: card,
          action: "Extend deadline or contact contractors directly",
        });
      }

      // High: Less than 2 hours remaining and no bids
      else if (
        percentage > 95 &&
        (card.bids_received || 0) === 0 &&
        card.status === "collecting_bids"
      ) {
        alerts.push({
          id: card.id,
          type: "urgent_no_bids",
          severity: "high",
          message: `${card.project_type} (${card.bid_card_number}) has less than 2 hours left with no bids`,
          card: card,
          action: "Expand contractor outreach or adjust requirements",
        });
      }

      // High: Severely behind schedule
      else if (performance === "behind" && percentage > 75) {
        const progressPercentage =
          ((card.bids_received || 0) / (card.contractor_count_needed || 1)) * 100;
        alerts.push({
          id: card.id,
          type: "behind_schedule",
          severity: "high",
          message: `${card.project_type} (${card.bid_card_number}) is ${Math.round(percentage)}% through timeline with only ${Math.round(progressPercentage)}% of bids`,
          card: card,
          action: "Escalate outreach or adjust timeline",
        });
      }

      // Medium: Generated cards sitting idle for more than 1 hour
      else if (card.status === "generated" && percentage > 10) {
        alerts.push({
          id: card.id,
          type: "idle_generated",
          severity: "medium",
          message: `${card.project_type} (${card.bid_card_number}) has been generated but not started for ${formatCountdown(card).text}`,
          card: card,
          action: "Start campaign or review requirements",
        });
      }
    });

    // Sort by severity: critical, high, medium
    alerts.sort((a, b) => {
      const severityOrder = { critical: 0, high: 1, medium: 2 };
      return severityOrder[a.severity] - severityOrder[b.severity];
    });

    return alerts;
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Bid Card Monitor</h3>
        <div className="animate-pulse space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">🔄 Live Bid Card Tracking</h3>
          <div className="flex items-center text-sm text-gray-500">
            <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
            <span>
              Real-time updates ({filteredCards.length} of {bidCards.length})
            </span>
          </div>
        </div>

        {/* Critical Alerts Banner */}
        {(() => {
          const alerts = getCriticalAlerts();
          if (alerts.length === 0) return null;

          return (
            <div className="mb-4 space-y-2">
              {alerts.slice(0, 3).map(
                (
                  alert // Show max 3 alerts
                ) => (
                  <div
                    key={alert.id}
                    className={`p-4 rounded-lg border-l-4 ${
                      alert.severity === "critical"
                        ? "bg-red-50 border-red-400 text-red-800"
                        : alert.severity === "high"
                          ? "bg-orange-50 border-orange-400 text-orange-800"
                          : "bg-yellow-50 border-yellow-400 text-yellow-800"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <div
                            className={`text-lg ${
                              alert.severity === "critical"
                                ? "text-red-600"
                                : alert.severity === "high"
                                  ? "text-orange-600"
                                  : "text-yellow-600"
                            }`}
                          >
                            {alert.severity === "critical"
                              ? "🚨"
                              : alert.severity === "high"
                                ? "⚠️"
                                : "⏰"}
                          </div>
                          <div className="text-sm font-medium uppercase tracking-wide">
                            {alert.severity === "critical"
                              ? "Critical"
                              : alert.severity === "high"
                                ? "High Priority"
                                : "Attention Needed"}
                          </div>
                        </div>
                        <div className="mt-1 text-sm font-medium">{alert.message}</div>
                        <div className="mt-1 text-xs opacity-75">
                          Recommended action: {alert.action}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setSelectedCard(alert.card.id)}
                          className={`px-3 py-1 text-xs rounded font-medium ${
                            alert.severity === "critical"
                              ? "bg-red-100 text-red-700 hover:bg-red-200"
                              : alert.severity === "high"
                                ? "bg-orange-100 text-orange-700 hover:bg-orange-200"
                                : "bg-yellow-100 text-yellow-700 hover:bg-yellow-200"
                          }`}
                        >
                          View Details
                        </button>
                      </div>
                    </div>
                  </div>
                )
              )}
              {alerts.length > 3 && (
                <div className="text-center">
                  <button
                    onClick={() => setActiveTab("needs_action")}
                    className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    View {alerts.length - 3} more alerts
                  </button>
                </div>
              )}
            </div>
          );
        })()}

        {/* Status Tabs */}
        <div className="flex flex-wrap gap-2 mb-4">
          {[
            { key: "all", label: "All", count: getStatusCounts().all },
            { key: "needs_action", label: "⚠️ Needs Action", count: getStatusCounts().needs_action },
            {
              key: "outreach_active",
              label: "📞 Active Outreach",
              count: getStatusCounts().outreach_active,
            },
            {
              key: "timeline_issues",
              label: "🕒 Behind Schedule",
              count: getStatusCounts().timeline_issues,
            },
            { key: "generated", label: "📋 Generated", count: getStatusCounts().generated },
            {
              key: "collecting_bids",
              label: "⚙️ Collecting",
              count: getStatusCounts().collecting_bids,
            },
            { key: "active", label: "✅ Active", count: getStatusCounts().active },
            { key: "bids_complete", label: "🎯 Complete", count: getStatusCounts().bids_complete },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-3 py-1 text-sm font-medium rounded-full transition-colors ${
                activeTab === tab.key
                  ? "bg-blue-100 text-blue-700 border border-blue-200"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>

        {/* Search and Filters */}
        <div className="flex flex-wrap gap-4">
          {/* Search */}
          <div className="flex-1 min-w-64">
            <input
              type="text"
              placeholder="Search by bid card number, project type, or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Timeline Filter */}
          <select
            value={timelineFilter}
            onChange={(e) => setTimelineFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Timeline</option>
            <option value="ahead">🚀 Ahead of Schedule</option>
            <option value="on_time">✅ On Time</option>
            <option value="behind">⚠️ Behind Schedule</option>
            <option value="completed">🎯 Completed</option>
          </select>

          {/* Outreach Filter */}
          <select
            value={outreachFilter}
            onChange={(e) => setOutreachFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Outreach</option>
            <option value="with_outreach">📞 With Outreach</option>
            <option value="no_outreach">❌ No Outreach</option>
          </select>

          {/* Clear Filters */}
          {(activeTab !== "all" ||
            searchTerm ||
            timelineFilter !== "all" ||
            outreachFilter !== "all") && (
            <button
              onClick={() => {
                setActiveTab("all");
                setSearchTerm("");
                setTimelineFilter("all");
                setOutreachFilter("all");
              }}
              className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md"
            >
              Clear All
            </button>
          )}
        </div>
      </div>

      <div className="p-6">
        {bidCards.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-4xl mb-4">📋</div>
            <p className="text-gray-500">No active bid cards</p>
            <p className="text-sm text-gray-400 mt-1">
              Bid cards will appear here when homeowners create projects
            </p>
          </div>
        ) : filteredCards.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-gray-400 text-4xl mb-4">🔍</div>
            <p className="text-gray-500">No bid cards match your filters</p>
            <p className="text-sm text-gray-400 mt-1">
              Try adjusting your search or filter criteria
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredCards.map((card) => (
              <div
                key={card.id}
                className={`border rounded-lg p-4 transition-all duration-200 cursor-pointer ${
                  selectedCard === card.id
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
                onClick={() => setSelectedCard(selectedCard === card.id ? null : card.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h4 className="font-medium text-gray-900">
                        {card.project_type} ({card.bid_card_number})
                      </h4>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(card.status)}`}
                      >
                        {card.status.replace("_", " ")}
                      </span>
                      <span
                        className={`text-xs font-medium ${getUrgencyColor(card.urgency_level)}`}
                      >
                        {getUrgencyLabel(card.urgency_level)}
                      </span>
                    </div>

                    <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                      <span>📍 {card.location}</span>
                      <span>🕒 Running: {formatFullTimestamp(card.created_at).running}</span>
                      <span>📅 Created: {formatFullTimestamp(card.created_at).absolute}</span>
                    </div>

                    {/* Homeowner Information */}
                    {(card.homeowner_name || card.user_id) && (
                      <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                        {card.homeowner_name && (
                          <span>👤 Homeowner: {card.homeowner_name}</span>
                        )}
                        {card.user_id && (
                          <span className="text-xs text-gray-500">ID: {card.user_id.slice(0, 8)}...</span>
                        )}
                        {card.homeowner_email && (
                          <span>📧 {card.homeowner_email}</span>
                        )}
                      </div>
                    )}

                    {/* Contractor Strategy Display */}
                    <div className="mt-2 flex items-center space-x-4 text-sm text-gray-600">
                      <span>🎯 Strategy: {getContractorStrategy(card).strategy}</span>
                      <span>⏱️ Collection: {getContractorStrategy(card).timeframe}</span>
                      <span>📋 Method: {getContractorStrategy(card).method}</span>
                    </div>

                    {/* Countdown Timer */}
                    <div className="mt-2 flex items-center space-x-4 text-sm">
                      <span className="text-gray-600">⏰ Deadline:</span>
                      <span
                        className={`font-medium ${
                          formatCountdown(card).isOverdue
                            ? "text-red-600"
                            : formatCountdown(card).percentage > 85
                              ? "text-red-500"
                              : formatCountdown(card).percentage > 60
                                ? "text-yellow-600"
                                : "text-blue-600"
                        }`}
                      >
                        {formatCountdown(card).text}
                      </span>
                      <span className="text-gray-500 text-xs">
                        (Due: {getBidDeadline(card).toLocaleString()})
                      </span>
                    </div>

                    {/* Enhanced Progress Bar */}
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-gray-600">
                          Bids Progress: {card.bids_received || card.progress || 0}/
                          {card.contractor_count_needed || card.target_bids || 4}
                        </span>
                        <div className="flex items-center space-x-2">
                          <span className="font-medium text-gray-900">
                            {(() => {
                              // Calculate progress percentage from current data
                              const bids = card.bids_received || card.progress || 0;
                              const target = card.contractor_count_needed || card.target_bids || 4;
                              return Math.round((bids / target) * 100);
                            })()}%
                          </span>
                          <span
                            className={`text-xs px-2 py-1 rounded ${
                              formatCountdown(card).isOverdue
                                ? "bg-red-100 text-red-700"
                                : formatCountdown(card).percentage > 85
                                  ? "bg-red-50 text-red-600"
                                  : formatCountdown(card).percentage > 60
                                    ? "bg-yellow-50 text-yellow-600"
                                    : "bg-blue-50 text-blue-600"
                            }`}
                          >
                            {Math.round(100 - formatCountdown(card).percentage)}% time left
                          </span>
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3 relative">
                        {/* Bid progress bar */}
                        <div
                          className={`h-3 rounded-full transition-all duration-500 ${getProgressBarColor(card)}`}
                          style={{
                            width: `${Math.min(
                              (() => {
                                const bids = card.bids_received || card.progress || 0;
                                const target =
                                  card.contractor_count_needed || card.target_bids || 4;
                                return (bids / target) * 100;
                              })(),
                              100
                            )}%`,
                          }}
                        ></div>
                        {/* Time progress indicator */}
                        <div
                          className="absolute top-0 h-3 bg-white bg-opacity-30 rounded-full"
                          style={{
                            left: `${Math.min(formatCountdown(card).percentage, 100)}%`,
                            width: "2px",
                          }}
                        ></div>
                      </div>
                      {/* Progress legend */}
                      <div className="flex items-center justify-between text-xs text-gray-500 mt-1">
                        <span>Bid collection target</span>
                        <span>Time remaining vs deadline</span>
                      </div>
                    </div>
                  </div>

                  <div className="ml-4 flex items-center">
                    {card.status === "bids_complete" && (
                      <div className="text-green-500 text-2xl">✅</div>
                    )}
                    {card.status === "collecting_bids" && (
                      <div className="text-blue-500 text-2xl animate-spin">⚙️</div>
                    )}
                    {card.status === "generated" && (
                      <div className="text-gray-500 text-2xl">⏳</div>
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {selectedCard === card.id && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-700">Created:</span>
                        <span className="ml-2 text-gray-600">
                          {new Date(card.created_at).toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Last Update:</span>
                        <span className="ml-2 text-gray-600">
                          {new Date(card.updated_at).toLocaleString()}
                        </span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Card ID:</span>
                        <span className="ml-2 text-gray-600 font-mono text-xs">{card.id}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Activity:</span>
                        <span className="ml-2 text-gray-600">{card.last_activity}</span>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="mt-4 flex space-x-2">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setLifecycleViewCard(card.id);
                        }}
                        className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                      >
                        View Lifecycle
                      </button>
                      {card.status === "collecting_bids" && (
                        <button
                          type="button"
                          className="px-3 py-1 text-xs bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 transition-colors"
                        >
                          Force Check
                        </button>
                      )}
                      {card.status === "generated" && (
                        <button
                          type="button"
                          className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                        >
                          Start Campaign
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Lifecycle View Modal */}
        {lifecycleViewCard && (
          <BidCardLifecycleView
            bidCardId={lifecycleViewCard}
            onClose={() => setLifecycleViewCard(null)}
          />
        )}
      </div>
    </div>
  );
};

export default BidCardMonitor;
