import {
  AlertCircle,
  Building,
  Calendar,
  Camera,
  CheckCircle,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Clock,
  DollarSign,
  Eye,
  FileText,
  MapPin,
  MessageSquare,
  Package,
  Shield,
  TrendingUp,
  Users,
  Wrench,
  Zap,
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
  complexity_score?: number;
  bid_document?: {
    all_extracted_data?: {
      // Location data
      location?: {
        city?: string | null;
        state?: string | null;
        address?: string | null;
        zip_code?: string | null;
        full_location?: string | null;
      };
      location_zip?: string;

      // Project details
      project_description?: string;
      service_type?: string;
      timeline_urgency?: string;
      urgency_reason?: string;

      // Materials and preferences
      material_preferences?: string[];
      materials_preferences?: string[];
      special_requirements?: string[];
      concerns_issues?: string[];

      // Property information
      property_details?: {
        type?: string;
      };
      property_context?: string;

      // Contractor requirements
      contractor_requirements?: {
        contractor_count?: number;
        equipment_needed?: string[];
        licenses_required?: string[];
        specialties_required?: string[];
      };

      // Images and analysis
      images?: string[];
      image_analysis?: string[];

      // Scoring and context
      intention_score?: number;
      budget_context?: string;
      group_bidding_potential?: boolean;

      // Legacy fields
      project_details?: {
        scope_of_work?: string[];
      };
      photo_urls?: string[];
    };
  };
  // Tracking data
  view_count?: number;
  click_count?: number;
  contractor_signups?: number;
}

interface EnhancedBidCardProps {
  bidCard: BidCardData;
  onContinueChat?: (e?: React.MouseEvent) => void;
  onViewAnalytics?: (e?: React.MouseEvent) => void;
}

const EnhancedBidCard: React.FC<EnhancedBidCardProps> = ({
  bidCard,
  onContinueChat,
  onViewAnalytics,
}) => {
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);
  const [isExpanded, setIsExpanded] = useState(false);

  const extractedData = bidCard.bid_document?.all_extracted_data || {};

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

  // Get images from either images or photo_urls field
  const photos = extractedData.images || extractedData.photo_urls || [];
  const validPhotos = Array.isArray(photos) ? photos : [];
  const projectDetails = extractedData.project_details;
  const scopeOfWork = projectDetails?.scope_of_work || [];

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const getComplexityBadge = (score?: number) => {
    if (!score) return null;
    if (score >= 8) return { text: "Complex", color: "bg-red-100 text-red-800" };
    if (score >= 5) return { text: "Moderate", color: "bg-yellow-100 text-yellow-800" };
    return { text: "Simple", color: "bg-green-100 text-green-800" };
  };

  const complexity = getComplexityBadge(bidCard.complexity_score);

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-shadow duration-300">
      {/* HEADER - Same as before */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-6 text-white">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-xl font-bold mb-2">{formatProjectType(bidCard.project_type)}</h3>
            <div className="flex items-center gap-2 text-blue-100">
              <MapPin className="w-4 h-4" />
              <span className="text-sm">
                {extractedData.location?.city ||
                  extractedData.location?.address ||
                  extractedData.location_zip ||
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
            {complexity && (
              <div
                className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold mt-2 ${complexity.color}`}
              >
                {complexity.text}
              </div>
            )}
            <div className="text-blue-100 text-sm mt-2">{bidCard.bid_card_number}</div>
          </div>
        </div>

        {/* KEY METRICS - Enhanced */}
        <div className="grid grid-cols-4 gap-3">
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
            <div className="text-xs text-blue-200">Contractors</div>
          </div>

          <div className="bg-white/10 rounded-lg p-3 text-center">
            <Clock className="w-5 h-5 mx-auto mb-1" />
            <div
              className={`text-xs font-semibold px-2 py-1 rounded ${getUrgencyColor(bidCard.urgency_level)}`}
            >
              {extractedData.timeline_urgency || getUrgencyText(bidCard.urgency_level)}
            </div>
          </div>
        </div>
      </div>

      {/* PHOTO SECTION - Enhanced */}
      {validPhotos.length > 0 && (
        <div className="relative">
          <div className="h-48 bg-gray-100">
            <img
              src={validPhotos[currentPhotoIndex]}
              alt="Project photo"
              className="w-full h-full object-cover"
              onError={(e) => {
                console.error("Image failed to load:", validPhotos[currentPhotoIndex]);
                e.currentTarget.src = "/placeholder-image.jpg";
              }}
            />

            {validPhotos.length > 1 && (
              <>
                <button
                  type="button"
                  onClick={() =>
                    setCurrentPhotoIndex(
                      (prev) => (prev - 1 + validPhotos.length) % validPhotos.length
                    )
                  }
                  className="absolute left-2 top-1/2 transform -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentPhotoIndex((prev) => (prev + 1) % validPhotos.length)}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-black/50 text-white p-2 rounded-full hover:bg-black/70"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>

                <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 flex gap-1">
                  {validPhotos.map((_, index) => (
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
            {validPhotos.length}
          </div>
        </div>
      )}

      {/* CONTENT SECTION - Enhanced */}
      <div className="p-6">
        {/* PROJECT DESCRIPTION */}
        {extractedData.project_description && (
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Project Description
            </h4>
            <p className="text-sm text-gray-700 leading-relaxed">
              {extractedData.project_description}
            </p>
          </div>
        )}

        {/* EXPAND/COLLAPSE BUTTON */}
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors mb-4 font-medium text-gray-700"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              Show Less Details
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              Show All Details ({Object.keys(extractedData).length} fields)
            </>
          )}
        </button>

        {/* EXPANDED DETAILS */}
        {isExpanded && (
          <div className="space-y-6 mb-6">
            {/* MATERIALS & PREFERENCES */}
            {(extractedData.material_preferences || extractedData.materials_preferences) && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Package className="w-4 h-4" />
                  Material Preferences
                </h4>
                <div className="flex flex-wrap gap-2">
                  {(
                    extractedData.material_preferences ||
                    extractedData.materials_preferences ||
                    []
                  ).map((material, index) => (
                    <span
                      key={index}
                      className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                    >
                      {material}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* PROPERTY DETAILS */}
            {extractedData.property_details && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Building className="w-4 h-4" />
                  Property Information
                </h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-600">Type:</span>
                      <span className="ml-2 text-gray-900">
                        {extractedData.property_details.type || "N/A"}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Service:</span>
                      <span className="ml-2 text-gray-900">
                        {extractedData.service_type || "N/A"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* CONTRACTOR REQUIREMENTS */}
            {extractedData.contractor_requirements && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Contractor Requirements
                </h4>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-600">Count Needed:</span>
                      <span className="ml-2 text-gray-900">
                        {extractedData.contractor_requirements.contractor_count || 0}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Equipment:</span>
                      <span className="ml-2 text-gray-900">
                        {extractedData.contractor_requirements.equipment_needed?.length || 0} items
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* SPECIAL REQUIREMENTS */}
            {extractedData.special_requirements &&
              extractedData.special_requirements.length > 0 && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <Zap className="w-4 h-4" />
                    Special Requirements
                  </h4>
                  <ul className="space-y-2">
                    {extractedData.special_requirements.map((req, index) => (
                      <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                        <AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                        <span>{req}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

            {/* CONCERNS/ISSUES */}
            {extractedData.concerns_issues && extractedData.concerns_issues.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Concerns & Issues
                </h4>
                <ul className="space-y-2">
                  {extractedData.concerns_issues.map((concern, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                      <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                      <span>{concern}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* GROUP BIDDING */}
            {extractedData.group_bidding_potential && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2 text-blue-800">
                  <Users className="w-4 h-4" />
                  <span className="font-semibold">Group Bidding Potential</span>
                </div>
                <p className="text-sm text-blue-700 mt-1">
                  This project may benefit from coordinated bidding with related projects.
                </p>
              </div>
            )}
          </div>
        )}

        {/* PROJECT SCOPE (if available) */}
        {scopeOfWork.length > 0 && (
          <div className="mb-6">
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Wrench className="w-4 h-4" />
              Project Scope
            </h4>
            <ul className="space-y-2">
              {scopeOfWork.slice(0, isExpanded ? scopeOfWork.length : 3).map((item, index) => (
                <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                  <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                  <span>{item}</span>
                </li>
              ))}
              {!isExpanded && scopeOfWork.length > 3 && (
                <li className="text-sm text-blue-600 font-medium">
                  + {scopeOfWork.length - 3} more items
                </li>
              )}
            </ul>
          </div>
        )}

        {/* TRACKING STATS */}
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

        {/* ACTION BUTTONS */}
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onContinueChat}
            className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
          >
            <MessageSquare className="w-4 h-4" />
            Continue Chat & Modify
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

        {/* FOOTER INFO */}
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

export default EnhancedBidCard;
