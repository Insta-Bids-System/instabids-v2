import { supabase } from "./supabase";

export interface PhotoData {
  id: string;
  user_id: string;
  project_id: string;
  photo_data: string; // base64 encoded
  mime_type: string;
  description: string;
  created_at: string;
}

export class PhotoService {
  /**
   * Convert photo ID to data URL for display
   * Handles both old URL format and new database storage
   */
  static async getPhotoDataUrl(photoRef: string): Promise<string | null> {
    try {
      // If it's already a full URL, return as-is
      if (photoRef.startsWith("http://") || photoRef.startsWith("https://")) {
        return photoRef;
      }

      // If it's a photo_id reference, fetch from database
      if (photoRef.startsWith("photo_id:")) {
        const photoId = photoRef.replace("photo_id:", "");
        return await PhotoService.getPhotoById(photoId);
      }

      // If it's just an ID, try to fetch directly
      return await PhotoService.getPhotoById(photoRef);
    } catch (error) {
      console.error("Error converting photo reference:", error);
      return null;
    }
  }

  /**
   * Get photo by ID from database and convert to data URL
   */
  static async getPhotoById(photoId: string): Promise<string | null> {
    try {
      const { data, error } = await supabase
        .from("photo_storage")
        .select("*")
        .eq("id", photoId)
        .single();

      if (error || !data) {
        console.error("Photo not found:", photoId, error);
        return null;
      }

      // Convert base64 data to data URL
      const mimeType = data.mime_type || "image/jpeg";
      return `data:${mimeType};base64,${data.photo_data}`;
    } catch (error) {
      console.error("Error fetching photo:", error);
      return null;
    }
  }

  /**
   * Get all photos for a project/session
   */
  static async getProjectPhotos(projectId: string): Promise<PhotoData[]> {
    try {
      const { data, error } = await supabase
        .from("photo_storage")
        .select("*")
        .eq("project_id", projectId)
        .order("created_at", { ascending: true });

      if (error) {
        console.error("Error fetching project photos:", error);
        return [];
      }

      return data || [];
    } catch (error) {
      console.error("Error fetching project photos:", error);
      return [];
    }
  }

  /**
   * Convert array of photo references to data URLs
   * Handles mixed arrays of URLs and photo IDs
   */
  static async convertPhotoRefsToUrls(photoRefs: string[]): Promise<string[]> {
    if (!photoRefs || photoRefs.length === 0) {
      return [];
    }

    const photoPromises = photoRefs.map((ref) => PhotoService.getPhotoDataUrl(ref));
    const results = await Promise.all(photoPromises);

    // Filter out null results
    return results.filter((url): url is string => url !== null);
  }

  /**
   * Get photo metadata without loading the actual image data
   */
  static async getPhotoMetadata(photoId: string): Promise<Omit<PhotoData, "photo_data"> | null> {
    try {
      const { data, error } = await supabase
        .from("photo_storage")
        .select("id, user_id, project_id, mime_type, description, created_at")
        .eq("id", photoId)
        .single();

      if (error || !data) {
        return null;
      }

      return data;
    } catch (error) {
      console.error("Error fetching photo metadata:", error);
      return null;
    }
  }
}
