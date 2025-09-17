import { ArrowRight, CheckCircle, Clock, MapPin, Trash2, Edit3 } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { useAgentActivity } from "../../hooks/useAgentActivity";
import { AgentActivityIndicator } from "../ui/AgentActivityIndicator";
import { BidCardEditModal } from "./BidCardEditModal";

interface PotentialBidCardProps {
  bidCard: {
    id: string;
    title: string;
    project_type: string;
    zip_code?: string;
    timeline?: string;
    urgency_level?: string;
    user_scope_notes?: string;
    completion_percentage: number;
    ready_for_conversion: boolean;
    completion_info?: {
      completion_percentage: number;
      missing_fields: string[];
      ready_for_conversion: boolean;
    };
  };
  onReview: (bidCard: any) => void;
  onDelete?: (bidCardId: string) => void;
  onBidCardUpdate?: () => void;
}

const PotentialBidCard: React.FC<PotentialBidCardProps> = ({ bidCard, onReview, onDelete, onBidCardUpdate }) => {
  const [showConfirm, setShowConfirm] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const completion = bidCard.completion_info?.completion_percentage || bidCard.completion_percentage || 0;
  const isReady = bidCard.completion_info?.ready_for_conversion || bidCard.ready_for_conversion;
  const missingFields = bidCard.completion_info?.missing_fields || [];
  
  // Agent activity tracking for real-time visual feedback
  const { isBeingModified, currentAgent, highlightedFields } = useAgentActivity("potential_bid_card", bidCard.id);

  // Simple button click handler
  const handleButtonClick = () => {
    if (isReady) {
      // If ready, convert to official bid card
      onReview(bidCard);
    } else {
      // If not ready, open edit modal
      setShowEditModal(true);
    }
  };

  // Determine status color
  const getStatusColor = () => {
    if (completion >= 80) return "text-green-600 bg-green-50";
    if (completion >= 60) return "text-yellow-600 bg-yellow-50";
    return "text-gray-600 bg-gray-50";
  };

  const getProgressBarColor = () => {
    if (completion >= 80) return "bg-green-500";
    if (completion >= 60) return "bg-yellow-500";
    return "bg-gray-400";
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border transition-all duration-300 ${
      isBeingModified 
        ? 'border-purple-300 shadow-lg shadow-purple-100 animate-pulse' 
        : 'border-gray-200 hover:shadow-md'
    }`}>
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h3 className={`text-lg font-semibold transition-colors ${
              highlightedFields.includes('title') 
                ? 'text-purple-700 animate-pulse' 
                : 'text-gray-900'
            }`}>
              {bidCard.title || `${bidCard.project_type || "Project"} Draft`}
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              {bidCard.project_type?.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Agent Activity Indicator */}
            {isBeingModified && currentAgent && (
              <AgentActivityIndicator 
                agentName={currentAgent} 
                isWorking={true}
                size="sm"
              />
            )}
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor()}`}>
              {completion}% Complete
            </div>
          </div>
        </div>

        {/* Project Details */}
        <div className="space-y-2 mb-4">
          {bidCard.zip_code && (
            <div className={`flex items-center text-sm transition-colors ${
              highlightedFields.includes('zip_code') 
                ? 'text-purple-700 animate-pulse' 
                : 'text-gray-600'
            }`}>
              <MapPin className="w-4 h-4 mr-2 text-gray-400" />
              {bidCard.zip_code}
            </div>
          )}
          
          {(bidCard.timeline || bidCard.urgency_level) && (
            <div className={`flex items-center text-sm transition-colors ${
              highlightedFields.includes('timeline') || highlightedFields.includes('urgency_level')
                ? 'text-purple-700 animate-pulse' 
                : 'text-gray-600'
            }`}>
              <Clock className="w-4 h-4 mr-2 text-gray-400" />
              {bidCard.timeline || `Urgency: ${bidCard.urgency_level}`}
            </div>
          )}

          {bidCard.user_scope_notes && (
            <p className={`text-sm line-clamp-2 transition-colors ${
              highlightedFields.includes('user_scope_notes') 
                ? 'text-purple-700 animate-pulse' 
                : 'text-gray-600'
            }`}>
              {bidCard.user_scope_notes}
            </p>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor()} ${
                highlightedFields.includes('completion_percentage') || isBeingModified
                  ? 'animate-pulse shadow-lg' 
                  : ''
              }`}
              style={{ width: `${completion}%` }}
            />
          </div>
          {isBeingModified && (
            <div className="text-xs text-purple-600 mt-1 animate-pulse">
              ✨ {currentAgent} is enhancing this project...
            </div>
          )}
        </div>

        {/* Missing Fields */}
        {missingFields.length > 0 && (
          <div className="mb-4 text-sm text-gray-500">
            <span className="font-medium">To complete:</span>
            <span className="ml-2">{missingFields.slice(0, 3).join(", ")}</span>
            {missingFields.length > 3 && <span> +{missingFields.length - 3} more</span>}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleButtonClick}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              isReady
                ? "bg-primary-600 text-white hover:bg-primary-700"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {isReady ? (
              <>
                <CheckCircle className="w-5 h-5" />
                Review & Get Bids
              </>
            ) : (
              <>
                Complete Project Details
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
          
          {onDelete && (
            <button
              onClick={() => setShowConfirm(true)}
              className="px-4 py-2 rounded-lg border border-red-300 text-red-600 hover:bg-red-50 transition-colors"
              title="Delete draft"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          )}
        </div>
        
        {/* Delete Confirmation Dialog */}
        {showConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Delete Draft?</h3>
              <p className="text-gray-600 mb-4">
                Are you sure you want to delete this draft bid card? This action cannot be undone.
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowConfirm(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() => {
                    onDelete(bidCard.id);
                    setShowConfirm(false);
                  }}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Edit Modal */}
      <BidCardEditModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        bidCard={bidCard}
        onBidCardUpdate={() => {
          // Refresh the bid card data
          if (onBidCardUpdate) {
            onBidCardUpdate();
          }
          // Also close the modal after successful update
          setShowEditModal(false);
        }}
        onConversionReady={(bidCardId) => {
          // Modal handles conversion internally and closes itself
          // Just refresh the bid card data to show the new official bid card
          if (onBidCardUpdate) {
            onBidCardUpdate();
          }
        }}
      />
    </div>
  );
};

export default PotentialBidCard;