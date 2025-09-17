import type React from "react";
import { useState } from "react";
import { ConversationList } from "./ConversationList";
import { MessageInput } from "./MessageInput";
import { MessageThread } from "./MessageThread";

interface MessagingInterfaceProps {
  userId: string;
  userType: "homeowner" | "contractor";
  bidCardId?: string; // Optional: pre-select a specific bid card conversation
}

export const MessagingInterface: React.FC<MessagingInterfaceProps> = ({
  userId,
  userType,
  bidCardId,
}) => {
  const [selectedConversation, setSelectedConversation] = useState<any>(null);
  const [isMobileConversationOpen, setIsMobileConversationOpen] = useState(false);

  const handleConversationSelect = (conversation: any) => {
    setSelectedConversation(conversation);
    setIsMobileConversationOpen(true);
  };

  const handleBackToList = () => {
    setIsMobileConversationOpen(false);
  };

  return (
    <div className="flex h-full bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Desktop Layout */}
      <div className="hidden md:flex w-full">
        {/* Conversation List */}
        <div className="w-1/3 border-r">
          <div className="p-4 border-b bg-gray-50">
            <h2 className="text-lg font-semibold">Messages</h2>
          </div>
          <ConversationList
            userId={userId}
            userType={userType}
            onConversationSelect={handleConversationSelect}
            selectedConversationId={selectedConversation?.id}
          />
        </div>

        {/* Message Thread */}
        <div className="flex-1 flex flex-col">
          {selectedConversation ? (
            <>
              {/* Conversation Header */}
              <div className="p-4 border-b bg-gray-50">
                <h3 className="text-lg font-semibold">
                  {userType === "homeowner"
                    ? selectedConversation.contractor_alias
                    : selectedConversation.bid_card?.title || "Conversation"}
                </h3>
                <p className="text-sm text-gray-600">
                  Bid Card: {selectedConversation.bid_card?.title || "Unknown"}
                </p>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-hidden">
                <MessageThread
                  conversationId={selectedConversation.id}
                  currentUserId={userId}
                  currentUserType={userType}
                  contractorAlias={selectedConversation.contractor_alias}
                />
              </div>

              {/* Message Input */}
              <MessageInput
                conversationId={selectedConversation.id}
                bidCardId={selectedConversation.bid_card_id}
                senderId={userId}
                senderType={userType}
              />
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <svg
                  className="w-24 h-24 mx-auto mb-4 text-gray-300"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                </svg>
                <p className="text-lg">Select a conversation to start messaging</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Layout */}
      <div className="md:hidden w-full h-full">
        {!isMobileConversationOpen ? (
          <div className="h-full">
            <div className="p-4 border-b bg-gray-50">
              <h2 className="text-lg font-semibold">Messages</h2>
            </div>
            <ConversationList
              userId={userId}
              userType={userType}
              onConversationSelect={handleConversationSelect}
              selectedConversationId={selectedConversation?.id}
            />
          </div>
        ) : (
          <div className="h-full flex flex-col">
            {/* Mobile Conversation Header with Back Button */}
            <div className="p-4 border-b bg-gray-50 flex items-center">
              <button
                type="button"
                onClick={handleBackToList}
                className="mr-3 p-1 hover:bg-gray-200 rounded"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 19l-7-7 7-7"
                  />
                </svg>
              </button>
              <div>
                <h3 className="text-lg font-semibold">
                  {userType === "homeowner"
                    ? selectedConversation?.contractor_alias
                    : selectedConversation?.bid_card?.title || "Conversation"}
                </h3>
                <p className="text-xs text-gray-600">
                  {selectedConversation?.bid_card?.title || "Unknown Bid Card"}
                </p>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-hidden">
              <MessageThread
                conversationId={selectedConversation?.id}
                currentUserId={userId}
                currentUserType={userType}
                contractorAlias={selectedConversation?.contractor_alias}
              />
            </div>

            {/* Message Input */}
            <MessageInput
              conversationId={selectedConversation?.id}
              bidCardId={selectedConversation?.bid_card_id}
              senderId={userId}
              senderType={userType}
            />
          </div>
        )}
      </div>
    </div>
  );
};
