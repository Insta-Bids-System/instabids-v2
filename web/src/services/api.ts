// API service for connecting to the Instabids backend
import { circuitBreakerManager } from '../utils/circuitBreaker';

const API_BASE_URL = ""; // Use relative URLs to go through Vite proxy
console.log("FORCED API_BASE_URL:", API_BASE_URL || "Using Vite proxy");

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  phase?: string;
  extractedData?: any;
}

export interface ChatMessage {
  message: string;
  images?: string[];
  user_id?: string;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  phase?: string;
  extractedData?: any;
  sessionId?: string;
  conversationState?: any;
}

class ApiService {
  // Generic HTTP methods that match axios-style API
  async get(endpoint: string, config?: { params?: any; headers?: any }) {
    let queryParams = "";
    if (config?.params) {
      const params = new URLSearchParams();
      Object.entries(config.params).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach((v) => params.append(key, v));
        } else if (value !== undefined && value !== null) {
          params.append(key, value);
        }
      });
      queryParams = params.toString() ? `?${params.toString()}` : "";
    }
    const response = await this.request(endpoint + queryParams, {
      method: "GET",
      headers: config?.headers,
    });
    if (!response.success) throw new Error(response.error);
    return { data: response.data };
  }

  async post(endpoint: string, data?: any, config?: { params?: any; headers?: any }) {
    const queryParams = config?.params ? `?${new URLSearchParams(config.params).toString()}` : "";
    const response = await this.request(endpoint + queryParams, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
      headers: config?.headers,
    });
    if (!response.success) throw new Error(response.error);
    return { data: response.data };
  }

  async put(endpoint: string, data?: any, config?: { params?: any; headers?: any }) {
    const queryParams = config?.params ? `?${new URLSearchParams(config.params).toString()}` : "";
    const response = await this.request(endpoint + queryParams, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
      headers: config?.headers,
    });
    if (!response.success) throw new Error(response.error);
    return { data: response.data };
  }

  async delete(endpoint: string, config?: { params?: any; headers?: any }) {
    const queryParams = config?.params ? `?${new URLSearchParams(config.params).toString()}` : "";
    const response = await this.request(endpoint + queryParams, {
      method: "DELETE",
      headers: config?.headers,
    });
    if (!response.success) throw new Error(response.error);
    return { data: response.data };
  }

  private async request<T>(endpoint: string, options: RequestInit = {}, retries = 3): Promise<ApiResponse<T>> {
    // Use circuit breaker for resilience
    const circuitBreakerName = `api-${endpoint.split('/')[1] || 'default'}`;
    
    try {
      return await circuitBreakerManager.execute(
        circuitBreakerName,
        async () => {
          let lastError: Error | null = null;
          
          // Retry logic with exponential backoff
          for (let attempt = 0; attempt < retries; attempt++) {
            try {
              const url = `${API_BASE_URL}${endpoint}`;
              console.log(`[API] Attempt ${attempt + 1}/${retries} to: ${url}`);

              const response = await fetch(url, {
                headers: {
                  "Content-Type": "application/json",
                  ...options.headers,
                },
                ...options,
              });

              if (!response.ok) {
                // Don't retry on client errors (4xx), only server errors (5xx)
                if (response.status >= 400 && response.status < 500) {
                  throw new Error(`HTTP error! status: ${response.status}`);
                }
                // Server error - will retry
                lastError = new Error(`HTTP error! status: ${response.status}`);
                if (attempt < retries - 1) {
                  const delay = Math.min(1000 * Math.pow(2, attempt), 5000); // Max 5 second delay
                  console.log(`[API] Server error, retrying in ${delay}ms...`);
                  await new Promise(resolve => setTimeout(resolve, delay));
                  continue;
                }
              }

              const data = await response.json();
              console.log(`[API] Success on attempt ${attempt + 1}:`, data);

              return {
                success: true,
                data,
              };
            } catch (error) {
              lastError = error instanceof Error ? error : new Error("Unknown error");
              console.error(`[API] Error on attempt ${attempt + 1} for ${endpoint}:`, error);
              
              // If it's a connection error and we have retries left, wait and retry
              if (attempt < retries - 1 && error instanceof TypeError && error.message.includes('fetch')) {
                const delay = Math.min(1000 * Math.pow(2, attempt), 5000);
                console.log(`[API] Connection failed, retrying in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
                continue;
              }
            }
          }
          
          // All retries failed
          console.error(`[API] All ${retries} attempts failed for ${endpoint}`);
          throw lastError || new Error("All retries failed");
        },
        {
          failureThreshold: 3,
          resetTimeout: 30000, // 30 seconds
          successThreshold: 2,
          timeout: 15000 // 15 seconds
        }
      );
    } catch (error) {
      console.error(`[API] Circuit breaker error for ${endpoint}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  // Health check endpoint
  async healthCheck(): Promise<ApiResponse<{ status: string; agents: string[] }>> {
    return this.request("/");
  }

  // Chat with CIA agent - DEPRECATED: Use SSE streaming instead
  async sendChatMessage(
    message: string,
    images: string[] = [],
    userId?: string,
    sessionId?: string,
    projectId?: string
  ): Promise<ApiResponse<ChatResponse>> {
    // Redirect to streaming endpoint - no fallbacks allowed
    throw new Error(
      "sendChatMessage is deprecated. Use SSE streaming endpoint /ai/chat/stream with useSSEChatStream hook. No fallback responses allowed."
    );
  }

  // Chat with contractor onboarding agent (COIA) - Authenticated version
  async sendContractorOnboardingMessage(
    message: string,
    sessionId: string,
    contractorLeadId?: string,
    projectId?: string,
    context?: any
  ): Promise<ApiResponse<ChatResponse & { bidCards?: any[]; aiRecommendation?: string }>> {
    const payload = {
      message,
      session_id: sessionId,
      contractor_lead_id: contractorLeadId,
      project_id: projectId,
      context: context,
    };

    return this.request<ChatResponse & { bidCards?: any[]; aiRecommendation?: string }>(
      "/api/coia/chat",
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  }

  // Chat with contractor onboarding agent (COIA) - Landing page version (unauthenticated)
  async sendContractorLandingMessage(
    message: string,
    sessionId: string,
    contractorLeadId?: string,
    context?: any
  ): Promise<ApiResponse<ChatResponse & { signup_data?: any; signup_link_generated?: boolean }>> {
    const payload = {
      message,
      session_id: sessionId,
      contractor_lead_id: contractorLeadId,
      context: context,
    };

    return this.request<ChatResponse & { signup_data?: any; signup_link_generated?: boolean }>(
      "/api/coia/landing",
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  }

  // Process conversation with JAA (Job Assessment Agent)
  async processWithJAA(conversationId: string): Promise<ApiResponse<any>> {
    return this.request(`/api/jaa/process/${conversationId}`, {
      method: "POST",
    });
  }

  // Get conversation history
  async getConversation(conversationId: string): Promise<ApiResponse<any>> {
    return this.request(`/api/conversation/${conversationId}`);
  }

  // Get user's conversations
  async getUserConversations(userId: string): Promise<ApiResponse<any[]>> {
    return this.request(`/api/user/${userId}/conversations`);
  }

  // Create new conversation
  async createConversation(
    userId: string,
    projectType?: string
  ): Promise<ApiResponse<{ conversationId: string }>> {
    return this.request("/api/conversation", {
      method: "POST",
      body: JSON.stringify({
        userId,
        projectType,
      }),
    });
  }

  // Get project details from bid card
  async getProjectDetails(projectId: string): Promise<ApiResponse<any>> {
    return this.request(`/api/project/${projectId}`);
  }

  // Contractor endpoints
  async getAvailableProjects(
    contractorId: string,
    filters?: {
      type?: string;
      location?: string;
      budgetMin?: number;
      budgetMax?: number;
      urgency?: string;
    }
  ): Promise<ApiResponse<any[]>> {
    const queryParams = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
          queryParams.append(key, value.toString());
        }
      });
    }

    const endpoint = `/api/contractor/${contractorId}/projects${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
    return this.request(endpoint);
  }

  // Submit bid for a project
  async submitBid(
    projectId: string,
    contractorId: string,
    bidData: {
      amount: number;
      timeline: string;
      description: string;
      materials?: string;
    }
  ): Promise<ApiResponse<any>> {
    return this.request(`/api/project/${projectId}/bid`, {
      method: "POST",
      body: JSON.stringify({
        contractorId,
        ...bidData,
      }),
    });
  }

  // Get contractor stats and dashboard data
  async getContractorDashboard(contractorId: string): Promise<
    ApiResponse<{
      stats: any;
      recentProjects: any[];
      activeBids: any[];
    }>
  > {
    return this.request(`/api/contractor/${contractorId}/dashboard`);
  }

  // File upload helper for images
  async uploadImages(files: File[]): Promise<ApiResponse<string[]>> {
    try {
      const formData = new FormData();
      files.forEach((file, index) => {
        formData.append(`image_${index}`, file);
      });

      const response = await fetch(`${API_BASE_URL}/api/upload/images`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data: data.urls || [],
      };
    } catch (error) {
      console.error("[API] Upload error:", error);
      return {
        success: false,
        error: error instanceof Error ? error.message : "Upload failed",
      };
    }
  }

  // Test connection to backend
  async testConnection(): Promise<boolean> {
    try {
      const result = await this.healthCheck();
      return result.success;
    } catch (error) {
      console.error("[API] Connection test failed:", error);
      return false;
    }
  }
}

// Helper function for single file upload
export async function uploadFile(file: File): Promise<{ url: string; name: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/upload/file`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.status}`);
  }

  const data = await response.json();
  return {
    url: data.url,
    name: file.name,
  };
}

// Export singleton instance
export const apiService = new ApiService();
export default apiService;
