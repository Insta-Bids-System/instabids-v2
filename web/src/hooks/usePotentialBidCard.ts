import { useState, useEffect, useCallback } from 'react';

interface PotentialBidCard {
  id: string;
  status: string;
  completion_percentage: number;
  fields_collected: {
    project_type?: string;
    service_type?: string;
    project_description?: string;
    zip_code?: string;
    email_address?: string;
    timeline?: string;
    contractor_size?: string;
    budget_context?: string;
    materials?: string[];
    special_requirements?: string[];
    quality_expectations?: string;
  };
  missing_fields: string[];
  ready_for_conversion: boolean;
  conversation_id?: string;
  session_id?: string;
  bid_card_preview: {
    title: string;
    project_type?: string;
    description?: string;
    location?: string;
    timeline?: string;
    contractor_preference?: string;
    special_notes?: string[];
  };
}

interface UsePotentialBidCardOptions {
  conversationId?: string;
  userId?: string;
  sessionId?: string;
  autoCreate?: boolean;
  pollInterval?: number;
}

export const usePotentialBidCard = ({
  conversationId,
  userId,
  sessionId,
  autoCreate = true,
  pollInterval = 3000
}: UsePotentialBidCardOptions = {}) => {
  const [bidCard, setBidCard] = useState<PotentialBidCard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create a new potential bid card
  const createPotentialBidCard = useCallback(async (title: string = "New Project") => {
    if (!conversationId || !sessionId) {
      setError('Conversation ID and Session ID required to create bid card');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/cia/potential-bid-cards', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          session_id: sessionId,
          user_id: userId,
          title
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to create potential bid card: ${response.statusText}`);
      }

      const newBidCard = await response.json();
      setBidCard(newBidCard);
      return newBidCard;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, [conversationId, sessionId, userId]);

  // Fetch potential bid card by conversation ID
  const fetchBidCard = useCallback(async () => {
    if (!conversationId) return;

    try {
      const response = await fetch(`/api/cia/conversation/${conversationId}/potential-bid-card`);
      
      if (response.ok) {
        const data = await response.json();
        setBidCard(data);
        setError(null);
      } else if (response.status === 404) {
        // No bid card exists yet
        if (autoCreate && sessionId) {
          await createPotentialBidCard();
        } else {
          setBidCard(null);
        }
      } else {
        throw new Error(`Failed to fetch bid card: ${response.statusText}`);
      }
    } catch (err) {
      console.log('Error fetching potential bid card:', err);
      // Don't set error for fetch failures - they're expected when no bid card exists
      if (err instanceof Error && !err.message.includes('fetch')) {
        setError(err.message);
      }
    }
  }, [conversationId, autoCreate, sessionId, createPotentialBidCard]);

  // Update a specific field
  const updateField = useCallback(async (fieldName: string, fieldValue: any, source: 'conversation' | 'manual' = 'manual') => {
    if (!bidCard) {
      setError('No bid card available to update');
      return false;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/cia/potential-bid-cards/${bidCard.id}/field`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          field_name: fieldName,
          field_value: fieldValue,
          source
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to update field: ${response.statusText}`);
      }

      const result = await response.json();
      
      // Refresh the bid card data
      await fetchBidCard();
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  }, [bidCard, fetchBidCard]);

  // Convert to official bid card
  const convertToOfficialBidCard = useCallback(async () => {
    if (!bidCard) {
      setError('No bid card available to convert');
      return null;
    }

    if (!bidCard.ready_for_conversion) {
      setError('Bid card is not ready for conversion. Please fill in all required fields.');
      return null;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/cia/potential-bid-cards/${bidCard.id}/convert-to-bid-card`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to convert bid card: ${response.statusText}`);
      }

      const result = await response.json();
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, [bidCard]);

  // Set up polling when conversation ID is available
  useEffect(() => {
    if (!conversationId) return;

    fetchBidCard();
    
    const interval = setInterval(fetchBidCard, pollInterval);
    return () => clearInterval(interval);
  }, [conversationId, fetchBidCard, pollInterval]);

  return {
    bidCard,
    loading,
    error,
    createPotentialBidCard,
    fetchBidCard,
    updateField,
    convertToOfficialBidCard,
    // Computed properties
    isComplete: bidCard?.ready_for_conversion || false,
    completionPercentage: bidCard?.completion_percentage || 0,
    missingFields: bidCard?.missing_fields || [],
    fieldsCollected: bidCard?.fields_collected || {}
  };
};

export default usePotentialBidCard;