import { format } from "date-fns";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import { useSupabase } from "../../contexts/SupabaseContext";

interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  sender_type: "homeowner" | "contractor";
  content: string;
  filtered_content?: string;
  is_filtered: boolean;
  created_at: string;
  read_at?: string;
  attachments?: Array<{
    id: string;
    file_url: string;
    file_name: string;
    file_type: string;
    file_size: number;
  }>;
}

interface MessageThreadProps {
  conversationId: string;
  currentUserId: string;
  currentUserType: "homeowner" | "contractor";
  contractorAlias?: string;
}

export const MessageThread: React.FC<MessageThreadProps> = ({
  conversationId,
  currentUserId,
  currentUserType,
  contractorAlias,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { supabase } = useSupabase();

  useEffect(() => {
    fetchMessages();
    markMessagesAsRead();

    // Subscribe to new messages
    const subscription = supabase
      .channel(`messages:${conversationId}`)
      .on(
        "postgres_changes",
        {
          event: "INSERT",
          schema: "public",
          table: "messages",
          filter: `conversation_id=eq.${conversationId}`,
        },
        (payload) => {
          const newMessage = payload.new as Message;
          setMessages((prev) => [...prev, newMessage]);

          // Mark as read if it's from the other party
          if (newMessage.sender_id !== currentUserId) {
            markMessageAsRead(newMessage.id);
          }
        }
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [
    conversationId,
    currentUserId,
    fetchMessages,
    markMessageAsRead,
    markMessagesAsRead,
    supabase.channel,
  ]);

  useEffect(() => {
    scrollToBottom();
  }, [scrollToBottom]);

  const fetchMessages = async () => {
    try {
      setLoading(true);

      const { data, error } = await supabase
        .from("messages")
        .select(`
          *,
          attachments:message_attachments(*)
        `)
        .eq("conversation_id", conversationId)
        .order("created_at", { ascending: true });

      if (error) throw error;
      setMessages(data || []);
    } catch (error) {
      console.error("Error fetching messages:", error);
    } finally {
      setLoading(false);
    }
  };

  const markMessagesAsRead = async () => {
    try {
      const { error } = await supabase
        .from("messages")
        .update({ read_at: new Date().toISOString() })
        .eq("conversation_id", conversationId)
        .neq("sender_id", currentUserId)
        .is("read_at", null);

      if (error) throw error;
    } catch (error) {
      console.error("Error marking messages as read:", error);
    }
  };

  const markMessageAsRead = async (messageId: string) => {
    try {
      const { error } = await supabase
        .from("messages")
        .update({ read_at: new Date().toISOString() })
        .eq("id", messageId);

      if (error) throw error;
    } catch (error) {
      console.error("Error marking message as read:", error);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const renderMessage = (message: Message) => {
    const isCurrentUser = message.sender_id === currentUserId;
    const displayContent = message.filtered_content || message.content;

    return (
      <div
        key={message.id}
        className={`flex ${isCurrentUser ? "justify-end" : "justify-start"} mb-4`}
      >
        <div
          className={`
            max-w-xs lg:max-w-md px-4 py-2 rounded-lg
            ${isCurrentUser ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-800"}
          `}
        >
          {!isCurrentUser && contractorAlias && (
            <div className="text-xs font-semibold mb-1 opacity-75">{contractorAlias}</div>
          )}

          <div className="break-words">{displayContent}</div>

          {message.is_filtered && (
            <div className="text-xs mt-1 opacity-75">
              <span className="italic">Contact information removed for your protection</span>
            </div>
          )}

          {message.attachments && message.attachments.length > 0 && (
            <div className="mt-2 space-y-1">
              {message.attachments.map((attachment) => (
                <a
                  key={attachment.id}
                  href={attachment.file_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`
                    block text-xs underline
                    ${isCurrentUser ? "text-blue-100" : "text-blue-600"}
                  `}
                >
                  📎 {attachment.file_name} ({(attachment.file_size / 1024).toFixed(1)}KB)
                </a>
              ))}
            </div>
          )}

          <div
            className={`
            text-xs mt-1
            ${isCurrentUser ? "text-blue-100" : "text-gray-500"}
          `}
          >
            {format(new Date(message.created_at), "h:mm a")}
            {message.read_at && " • Read"}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">
            <p>No messages yet. Start the conversation!</p>
          </div>
        ) : (
          <>
            {messages.map(renderMessage)}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
    </div>
  );
};
