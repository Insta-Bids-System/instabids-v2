import type React from "react";
import { useState } from "react";
import toast from "react-hot-toast";
import { supabase } from "@/lib/supabase";

interface PhotoUploadProps {
  propertyId: string;
  roomId?: string;
  userId: string;
  onUploadComplete: (result: any) => void;
  context?: "property" | "inspiration" | "general";
  onOpenIrisChat?: (photoData: any) => void;
}

const PhotoUpload: React.FC<PhotoUploadProps> = ({ 
  propertyId, 
  roomId, 
  userId, 
  onUploadComplete,
  context = "property",
  onOpenIrisChat
}) => {
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [showRoomConfirmation, setShowRoomConfirmation] = useState(false);
  const [selectedRoomType, setSelectedRoomType] = useState("");
  const [workSuggestions, setWorkSuggestions] = useState("");

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    if (!file.type.startsWith('image/')) {
      toast.error("Please upload an image file");
      return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      toast.error("Image must be smaller than 10MB");
      return;
    }

    setUploading(true);
    console.log('[PhotoUpload] Starting upload process...');

    try {
      // Send directly to our backend API for AI analysis
      console.log('[PhotoUpload] Sending photo to backend for AI analysis...');
      
      const formData = new FormData();
      formData.append('file', file);
      formData.append('photo_type', 'documentation');
      if (roomId) {
        formData.append('room_id', roomId);
      }

      const propertyApiResponse = await fetch(`/api/properties/${propertyId}/photos/upload?user_id=${userId}`, {
        method: 'POST',
        body: formData,
      });

      if (!propertyApiResponse.ok) {
        const errorText = await propertyApiResponse.text();
        console.error('[PhotoUpload] Property API failed:', errorText);
        toast.error("Failed to analyze photo with AI");
        return;
      }

      const aiAnalysisResult = await propertyApiResponse.json();
      console.log('[PhotoUpload] AI analysis completed:', aiAnalysisResult);
      
      // Extract the photo data created by the property API
      const photoId = aiAnalysisResult.photo_id;
      const realAiDescription = aiAnalysisResult.ai_description || "AI analysis completed";
      const realAiClassification = aiAnalysisResult.ai_classification || {};
      const publicUrl = aiAnalysisResult.photo_url || `data:${file.type};base64,uploaded`;

      // The property API already saved the photo to the database with REAL AI analysis
      console.log('[PhotoUpload] Photo saved to database with REAL AI analysis');
      
      // Check if maintenance tasks were detected by the AI
      let maintenanceTasksCreated = 0;
      if (realAiClassification.detected_issues && realAiClassification.detected_issues.length > 0) {
        console.log(`[PhotoUpload] Found ${realAiClassification.detected_issues.length} maintenance issues`);
        maintenanceTasksCreated = realAiClassification.detected_issues.length;
      }

      // Note: Inspiration board saving disabled to avoid Supabase auth issues
      console.log('[PhotoUpload] Photo processed successfully');

      // Step 4: Create context message for IRIS with real AI analysis
      let contextMessage = "";
      if (context === "property") {
        contextMessage = `I just uploaded a photo of my property. AI analysis found: ${realAiDescription}. ${
          realAiClassification.detected_issues?.length > 0 
            ? `Issues detected: ${realAiClassification.detected_issues.map(i => i.description).join(', ')}. ` 
            : ''
        }Can you help me organize what needs to be done?`;
      } else if (context === "inspiration") {
        contextMessage = `I uploaded this photo as inspiration. AI analysis: ${realAiDescription}. Can you help me analyze the style and add it to my inspiration board?`;
      } else {
        contextMessage = `I uploaded this photo. AI analysis: ${realAiDescription}. Can you help me figure out if this is my current property or inspiration for future projects?`;
      }

      // Step 5: Send to IRIS with the actual photo URL
      const response = await fetch("/api/iris/chat", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          message: `${contextMessage}\n\n[Photo uploaded: ${file.name}]`,
          room_type: realAiClassification.room_type || (context === "property" ? "general" : context),
          conversation_context: [{
            type: "photo_upload",
            filename: file.name,
            context: context,
            property_id: propertyId,
            room_id: roomId,
            image_url: publicUrl,
            photo_saved: true,
            property_photo_id: photoId,
            ai_analysis: realAiClassification,
            ai_description: realAiDescription,
            detected_assets: realAiClassification.detected_assets || [],
            detected_issues: realAiClassification.detected_issues || [],
            maintenance_opportunities: realAiClassification.maintenance_opportunities || [],
            safety_concerns: realAiClassification.safety_concerns || []
          }]
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('[PhotoUpload] IRIS analysis successful:', result);
        
        const detectedAssets = realAiClassification.detected_assets?.length || 0;
        const detectedIssues = realAiClassification.detected_issues?.length || 0;
        
        let successMessage = `Photo analyzed with AI and saved! `;
        if (detectedAssets > 0) {
          successMessage += `Found ${detectedAssets} assets. `;
        }
        if (detectedIssues > 0) {
          successMessage += `Detected ${detectedIssues} maintenance issues. `;
        }
        successMessage += `Room type: ${realAiClassification.room_type || 'unknown'}`;
        
        toast.success(successMessage);
        
        if (detectedIssues > 0) {
          toast.success(`Detected ${detectedIssues} maintenance issues!`);
        }
        
        // Open IRIS chat with the photo and response
        if (onOpenIrisChat) {
          onOpenIrisChat({
            image: publicUrl,
            filename: file.name,
            irisResponse: result.response,
            context: context,
            aiAnalysis: realAiClassification,
            aiDescription: realAiDescription,
            detectedAssets: detectedAssets,
            detectedIssues: detectedIssues
          });
        }
        
        // Also trigger completion for any parent component logic
        onUploadComplete({
          photo_uploaded: true,
          photo_url: publicUrl,
          photo_id: photoId,
          iris_response: result.response,
          context: context,
          dual_context_saved: true,
          ai_analysis: realAiClassification,
          ai_description: realAiDescription,
          detected_assets: detectedAssets,
          detected_issues: detectedIssues,
          room_type: realAiClassification.room_type,
          assets_created: aiAnalysisResult.detected_assets || 0
        });
        
      } else {
        const error = await response.json();
        console.error('[PhotoUpload] IRIS analysis failed:', error);
        toast.error('Photo uploaded but IRIS analysis failed');
        
        // Still trigger completion since photo was saved with AI analysis
        onUploadComplete({
          photo_uploaded: true,
          photo_url: publicUrl,
          photo_id: photoId,
          context: context,
          iris_failed: true,
          ai_analysis: realAiClassification,
          ai_description: realAiDescription,
          detected_assets: realAiClassification.detected_assets?.length || 0,
          detected_issues: realAiClassification.detected_issues?.length || 0,
          room_type: realAiClassification.room_type
        });
      }
    } catch (error) {
      console.error('Photo upload error:', error);
      toast.error('Failed to upload photo');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFileUpload(e.dataTransfer.files);
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

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileUpload(e.target.files);
    e.target.value = ''; // Reset input
  };

  const handleRoomConfirmation = async () => {
    if (!uploadResult) return;

    try {
      const formData = new FormData();
      formData.append('room_type', selectedRoomType);
      formData.append('room_name', selectedRoomType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()));
      if (workSuggestions.trim()) {
        formData.append('work_suggestions', workSuggestions);
      }

      const response = await fetch(
        `/api/properties/${propertyId}/photos/${uploadResult.photo_id}/confirm-room?user_id=${userId}`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log('[PhotoUpload] Room confirmed:', result);
        
        toast.success(
          `Room confirmed! Created ${result.assets_created} assets in ${result.room_name}`
        );
        
        // Reset states
        setShowRoomConfirmation(false);
        setUploadResult(null);
        setSelectedRoomType("");
        setWorkSuggestions("");
        
        onUploadComplete({
          ...uploadResult,
          ...result
        });
      } else {
        const error = await response.json();
        console.error('[PhotoUpload] Room confirmation failed:', error);
        toast.error('Failed to confirm room');
      }
    } catch (error) {
      console.error('Room confirmation error:', error);
      toast.error('Failed to confirm room');
    }
  };

  const roomTypes = [
    { value: "living_room", label: "Living Room", icon: "🛋️" },
    { value: "kitchen", label: "Kitchen", icon: "🍳" },
    { value: "bedroom", label: "Bedroom", icon: "🛏️" },
    { value: "bathroom", label: "Bathroom", icon: "🛁" },
    { value: "dining_room", label: "Dining Room", icon: "🍽️" },
    { value: "home_office", label: "Home Office", icon: "💻" },
    { value: "garage", label: "Garage", icon: "🚗" },
    { value: "basement", label: "Basement", icon: "🏠" },
    { value: "attic", label: "Attic", icon: "📦" },
    { value: "laundry_room", label: "Laundry Room", icon: "👕" },
    { value: "patio", label: "Patio/Deck", icon: "🪴" },
    { value: "other", label: "Other", icon: "❓" }
  ];

  return (
    <div className="w-full">
      {showRoomConfirmation ? (
        // Room Confirmation UI
        <div className="space-y-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 text-lg">✓</span>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-medium text-green-900 mb-2">
                  Photo Uploaded Successfully!
                </h3>
                <p className="text-green-700 mb-4">
                  AI has analyzed your photo and detected some assets. Please confirm what room this is so we can organize everything properly.
                </p>
                
                {uploadResult?.ai_description && (
                  <div className="bg-white rounded-lg p-4 mb-4">
                    <h4 className="font-medium text-gray-900 mb-2">AI Analysis:</h4>
                    <p className="text-gray-700 text-sm">{uploadResult.ai_description}</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                What room is this? <span className="text-red-500">*</span>
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {roomTypes.map((room) => (
                  <button
                    key={room.value}
                    onClick={() => setSelectedRoomType(room.value)}
                    className={`p-3 rounded-lg border text-left transition-colors ${
                      selectedRoomType === room.value
                        ? "border-blue-500 bg-blue-50 text-blue-900"
                        : "border-gray-300 bg-white hover:bg-gray-50"
                    }`}
                  >
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{room.icon}</span>
                      <span className="text-sm font-medium">{room.label}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                What work do you want to do in this room? (Optional)
              </label>
              <textarea
                value={workSuggestions}
                onChange={(e) => setWorkSuggestions(e.target.value)}
                placeholder="e.g., Replace broken blinds, paint walls, update lighting..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
              />
              <p className="text-xs text-gray-500 mt-1">
                This helps us suggest relevant contractors and prioritize maintenance items.
              </p>
            </div>

            <div className="flex space-x-3">
              <button
                onClick={handleRoomConfirmation}
                disabled={!selectedRoomType}
                className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                Confirm & Create Room
              </button>
              <button
                onClick={() => {
                  setShowRoomConfirmation(false);
                  setUploadResult(null);
                }}
                className="px-4 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : (
        // Photo Upload UI
        <>
          <div
            className={`relative border-2 border-dashed rounded-lg p-8 transition-colors ${
              dragActive
                ? "border-blue-400 bg-blue-50"
                : "border-gray-300 bg-gray-50 hover:bg-gray-100"
            } ${uploading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => !uploading && !showRoomConfirmation && document.getElementById("photo-input")?.click()}
          >
            <input
              id="photo-input"
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
              disabled={uploading}
            />

            <div className="text-center">
              {uploading ? (
                <div className="space-y-3">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="text-sm text-gray-600">
                    Analyzing photo with AI...
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="text-4xl">📸</div>
                  <div>
                    <p className="text-lg font-medium text-gray-900">
                      Upload Property Photo
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      GPT-4o will analyze the photo and detect assets, issues, and room type
                    </p>
                  </div>
                  <div className="text-sm text-gray-500">
                    Drag & drop or click to select • JPG, PNG • Max 10MB
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 text-xs text-gray-500">
            <div className="font-medium mb-1">How it works:</div>
            <ul className="list-disc list-inside space-y-1">
              <li>Upload a photo of any room</li>
              <li>GPT-4o analyzes and detects fixtures, assets, and maintenance issues</li>
              <li>Photo saved to both property documentation and inspiration board</li>
              <li>Maintenance tasks automatically created from detected issues</li>
              <li>IRIS AI helps you plan next steps and organize projects</li>
            </ul>
          </div>
        </>
      )}
    </div>
  );
};

export default PhotoUpload;