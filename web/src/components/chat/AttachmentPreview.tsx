"use client";

import React, { useState } from "react";
import { Image as ImageIcon, Download, Eye, X, FileText } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface UnifiedAttachment {
  id: string;
  message_id: string;
  type: "image" | "document";
  name: string;
  url: string;
  mime_type: string;
  file_size: number;
  storage_path: string;
  created_at: string;
  metadata?: Record<string, any>;
}

interface AttachmentPreviewProps {
  attachment: UnifiedAttachment;
  className?: string;
}

const AttachmentPreview: React.FC<AttachmentPreviewProps> = ({
  attachment,
  className = ""
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const handleDownload = async () => {
    try {
      const response = await fetch(attachment.url);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = attachment.name || `attachment_${attachment.id}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to download attachment:", error);
    }
  };

  const handleImageLoad = () => {
    setImageLoaded(true);
    setImageError(false);
  };

  const handleImageError = () => {
    setImageLoaded(false);
    setImageError(true);
  };

  if (attachment.type === "image" && !imageError) {
    return (
      <>
        <div className={`relative group ${className}`}>
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative bg-gray-100 rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-all duration-200"
          >
            {/* Loading State */}
            {!imageLoaded && (
              <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
                <div className="animate-spin">
                  <ImageIcon className="h-8 w-8 text-gray-400" />
                </div>
              </div>
            )}

            {/* Image */}
            <img
              src={attachment.url}
              alt={attachment.name}
              className={`max-w-full max-h-64 object-contain cursor-pointer transition-opacity duration-200 ${
                imageLoaded ? "opacity-100" : "opacity-0"
              }`}
              onLoad={handleImageLoad}
              onError={handleImageError}
              onClick={() => setIsFullscreen(true)}
            />

            {/* Overlay Controls */}
            <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center opacity-0 group-hover:opacity-100">
              <div className="flex gap-2">
                <button
                  onClick={() => setIsFullscreen(true)}
                  className="bg-white bg-opacity-90 hover:bg-opacity-100 p-2 rounded-full transition-all duration-200"
                  title="View full size"
                >
                  <Eye className="h-4 w-4 text-gray-700" />
                </button>
                <button
                  onClick={handleDownload}
                  className="bg-white bg-opacity-90 hover:bg-opacity-100 p-2 rounded-full transition-all duration-200"
                  title="Download image"
                >
                  <Download className="h-4 w-4 text-gray-700" />
                </button>
              </div>
            </div>

            {/* Image Info Badge */}
            <div className="absolute bottom-2 left-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
              {formatFileSize(attachment.file_size)}
            </div>
          </motion.div>

          {/* Image Metadata */}
          <div className="mt-2 text-xs text-gray-500">
            <div className="truncate">{attachment.name}</div>
            <div>{attachment.mime_type}</div>
          </div>
        </div>

        {/* Fullscreen Modal */}
        <AnimatePresence>
          {isFullscreen && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 bg-black bg-opacity-90 flex items-center justify-center p-4"
              onClick={() => setIsFullscreen(false)}
            >
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                className="relative max-w-full max-h-full"
                onClick={(e) => e.stopPropagation()}
              >
                <img
                  src={attachment.url}
                  alt={attachment.name}
                  className="max-w-full max-h-full object-contain"
                />
                <button
                  onClick={() => setIsFullscreen(false)}
                  className="absolute top-4 right-4 bg-white bg-opacity-20 hover:bg-opacity-30 p-2 rounded-full transition-all duration-200"
                >
                  <X className="h-6 w-6 text-white" />
                </button>
                <div className="absolute bottom-4 left-4 bg-black bg-opacity-70 text-white px-3 py-2 rounded">
                  <div className="font-medium">{attachment.name}</div>
                  <div className="text-sm opacity-80">
                    {formatFileSize(attachment.file_size)} • {attachment.mime_type}
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </>
    );
  }

  // Document/File Attachment
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex items-center gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors duration-200 ${className}`}
    >
      <div className="flex-shrink-0">
        <FileText className="h-8 w-8 text-blue-600" />
      </div>
      
      <div className="flex-grow min-w-0">
        <div className="font-medium text-gray-900 truncate">{attachment.name}</div>
        <div className="text-sm text-gray-500">
          {formatFileSize(attachment.file_size)} • {attachment.mime_type}
        </div>
      </div>

      <button
        onClick={handleDownload}
        className="flex-shrink-0 p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded-full transition-all duration-200"
        title="Download file"
      >
        <Download className="h-4 w-4" />
      </button>
    </motion.div>
  );
};

export default AttachmentPreview;