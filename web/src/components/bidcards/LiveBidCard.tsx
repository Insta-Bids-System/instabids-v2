import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useAgentActivity, useFieldHighlight } from '../../hooks/useAgentActivity';
import { AgentActivityWrapper } from '../ui/AgentActivityIndicator';
import { supabase } from '../../utils/supabase';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { DollarSign, Calendar, MapPin, Wrench } from 'lucide-react';

interface BidCard {
  id: string;
  project_title: string;
  description: string;
  budget_min: number;
  budget_max: number;
  timeline_start: string;
  timeline_end: string;
  urgency_level: string;
  location: string;
  trade_type: string;
  status: string;
  items?: any[];
}

interface LiveBidCardProps {
  bidCardId: string;
  initialData?: BidCard;
}

/**
 * Bid Card component with real-time updates and agent activity visualization
 */
export function LiveBidCard({ bidCardId, initialData }: LiveBidCardProps) {
  const [bidCard, setBidCard] = useState<BidCard | null>(initialData || null);
  const [loading, setLoading] = useState(!initialData);
  
  // Hook for agent activity animations
  const { 
    isBeingModified, 
    currentAgent, 
    lastChange,
    highlightFields,
    containerClass 
  } = useAgentActivity('bid_card', bidCardId);
  
  // Field-level highlight hooks
  const budgetHighlight = useFieldHighlight('budget', bidCard?.budget_max);
  const urgencyHighlight = useFieldHighlight('urgency', bidCard?.urgency_level);
  const itemsHighlight = useFieldHighlight('items', bidCard?.items?.length);

  useEffect(() => {
    // Initial fetch if no data provided
    if (!initialData) {
      fetchBidCard();
    }

    // Subscribe to real-time updates
    const channel = supabase
      .channel(`bid-card-${bidCardId}`)
      .on('postgres_changes', {
        event: '*',
        schema: 'public',
        table: 'bid_cards',
        filter: `id=eq.${bidCardId}`
      }, (payload) => {
        console.log('Bid card updated:', payload);
        if (payload.eventType === 'UPDATE') {
          setBidCard(payload.new as BidCard);
        }
      })
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [bidCardId]);

  const fetchBidCard = async () => {
    try {
      const { data, error } = await supabase
        .from('bid_cards')
        .select('*')
        .eq('id', bidCardId)
        .single();
      
      if (error) throw error;
      setBidCard(data);
    } catch (error) {
      console.error('Error fetching bid card:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="shimmer-loading">
        <CardContent className="h-48" />
      </Card>
    );
  }

  if (!bidCard) {
    return <div>Bid card not found</div>;
  }

  return (
    <AgentActivityWrapper
      isBeingModified={isBeingModified}
      currentAgent={currentAgent}
      lastChange={lastChange}
      className={containerClass}
    >
      <Card className="overflow-hidden transition-all duration-300">
        <CardHeader>
          <div className="flex justify-between items-start">
            <CardTitle className="text-xl">
              {bidCard.project_title}
            </CardTitle>
            <Badge 
              variant={bidCard.status === 'active' ? 'default' : 'secondary'}
              className={highlightFields.has('status') ? 'animate-pulse' : ''}
            >
              {bidCard.status}
            </Badge>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Description */}
          <p className={`text-gray-600 ${highlightFields.has('description') ? 'field-highlight' : ''}`}>
            {bidCard.description}
          </p>
          
          {/* Budget Range */}
          <motion.div 
            className={`flex items-center gap-2 ${budgetHighlight.className}`}
            animate={highlightFields.has('budget') ? { scale: [1, 1.05, 1] } : {}}
          >
            <DollarSign className="w-4 h-4 text-gray-500" />
            <span className="font-semibold">
              ${bidCard.budget_min.toLocaleString()} - ${bidCard.budget_max.toLocaleString()}
            </span>
          </motion.div>
          
          {/* Timeline */}
          <div className={`flex items-center gap-2 ${highlightFields.has('timeline') ? 'field-highlight' : ''}`}>
            <Calendar className="w-4 h-4 text-gray-500" />
            <span>
              {new Date(bidCard.timeline_start).toLocaleDateString()} - 
              {new Date(bidCard.timeline_end).toLocaleDateString()}
            </span>
          </div>
          
          {/* Location */}
          <div className={`flex items-center gap-2 ${highlightFields.has('location') ? 'field-highlight' : ''}`}>
            <MapPin className="w-4 h-4 text-gray-500" />
            <span>{bidCard.location}</span>
          </div>
          
          {/* Trade Type */}
          <div className={`flex items-center gap-2 ${highlightFields.has('trade_type') ? 'field-highlight' : ''}`}>
            <Wrench className="w-4 h-4 text-gray-500" />
            <span>{bidCard.trade_type}</span>
          </div>
          
          {/* Urgency Level */}
          <motion.div
            animate={urgencyHighlight.isHighlighted ? { 
              backgroundColor: ['rgba(251, 191, 36, 0)', 'rgba(251, 191, 36, 0.1)', 'rgba(251, 191, 36, 0)']
            } : {}}
            transition={{ duration: 1 }}
          >
            <Badge 
              variant={bidCard.urgency_level === 'emergency' ? 'destructive' : 
                      bidCard.urgency_level === 'urgent' ? 'warning' : 'default'}
              className={urgencyHighlight.className}
            >
              {bidCard.urgency_level}
            </Badge>
          </motion.div>
          
          {/* Items Count */}
          {bidCard.items && bidCard.items.length > 0 && (
            <motion.div
              className={`text-sm text-gray-600 ${itemsHighlight.className}`}
              animate={itemsHighlight.isHighlighted ? { x: [0, 5, 0] } : {}}
            >
              {bidCard.items.length} repair items
            </motion.div>
          )}
          
          {/* Show when agent is adding something */}
          {isBeingModified && currentAgent === 'IRIS' && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="bg-purple-50 p-2 rounded text-sm text-purple-700"
            >
              IRIS is updating this bid card...
            </motion.div>
          )}
        </CardContent>
      </Card>
    </AgentActivityWrapper>
  );
}