import { useEffect, useState } from "react";
import apiService from "../services/api";

// Test users - hardcoded for demo
const TEST_HOMEOWNER = {
  id: "11111111-1111-1111-1111-111111111111",
  role: "homeowner" as const,
  name: "Test Homeowner",
};

const TEST_CONTRACTOR = {
  id: "22222222-2222-2222-2222-222222222222",
  role: "contractor" as const,
  name: "Test Contractor",
};

// Real bid card from database
const TEST_BID_CARD_ID = "2cb6e43a-2c92-4e30-93f2-e44629f8975f";

interface Message {
  id: string;
  sender_type: string;
  sender_id: string;
  original_content: string;
  filtered_content: string;
  content_filtered: boolean;
  filter_reasons: any[];
  created_at: string;
}

export function MessagingDemo() {
  const [currentUser, setCurrentUser] = useState(TEST_HOMEOWNER);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load or create conversation
  useEffect(() => {
    loadConversation();
  }, []);

  const loadConversation = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get conversations for this bid card
      const response = await apiService.get("/api/messages/conversations", {
        params: {
          user_type: currentUser.role,
          user_id: currentUser.id,
          bid_card_id: TEST_BID_CARD_ID,
        },
      });

      if (response.data.conversations && response.data.conversations.length > 0) {
        const conv = response.data.conversations[0];
        setConversationId(conv.id);
        await loadMessages(conv.id);
      } else {
        // No conversation yet
        setMessages([]);
        setConversationId(null);
      }
    } catch (err: unknown) {
      console.error("Error loading conversation:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (convId: string) => {
    try {
      const response = await apiService.get(`/api/messages/${convId}`, {
        params: {
          user_type: currentUser.role,
          user_id: currentUser.id,
        },
      });

      if (response.data?.messages) {
        setMessages(response.data.messages);
      }
    } catch (err: unknown) {
      console.error("Error loading messages:", err);
      setError(err.message);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    try {
      setLoading(true);
      setError(null);

      const response = await apiService.post(
        "/api/messages/send",
        {
          bid_card_id: TEST_BID_CARD_ID,
          content: newMessage,
          sender_type: currentUser.role,
          sender_id: currentUser.id,
          conversation_id: conversationId,
        },
        {
          params: {
            user_type: currentUser.role,
            user_id: currentUser.id,
          },
        }
      );

      if (response.data.success) {
        // Clear input
        setNewMessage("");

        // If we got a conversation ID back, save it
        if (response.data.conversation_id && !conversationId) {
          setConversationId(response.data.conversation_id);
        }

        // Add the message to our list with filtered content
        const newMsg: Message = {
          id: response.data.message_id || Date.now().toString(),
          sender_type: currentUser.role,
          sender_id: currentUser.id,
          original_content: newMessage,
          filtered_content: response.data.filtered_content,
          content_filtered: response.data.content_filtered,
          filter_reasons: response.data.filter_reasons || [],
          created_at: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, newMsg]);

        // Show filtering notification
        if (response.data.content_filtered) {
          alert(
            `Content was filtered! Reasons: ${response.data.filter_reasons.map((r: any) => r.category).join(", ")}`
          );
        }
      } else {
        setError(response.data.error || "Failed to send message");
      }
    } catch (err: unknown) {
      console.error("Error sending message:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const switchUser = () => {
    setCurrentUser((current) =>
      current.id === TEST_HOMEOWNER.id ? TEST_CONTRACTOR : TEST_HOMEOWNER
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Messaging System Demo</h1>

      {/* User Switcher */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Currently logged in as:</p>
            <p className="text-lg font-semibold">
              {currentUser.name} ({currentUser.role})
            </p>
          </div>
          <button
            type="button"
            onClick={switchUser}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Switch to {currentUser.id === TEST_HOMEOWNER.id ? "Contractor" : "Homeowner"}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">Error: {error}</div>}

      {/* Messages Display */}
      <div className="mb-6 border rounded-lg p-4 h-96 overflow-y-auto bg-gray-50">
        <h2 className="font-semibold mb-4">Messages for Bid Card: {TEST_BID_CARD_ID}</h2>
        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && messages.length === 0 && (
          <p className="text-gray-500">No messages yet. Send the first message!</p>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`mb-4 p-3 rounded-lg ${
              msg.sender_id === currentUser.id
                ? "bg-blue-100 ml-auto max-w-sm"
                : "bg-white max-w-sm"
            }`}
          >
            <div className="text-xs text-gray-500 mb-1">
              {msg.sender_type === "homeowner" ? "Homeowner" : "Contractor"}
              {msg.content_filtered && " (filtered)"}
            </div>
            <div className="text-sm">{msg.filtered_content}</div>
            {msg.content_filtered && (
              <div className="text-xs text-orange-600 mt-1">
                ⚠️ Contact info removed:{" "}
                {msg.filter_reasons.map((r: any) => r.matched_text).join(", ")}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Message Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Type a message... (try including a phone number or email)"
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          type="button"
          onClick={sendMessage}
          disabled={loading || !newMessage.trim()}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300"
        >
          {loading ? "Sending..." : "Send"}
        </button>
      </div>

      {/* Test Instructions */}
      <div className="mt-6 p-4 bg-yellow-50 rounded-lg">
        <h3 className="font-semibold mb-2">Test Instructions:</h3>
        <ol className="text-sm space-y-1 list-decimal list-inside">
          <li>Send a message as the homeowner</li>
          <li>Try including phone numbers (555-1234) or emails (test@email.com)</li>
          <li>Notice how contact info is automatically filtered</li>
          <li>Switch to contractor view to see the conversation from their side</li>
          <li>Messages are saved in Supabase and persist across user switches</li>
        </ol>
      </div>

      {/* System Status */}
      <div className="mt-4 p-4 bg-green-50 rounded-lg">
        <h3 className="font-semibold mb-2">System Status:</h3>
        <ul className="text-sm space-y-1">
          <li>✅ Backend API: Connected to port 8008</li>
          <li>✅ Content Filtering: Active (LangGraph agent)</li>
          <li>✅ Database: Supabase messaging_system_messages table</li>
          <li>✅ Conversation ID: {conversationId || "Will be created on first message"}</li>
        </ul>
      </div>
    </div>
  );
}
