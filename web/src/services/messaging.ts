/**
 * Messaging Service for Contractor-Homeowner Communication
 * Integrates with the existing messaging API for bid card conversations
 */

import apiService from "./api";

export interface Message {
  id: string;
  conversation_id: string;
  sender_type: "homeowner" | "contractor";
  sender_id: string;
  filtered_content: string;
  content_filtered: boolean;
  filter_reasons: Array<{
    category: string;
    matched_text: string;
  }>;
  message_type: string;
  is_read: boolean;
  created_at: string;
}

export interface Conversation {
  id: string;
  bid_card_id: string;
  user_id: string;
  contractor_id: string;
  contractor_alias: string;
  status: string;
  last_message_at?: string;
  homeowner_unread_count: number;
  contractor_unread_count: number;
  created_at: string;
  updated_at: string;
}

export interface SendMessageRequest {
  content: string;
  sender_type: "homeowner" | "contractor";
  sender_id: string;
  bid_card_id: string;
  conversation_id?: string;
  message_type?: string;
  metadata?: Record<string, any>;
}

export interface SendMessageResponse {
  success: boolean;
  message_id: string;
  conversation_id: string;
  filtered_content: string;
  content_filtered: boolean;
  filter_reasons: Array<{
    category: string;
    matched_text: string;
  }>;
  error?: string;
}

/**
 * Check if a conversation already exists for a bid card
 */
export async function checkExistingConversation(
  bid_card_id: string,
  contractor_id: string
): Promise<Conversation | null> {
  try {
    const response = await apiService.get("/api/messages/conversations", {
      params: {
        user_type: "contractor",
        user_id: contractor_id,
        bid_card_id: bid_card_id,
      },
    });

    if (response.data.conversations && response.data.conversations.length > 0) {
      return response.data.conversations[0];
    }
    return null;
  } catch (error) {
    console.error("Error checking existing conversation:", error);
    return null;
  }
}

/**
 * Send a message in a bid card conversation
 */
export async function sendBidCardMessage(
  bid_card_id: string,
  contractor_id: string,
  content: string,
  conversation_id?: string
): Promise<SendMessageResponse> {
  try {
    const response = await apiService.post("/api/messages/send", {
      bid_card_id,
      content,
      sender_type: "contractor",
      sender_id: contractor_id,
      conversation_id,
      message_type: "text",
    });

    return {
      success: true,
      message_id: response.data.id,
      conversation_id: response.data.conversation_id,
      filtered_content: response.data.filtered_content,
      content_filtered: response.data.content_filtered,
      filter_reasons: response.data.filter_reasons || [],
    };
  } catch (error: unknown) {
    console.error("Error sending message:", error);
    return {
      success: false,
      message_id: "",
      conversation_id: "",
      filtered_content: "",
      content_filtered: false,
      filter_reasons: [],
      error: error.message || "Failed to send message",
    };
  }
}

/**
 * Get messages for a conversation
 */
export async function getConversationMessages(
  conversation_id: string,
  _user_type: "homeowner" | "contractor",
  _user_id: string
): Promise<Message[]> {
  try {
    const response = await apiService.get(`/api/messages/conversation/${conversation_id}/messages`);

    return response.data || [];
  } catch (error) {
    console.error("Error loading messages:", error);
    return [];
  }
}

/**
 * Get all conversations for a user
 */
export async function getUserConversations(
  user_type: "homeowner" | "contractor",
  user_id: string,
  bid_card_id?: string
): Promise<Conversation[]> {
  try {
    let endpoint = "/api/messages/conversations";
    if (bid_card_id) {
      endpoint = `/api/messages/conversations/${bid_card_id}`;
    }

    const response = await apiService.get(endpoint, {
      params: {
        user_type,
        user_id,
      },
    });

    return response.data || [];
  } catch (error) {
    console.error("Error loading conversations:", error);
    return [];
  }
}

/**
 * Mark messages as read
 */
export async function markMessagesRead(
  message_ids: string[],
  reader_type: "homeowner" | "contractor"
): Promise<boolean> {
  try {
    await apiService.post("/api/messages/mark-read", {
      message_ids,
      reader_type,
    });
    return true;
  } catch (error) {
    console.error("Error marking messages as read:", error);
    return false;
  }
}

/**
 * Get unread message count for a user
 */
export async function getUnreadCount(
  user_type: "homeowner" | "contractor",
  user_id: string,
  bid_card_id?: string
): Promise<{ total_unread: number; conversations_with_unread: number }> {
  try {
    const response = await apiService.get("/api/messages/unread-count", {
      params: {
        user_type,
        user_id,
        bid_card_id,
      },
    });

    return {
      total_unread: response.data.total_unread || 0,
      conversations_with_unread: response.data.conversations_with_unread || 0,
    };
  } catch (error) {
    console.error("Error getting unread count:", error);
    return { total_unread: 0, conversations_with_unread: 0 };
  }
}

/**
 * Start a conversation about a bid card (main function for contractors)
 */
export async function startBidCardConversation(
  bid_card_id: string,
  contractor_id: string,
  _user_id: string,
  initialMessage?: string
): Promise<{
  success: boolean;
  conversation_id?: string;
  error?: string;
}> {
  try {
    // Check if conversation already exists
    const existingConversation = await checkExistingConversation(bid_card_id, contractor_id);

    if (existingConversation) {
      return {
        success: true,
        conversation_id: existingConversation.id,
      };
    }

    // Create new conversation by sending initial message
    const defaultMessage =
      initialMessage ||
      "Hi! I'm interested in your project and have some questions about the requirements.";
    const result = await sendBidCardMessage(bid_card_id, contractor_id, defaultMessage);

    if (result.success) {
      return {
        success: true,
        conversation_id: result.conversation_id,
      };
    } else {
      return {
        success: false,
        error: result.error || "Failed to start conversation",
      };
    }
  } catch (error: unknown) {
    console.error("Error starting conversation:", error);
    return {
      success: false,
      error: error.message || "Failed to start conversation",
    };
  }
}

/**
 * Check if messaging is available for a bid card
 */
export async function isMessagingAvailable(
  _bid_card_id: string,
  _contractor_id: string
): Promise<boolean> {
  try {
    // For now, assume messaging is always available
    // In the future, this could check bid card status, contractor permissions, etc.
    return true;
  } catch (error) {
    console.error("Error checking messaging availability:", error);
    return false;
  }
}

// Export default object with all functions for easy importing
export default {
  checkExistingConversation,
  sendBidCardMessage,
  getConversationMessages,
  getUserConversations,
  markMessagesRead,
  getUnreadCount,
  startBidCardConversation,
  isMessagingAvailable,
};
