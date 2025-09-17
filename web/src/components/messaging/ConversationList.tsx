import { format } from "date-fns";
import type React from "react";
import { useEffect, useState } from "react";
import { useSupabase } from "../../contexts/SupabaseContext";

interface Conversation {
  id: string;
  bid_card_id: string;
  contractor_id: string;
  contractor_alias: string;
  last_message?: string;
  last_message_at?: string;
  unread_count: number;
  bid_card?: {
    title: string;
    status: string;
  };
}

interface ConversationListProps {
  userId: string;
  userType: "homeowner" | "contractor";
  onConversationSelect: (conversation: Conversation) => void;
  selectedConversationId?: string;
}

export const ConversationList: React.FC<ConversationListProps> = ({
  userId,
  userType,
  onConversationSelect,
  selectedConversationId,
}) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const { supabase } = useSupabase();

  useEffect(() => {
    fetchConversations();

    // Subscribe to real-time updates
    const subscription = supabase
      .channel("conversations")
      .on(
        "postgres_changes",
        {
          event: "*",
          schema: "public",
          table: "conversations",
          filter:
            userType === "homeowner" ? `user_id=eq.${userId}` : `contractor_id=eq.${userId}`,
        },
        () => {
          fetchConversations();
        }
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [userId, userType, fetchConversations, supabase.channel]);

  const fetchConversations = async () => {
    try {
      setLoading(true);

      let query = supabase
        .from("conversations")
        .select(`
          *,
          bid_card:bid_cards(title, status)
        `)
        .order("last_message_at", { ascending: false, nullsFirst: false });

      if (userType === "homeowner") {
        query = query.eq("user_id", userId);
      } else {
        query = query.eq("contractor_id", userId);
      }

      const { data, error } = await query;

      if (error) throw error;
      setConversations(data || []);
    } catch (error) {
      console.error("Error fetching conversations:", error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (conversationId: string) => {
    try {
      const { error } = await supabase
        .from("conversations")
        .update({
          [`unread_${userType}_count`]: 0,
          updated_at: new Date().toISOString(),
        })
        .eq("id", conversationId);

      if (error) throw error;

      // Update local state
      setConversations((prev) =>
        prev.map((conv) => (conv.id === conversationId ? { ...conv, unread_count: 0 } : conv))
      );
    } catch (error) {
      console.error("Error marking conversation as read:", error);
    }
  };

  const handleConversationClick = (conversation: Conversation) => {
    onConversationSelect(conversation);
    if (conversation.unread_count > 0) {
      markAsRead(conversation.id);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        <p>No conversations yet</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      {conversations.map((conversation) => (
        <div
          key={conversation.id}
          onClick={() => handleConversationClick(conversation)}
          className={`
            p-4 border-b cursor-pointer hover:bg-gray-50 transition-colors
            ${selectedConversationId === conversation.id ? "bg-blue-50" : ""}
            ${conversation.unread_count > 0 ? "font-semibold" : ""}
          `}
        >
          <div className="flex justify-between items-start mb-1">
            <h3 className="text-sm font-medium text-gray-900">
              {userType === "homeowner"
                ? conversation.contractor_alias
                : conversation.bid_card?.title || "Bid Card"}
            </h3>
            {conversation.last_message_at && (
              <span className="text-xs text-gray-500">
                {format(new Date(conversation.last_message_at), "MMM d, h:mm a")}
              </span>
            )}
          </div>

          {conversation.last_message && (
            <p className="text-sm text-gray-600 truncate">{conversation.last_message}</p>
          )}

          <div className="flex justify-between items-center mt-2">
            <span
              className={`
              text-xs px-2 py-1 rounded-full
              ${
                conversation.bid_card?.status === "active"
                  ? "bg-green-100 text-green-800"
                  : "bg-gray-100 text-gray-800"
              }
            `}
            >
              {conversation.bid_card?.status || "unknown"}
            </span>

            {conversation.unread_count > 0 && (
              <span className="bg-blue-500 text-white text-xs rounded-full px-2 py-1">
                {conversation.unread_count}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
