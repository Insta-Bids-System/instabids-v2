import type React from "react";
import { useRef, useState } from "react";
import { useBidCard } from "../../contexts/BidCardContext";

interface MessageInputProps {
  conversationId: string;
  bidCardId: string;
  senderId: string;
  senderType: "homeowner" | "contractor";
  onMessageSent?: () => void;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  conversationId,
  bidCardId,
  senderId,
  senderType,
  onMessageSent,
}) => {
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [attachments, setAttachments] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { sendMessage } = useBidCard();

  const handleSend = async () => {
    if (!message.trim() && attachments.length === 0) return;

    try {
      setSending(true);

      await sendMessage({
        conversationId,
        bidCardId,
        senderId,
        senderType,
        content: message.trim(),
        attachments: attachments.map((file) => ({
          file,
          fileName: file.name,
          fileType: file.type,
          fileSize: file.size,
        })),
      });

      // Clear form
      setMessage("");
      setAttachments([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      onMessageSent?.();
    } catch (error) {
      console.error("Error sending message:", error);
      alert("Failed to send message. Please try again.");
    } finally {
      setSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const maxSize = 5 * 1024 * 1024; // 5MB

    const validFiles = files.filter((file) => {
      if (file.size > maxSize) {
        alert(`${file.name} is too large. Maximum file size is 5MB.`);
        return false;
      }
      return true;
    });

    setAttachments((prev) => [...prev, ...validFiles]);
  };

  const removeAttachment = (index: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="border-t bg-white p-4">
      {attachments.length > 0 && (
        <div className="mb-2 space-y-1">
          {attachments.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between bg-gray-100 rounded px-3 py-1"
            >
              <span className="text-sm text-gray-700 truncate flex-1">
                📎 {file.name} ({(file.size / 1024).toFixed(1)}KB)
              </span>
              <button
                type="button"
                onClick={() => removeAttachment(index)}
                className="ml-2 text-red-500 hover:text-red-700"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-end space-x-2">
        <div className="flex-1">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="w-full px-3 py-2 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={1}
            style={{ minHeight: "40px", maxHeight: "120px" }}
            disabled={sending}
          />
        </div>

        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          multiple
          accept="image/*,.pdf,.doc,.docx"
          className="hidden"
        />

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
          disabled={sending}
          title="Attach files"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
            />
          </svg>
        </button>

        <button
          type="button"
          onClick={handleSend}
          disabled={sending || (!message.trim() && attachments.length === 0)}
          className={`
            px-4 py-2 rounded-lg font-medium transition-colors
            ${
              sending || (!message.trim() && attachments.length === 0)
                ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                : "bg-blue-500 text-white hover:bg-blue-600"
            }
          `}
        >
          {sending ? (
            <div className="flex items-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Sending...
            </div>
          ) : (
            "Send"
          )}
        </button>
      </div>

      <div className="mt-2 text-xs text-gray-500">
        <p>
          ⚠️ Do not share personal contact information. Messages are filtered for your protection.
        </p>
      </div>
    </div>
  );
};
