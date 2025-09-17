import type React from "react";
import { useState } from "react";
import toast from "react-hot-toast";
import { StorageService } from "@/lib/storage";
import { supabase } from "@/lib/supabase";
import { Upload, X, Image, Send, MessageSquare } from "lucide-react";

interface RFIResponseFormProps {
  rfiId: string;
  bidCardId: string;
  contractorName: string;
  requestedItems: string[];
  onClose: () => void;
  onSuccess: () => void;
}

const RFIResponseForm: React.FC<RFIResponseFormProps> = ({
  rfiId,
  bidCardId,
  contractorName,
  requestedItems,
  onClose,
  onSuccess,
}) => {
  const [photos, setPhotos] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [responseMessage, setResponseMessage] = useState("");
  const [dragActive, setDragActive] = useState(false);

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;
    
    const newFiles = Array.from(files).filter(file => {
      const validation = StorageService.validateImage(file);
      if (validation) {
        toast.error(`${file.name}: ${validation}`);
        return false;
      }
      return true;
    });

    setPhotos(prev => [...prev, ...newFiles]);
  };

  const removePhoto = (index: number) => {
    setPhotos(prev => prev.filter((_, i) => i !== index));
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleSubmit = async () => {
    if (photos.length === 0 && !responseMessage.trim()) {
      toast.error("Please add photos or a message to respond");
      return;
    }

    setUploading(true);

    try {
      // Step 1: Upload photos to Supabase Storage
      const uploadedPhotoUrls: string[] = [];
      
      for (const photo of photos) {
        try {
          // Use real homeowner ID from database
          const result = await StorageService.uploadProjectImage(
            "2228799c-31af-47bd-92c6-04c7e454b0ae", // Real homeowner ID
            bidCardId,
            photo
          );
          uploadedPhotoUrls.push(result.url);
          console.log(`[RFI] Photo uploaded: ${result.url}`);
        } catch (error) {
          console.error(`[RFI] Failed to upload ${photo.name}:`, error);
          toast.error(`Failed to upload ${photo.name}`);
        }
      }

      // Step 2: Get current bid card data
      const { data: bidCard, error: fetchError } = await supabase
        .from("bid_cards")
        .select("bid_document")
        .eq("id", bidCardId)
        .single();

      if (fetchError) {
        throw new Error(`Failed to fetch bid card: ${fetchError.message}`);
      }

      // Step 3: Add new photos to existing images array
      const currentBidDocument = bidCard.bid_document || {};
      const currentExtractedData = currentBidDocument.all_extracted_data || {};
      const currentImages = currentExtractedData.images || [];
      
      const updatedImages = [...currentImages, ...uploadedPhotoUrls];
      
      const updatedBidDocument = {
        ...currentBidDocument,
        all_extracted_data: {
          ...currentExtractedData,
          images: updatedImages
        }
      };

      // Step 4: Update bid card with new photos
      const { error: updateError } = await supabase
        .from("bid_cards")
        .update({ 
          bid_document: updatedBidDocument,
          updated_at: new Date().toISOString()
        })
        .eq("id", bidCardId);

      if (updateError) {
        throw new Error(`Failed to update bid card: ${updateError.message}`);
      }

      // Step 5: Update RFI record as responded
      const { error: rfiError } = await supabase
        .from("rfi_requests")
        .update({ 
          status: "responded",
          response_message: responseMessage,
          photos_added: uploadedPhotoUrls.length,
          responded_at: new Date().toISOString()
        })
        .eq("id", rfiId);

      if (rfiError) {
        console.error("[RFI] Failed to update RFI record:", rfiError);
        // Don't fail the whole operation for this
      }

      // Step 6: Send notification to backend for contractor notification
      try {
        await fetch("/api/rfi/notify-response", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            rfi_id: rfiId,
            bid_card_id: bidCardId,
            photos_added: uploadedPhotoUrls.length,
            response_message: responseMessage
          })
        });
      } catch (notifyError) {
        console.error("[RFI] Notification failed:", notifyError);
        // Don't fail for notification issues
      }

      toast.success(`Response sent! Added ${uploadedPhotoUrls.length} photos to your bid card`);
      onSuccess();
      onClose();
      
    } catch (error) {
      console.error("[RFI] Response submission failed:", error);
      toast.error(`Failed to submit response: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-semibold text-gray-900">
                Respond to Information Request
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                From {contractorName}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Requested Items */}
        <div className="p-6 border-b border-gray-200 bg-blue-50">
          <h4 className="font-medium text-gray-900 mb-3">Information Requested:</h4>
          <ul className="space-y-2">
            {requestedItems.map((item, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Photo Upload Section */}
        <div className="p-6">
          <h4 className="font-medium text-gray-900 mb-4 flex items-center gap-2">
            <Image className="w-5 h-5" />
            Add Photos to Your Bid Card
          </h4>

          {/* Drop Zone */}
          <div
            className={`relative border-2 border-dashed rounded-lg p-6 transition-colors ${
              dragActive
                ? "border-blue-400 bg-blue-50"
                : "border-gray-300 bg-gray-50 hover:bg-gray-100"
            } ${uploading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => !uploading && document.getElementById("rfi-photo-input")?.click()}
          >
            <input
              id="rfi-photo-input"
              type="file"
              accept="image/*"
              multiple
              onChange={(e) => handleFileSelect(e.target.files)}
              className="hidden"
              disabled={uploading}
            />

            <div className="text-center">
              <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm font-medium text-gray-900">
                Upload Photos
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Drag & drop or click to select • JPG, PNG, WebP • Max 5MB each
              </p>
            </div>
          </div>

          {/* Selected Photos Preview */}
          {photos.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-900 mb-3">
                Selected Photos ({photos.length})
              </p>
              <div className="grid grid-cols-3 gap-3">
                {photos.map((photo, index) => (
                  <div key={index} className="relative group">
                    <img
                      src={URL.createObjectURL(photo)}
                      alt={`Preview ${index + 1}`}
                      className="w-full h-20 object-cover rounded-lg border border-gray-200"
                    />
                    <button
                      onClick={() => removePhoto(index)}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="w-4 h-4" />
                    </button>
                    <div className="absolute bottom-1 left-1 bg-black bg-opacity-60 text-white text-xs px-1 rounded">
                      {photo.name.length > 15 ? `${photo.name.substring(0, 15)}...` : photo.name}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Message Section */}
          <div className="mt-6">
            <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Additional Message (Optional)
            </h4>
            <textarea
              value={responseMessage}
              onChange={(e) => setResponseMessage(e.target.value)}
              placeholder="Add any additional details or context..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
            />
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 bg-gray-50 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={uploading || (photos.length === 0 && !responseMessage.trim())}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Uploading...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Send Response
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RFIResponseForm;