import { AlertCircle, CheckCircle, Home, Sparkles, Target, Upload, X } from "lucide-react";
import type React from "react";
import { useState } from "react";
import toast from "react-hot-toast";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/lib/supabase";
import DragDropZone from "./DragDropZone";

interface ImageUploaderProps {
  boardId: string;
  onUploadComplete: (uploadedImages: UploadedImage[]) => void;
  onClose?: () => void;
  defaultCategory?: "current" | "inspiration" | "vision";
}

interface UploadedImage {
  id: string;
  boardId: string;
  imageUrl: string;
  thumbnailUrl: string;
}

interface UploadProgress {
  file: File;
  progress: number;
  status: "pending" | "uploading" | "success" | "error";
  error?: string;
  url?: string;
}

const ImageUploader: React.FC<ImageUploaderProps> = ({
  boardId,
  onUploadComplete,
  onClose,
  defaultCategory = "inspiration",
}) => {
  const { user } = useAuth();
  const [uploadQueue, setUploadQueue] = useState<UploadProgress[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadCategory, _setUploadCategory] = useState<"current" | "inspiration" | "vision">(
    defaultCategory
  );

  // Check for demo user
  const demoUser = localStorage.getItem("DEMO_USER");
  const userId = user?.id || (demoUser ? JSON.parse(demoUser).id : null);

  const handleFilesAccepted = (files: File[]) => {
    const newUploads = files.map((file) => ({
      file,
      progress: 0,
      status: "pending" as const,
    }));

    setUploadQueue((prev) => [...prev, ...newUploads]);
    uploadFiles(newUploads);
  };

  const uploadFiles = async (uploads: UploadProgress[]) => {
    setIsUploading(true);
    const uploadedImages: UploadedImage[] = [];

    for (let i = 0; i < uploads.length; i++) {
      const upload = uploads[i];

      // Update status to uploading
      setUploadQueue((prev) =>
        prev.map((u, idx) => (idx === i ? { ...u, status: "uploading" } : u))
      );

      try {
        // Generate unique filename
        const timestamp = Date.now();
        const fileExt = upload.file.name.split(".").pop();
        const fileName = `${userId}/${boardId}/${timestamp}_${Math.random().toString(36).substring(7)}.${fileExt}`;

        // Upload to Supabase storage
        const { data, error } = await supabase.storage
          .from("inspiration")
          .upload(fileName, upload.file, {
            cacheControl: "3600",
            upsert: false,
          });

        if (error) throw error;

        // Get public URL
        const {
          data: { publicUrl },
        } = supabase.storage.from("inspiration").getPublicUrl(fileName);

        // Create database record with category tags
        const tags =
          uploadCategory === "current"
            ? ["current"]
            : uploadCategory === "vision"
              ? ["vision"]
              : [];

        const { data: imageRecord, error: dbError } = await supabase
          .from("inspiration_images")
          .insert({
            board_id: boardId,
            user_id: userId,
            image_url: publicUrl,
            thumbnail_url: publicUrl, // For now, same as image_url
            source: "upload",
            tags: tags,
            position: i,
          })
          .select()
          .single();

        if (dbError) throw dbError;

        // Update progress
        setUploadQueue((prev) =>
          prev.map((u, idx) =>
            idx === i
              ? {
                  ...u,
                  status: "success",
                  progress: 100,
                  url: publicUrl,
                }
              : u
          )
        );

        uploadedImages.push({
          id: imageRecord.id,
          boardId: boardId,
          imageUrl: publicUrl,
          thumbnailUrl: publicUrl,
        });
      } catch (error) {
        console.error("Upload error:", error);

        setUploadQueue((prev) =>
          prev.map((u, idx) =>
            idx === i
              ? {
                  ...u,
                  status: "error",
                  error: error instanceof Error ? error.message : "Upload failed",
                }
              : u
          )
        );

        toast.error(`Failed to upload ${upload.file.name}`);
      }
    }

    setIsUploading(false);

    if (uploadedImages.length > 0) {
      onUploadComplete(uploadedImages);
      toast.success(
        `Successfully uploaded ${uploadedImages.length} image${uploadedImages.length > 1 ? "s" : ""}`
      );
    }
  };

  const _removeFromQueue = (index: number) => {
    setUploadQueue((prev) => prev.filter((_, i) => i !== index));
  };

  const _clearCompleted = () => {
    setUploadQueue((prev) => prev.filter((u) => u.status !== "success"));
  };

  return (
    <div className="space-y-4">
      {/* Category Selector */}
      <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
        <span className="text-sm font-medium text-gray-700">Upload images to:</span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => _setUploadCategory("current")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all ${
              uploadCategory === "current"
                ? "bg-blue-500 text-white"
                : "bg-white text-gray-600 hover:bg-gray-100"
            }`}
          >
            <Home className="w-4 h-4" />
            Current Space
          </button>
          <button
            type="button"
            onClick={() => _setUploadCategory("inspiration")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all ${
              uploadCategory === "inspiration"
                ? "bg-purple-500 text-white"
                : "bg-white text-gray-600 hover:bg-gray-100"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            Inspiration
          </button>
          <button
            type="button"
            onClick={() => _setUploadCategory("vision")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all ${
              uploadCategory === "vision"
                ? "bg-green-500 text-white"
                : "bg-white text-gray-600 hover:bg-gray-100"
            }`}
          >
            <Target className="w-4 h-4" />
            My Vision
          </button>
        </div>
      </div>

      {/* Drag Drop Zone */}
      {uploadQueue.length === 0 || uploadQueue.every((u) => u.status === "success") ? (
        <DragDropZone onFilesAccepted={handleFilesAccepted} />
      ) : null}

      {/* Upload Queue */}
      {uploadQueue.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="font-medium text-gray-900">Upload Queue</h4>
            {uploadQueue.some((u) => u.status === "success") && (
              <button
                type="button"
                onClick={_clearCompleted}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Clear completed
              </button>
            )}
          </div>

          <div className="space-y-2">
            {uploadQueue.map((upload, index) => (
              <div key={index} className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
                {/* Status Icon */}
                <div className="flex-shrink-0">
                  {upload.status === "pending" && (
                    <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
                      <Upload className="w-4 h-4 text-gray-500" />
                    </div>
                  )}
                  {upload.status === "uploading" && (
                    <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                    </div>
                  )}
                  {upload.status === "success" && (
                    <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    </div>
                  )}
                  {upload.status === "error" && (
                    <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                      <AlertCircle className="w-4 h-4 text-red-600" />
                    </div>
                  )}
                </div>

                {/* File Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{upload.file.name}</p>
                  <p className="text-xs text-gray-500">
                    {(upload.file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                  {upload.error && <p className="text-xs text-red-600 mt-1">{upload.error}</p>}
                </div>

                {/* Remove Button */}
                {(upload.status === "pending" ||
                  upload.status === "error" ||
                  upload.status === "success") && (
                  <button
                    type="button"
                    onClick={() => _removeFromQueue(index)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add More Button */}
      {uploadQueue.length > 0 && !isUploading && (
        <button
          type="button"
          onClick={() => {
            const input = document.createElement("input");
            input.type = "file";
            input.click();
          }}
          className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-700 transition-colors"
        >
          + Add more images
        </button>
      )}
    </div>
  );
};

export default ImageUploader;
