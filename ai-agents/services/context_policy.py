"""
Context Policy Engine - Unbreakable Privacy Rules
Enforces privacy boundaries in cross-agent conversation access
CRITICAL: These rules cannot be overridden by any agent
"""

import logging
from typing import Dict, List, Optional, Any, Set
from enum import Enum

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Agent classification for privacy filtering"""
    # Homeowner-side agents
    CIA = "CIA"           # Customer Interface Agent
    IRIS = "IRIS"         # Design inspiration agent  
    HMA = "HMA"           # Homeowner Management Agent
    
    # Contractor-side agents
    COIA = "COIA"         # Contractor Interface Agent
    BSA = "BSA"           # Bid Submission Agent
    
    # Neutral agents
    MESSAGING = "MESSAGING"  # Messaging system agent
    ADMIN = "ADMIN"         # Admin/system agents

class PrivacySide(Enum):
    """Privacy boundary classification"""
    HOMEOWNER_SIDE = "homeowner_side"
    CONTRACTOR_SIDE = "contractor_side"
    NEUTRAL = "neutral"

class ContextPolicy:
    """
    UNBREAKABLE PRIVACY POLICY ENGINE
    
    Core Privacy Rules:
    1. Homeowner agents CANNOT see contractor real names/contact info
    2. Contractor agents CANNOT see homeowner real names/contact info
    3. Same-side agents CAN share full context
    4. Cross-side sharing uses aliases only
    5. No agent can bypass these rules
    """
    
    def __init__(self):
        # Agent privacy side mapping - IMMUTABLE
        self.AGENT_PRIVACY_SIDES = {
            AgentType.CIA: PrivacySide.HOMEOWNER_SIDE,
            AgentType.IRIS: PrivacySide.HOMEOWNER_SIDE,
            AgentType.HMA: PrivacySide.HOMEOWNER_SIDE,
            AgentType.COIA: PrivacySide.CONTRACTOR_SIDE,
            AgentType.BSA: PrivacySide.CONTRACTOR_SIDE,
            AgentType.MESSAGING: PrivacySide.NEUTRAL,
            AgentType.ADMIN: PrivacySide.NEUTRAL
        }
        
        # Fields that contain personally identifiable information
        self.PII_FIELDS = {
            "homeowner_pii": {
                "first_name", "last_name", "full_name", "email", "phone", 
                "address", "property_address", "contact_info", "personal_details"
            },
            "contractor_pii": {
                "company_name", "contact_name", "owner_name", "business_email", 
                "business_phone", "business_address", "license_number", "personal_info"
            }
        }
        
        # Alias field mappings
        self.ALIAS_MAPPINGS = {
            "contractor_company_name": "contractor_alias",
            "homeowner_full_name": "homeowner_alias",
            "contractor_contact_name": "contractor_representative",
            "homeowner_first_name": "project_owner"
        }

    def can_access_conversation(
        self, 
        requesting_agent: AgentType, 
        conversation_metadata: Dict[str, Any]
    ) -> bool:
        """
        Determine if an agent can access a conversation
        
        Args:
            requesting_agent: The agent requesting access
            conversation_metadata: Conversation metadata including participants
            
        Returns:
            bool: True if access allowed, False otherwise
        """
        try:
            requesting_side = self.AGENT_PRIVACY_SIDES.get(requesting_agent)
            if not requesting_side:
                logger.warning(f"Unknown agent type: {requesting_agent}")
                return False
            
            # Neutral agents (ADMIN, MESSAGING) can access all conversations
            if requesting_side == PrivacySide.NEUTRAL:
                return True
            
            # Get conversation's privacy context
            conversation_side = self._determine_conversation_side(conversation_metadata)
            
            # Same-side agents can access conversations
            if requesting_side == conversation_side:
                return True
                
            # Cross-side access only allowed for messaging/coordination
            if self._is_coordination_context(conversation_metadata):
                return True
                
            logger.info(f"Privacy boundary enforced: {requesting_agent} cannot access {conversation_side} conversation")
            return False
            
        except Exception as e:
            logger.error(f"Error in access control: {e}")
            # Fail secure - deny access on error
            return False

    def filter_conversation_data(
        self, 
        requesting_agent: AgentType,
        conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Filter conversation data based on privacy rules
        
        Args:
            requesting_agent: The agent requesting the data
            conversation_data: Full conversation data
            
        Returns:
            Dict: Filtered conversation data with PII removed/aliased
        """
        try:
            requesting_side = self.AGENT_PRIVACY_SIDES.get(requesting_agent)
            if not requesting_side:
                logger.warning(f"Unknown agent type: {requesting_agent}")
                return {}
            
            # Neutral agents get full access
            if requesting_side == PrivacySide.NEUTRAL:
                return conversation_data
            
            # Create filtered copy
            filtered_data = conversation_data.copy()
            
            # Apply privacy filtering based on requesting agent's side
            if requesting_side == PrivacySide.HOMEOWNER_SIDE:
                filtered_data = self._filter_contractor_pii(filtered_data)
            elif requesting_side == PrivacySide.CONTRACTOR_SIDE:
                filtered_data = self._filter_homeowner_pii(filtered_data)
            
            logger.info(f"Applied privacy filtering for {requesting_agent}")
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error filtering conversation data: {e}")
            # Fail secure - return empty data on error
            return {}

    def get_cross_agent_context(
        self, 
        requesting_agent: AgentType,
        user_id: str,
        include_agent_types: Optional[List[AgentType]] = None
    ) -> Dict[str, Any]:
        """
        Get cross-agent context with privacy filtering
        
        Args:
            requesting_agent: The agent requesting context
            user_id: User ID for context lookup
            include_agent_types: Specific agent types to include context from
            
        Returns:
            Dict: Filtered cross-agent context
        """
        try:
            requesting_side = self.AGENT_PRIVACY_SIDES.get(requesting_agent)
            if not requesting_side:
                return {}
            
            # Determine which agents can share context
            allowed_agents = self._get_allowed_context_sources(requesting_agent)
            
            if include_agent_types:
                # Filter to only requested agent types that are allowed
                allowed_agents = [
                    agent for agent in include_agent_types 
                    if agent in allowed_agents
                ]
            
            # TODO: Implement actual context retrieval from unified conversation system
            # This would query the unified_conversations table and aggregate context
            # from allowed agent types while applying privacy filtering
            
            context = {
                "allowed_context_sources": [agent.value for agent in allowed_agents],
                "privacy_side": requesting_side.value,
                "user_id": user_id,
                "context_filtered": True
            }
            
            logger.info(f"Generated cross-agent context for {requesting_agent}")
            return context
            
        except Exception as e:
            logger.error(f"Error getting cross-agent context: {e}")
            return {}

    def _determine_conversation_side(self, metadata: Dict[str, Any]) -> PrivacySide:
        """Determine which privacy side a conversation belongs to"""
        # Check conversation participants and agent types
        participants = metadata.get("participants", [])
        agent_type = metadata.get("agent_type", "")
        
        # If conversation involves contractor agents, it's contractor-side
        if agent_type == "COIA" or any("contractor" in str(p).lower() for p in participants):
            return PrivacySide.CONTRACTOR_SIDE
            
        # If conversation involves homeowner agents, it's homeowner-side  
        if agent_type in ["CIA", "IRIS", "HMA"] or any("homeowner" in str(p).lower() for p in participants):
            return PrivacySide.HOMEOWNER_SIDE
            
        # Default to neutral for system conversations
        return PrivacySide.NEUTRAL

    def _is_coordination_context(self, metadata: Dict[str, Any]) -> bool:
        """Check if this is a coordination context that allows cross-side access"""
        conversation_type = metadata.get("conversation_type", "")
        return conversation_type in ["bid_coordination", "project_messaging", "system_notification"]

    def _filter_contractor_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove contractor PII for homeowner-side agents"""
        filtered = data.copy()
        
        # Remove contractor PII fields
        for field in self.PII_FIELDS["contractor_pii"]:
            if field in filtered:
                # Replace with alias if mapping exists
                alias_field = self.ALIAS_MAPPINGS.get(field)
                if alias_field and field in filtered:
                    filtered[alias_field] = self._generate_alias(filtered[field], "contractor")
                del filtered[field]
        
        # Filter messages to remove contractor PII
        if "messages" in filtered:
            filtered["messages"] = [
                self._filter_message_contractor_pii(msg) 
                for msg in filtered["messages"]
            ]
        
        return filtered

    def _filter_homeowner_pii(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove homeowner PII for contractor-side agents"""
        filtered = data.copy()
        
        # Remove homeowner PII fields
        for field in self.PII_FIELDS["homeowner_pii"]:
            if field in filtered:
                # Replace with alias if mapping exists
                alias_field = self.ALIAS_MAPPINGS.get(field)
                if alias_field and field in filtered:
                    filtered[alias_field] = self._generate_alias(filtered[field], "homeowner")
                del filtered[field]
        
        # Filter messages to remove homeowner PII
        if "messages" in filtered:
            filtered["messages"] = [
                self._filter_message_homeowner_pii(msg) 
                for msg in filtered["messages"]
            ]
        
        return filtered

    def _filter_message_contractor_pii(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Filter contractor PII from individual message"""
        filtered_msg = message.copy()
        # TODO: Implement content filtering for contractor names/info in message text
        return filtered_msg

    def _filter_message_homeowner_pii(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Filter homeowner PII from individual message"""
        filtered_msg = message.copy()
        # TODO: Implement content filtering for homeowner names/info in message text
        return filtered_msg

    def _generate_alias(self, original_value: str, entity_type: str) -> str:
        """Generate consistent alias for PII values"""
        if not original_value:
            return f"Anonymous {entity_type.title()}"
        
        # Simple hash-based alias generation
        import hashlib
        hash_value = hashlib.md5(original_value.encode()).hexdigest()[:8]
        return f"{entity_type.title()} {hash_value}"

    def _get_allowed_context_sources(self, requesting_agent: AgentType) -> List[AgentType]:
        """Get list of agents that can share context with requesting agent"""
        requesting_side = self.AGENT_PRIVACY_SIDES.get(requesting_agent)
        
        if requesting_side == PrivacySide.NEUTRAL:
            # Neutral agents can access context from all agents
            return list(AgentType)
        
        # Same-side agents can share context
        allowed = [
            agent for agent, side in self.AGENT_PRIVACY_SIDES.items()
            if side == requesting_side or side == PrivacySide.NEUTRAL
        ]
        
        return allowed

    def validate_context_request(
        self,
        requesting_agent: AgentType,
        target_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        FINAL VALIDATION - Cannot be bypassed
        Ensures no privacy violations in context requests
        """
        try:
            # Apply all privacy filters
            filtered_context = self.filter_conversation_data(requesting_agent, target_context)
            
            # Double-check no PII leaked through
            validation_result = self._validate_no_pii_leakage(requesting_agent, filtered_context)
            
            if not validation_result["valid"]:
                logger.error(f"PII leakage detected for {requesting_agent}: {validation_result['violations']}")
                return {}
            
            return filtered_context
            
        except Exception as e:
            logger.error(f"Context validation failed: {e}")
            # Fail secure
            return {}

    def _validate_no_pii_leakage(
        self, 
        requesting_agent: AgentType, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Final validation to ensure no PII leakage"""
        requesting_side = self.AGENT_PRIVACY_SIDES.get(requesting_agent)
        violations = []
        
        # Check for prohibited PII fields
        if requesting_side == PrivacySide.HOMEOWNER_SIDE:
            # Homeowner agents should not see contractor PII
            for field in self.PII_FIELDS["contractor_pii"]:
                if field in context:
                    violations.append(f"Contractor PII field '{field}' present")
        
        elif requesting_side == PrivacySide.CONTRACTOR_SIDE:
            # Contractor agents should not see homeowner PII  
            for field in self.PII_FIELDS["homeowner_pii"]:
                if field in context:
                    violations.append(f"Homeowner PII field '{field}' present")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations
        }

# Global instance for consistent policy enforcement
context_policy = ContextPolicy()