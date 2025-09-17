import { ArrowRight, CheckCircle, Clock, MapPin, Trash2, Image } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { useAgentActivity } from "../../hooks/useAgentActivity";
import { AgentActivityIndicator } from "../ui/AgentActivityIndicator";

interface ImageData {
  id: string;
  url: string;
  caption?: string;
  uploaded_at?: string;
  storage_path?: string;
}

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
    photo_ids?: ImageData[] | string[]; // Can be array of objects or URLs
    completion_info?: {
      completion_percentage: number;
      missing_fields: string[];
      ready_for_conversion: boolean;
    };
  };
  onReview: (bidCard: any) => void;
  onDelete?: (bidCardId: string) => void;
  onImageClick?: (image: ImageData | string) => void;
}

const PotentialBidCardWithImages: React.FC<PotentialBidCardProps> = ({ 
  bidCard, 
  onReview, 
  onDelete,
  onImageClick 
}) => {
  const [showConfirm, setShowConfirm] = useState(false);
  const [showAllImages, setShowAllImages] = useState(false);
  const completion = bidCard.completion_info?.completion_percentage || bidCard.completion_percentage || 0;
  const isReady = bidCard.completion_info?.ready_for_conversion || bidCard.ready_for_conversion;
  const missingFields = bidCard.completion_info?.missing_fields || [];
  
  // Agent activity tracking for real-time visual feedback
  const { isBeingModified, currentAgent, highlightedFields } = useAgentActivity("potential_bid_card", bidCard.id);

  // Process images - handle JSON string, object array, and string array
  const processPhotoIds = () => {
    try {
      let photoData = bidCard.photo_ids;
      
      // If it's a string, try to parse as JSON
      if (typeof photoData === 'string') {
        try {
          photoData = JSON.parse(photoData);
        } catch {
          // If JSON parsing fails, treat as single URL
          return [{ id: 'image-1', url: photoData, caption: 'Project Image' }];
        }
      }
      
      // If it's not an array, return empty
      if (!Array.isArray(photoData)) {
        return [];
      }
      
      // Map array elements to ImageData format
      return photoData.map((photo, index) => {
        if (typeof photo === 'string') {
          return {
            id: `image-${index}`,
            url: photo,
            caption: `Image ${index + 1}`
          };
        }
        return photo as ImageData;
      });
    } catch (error) {
      console.warn('Error processing photo_ids:', error);
      return [];
    }
  };

  const images: ImageData[] = processPhotoIds();

  const hasImages = images.length > 0;
  const displayImages = showAllImages ? images : images.slice(0, 3);

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
      {/* Image Gallery Section */}
      {hasImages && (
        <div className="relative">
          <div className="grid grid-cols-3 gap-1 p-1 bg-gray-100 rounded-t-lg">
            {displayImages.map((image, index) => (
              <div 
                key={image.id}
                className="relative aspect-square overflow-hidden rounded cursor-pointer hover:opacity-90 transition-opacity"
                onClick={() => onImageClick?.(image)}
              >
                <img 
                  src={image.url} 
                  alt={image.caption || `Project image ${index + 1}`}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
                {index === 2 && images.length > 3 && !showAllImages && (
                  <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                    <span className="text-white font-semibold text-lg">+{images.length - 3}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
          
          {/* Image count badge */}
          <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded-full text-xs flex items-center gap-1">
            <Image className="w-3 h-3" />
            {images.length}
          </div>
          
          {images.length > 3 && (
            <button
              onClick={() => setShowAllImages(!showAllImages)}
              className="absolute bottom-2 right-2 bg-white bg-opacity-90 hover:bg-opacity-100 text-gray-700 px-2 py-1 rounded text-xs transition-all"
            >
              {showAllImages ? 'Show less' : `View all ${images.length} images`}
            </button>
          )}
        </div>
      )}

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
              {bidCard.timeline || bidCard.urgency_level || "Timeline TBD"}
            </div>
          )}
        </div>

        {/* Scope Notes */}
        {bidCard.user_scope_notes && (
          <div className={`text-sm text-gray-600 mb-4 p-3 bg-gray-50 rounded transition-colors ${
            highlightedFields.includes('user_scope_notes')
              ? 'bg-purple-50 text-purple-700 animate-pulse' 
              : ''
          }`}>
            {bidCard.user_scope_notes}
          </div>
        )}

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div 
              className={`h-full transition-all duration-500 ${getProgressBarColor()}`}
              style={{ width: `${completion}%` }}
            />
          </div>
        </div>

        {/* Missing Fields */}
        {missingFields.length > 0 && (
          <div className="mb-4 text-xs text-gray-500">
            <span className="font-medium">Needs:</span> {missingFields.slice(0, 3).join(", ")}
            {missingFields.length > 3 && ` +${missingFields.length - 3} more`}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => onReview(bidCard)}
            className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              isReady 
                ? 'bg-green-600 hover:bg-green-700 text-white'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            }`}
          >
            {isReady ? (
              <>
                <CheckCircle className="w-4 h-4" />
                Review & Submit
              </>
            ) : (
              <>
                Continue Setup
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
          
          {onDelete && (
            <button
              onClick={() => setShowConfirm(true)}
              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Delete draft"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Delete Confirmation */}
        {showConfirm && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700 mb-2">Delete this draft bid card?</p>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  onDelete?.(bidCard.id);
                  setShowConfirm(false);
                }}
                className="flex-1 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
              >
                Delete
              </button>
              <button
                onClick={() => setShowConfirm(false)}
                className="flex-1 px-3 py-1 bg-white text-gray-700 rounded hover:bg-gray-50 text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PotentialBidCardWithImages;