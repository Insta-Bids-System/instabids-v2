import {
  Calendar,
  Camera,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Clock,
  DollarSign,
  Eye,
  MapPin,
  MessageSquare,
  TrendingUp,
  Users,
} from "lucide-react";
import type React from "react";
import { useState } from "react";

interface BidCardData {
  id: string;
  bid_card_number: string;
  public_token?: string;
  project_type: string;
  urgency_level: string;
  budget_min: number;
  budget_max: number;
  contractor_count_needed: number;
  created_at: string;
  status: string;
  bid_document?: {
    all_extracted_data?: {
      location?: {
        city?: string | null;
        state?: string | null;
        address?: string | null;
        zip_code?: string | null;
        full_location?: string | null;
      };
      project_details?: {
        scope_of_work?: string[];
      };
      photo_urls?: string[];
      project_description?: string;
    };
  };
  // Tracking data
  view_count?: number;
  click_count?: number;
  contractor_signups?: number;
}

interface InternalBidCardProps {
  bidCard: BidCardData;
  onContinueChat?: () => void;
  onViewAnalytics?: () => void;
}

const InternalBidCard: React.FC<InternalBidCardProps> = ({
  bidCard,
  onContinueChat,
  onViewAnalytics,
}) => {
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);

  const formatProjectType = (type: string) => {
    return type?.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()) || "Home Project";
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "active":
        return "bg-green-100 text-green-800 border-green-200";
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "completed":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "cancelled":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case "emergency":
        return "bg-red-500 text-white";
      case "week":
        return "bg-orange-500 text-white";
      case "month":
        return "bg-blue-500 text-white";
      default:
        return "bg-gray-500 text-white";
    }
  };

  const getUrgencyText = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case "emergency":
        return "Urgent - ASAP";
      case "week":
        return "Within 7 Days";
      case "month":
        return "Within 30 Days";
      default:
        return "Flexible Timeline";
    }
  };

  const photos = bidCard.bid_document?.all_extracted_data?.photo_urls || [];
  const projectDetails = bidCard.bid_document?.all_extracted_data?.project_details;
  const scopeOfWork = projectDetails?.scope_of_work || [];

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-shadow duration-300">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-xl font-bold mb-2">{formatProjectType(bidCard.project_type)}</h3>
            <div className="flex items-center gap-2 text-blue-100">
              <MapPin className="w-4 h-4" />
              <span className="text-sm">
                {bidCard.bid_document?.all_extracted_data?.location?.city ||
                  bidCard.bid_document?.all_extracted_data?.location?.address ||
                  bidCard.bid_document?.all_extracted_data?.location?.zip_code ||
                  "Location TBD"}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div
              className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(bidCard.status)}`}
            >
              {bidCard.status?.toUpperCase() || "ACTIVE"}
            </div>
            <div className="text-blue-100 text-sm mt-2">{bidCard.bid_card_number}</div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white/10 rounded-lg p-3 text-center">
            <DollarSign className="w-5 h-5 mx-auto mb-1" />
            <div className="text-sm font-semibold">
              ${bidCard.budget_min?.toLocaleString()} - ${bidCard.budget_max?.toLocaleString()}
            </div>
            <div className="text-xs text-blue-200">Budget</div>
          </div>

          <div className="bg-white/10 rounded-lg p-3 text-center">
            <Users className="w-5 h-5 mx-auto mb-1" />
            <div className="text-sm font-semibold">{bidCard.contractor_count_needed}</div>
            <div className="text-xs text-blue-200">Contractors Needed</div>
          </div>

          <div className="bg-white/10 rounded-lg p-3 text-center">
            <Clock className="w-5 h-5 mx-auto mb-1" />
            <div
              className={`text-xs font-semibold px-2 py-1 rounded ${getUrgencyColor(bidCard.urgency_level)}`}
            >
              {getUrgencyText(bidCard.urgency_level)}
            </div>
          </div>
        </div>
      </div>

      {/* Photo Section */}
      {photos.length > 0 && (
        <div className="relative">
          <div className="h-48 bg-gray-100">
            <img
              src={photos[currentPhotoIndex]}
              alt="Project photo"
              className="w-full h-full object-cover"
            />

            {photos.length > 1 && (
              <>
                <button
                  type="button"
                  onClick={() =>
                    setCurrentPhotoIndex((prev) => (prev - 1 + photos.length) % photos.length)
                  }
                  className="absolute left-2 top-1/2 transform -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentPhotoIndex((prev) => (prev + 1) % photos.length)}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>

                <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 flex gap-1">
                  {photos.map((_, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => setCurrentPhotoIndex(index)}
                      className={`w-2 h-2 rounded-full ${
                        index === currentPhotoIndex ? "bg-white" : "bg-white/50"
                      }`}
                    />
                  ))}
                </div>
              </>
            )}
          </div>

          <div className="absolute top-2 right-2 bg-black/50 text-white px-2 py-1 rounded-full text-xs flex items-center gap-1">
            <Camera className="w-3 h-3" />
            {photos.length}
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-6">
        {/* Project Details */}
        {scopeOfWork.length > 0 && (
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-3">Project Scope</h4>
            <ul className="space-y-2">
              {scopeOfWork.slice(0, 3).map((item, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>{item}</span>
                </li>
              ))}
              {scopeOfWork.length > 3 && (
                <li className="text-sm text-blue-600 font-medium">
                  + {scopeOfWork.length - 3} more items
                </li>
              )}
            </ul>
          </div>
        )}

        {/* Tracking Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-gray-600 mb-1">
              <Eye className="w-4 h-4" />
              <span className="text-xs">Views</span>
            </div>
            <div className="text-lg font-semibold text-gray-900">{bidCard.view_count || 0}</div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-gray-600 mb-1">
              <TrendingUp className="w-4 h-4" />
              <span className="text-xs">Clicks</span>
            </div>
            <div className="text-lg font-semibold text-gray-900">{bidCard.click_count || 0}</div>
          </div>

          <div className="text-center">
            <div className="flex items-center justify-center gap-1 text-gray-600 mb-1">
              <Users className="w-4 h-4" />
              <span className="text-xs">Signups</span>
            </div>
            <div className="text-lg font-semibold text-green-600">
              {bidCard.contractor_signups || 0}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onContinueChat}
            className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
          >
            <MessageSquare className="w-4 h-4" />
            Continue Chat
          </button>

          <button
            type="button"
            onClick={onViewAnalytics}
            className="bg-gray-100 text-gray-700 py-3 px-4 rounded-lg font-semibold hover:bg-gray-200 transition-colors flex items-center gap-2"
          >
            <TrendingUp className="w-4 h-4" />
            Analytics
          </button>
        </div>

        {/* Footer Info */}
        <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            <span>Created {formatDate(bidCard.created_at)}</span>
          </div>

          {(bidCard.contractor_signups || 0) > 0 && (
            <div className="flex items-center gap-1 text-green-600">
              <CheckCircle className="w-4 h-4" />
              <span className="font-medium">Active Campaign</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InternalBidCard;
