import {
  Building,
  Calendar,
  Camera,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  DollarSign,
  FileText,
  MapPin,
  Star,
  Users,
} from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { PhotoService } from "../../../lib/photoService";

interface BidCardData {
  id: string;
  bid_card_number: string;
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
      project_description?: string;
      location?: {
        city?: string;
        state?: string;
        address?: string;
      };
      photos?: string[]; // Array of photo IDs or URLs
      timeline_start?: string;
      timeline_duration?: string;
      materials_specified?: string[];
      special_requirements?: string[];
      ai_insights?: {
        project_analysis?: string;
        complexity_factors?: string[];
      };
    };
  };
}

interface BidCardPreviewProps {
  bidCard: BidCardData;
  sessionId?: string; // For loading photos by session
  className?: string;
  showFullDetails?: boolean;
}

export const BidCardPreview: React.FC<BidCardPreviewProps> = ({
  bidCard,
  sessionId,
  className = "",
  showFullDetails = true,
}) => {
  const [photoUrls, setPhotoUrls] = useState<string[]>([]);
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);
  const [photosLoading, setPhotosLoading] = useState(true);
  const [showExpanded, setShowExpanded] = useState(false);

  // Extract data from bid card
  const extractedData = bidCard.bid_document?.all_extracted_data || {};
  const location = extractedData.location || {};
  const aiInsights = extractedData.ai_insights || {};

  // Load photos on component mount
  useEffect(() => {
    loadProjectPhotos();
  }, []);

  const loadProjectPhotos = async () => {
    setPhotosLoading(true);
    try {
      let photos: string[] = [];

      // Try to load from bid card data first
      if (extractedData.photos && extractedData.photos.length > 0) {
        photos = await PhotoService.convertPhotoRefsToUrls(extractedData.photos);
      }

      // If no photos in bid card but we have a session ID, try loading from session
      if (photos.length === 0 && sessionId) {
        const sessionPhotos = await PhotoService.getProjectPhotos(sessionId);
        photos = await Promise.all(
          sessionPhotos.map((photo) => `data:${photo.mime_type};base64,${photo.photo_data}`)
        );
      }

      setPhotoUrls(photos);
    } catch (error) {
      console.error("Error loading project photos:", error);
    } finally {
      setPhotosLoading(false);
    }
  };

  const nextPhoto = () => {
    setCurrentPhotoIndex((prev) => (prev + 1) % photoUrls.length);
  };

  const prevPhoto = () => {
    setCurrentPhotoIndex((prev) => (prev - 1 + photoUrls.length) % photoUrls.length);
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case "emergency":
        return "bg-red-100 text-red-800 border-red-200";
      case "urgent":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "flexible":
        return "bg-green-100 text-green-800 border-green-200";
      default:
        return "bg-blue-100 text-blue-800 border-blue-200";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "generated":
        return "bg-blue-100 text-blue-800";
      case "sent":
        return "bg-yellow-100 text-yellow-800";
      case "responses":
        return "bg-purple-100 text-purple-800";
      case "completed":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div
      className={`bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden ${className}`}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold mb-2">Bid Card #{bidCard.bid_card_number}</h2>
            <div className="flex items-center gap-4 text-blue-100">
              <span className="flex items-center gap-1">
                <Building className="w-4 h-4" />
                {bidCard.project_type.charAt(0).toUpperCase() + bidCard.project_type.slice(1)}
              </span>
              <span className="flex items-center gap-1">
                <DollarSign className="w-4 h-4" />${bidCard.budget_min.toLocaleString()} - $
                {bidCard.budget_max.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="text-right">
            <div
              className={`inline-block px-3 py-1 rounded-full text-sm font-medium border ${getUrgencyColor(bidCard.urgency_level)}`}
            >
              {bidCard.urgency_level.charAt(0).toUpperCase() + bidCard.urgency_level.slice(1)}
            </div>
            <div
              className={`inline-block px-3 py-1 rounded-full text-sm font-medium mt-2 ${getStatusColor(bidCard.status)}`}
            >
              {bidCard.status.charAt(0).toUpperCase() + bidCard.status.slice(1)}
            </div>
          </div>
        </div>
      </div>

      {/* Photo Gallery */}
      {photoUrls.length > 0 && (
        <div className="relative h-64 bg-gray-100">
          {photosLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              <img
                src={photoUrls[currentPhotoIndex]}
                alt="Project photo"
                className="w-full h-full object-cover"
                onError={(e) => {
                  console.error("Photo failed to load:", photoUrls[currentPhotoIndex]);
                  e.currentTarget.src = "/placeholder-image.jpg";
                }}
              />

              {photoUrls.length > 1 && (
                <>
                  <button
                    type="button"
                    onClick={prevPhoto}
                    className="absolute left-2 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>

                  <button
                    type="button"
                    onClick={nextPhoto}
                    className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-2 rounded-full transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </>
              )}

              <div className="absolute top-2 right-2 bg-black/50 text-white px-2 py-1 rounded-full text-xs flex items-center gap-1">
                <Camera className="w-3 h-3" />
                {photoUrls.length}
              </div>

              {photoUrls.length > 1 && (
                <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 flex gap-2">
                  {photoUrls.map((_, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => setCurrentPhotoIndex(index)}
                      className={`w-2 h-2 rounded-full transition-colors ${
                        index === currentPhotoIndex ? "bg-white" : "bg-white/50"
                      }`}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Content */}
      <div className="p-6">
        {/* Project Description */}
        {extractedData.project_description && (
          <div className="mb-6">
            <h3 className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Project Description
            </h3>
            <p className="text-gray-700 leading-relaxed">{extractedData.project_description}</p>
          </div>
        )}

        {/* Key Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Location */}
          {(location.city || location.state) && (
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <MapPin className="w-5 h-5 text-blue-600" />
              <div>
                <div className="font-medium text-gray-900">Location</div>
                <div className="text-gray-600">
                  {location.city && location.state
                    ? `${location.city}, ${location.state}`
                    : location.city || location.state || "Not specified"}
                </div>
              </div>
            </div>
          )}

          {/* Timeline */}
          {extractedData.timeline_start && (
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Calendar className="w-5 h-5 text-green-600" />
              <div>
                <div className="font-medium text-gray-900">Timeline</div>
                <div className="text-gray-600">{extractedData.timeline_start}</div>
              </div>
            </div>
          )}

          {/* Contractors Needed */}
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <Users className="w-5 h-5 text-purple-600" />
            <div>
              <div className="font-medium text-gray-900">Contractors Needed</div>
              <div className="text-gray-600">
                {bidCard.contractor_count_needed} qualified contractors
              </div>
            </div>
          </div>

          {/* Complexity Score */}
          {bidCard.complexity_score && (
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Star className="w-5 h-5 text-yellow-600" />
              <div>
                <div className="font-medium text-gray-900">Complexity</div>
                <div className="text-gray-600">{bidCard.complexity_score}/10</div>
              </div>
            </div>
          )}
        </div>

        {/* Expandable Sections */}
        {showFullDetails &&
          (extractedData.materials_specified?.length ||
            extractedData.special_requirements?.length ||
            aiInsights.project_analysis) && (
            <div className="border-t pt-6">
              <button
                type="button"
                onClick={() => setShowExpanded(!showExpanded)}
                className="flex items-center justify-between w-full p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <span className="font-medium text-gray-900">Additional Details</span>
                <div className="transform transition-transform">{showExpanded ? "↑" : "↓"}</div>
              </button>

              {showExpanded && (
                <div className="mt-4 space-y-4">
                  {/* Materials */}
                  {extractedData.materials_specified &&
                    extractedData.materials_specified.length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Materials Specified</h4>
                        <div className="flex flex-wrap gap-2">
                          {extractedData.materials_specified.map((material, index) => (
                            <span
                              key={index}
                              className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                            >
                              {material}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                  {/* Special Requirements */}
                  {extractedData.special_requirements &&
                    extractedData.special_requirements.length > 0 && (
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Special Requirements</h4>
                        <div className="flex flex-wrap gap-2">
                          {extractedData.special_requirements.map((req, index) => (
                            <span
                              key={index}
                              className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm"
                            >
                              {req}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                  {/* AI Analysis */}
                  {aiInsights.project_analysis && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">AI Project Analysis</h4>
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <p className="text-gray-700 whitespace-pre-line">
                          {aiInsights.project_analysis.slice(0, 500)}
                          {aiInsights.project_analysis.length > 500 && "..."}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

        {/* Footer */}
        <div className="flex justify-between items-center pt-4 border-t text-sm text-gray-500">
          <span>Created: {new Date(bidCard.created_at).toLocaleDateString()}</span>
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            Ready for contractor outreach
          </div>
        </div>
      </div>
    </div>
  );
};

export default BidCardPreview;
