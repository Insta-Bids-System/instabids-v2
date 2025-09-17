import { useState, useEffect, useCallback } from 'react';

interface BidCardData {
  id: string;
  status: string;
  completion_percentage: number;
  fields_collected: Record<string, any>;
  missing_fields: string[];
  ready_for_conversion: boolean;
  created_at: string;
  updated_at: string;
  conversation_id: string;
  bid_card_preview: {
    title: string;
    project_type: string;
    description: string;
    location: string;
    timeline: string;
    contractor_preference: string;
    special_notes: string[];
    uploaded_photos: string[];
  };
}

interface UseBidCardUpdatesProps {
  conversationId: string;
  enabled: boolean;
  pollInterval?: number; // milliseconds
}

export const useBidCardUpdates = ({ 
  conversationId, 
  enabled, 
  pollInterval = 3000 
}: UseBidCardUpdatesProps) => {
  const [bidCardData, setBidCardData] = useState<BidCardData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBidCard = useCallback(async () => {
    if (!enabled || !conversationId) return;

    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/cia/conversation/${conversationId}/potential-bid-card`);
      
      if (response.ok) {
        const data = await response.json();
        setBidCardData(data);
      } else if (response.status === 404) {
        // No bid card yet - this is normal for new conversations
        setBidCardData(null);
      } else {
        const errorText = await response.text();
        setError(`Failed to fetch bid card: ${errorText}`);
      }
    } catch (err) {
      setError(`Error fetching bid card: ${err}`);
      console.error('Bid card fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [conversationId, enabled]);

  // Initial fetch
  useEffect(() => {
    if (enabled) {
      fetchBidCard();
    }
  }, [fetchBidCard, enabled]);

  // Polling
  useEffect(() => {
    if (!enabled || !conversationId) return;

    const interval = setInterval(fetchBidCard, pollInterval);
    
    return () => clearInterval(interval);
  }, [fetchBidCard, enabled, conversationId, pollInterval]);

  // Manual refresh function
  const refresh = useCallback(() => {
    fetchBidCard();
  }, [fetchBidCard]);

  return {
    bidCardData,
    loading,
    error,
    refresh
  };
};