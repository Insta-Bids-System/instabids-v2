import type React from "react";
import { createContext, useCallback, useContext, useState } from "react";
import apiService from "../services/api";
import type {
  BidCard,
  BidCardFilters,
  BidCardMessage,
  BidSubmissionRequest,
  ContractorBid,
  ContractorBidCardView,
  HomeownerBidCardView,
  MarketplaceBidCardView,
  MessageSendRequest,
} from "../types/bidCard";
import { useAuth } from "./AuthContext";

interface BidCardContextType {
  // Bid card management
  activeBidCard: BidCard | null;
  bidCards: BidCard[];
  isLoading: boolean;
  error: string | null;

  // Homeowner functions
  createBidCard: (bidCard: Partial<BidCard>) => Promise<BidCard>;
  updateBidCard: (id: string, updates: Partial<BidCard>) => Promise<BidCard>;
  deleteBidCard: (id: string) => Promise<void>;
  publishBidCard: (id: string) => Promise<void>;
  getHomeownerBidCards: () => Promise<HomeownerBidCardView[]>;

  // Contractor functions
  searchBidCards: (
    filters: BidCardFilters
  ) => Promise<{
    bid_cards: MarketplaceBidCardView[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
  }>;
  getBidCardDetails: (id: string) => Promise<ContractorBidCardView>;
  submitBid: (bid: BidSubmissionRequest) => Promise<ContractorBid>;
  updateBid: (bidId: string, updates: Partial<ContractorBid>) => Promise<ContractorBid>;
  withdrawBid: (bidId: string) => Promise<void>;

  // Messaging functions
  sendMessage: (message: MessageSendRequest) => Promise<BidCardMessage>;
  getMessages: (bidCardId: string, bidId?: string) => Promise<BidCardMessage[]>;
  markMessageAsRead: (messageId: string) => Promise<void>;
  getUnreadCount: (bidCardId: string) => Promise<number>;

  // Real-time updates
  subscribeToUpdates: (bidCardId: string) => () => void;
  subscribeToMessages: (bidCardId: string) => () => void;
}

const BidCardContext = createContext<BidCardContextType | undefined>(undefined);

export const useBidCard = () => {
  const context = useContext(BidCardContext);
  if (!context) {
    throw new Error("useBidCard must be used within a BidCardProvider");
  }
  return context;
};

export const BidCardProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, profile } = useAuth();
  const [activeBidCard, setActiveBidCard] = useState<BidCard | null>(null);
  const [bidCards, setBidCards] = useState<BidCard[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Homeowner functions
  const createBidCard = useCallback(
    async (bidCard: Partial<BidCard>): Promise<BidCard> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await apiService.post("/api/bid-cards", {
          ...bidCard,
          user_id: user?.id,
        });
        const newBidCard = response.data;
        setBidCards((prev) => [...prev, newBidCard]);
        return newBidCard;
      } catch (err: unknown) {
        setError(err.message || "Failed to create bid card");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [user]
  );

  const updateBidCard = useCallback(
    async (id: string, updates: Partial<BidCard>): Promise<BidCard> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await apiService.put(`/api/bid-cards/${id}`, updates);
        const updatedBidCard = response.data;
        setBidCards((prev) => prev.map((card) => (card.id === id ? updatedBidCard : card)));
        if (activeBidCard?.id === id) {
          setActiveBidCard(updatedBidCard);
        }
        return updatedBidCard;
      } catch (err: unknown) {
        setError(err.message || "Failed to update bid card");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [activeBidCard]
  );

  const deleteBidCard = useCallback(
    async (id: string): Promise<void> => {
      setIsLoading(true);
      setError(null);
      try {
        await apiService.delete(`/api/bid-cards/${id}`);
        setBidCards((prev) => prev.filter((card) => card.id !== id));
        if (activeBidCard?.id === id) {
          setActiveBidCard(null);
        }
      } catch (err: unknown) {
        setError(err.message || "Failed to delete bid card");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [activeBidCard]
  );

  const publishBidCard = useCallback(
    async (id: string): Promise<void> => {
      await updateBidCard(id, {
        status: "active",
        published_at: new Date().toISOString(),
      });
    },
    [updateBidCard]
  );

  const getHomeownerBidCards = useCallback(async (): Promise<HomeownerBidCardView[]> => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.get("/api/bid-cards/homeowner");
      return response.data;
    } catch (err: unknown) {
      setError(err.message || "Failed to fetch bid cards");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Contractor functions
  const searchBidCards = useCallback(async (filters: BidCardFilters) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.get("/api/bid-cards/search", { params: filters });
      return response.data;
    } catch (err: unknown) {
      setError(err.message || "Failed to search bid cards");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getBidCardDetails = useCallback(async (id: string): Promise<ContractorBidCardView> => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.get(`/api/bid-cards/${id}/contractor-view`);
      return response.data;
    } catch (err: unknown) {
      setError(err.message || "Failed to fetch bid card details");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const submitBid = useCallback(
    async (bid: BidSubmissionRequest): Promise<ContractorBid> => {
      setIsLoading(true);
      setError(null);
      try {
        // Check if we have attachments to handle file upload
        if (bid.attachments && bid.attachments.length > 0) {
          // Use multipart form data endpoint for file uploads
          const formData = new FormData();

          // Prepare bid data without attachments for JSON string
          const bidDataWithoutFiles = {
            ...bid,
            contractor_id: user?.id || "22222222-2222-2222-2222-222222222222",
            attachments: undefined, // Remove attachments from JSON
          };

          // Convert to JSON string
          formData.append("bid_data", JSON.stringify(bidDataWithoutFiles));

          // Add files to form data
          for (const attachment of bid.attachments) {
            if (attachment.file) {
              formData.append("files", attachment.file);
            }
          }

          const response = await apiService.post("/api/bid-cards/submit-bid-with-files", formData, {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          });

          return {
            id: response.data.proposal_id,
            bid_card_id: bid.bid_card_id,
            contractor_id: user?.id || "22222222-2222-2222-2222-222222222222",
            amount: bid.amount,
            timeline: {
              start_date: bid.timeline.start_date,
              end_date: bid.timeline.end_date,
              milestones: bid.milestones,
            },
            proposal: bid.proposal,
            approach: bid.approach,
            materials_included: bid.materials_included,
            warranty_details: bid.warranty_details,
            status: "submitted",
            allows_messages: true,
            submitted_at: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          } as ContractorBid;
        } else {
          // Use regular JSON endpoint for bids without files - FIXED ENDPOINT
          const response = await apiService.post("/api/contractor-proposals/submit", {
            bid_card_id: bid.bid_card_id,
            contractor_id: user?.id || "22222222-2222-2222-2222-222222222222",
            contractor_name: user?.name || user?.full_name || "Contractor",
            contractor_company: user?.full_name || null,  // Use full_name as company name
            bid_amount: bid.amount,
            timeline_days: Math.ceil((new Date(bid.timeline.end_date).getTime() - new Date(bid.timeline.start_date).getTime()) / (1000 * 60 * 60 * 24)),
            proposal_text: bid.proposal,
            attachments: []
          });

          return {
            id: response.data.proposal_id,
            bid_card_id: bid.bid_card_id,
            contractor_id: user?.id || "22222222-2222-2222-2222-222222222222",
            amount: bid.amount,
            timeline: {
              start_date: bid.timeline.start_date,
              end_date: bid.timeline.end_date,
              milestones: bid.milestones,
            },
            proposal: bid.proposal,
            approach: bid.approach,
            materials_included: bid.materials_included,
            warranty_details: bid.warranty_details,
            status: "submitted",
            allows_messages: true,
            submitted_at: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          } as ContractorBid;
        }
      } catch (err: any) {
        const errorMessage = err.response?.data?.detail || err.message || "Failed to submit bid";
        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setIsLoading(false);
      }
    },
    [user]
  );

  const updateBid = useCallback(
    async (bidId: string, updates: Partial<ContractorBid>): Promise<ContractorBid> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await apiService.put(`/api/contractor-bids/${bidId}`, updates);
        return response.data;
      } catch (err: unknown) {
        setError(err.message || "Failed to update bid");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const withdrawBid = useCallback(
    async (bidId: string): Promise<void> => {
      await updateBid(bidId, { status: "withdrawn" });
    },
    [updateBid]
  );

  // Messaging functions
  const sendMessage = useCallback(
    async (message: MessageSendRequest): Promise<BidCardMessage> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await apiService.post(
          "/api/messages/send",
          {
            bid_card_id: message.bidCardId,
            content: message.content,
            sender_type: profile?.role || "homeowner",
            sender_id: user?.id,
            conversation_id: message.conversationId,
          },
          {
            params: {
              user_type: profile?.role || "homeowner",
              user_id: user?.id,
            },
          }
        );

        // Handle filtered response
        if (response.data.success) {
          return {
            id: response.data.message_id || Date.now().toString(),
            bid_card_id: message.bidCardId,
            conversation_id: message.conversationId,
            sender_id: user?.id || "",
            sender_type: profile?.role || "homeowner",
            content: response.data.filtered_content, // Use filtered content!
            original_content: message.content,
            content_filtered: response.data.content_filtered,
            filter_reasons: response.data.filter_reasons,
            created_at: new Date().toISOString(),
            read_at: null,
            attachments: message.attachments,
          } as BidCardMessage;
        }
        throw new Error(response.data.error || "Failed to send message");
      } catch (err: unknown) {
        setError(err.message || "Failed to send message");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [user, profile?.role]
  );

  const getMessages = useCallback(
    async (bidCardId: string, conversationId?: string): Promise<BidCardMessage[]> => {
      setIsLoading(true);
      setError(null);
      try {
        if (!conversationId) {
          // If no conversation ID, get all conversations for bid card
          const response = await apiService.get("/api/messages/conversations", {
            params: {
              user_type: profile?.role || "homeowner",
              user_id: user?.id,
              bid_card_id: bidCardId,
            },
          });
          // Get messages from first conversation if exists
          if (response.data.conversations && response.data.conversations.length > 0) {
            conversationId = response.data.conversations[0].id;
          } else {
            return [];
          }
        }

        const response = await apiService.get(`/api/messages/conversation/${conversationId}`, {
          params: {
            user_type: profile?.role || "homeowner",
            user_id: user?.id,
          },
        });
        return response.data.messages || [];
      } catch (err: unknown) {
        setError(err.message || "Failed to fetch messages");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [user, profile?.role]
  );

  const markMessageAsRead = useCallback(
    async (messageId: string): Promise<void> => {
      try {
        await apiService.put(`/api/messages/${messageId}/read`, null, {
          params: {
            user_type: profile?.role || "homeowner",
            user_id: user?.id,
          },
        });
      } catch (err: unknown) {
        console.error("Failed to mark message as read:", err);
      }
    },
    [profile?.role, user?.id]
  );

  const getUnreadCount = useCallback(async (bidCardId: string): Promise<number> => {
    try {
      const response = await apiService.get(`/api/bid-cards/${bidCardId}/unread-count`);
      return response.data.count;
    } catch (err: unknown) {
      console.error("Failed to get unread count:", err);
      return 0;
    }
  }, []);

  // Real-time subscriptions (WebSocket implementation)
  const subscribeToUpdates = useCallback((bidCardId: string) => {
    // TODO: Implement WebSocket subscription for bid card updates
    console.log("Subscribing to updates for bid card:", bidCardId);
    return () => {
      console.log("Unsubscribing from updates for bid card:", bidCardId);
    };
  }, []);

  const subscribeToMessages = useCallback((bidCardId: string) => {
    // TODO: Implement WebSocket subscription for messages
    console.log("Subscribing to messages for bid card:", bidCardId);
    return () => {
      console.log("Unsubscribing from messages for bid card:", bidCardId);
    };
  }, []);

  const value: BidCardContextType = {
    activeBidCard,
    bidCards,
    isLoading,
    error,
    createBidCard,
    updateBidCard,
    deleteBidCard,
    publishBidCard,
    getHomeownerBidCards,
    searchBidCards,
    getBidCardDetails,
    submitBid,
    updateBid,
    withdrawBid,
    sendMessage,
    getMessages,
    markMessageAsRead,
    getUnreadCount,
    subscribeToUpdates,
    subscribeToMessages,
  };

  return <BidCardContext.Provider value={value}>{children}</BidCardContext.Provider>;
};
