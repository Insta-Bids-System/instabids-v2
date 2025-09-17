import { AlertCircle, Camera, Upload, X } from "lucide-react";
import type React from "react";
import { useRef, useState } from "react";
import toast from "react-hot-toast";

interface ImageUploadButtonProps {
  onUpload: (file: File) => Promise<void>;
  loading?: boolean;
  accept?: string;
  maxSize?: number; // in MB
  buttonText?: string;
  buttonIcon?: "camera" | "upload";
  className?: string;
}

const ImageUploadButton: React.FC<ImageUploadButtonProps> = ({
  onUpload,
  loading = false,
  accept = "image/jpeg,image/jpg,image/png,image/gif,image/webp",
  maxSize = 10,
  buttonText = "Upload Image",
  buttonIcon = "camera",
  className = "",
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = accept.split(",").map((t) => t.trim());
    if (!allowedTypes.some((type) => file.type.match(type.replace("*", ".*")))) {
      toast.error(`Invalid file type. Allowed: ${allowedTypes.join(", ")}`);
      return;
    }

    // Validate file size
    const maxSizeBytes = maxSize * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      toast.error(`File size exceeds ${maxSize}MB limit`);
      return;
    }

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      await onUpload(selectedFile);
      // Clear after successful upload
      setPreview(null);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      console.error("Upload failed:", error);
      toast.error("Failed to upload image");
    } finally {
      setUploading(false);
    }
  };

  const handleCancel = () => {
    setPreview(null);
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const Icon = buttonIcon === "camera" ? Camera : Upload;

  if (preview && selectedFile) {
    return (
      <div className="relative inline-block">
        <div className="bg-white border rounded-lg p-2 shadow-sm">
          <img src={preview} alt="Preview" className="max-h-32 max-w-full rounded" />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleUpload}
              disabled={uploading || loading}
              className="flex-1 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? "Uploading..." : "Send"}
            </button>
            <button
              onClick={handleCancel}
              disabled={uploading}
              className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleFileSelect}
        className="hidden"
      />
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={loading || uploading}
        className={`flex items-center gap-2 px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      >
        <Icon className="w-5 h-5" />
        {buttonText}
      </button>
    </>
  );
};

export default ImageUploadButton;
