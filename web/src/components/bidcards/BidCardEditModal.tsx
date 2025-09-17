import React, { useState, useEffect } from "react";
import { X, MessageSquare, CheckCircle, AlertCircle } from "lucide-react";
import UltimateCIAChat from "../chat/UltimateCIAChat";

interface BidCardEditModalProps {
  isOpen: boolean;
  onClose: () => void;
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
    primary_trade?: string;
    secondary_trades?: string[];
    budget_range_min?: number;
    budget_range_max?: number;
    materials_specified?: string[];
    special_requirements?: string[];
    contractor_size_preference?: string;
    quality_expectations?: string;
    timeline_flexibility?: string;
    service_complexity?: string;
    bid_collection_deadline?: string;
    project_completion_deadline?: string;
  };
  onBidCardUpdate?: () => void;
  onConversionReady?: (bidCardId: string) => void;
}

export const BidCardEditModal: React.FC<BidCardEditModalProps> = ({
  isOpen,
  onClose,
  bidCard,
  onBidCardUpdate,
  onConversionReady
}) => {
  const [isConverting, setIsConverting] = useState(false);
  const [conversionError, setConversionError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [currentBidCard, setCurrentBidCard] = useState(bidCard);

  useEffect(() => {
    console.log('[BidCardEditModal] Modal state changed - isOpen:', isOpen);
    // Generate a unique session ID for this edit session
    if (isOpen && bidCard) {
      console.log('[BidCardEditModal] Modal opening for bid card:', bidCard.id);
      setSessionId(`edit-${bidCard.id}-${Date.now()}`);
      setCurrentBidCard(bidCard);
    }
  }, [isOpen, bidCard]);

  if (!isOpen || !bidCard) {
    console.log('[BidCardEditModal] Not rendering - isOpen:', isOpen, 'bidCard:', !!bidCard);
    return null;
  }

  console.log('[BidCardEditModal] Rendering modal UI for bid card:', bidCard.id);

  // Format the bid card data into a context message
  const formatBidCardContext = () => {
    const fields = [];
    
    if (bidCard.project_type) fields.push(`Project Type: ${bidCard.project_type}`);
    if (bidCard.user_scope_notes) fields.push(`Description: ${bidCard.user_scope_notes}`);
    if (bidCard.zip_code) fields.push(`Location: ${bidCard.zip_code}`);
    if (bidCard.urgency_level) fields.push(`Urgency: ${bidCard.urgency_level}`);
    if (bidCard.timeline) fields.push(`Timeline: ${bidCard.timeline}`);
    if (bidCard.contractor_size_preference) fields.push(`Contractor Preference: ${bidCard.contractor_size_preference}`);
    if (bidCard.materials_specified?.length) fields.push(`Materials: ${bidCard.materials_specified.join(", ")}`);
    if (bidCard.special_requirements?.length) fields.push(`Requirements: ${bidCard.special_requirements.join(", ")}`);
    if (bidCard.budget_range_min || bidCard.budget_range_max) {
      const budget = [];
      if (bidCard.budget_range_min) budget.push(`$${bidCard.budget_range_min.toLocaleString()}`);
      if (bidCard.budget_range_max) budget.push(`$${bidCard.budget_range_max.toLocaleString()}`);
      fields.push(`Budget: ${budget.join(" - ")}`);
    }

    return `I'm reviewing my ${bidCard.project_type || "project"} details before posting for bids. Here's what I have so far:\n\n${fields.join("\n")}\n\nIs there anything I should add or change to get better contractor responses?`;
  };



  const handleConvertToBidCard = async () => {
    setIsConverting(true);
    setConversionError(null);

    try {
      const response = await fetch(
        `/api/cia/potential-bid-cards/${bidCard.id}/convert-to-bid-card`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (response.ok) {
        const result = await response.json();
        
        // Close the modal
        onClose();
        
        // Notify parent of successful conversion
        if (onConversionReady) {
          onConversionReady(result.official_bid_card_id);
        }
      } else {
        const error = await response.json();
        setConversionError(error.detail || "Failed to convert bid card");
      }
    } catch (error) {
      console.error("Error converting bid card:", error);
      setConversionError("An error occurred while converting the bid card");
    } finally {
      setIsConverting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-6xl bg-white rounded-xl shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <div className="flex items-center gap-3">
              <MessageSquare className="w-6 h-6 text-primary-600" />
              <div>
                <h2 className="text-2xl font-semibold text-gray-900">
                  Review & Refine Your Project
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  Chat with Alex to perfect your project details before getting bids
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          <div className="flex h-[600px]">
            {/* Left side - Chat */}
            <div className="flex-1 border-r">
              <UltimateCIAChat
                sessionId={sessionId}
                initialMessage={formatBidCardContext()}
                projectContext={{
                  bid_card_id: bidCard.id,
                  project_type: bidCard.project_type,
                  editing_mode: true,
                  potential_bid_card_id: bidCard.id
                }}
              />
            </div>

            {/* Right side - Current Details & Actions */}
            <div className="w-80 p-6 bg-gray-50">
              <div className="space-y-6">
                {/* Completion Status */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">
                    Project Completion
                  </h3>
                  <div className="bg-white rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-600">Progress</span>
                      <span className="text-sm font-medium text-gray-900">
                        {currentBidCard.completion_percentage}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          currentBidCard.completion_percentage >= 80
                            ? "bg-green-500"
                            : currentBidCard.completion_percentage >= 60
                            ? "bg-yellow-500"
                            : "bg-gray-400"
                        }`}
                        style={{ width: `${currentBidCard.completion_percentage}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Current Details Summary */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">
                    Current Details
                  </h3>
                  <div className="bg-white rounded-lg p-4 space-y-2 text-sm">
                    {currentBidCard.project_type && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Type:</span>
                        <span className="text-gray-900 font-medium">
                          {currentBidCard.project_type}
                        </span>
                      </div>
                    )}
                    {currentBidCard.urgency_level && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Urgency:</span>
                        <span className="text-gray-900 font-medium">
                          {currentBidCard.urgency_level}
                        </span>
                      </div>
                    )}
                    {currentBidCard.zip_code && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Location:</span>
                        <span className="text-gray-900 font-medium">
                          {currentBidCard.zip_code}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Tips */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">
                    Quick Tips
                  </h3>
                  <div className="bg-blue-50 rounded-lg p-4 space-y-2">
                    <p className="text-sm text-blue-900">
                      💡 Add photos for more accurate bids
                    </p>
                    <p className="text-sm text-blue-900">
                      📅 Specify your timeline clearly
                    </p>
                    <p className="text-sm text-blue-900">
                      💰 Mention your budget range if comfortable
                    </p>
                    <p className="text-sm text-blue-900">
                      📝 Include any special requirements
                    </p>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="space-y-3 pt-4">
                  <button
                    onClick={handleConvertToBidCard}
                    disabled={!currentBidCard.ready_for_conversion || isConverting}
                    className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors ${
                      currentBidCard.ready_for_conversion && !isConverting
                        ? "bg-primary-600 text-white hover:bg-primary-700"
                        : "bg-gray-200 text-gray-500 cursor-not-allowed"
                    }`}
                  >
                    {isConverting ? (
                      <>
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                        Converting...
                      </>
                    ) : currentBidCard.ready_for_conversion ? (
                      <>
                        <CheckCircle className="w-5 h-5" />
                        Get Contractor Bids
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-5 h-5" />
                        Complete Required Fields
                      </>
                    )}
                  </button>

                  {conversionError && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-800">{conversionError}</p>
                    </div>
                  )}

                  <button
                    onClick={onClose}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Continue Editing Later
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};