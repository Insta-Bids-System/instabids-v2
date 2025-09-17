import { Image as ImageIcon, Upload, X } from "lucide-react";
import type React from "react";
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import toast from "react-hot-toast";

interface DragDropZoneProps {
  onFilesAccepted: (files: File[]) => void;
  maxFiles?: number;
  maxSize?: number; // in bytes
  accept?: Record<string, string[]>;
}

const DragDropZone: React.FC<DragDropZoneProps> = ({
  onFilesAccepted,
  maxFiles = 10,
  maxSize = 10 * 1024 * 1024, // 10MB default
  accept = {
    "image/*": [".jpeg", ".jpg", ".png", ".webp", ".gif"],
  },
}) => {
  const onDrop = useCallback(
    (acceptedFiles: File[], fileRejections: any[]) => {
      if (fileRejections.length > 0) {
        const errors = fileRejections.map((rejection) => {
          const error = rejection.errors[0];
          if (error.code === "file-too-large") {
            return `${rejection.file.name} is too large. Max size is ${maxSize / 1024 / 1024}MB`;
          } else if (error.code === "file-invalid-type") {
            return `${rejection.file.name} is not a supported image format`;
          } else if (error.code === "too-many-files") {
            return `Too many files. Max ${maxFiles} files allowed`;
          }
          return error.message;
        });

        errors.forEach((error) => toast.error(error));
        return;
      }

      if (acceptedFiles.length > 0) {
        onFilesAccepted(acceptedFiles);
        toast.success(
          `${acceptedFiles.length} image${acceptedFiles.length > 1 ? "s" : ""} ready to upload`
        );
      }
    },
    [onFilesAccepted, maxFiles, maxSize]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept,
    maxFiles,
    maxSize,
  });

  return (
    <div
      {...getRootProps()}
      className={`
        relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
        ${isDragActive && !isDragReject ? "border-primary-500 bg-primary-50" : ""}
        ${isDragReject ? "border-red-500 bg-red-50" : ""}
        ${!isDragActive && !isDragReject ? "border-gray-300 hover:border-gray-400" : ""}
      `}
    >
      <input {...getInputProps()} />

      <div className="flex flex-col items-center">
        {isDragReject ? (
          <>
            <X className="w-12 h-12 text-red-500 mb-4" />
            <p className="text-red-600 font-medium mb-2">File type not accepted</p>
            <p className="text-sm text-red-600">Please upload image files only</p>
          </>
        ) : isDragActive ? (
          <>
            <Upload className="w-12 h-12 text-primary-500 mb-4 animate-bounce" />
            <p className="text-primary-600 font-medium mb-2">Drop your images here</p>
            <p className="text-sm text-primary-600">Release to upload</p>
          </>
        ) : (
          <>
            <ImageIcon className="w-12 h-12 text-gray-400 mb-4" />
            <p className="text-gray-700 font-medium mb-2">Drag & drop images here</p>
            <p className="text-sm text-gray-500 mb-4">or click to browse</p>
            <div className="space-y-1">
              <p className="text-xs text-gray-400">Supports: JPG, PNG, WebP, GIF</p>
              <p className="text-xs text-gray-400">Max size: {maxSize / 1024 / 1024}MB per file</p>
              <p className="text-xs text-gray-400">Max files: {maxFiles} at once</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DragDropZone;
