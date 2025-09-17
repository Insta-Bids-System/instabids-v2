"""
My Bids Tracking Service
Tracks contractor interactions with bid cards and manages "My Bids" section
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from database_simple import get_client

logger = logging.getLogger(__name__)

class MyBidsTracker:
    """Tracks and manages contractor's bid card interactions"""
    
    def __init__(self):
        self.supabase = get_client()
    
    async def track_bid_interaction(
        self, 
        contractor_id: str, 
        bid_card_id: str, 
        interaction_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track when a contractor interacts with a bid card
        
        Args:
            contractor_id: The contractor's ID
            bid_card_id: The bid card they interacted with
            interaction_type: Type of interaction (message, quote, question, view)
            details: Additional details about the interaction
        
        Returns:
            True if successfully tracked
        """
        try:
            # Check if already tracked
            existing = self.supabase.table('contractor_my_bids').select('*').eq(
                'contractor_id', contractor_id
            ).eq('bid_card_id', bid_card_id).execute()
            
            if existing.data:
                # Update existing record
                update_data = {
                    'last_interaction': datetime.utcnow().isoformat(),
                    'interaction_count': existing.data[0].get('interaction_count', 0) + 1,
                    'last_interaction_type': interaction_type,
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                # Update interaction history
                history = existing.data[0].get('interaction_history', [])
                history.append({
                    'type': interaction_type,
                    'timestamp': datetime.utcnow().isoformat(),
                    'details': details
                })
                update_data['interaction_history'] = history[-10:]  # Keep last 10 interactions
                
                # Update status based on interaction type
                if interaction_type in ['quote_submitted', 'proposal_submitted']:
                    update_data['status'] = 'quoted'
                elif interaction_type == 'message_sent':
                    update_data['status'] = 'engaged'
                
                self.supabase.table('contractor_my_bids').update(update_data).eq(
                    'contractor_id', contractor_id
                ).eq('bid_card_id', bid_card_id).execute()
                
                logger.info(f"Updated My Bid tracking for contractor {contractor_id} on bid {bid_card_id}")
                
            else:
                # Create new tracking record
                import uuid
                
                # Get bid card details
                bid_card = self.supabase.table('bid_cards').select('*').eq(
                    'id', bid_card_id
                ).execute()
                
                if not bid_card.data:
                    logger.error(f"Bid card {bid_card_id} not found")
                    return False
                
                card = bid_card.data[0]
                
                # Determine initial status
                status = 'viewed'
                if interaction_type in ['quote_submitted', 'proposal_submitted']:
                    status = 'quoted'
                elif interaction_type == 'message_sent':
                    status = 'engaged'
                
                tracking_data = {
                    'id': str(uuid.uuid4()),
                    'contractor_id': contractor_id,
                    'bid_card_id': bid_card_id,
                    'first_interaction': datetime.utcnow().isoformat(),
                    'last_interaction': datetime.utcnow().isoformat(),
                    'interaction_count': 1,
                    'last_interaction_type': interaction_type,
                    'status': status,
                    'bid_card_title': card.get('title', 'Untitled Project'),
                    'project_type': card.get('project_type'),
                    'location_zip': card.get('location_zip'),
                    'interaction_history': [{
                        'type': interaction_type,
                        'timestamp': datetime.utcnow().isoformat(),
                        'details': details
                    }],
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                self.supabase.table('contractor_my_bids').insert(tracking_data).execute()
                logger.info(f"Created new My Bid tracking for contractor {contractor_id} on bid {bid_card_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking bid interaction: {e}")
            return False
    
    async def get_contractor_my_bids(
        self, 
        contractor_id: str,
        include_full_details: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all bid cards a contractor has interacted with
        
        Args:
            contractor_id: The contractor's ID
            include_full_details: Whether to include full bid card details
        
        Returns:
            List of bid cards in contractor's "My Bids" section
        """
        try:
            # Get all tracked bid interactions
            my_bids = self.supabase.table('contractor_my_bids').select('*').eq(
                'contractor_id', contractor_id
            ).order('last_interaction', desc=True).execute()
            
            if not my_bids.data:
                return []
            
            results = []
            
            for bid_tracking in my_bids.data:
                bid_data = {
                    'bid_card_id': bid_tracking['bid_card_id'],
                    'status': bid_tracking['status'],
                    'first_interaction': bid_tracking['first_interaction'],
                    'last_interaction': bid_tracking['last_interaction'],
                    'interaction_count': bid_tracking['interaction_count'],
                    'last_interaction_type': bid_tracking['last_interaction_type'],
                    'bid_card_title': bid_tracking.get('bid_card_title'),
                    'project_type': bid_tracking.get('project_type')
                }
                
                if include_full_details:
                    # Get full bid card details
                    bid_card = self.supabase.table('bid_cards').select('*').eq(
                        'id', bid_tracking['bid_card_id']
                    ).execute()
                    
                    if bid_card.data:
                        bid_data['bid_card'] = bid_card.data[0]
                    
                    # Get messages for this bid card
                    messages = self.supabase.table('messages').select('*').eq(
                        'bid_card_id', bid_tracking['bid_card_id']
                    ).eq('sender_id', contractor_id).execute()
                    
                    bid_data['messages'] = messages.data if messages.data else []
                    
                    # Get proposals/quotes for this bid card
                    proposals = self.supabase.table('contractor_proposals').select('*').eq(
                        'bid_card_id', bid_tracking['bid_card_id']
                    ).eq('contractor_id', contractor_id).execute()
                    
                    bid_data['proposals'] = proposals.data if proposals.data else []
                
                results.append(bid_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting contractor My Bids: {e}")
            return []
    
    async def get_bid_interaction_context(
        self,
        contractor_id: str,
        bid_card_id: str
    ) -> Dict[str, Any]:
        """
        Get full interaction context for a specific bid card
        
        Args:
            contractor_id: The contractor's ID
            bid_card_id: The bid card ID
        
        Returns:
            Complete interaction history and context
        """
        try:
            context = {
                'has_interaction': False,
                'messages': [],
                'proposals': [],
                'questions': [],
                'interaction_summary': None
            }
            
            # Get tracking record
            tracking = self.supabase.table('contractor_my_bids').select('*').eq(
                'contractor_id', contractor_id
            ).eq('bid_card_id', bid_card_id).execute()
            
            if tracking.data:
                context['has_interaction'] = True
                context['interaction_summary'] = tracking.data[0]
            
            # Get all messages
            messages = self.supabase.table('messages').select('*').eq(
                'bid_card_id', bid_card_id
            ).or_(f"sender_id.eq.{contractor_id},recipient_id.eq.{contractor_id}").order(
                'created_at', desc=False
            ).execute()
            
            context['messages'] = messages.data if messages.data else []
            
            # Get all proposals
            proposals = self.supabase.table('contractor_proposals').select('*').eq(
                'bid_card_id', bid_card_id
            ).eq('contractor_id', contractor_id).execute()
            
            context['proposals'] = proposals.data if proposals.data else []
            
            # Get all questions (filtered from messages)
            if context['messages']:
                context['questions'] = [
                    msg for msg in context['messages']
                    if msg.get('sender_id') == contractor_id and '?' in msg.get('content', '')
                ]
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting bid interaction context: {e}")
            return {
                'has_interaction': False,
                'messages': [],
                'proposals': [],
                'questions': []
            }
    
    async def load_full_my_bids_context(self, contractor_id: str) -> Dict[str, Any]:
        """
        Load complete "My Bids" context for BSA memory
        
        Args:
            contractor_id: The contractor's ID
        
        Returns:
            Full context including all bid interactions, messages, and proposals
        """
        try:
            # Get all My Bids
            my_bids = await self.get_contractor_my_bids(contractor_id, include_full_details=True)
            
            context = {
                'total_my_bids': len(my_bids),
                'my_bids': my_bids,
                'total_messages': 0,
                'total_proposals': 0,
                'total_questions': 0,
                'engagement_level': 'low',
                'most_recent_interaction': None,
                'active_conversations': []
            }
            
            # Calculate totals and find active conversations
            for bid in my_bids:
                context['total_messages'] += len(bid.get('messages', []))
                context['total_proposals'] += len(bid.get('proposals', []))
                
                # Track active conversations (interacted in last 7 days)
                last_interaction = bid.get('last_interaction')
                if last_interaction:
                    try:
                        last_date = datetime.fromisoformat(last_interaction.replace('Z', '+00:00'))
                        days_ago = (datetime.utcnow() - last_date.replace(tzinfo=None)).days
                        if days_ago <= 7:
                            context['active_conversations'].append({
                                'bid_card_id': bid['bid_card_id'],
                                'title': bid.get('bid_card_title'),
                                'days_ago': days_ago,
                                'last_interaction_type': bid.get('last_interaction_type')
                            })
                    except:
                        pass
                
                # Track most recent interaction
                if not context['most_recent_interaction'] or (
                    last_interaction and last_interaction > context['most_recent_interaction']
                ):
                    context['most_recent_interaction'] = last_interaction
            
            # Determine engagement level
            if context['total_proposals'] > 0:
                context['engagement_level'] = 'high'
            elif context['total_messages'] > 5:
                context['engagement_level'] = 'medium'
            elif context['total_my_bids'] > 0:
                context['engagement_level'] = 'low'
            else:
                context['engagement_level'] = 'none'
            
            logger.info(f"Loaded My Bids context for {contractor_id}: {context['total_my_bids']} bids, "
                       f"{context['total_messages']} messages, {context['total_proposals']} proposals")
            
            return context
            
        except Exception as e:
            logger.error(f"Error loading full My Bids context: {e}")
            return {
                'total_my_bids': 0,
                'my_bids': [],
                'total_messages': 0,
                'total_proposals': 0,
                'engagement_level': 'none'
            }

# Global instance
my_bids_tracker = MyBidsTracker()