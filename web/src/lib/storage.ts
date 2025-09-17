import { supabase } from "./supabase";

export type UploadResult = {
  url: string;
  path: string;
};

export type UploadResponse = {
  success: boolean;
  url?: string;
  path?: string;
  error?: string;
};

export class StorageService {
  static async uploadProjectImage(
    userId: string,
    projectId: string,
    file: File
  ): Promise<UploadResult> {
    const fileExt = file.name.split(".").pop();
    const fileName = `${Date.now()}.${fileExt}`;
    const filePath = `${userId}/${projectId}/${fileName}`;

    const { data, error } = await supabase.storage.from("project-images").upload(filePath, file, {
      contentType: file.type,
      upsert: false,
    });

    if (error) {
      throw new Error(`Upload failed: ${error.message}`);
    }

    const {
      data: { publicUrl },
    } = supabase.storage.from("project-images").getPublicUrl(filePath);

    return {
      url: publicUrl,
      path: filePath,
    };
  }

  static async uploadProjectDocument(
    userId: string,
    projectId: string,
    file: File
  ): Promise<UploadResult> {
    const _fileExt = file.name.split(".").pop();
    const fileName = `${Date.now()}-${file.name}`;
    const filePath = `${userId}/${projectId}/${fileName}`;

    const { data, error } = await supabase.storage
      .from("project-documents")
      .upload(filePath, file, {
        contentType: file.type,
        upsert: false,
      });

    if (error) {
      throw new Error(`Upload failed: ${error.message}`);
    }

    const {
      data: { publicUrl },
    } = supabase.storage.from("project-documents").getPublicUrl(filePath);

    return {
      url: publicUrl,
      path: filePath,
    };
  }

  static async deleteFile(bucket: string, path: string): Promise<void> {
    const { error } = await supabase.storage.from(bucket).remove([path]);

    if (error) {
      throw new Error(`Delete failed: ${error.message}`);
    }
  }

  static async uploadProfileImage(userId: string, file: File): Promise<UploadResult> {
    const fileExt = file.name.split(".").pop();
    const fileName = `avatar.${fileExt}`;
    const filePath = `${userId}/${fileName}`;

    const { data, error } = await supabase.storage.from("profile-images").upload(filePath, file, {
      contentType: file.type,
      upsert: true, // Replace existing avatar
    });

    if (error) {
      throw new Error(`Upload failed: ${error.message}`);
    }

    const {
      data: { publicUrl },
    } = supabase.storage.from("profile-images").getPublicUrl(filePath);

    return {
      url: publicUrl,
      path: filePath,
    };
  }

  // Helper to convert File to base64 for sending to backend
  static async fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = (error) => reject(error);
    });
  }

  // Helper to validate file size and type
  static validateImage(file: File, maxSizeMB: number = 5): string | null {
    const maxSize = maxSizeMB * 1024 * 1024; // Convert to bytes

    if (file.size > maxSize) {
      return `File size must be less than ${maxSizeMB}MB`;
    }

    const allowedTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
      return "File must be a JPEG, PNG, or WebP image";
    }

    return null;
  }

  // Generic image upload method for chat interface - now uses database storage
  static async uploadImage(file: File): Promise<UploadResponse> {
    try {
      // Validate the image first
      const validationError = StorageService.validateImage(file);
      if (validationError) {
        return {
          success: false,
          error: validationError,
        };
      }

      // Convert file to base64
      const base64Data = await StorageService.fileToBase64(file);

      // Extract clean base64 (without data: prefix)
      const cleanBase64 = base64Data.split(",")[1];

      // For now, use a default user ID and project ID for chat uploads
      // In production, these would come from the authenticated user context
      const defaultUserId = "0912f528-924c-4a7c-8b70-2708b3f5f227"; // Working test user
      const defaultProjectId = `chat-upload-${Date.now()}`;

      // Store in photo_storage table via database
      const photoRecord = {
        user_id: defaultUserId,
        project_id: defaultProjectId,
        photo_data: cleanBase64,
        mime_type: file.type,
        description: `Chat uploaded ${file.name}`,
      };

      const { data, error } = await supabase
        .from("photo_storage")
        .insert(photoRecord)
        .select()
        .single();

      if (error) {
        return {
          success: false,
          error: `Database storage failed: ${error.message}`,
        };
      }

      // Return photo ID as reference
      return {
        success: true,
        url: `photo_id:${data.id}`,
        path: data.id,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown upload error",
      };
    }
  }
}
