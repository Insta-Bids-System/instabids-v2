import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, 
  Clock, 
  Zap, 
  MapPin, 
  DollarSign, 
  User,
  Calendar,
  Star,
  Camera,
  AlertTriangle,
  Loader2
} from 'lucide-react';

interface BidCardData {
  id: string;
  status: string;
  completion_percentage: number;
  fields_collected: Record<string, any>;
  missing_fields: string[];
  ready_for_conversion: boolean;
  created_at: string;
  updated_at: string;
  conversation_id: string;
  bid_card_preview: {
    title: string;
    project_type: string;
    description: string;
    location: string;
    timeline: string;
    contractor_preference: string;
    special_notes: string[];
    uploaded_photos: string[];
  };
}

interface RealTimeBidCardDisplayProps {
  bidCardData: BidCardData | null;
  loading: boolean;
  error: string | null;
  onRefresh?: () => void;
}

export const RealTimeBidCardDisplay: React.FC<RealTimeBidCardDisplayProps> = ({
  bidCardData,
  loading,
  error,
  onRefresh
}) => {
  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center gap-2 text-red-700">
          <AlertTriangle className="w-4 h-4" />
          <span className="text-sm">Error loading bid card</span>
        </div>
        {onRefresh && (
          <button 
            onClick={onRefresh}
            className="mt-2 text-xs text-red-600 hover:text-red-700"
          >
            Try again
          </button>
        )}
      </div>
    );
  }

  if (!bidCardData) {
    return (
      <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
        <div className="flex items-center gap-2 text-gray-600">
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Clock className="w-4 h-4" />
          )}
          <span className="text-sm">
            {loading ? 'Checking for bid card...' : 'No bid card created yet'}
          </span>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Continue chatting to build your project details
        </p>
      </div>
    );
  }

  const getCompletionColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600 bg-green-50 border-green-200';
    if (percentage >= 60) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (percentage >= 40) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-gray-600 bg-gray-50 border-gray-200';
  };

  const getUrgencyIcon = (timeline: string) => {
    if (timeline?.toLowerCase().includes('emergency')) return <Zap className="w-4 h-4 text-red-500" />;
    if (timeline?.toLowerCase().includes('urgent')) return <Clock className="w-4 h-4 text-orange-500" />;
    return <Calendar className="w-4 h-4 text-blue-500" />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-gray-200 rounded-lg shadow-sm"
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-900">
            🏗️ Your Project Card
          </h3>
          <motion.div
            key={bidCardData.completion_percentage}
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            className={`px-2 py-1 rounded-full text-xs font-medium border ${getCompletionColor(bidCardData.completion_percentage)}`}
          >
            {bidCardData.completion_percentage}% Complete
          </motion.div>
        </div>
      </div>

      {/* Project Details */}
      <div className="p-4 space-y-3">
        {/* Title and Type */}
        <div>
          <h4 className="font-medium text-gray-900 text-sm">
            {bidCardData.bid_card_preview?.title || 'New Project'}
          </h4>
          {bidCardData.bid_card_preview?.project_type && (
            <p className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-full inline-block mt-1">
              {bidCardData.bid_card_preview.project_type}
            </p>
          )}
        </div>

        {/* Description */}
        <AnimatePresence>
          {bidCardData.bid_card_preview?.description && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              <p className="text-xs text-gray-700 bg-gray-50 p-2 rounded">
                {bidCardData.bid_card_preview.description}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Location */}
        <AnimatePresence>
          {bidCardData.bid_card_preview?.location && (
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2 text-xs text-gray-600"
            >
              <MapPin className="w-3 h-3" />
              <span>{bidCardData.bid_card_preview.location}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Timeline */}
        <AnimatePresence>
          {bidCardData.bid_card_preview?.timeline && (
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2 text-xs text-gray-600"
            >
              {getUrgencyIcon(bidCardData.bid_card_preview.timeline)}
              <span>{bidCardData.bid_card_preview.timeline}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Contractor Preference */}
        <AnimatePresence>
          {bidCardData.bid_card_preview?.contractor_preference && (
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2 text-xs text-gray-600"
            >
              <User className="w-3 h-3" />
              <span>{bidCardData.bid_card_preview.contractor_preference}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Photos */}
        <AnimatePresence>
          {bidCardData.bid_card_preview?.uploaded_photos?.length > 0 && (
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2 text-xs text-gray-600"
            >
              <Camera className="w-3 h-3" />
              <span>{bidCardData.bid_card_preview.uploaded_photos.length} photo(s) uploaded</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Missing Fields */}
        {bidCardData.missing_fields && bidCardData.missing_fields.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-3 pt-3 border-t border-gray-100"
          >
            <p className="text-xs text-gray-500 mb-2">Still need:</p>
            <div className="flex flex-wrap gap-1">
              {bidCardData.missing_fields.map((field) => (
                <span
                  key={field}
                  className="px-2 py-1 text-xs bg-yellow-50 text-yellow-700 border border-yellow-200 rounded-full"
                >
                  {field.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </motion.div>
        )}

        {/* Ready for Conversion */}
        <AnimatePresence>
          {bidCardData.ready_for_conversion && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg"
            >
              <div className="flex items-center gap-2 text-green-700">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm font-medium">Ready for contractors!</span>
              </div>
              <p className="text-xs text-green-600 mt-1">
                Your project has all the details contractors need to provide accurate bids.
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-gray-50 border-t border-gray-100 rounded-b-lg">
        <p className="text-xs text-gray-500 text-center">
          Updates automatically as you chat
        </p>
      </div>
    </motion.div>
  );
};