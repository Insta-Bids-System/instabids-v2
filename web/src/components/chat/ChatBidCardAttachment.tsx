import { ArrowRight, Clock, DollarSign, ExternalLink, MapPin, Users } from "lucide-react";
import type React from "react";

interface BidCard {
  id: string;
  bid_card_number: string;
  title: string;
  description: string;
  project_type: string;
  location_city: string;
  location_state: string;
  budget_min: number;
  budget_max: number;
  timeline?: {
    start_date: string;
    duration?: string;
  };
  urgency_level: string;
  bids_received_count: number;
  contractor_count_needed: number;
  group_buying_eligible?: boolean;
  status: string;
  created_at: string;
}

interface ChatBidCardAttachmentProps {
  bidCards: BidCard[];
  aiRecommendation?: string;
  onCardClick?: (card: BidCard) => void;
}

const ChatBidCardAttachment: React.FC<ChatBidCardAttachmentProps> = ({
  bidCards,
  aiRecommendation,
  onCardClick,
}) => {
  
  const handleCardClick = (card: BidCard) => {
    if (onCardClick) {
      onCardClick(card);
    } else {
      // Default action: Navigate to submit proposal page
      const submitUrl = `/contractor/submit-proposal?bid=${card.bid_card_number}`;
      window.open(submitUrl, "_blank");
    }
  };

  const formatBudget = (min: number, max: number) => {
    if (!min && !max) {
      return "Budget TBD";
    }
    if (!min) {
      return max ? `Up to $${max.toLocaleString()}` : "Budget TBD";
    }
    if (max && max > min) {
      return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    }
    return `$${min.toLocaleString()}+`;
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case "emergency":
        return "text-red-600 bg-red-50 border-red-200";
      case "urgent":
        return "text-orange-600 bg-orange-50 border-orange-200";
      case "flexible":
        return "text-green-600 bg-green-50 border-green-200";
      default:
        return "text-blue-600 bg-blue-50 border-blue-200";
    }
  };

  const getBidProgress = (received: number, needed: number) => {
    const percentage = (received / needed) * 100;
    return Math.min(100, percentage);
  };

  if (!bidCards || bidCards.length === 0) {
    return null;
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4 my-3 border border-gray-200">
      {/* AI Recommendation Header */}
      {aiRecommendation && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border-l-4 border-blue-400">
          <p className="text-sm text-blue-800">
            <strong>🤖 AI Recommendation:</strong> {aiRecommendation}
          </p>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
        <h3 className="font-semibold text-gray-900">
          {bidCards.length === 1
            ? "Matching Project Found"
            : `${bidCards.length} Matching Projects Found`}
        </h3>
      </div>

      {/* Bid Cards Grid */}
      <div className="space-y-3">
        {bidCards.map((card) => (
          <div
            key={card.id}
            className="bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200 cursor-pointer"
            onClick={() => handleCardClick(card)}
          >
            {/* Card Header */}
            <div className="p-4 border-b border-gray-100">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900 text-sm mb-1">{card.title}</h4>
                  <div className="flex items-center gap-4 text-xs text-gray-600">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3" />
                      {card.location_city}, {card.location_state}
                    </span>
                    <span className="flex items-center gap-1">
                      <DollarSign className="w-3 h-3" />
                      {formatBudget(card.budget_min, card.budget_max)}
                    </span>
                  </div>
                </div>

                {/* Urgency Badge */}
                <span
                  className={`px-2 py-1 rounded-full text-xs font-medium border ${getUrgencyColor(card.urgency_level)}`}
                >
                  {card.urgency_level.charAt(0).toUpperCase() + card.urgency_level.slice(1)}
                </span>
              </div>
            </div>

            {/* Card Body */}
            <div className="p-4">
              {/* Description */}
              {card.description && (
                <p className="text-sm text-gray-700 mb-3 line-clamp-2">
                  {card.description.substring(0, 120)}
                  {card.description.length > 120 ? "..." : ""}
                </p>
              )}

              {/* Timeline */}
              {card.timeline?.start_date && (
                <div className="flex items-center gap-1 mb-2 text-sm text-gray-600">
                  <Clock className="w-4 h-4" />
                  <span>Start: {card.timeline.start_date}</span>
                  {card.timeline.duration && (
                    <span className="text-gray-500">• Duration: {card.timeline.duration}</span>
                  )}
                </div>
              )}

              {/* Bid Progress */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2 text-sm">
                  <Users className="w-4 h-4 text-gray-500" />
                  <span className="text-gray-700">
                    {card.bids_received_count}/{card.contractor_count_needed} bids received
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{
                        width: `${getBidProgress(card.bids_received_count, card.contractor_count_needed)}%`,
                      }}
                    ></div>
                  </div>
                  <span className="text-xs text-gray-500">
                    {Math.round(
                      getBidProgress(card.bids_received_count, card.contractor_count_needed)
                    )}
                    %
                  </span>
                </div>
              </div>

              {/* Group Bidding Badge */}
              {card.group_buying_eligible && (
                <div className="mb-3">
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 text-xs font-medium rounded-full border border-green-200">
                    👥 Group Bidding Available - Save 15-25%
                  </span>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    const messageUrl = `/contractor/message?bid=${card.bid_card_number}&action=chat`;
                    window.open(messageUrl, "_blank");
                  }}
                  className="flex-1 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  Message Homeowner
                </button>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCardClick(card);
                  }}
                  className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors duration-200 flex items-center justify-center gap-2"
                >
                  Submit Proposal
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer Actions */}
      {bidCards.length > 1 && (
        <div className="mt-4 pt-3 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Showing top {bidCards.length} results</span>
            <button className="text-blue-600 hover:text-blue-700 font-medium">
              View All Projects →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatBidCardAttachment;
