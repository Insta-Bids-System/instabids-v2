"""
AI Contractor Relationship Memory System
Builds intimate understanding of contractors through conversation analysis
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from database import SupabaseDB
import uuid
from openai import AsyncOpenAI
import os

logger = logging.getLogger(__name__)

class ContractorAIMemory:
    """
    AI-powered contractor relationship memory system that builds intimate 
    understanding of contractors over time through conversation analysis.
    """
    
    def __init__(self):
        self.db = SupabaseDB()
        
        # Initialize OpenAI for memory analysis
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = AsyncOpenAI(api_key=api_key)
        else:
            self.openai_client = None
            logger.warning("No OpenAI API key - AI memory updates disabled")
    
    async def update_contractor_memory(self, contractor_id: str, conversation_data: Dict) -> Dict:
        """
        Update contractor memory based on conversation data using AI analysis.
        
        Args:
            contractor_id: The contractor's ID
            conversation_data: {
                'input': str,           # What contractor said
                'response': str,        # AI agent response
                'context': str,         # Conversation context
                'project_type': str,    # Type of project discussed
                'bid_amount': float,    # Any bid amounts mentioned
                'timeline': str         # Timeline preferences
            }
        
        Returns:
            Updated memory profile
        """
        try:
            # Get current memory
            current_memory = await self.get_contractor_memory(contractor_id)
            logger.info(f"Current memory loaded: {len(current_memory) if current_memory else 0} items")
            
            # Use AI to analyze conversation and extract insights
            memory_update = await self._analyze_conversation_for_memory(
                conversation_data, current_memory
            )
            logger.info(f"Memory update result: {memory_update}")
            
            if memory_update:
                # Merge with current memory
                updated_memory = await self._merge_memory_insights(
                    current_memory, memory_update
                )
                
                # Save to database
                await self._save_contractor_memory(contractor_id, updated_memory)
                
                logger.info(f"Updated contractor memory for {contractor_id}")
                return updated_memory
            else:
                logger.warning("No memory update generated from conversation")
            
            return current_memory
            
        except Exception as e:
            logger.error(f"Error updating contractor memory: {e}")
            return {}
    
    async def get_contractor_memory(self, contractor_id: str) -> Dict:
        """
        Get current AI memory profile for contractor.
        """
        try:
            result = self.db.client.table("contractor_ai_memory").select("*").eq(
                "contractor_id", contractor_id
            ).execute()
            
            if result.data:
                memory_data = result.data[0].get("memory_data", {})
                return memory_data
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting contractor memory: {e}")
            return {}
    
    async def get_memory_for_system_prompt(self, contractor_id: str) -> str:
        """
        Get formatted memory string for injection into system prompts.
        """
        memory = await self.get_contractor_memory(contractor_id)
        
        if not memory:
            return ""
        
        # Format memory for system prompt
        memory_sections = []
        
        # Personal preferences
        if memory.get("personal_preferences"):
            prefs = memory["personal_preferences"]
            memory_sections.append(f"Personal Preferences: {', '.join(prefs)}")
        
        # Communication style
        if memory.get("communication_style"):
            style = memory["communication_style"]
            memory_sections.append(f"Communication Style: {style}")
        
        # Business focus areas
        if memory.get("business_focus"):
            focus = memory["business_focus"]
            memory_sections.append(f"Business Focus: {', '.join(focus)}")
        
        # Pricing patterns
        if memory.get("pricing_patterns"):
            pricing = memory["pricing_patterns"]
            memory_sections.append(f"Pricing Approach: {pricing}")
        
        # Project preferences
        if memory.get("project_preferences"):
            projects = memory["project_preferences"]
            memory_sections.append(f"Project Preferences: {', '.join(projects)}")
        
        # Customer relationship insights
        if memory.get("customer_relationship_style"):
            style = memory["customer_relationship_style"]
            memory_sections.append(f"Customer Relationship Style: {style}")
        
        # Quality standards
        if memory.get("quality_standards"):
            quality = memory["quality_standards"]
            memory_sections.append(f"Quality Standards: {quality}")
        
        if memory_sections:
            return f"\n\n## Contractor Relationship Memory:\n" + "\n".join([f"- {section}" for section in memory_sections])
        
        return ""
    
    async def _analyze_conversation_for_memory(self, conversation_data: Dict, current_memory: Dict) -> Optional[Dict]:
        """
        Use AI to analyze conversation and extract memory-worthy insights.
        """
        if not self.openai_client:
            logger.warning("OpenAI client not available - skipping AI analysis")
            return None
        
        try:
            logger.info("Starting AI conversation analysis...")
            # Build prompt for AI analysis
            analysis_prompt = f"""
Analyze this contractor conversation to extract relationship memory insights.
Focus on personal preferences, communication style, business approach, and personality traits.

Contractor Input: "{conversation_data.get('input', '')}"
AI Response: "{conversation_data.get('response', '')}"
Project Type: {conversation_data.get('project_type', 'Unknown')}
Context: {conversation_data.get('context', '')}

Current Memory: {json.dumps(current_memory, indent=2)}

Extract NEW insights about this contractor's:
1. Personal preferences (work style, scheduling, materials)
2. Communication style (formal/casual, detail-oriented, direct)
3. Business focus areas (specialties, market segments)
4. Pricing patterns (premium/budget, fixed/flexible)
5. Project preferences (size, complexity, timeline)
6. Customer relationship style (consultative, transactional)
7. Quality standards (perfectionist, practical, efficient)

Return ONLY new insights that aren't already captured. Format as JSON:
{{
    "personal_preferences": ["new preference 1", "new preference 2"],
    "communication_style": "new style insight",
    "business_focus": ["new focus area"],
    "pricing_patterns": "new pricing insight",
    "project_preferences": ["new project type preference"],
    "customer_relationship_style": "new relationship insight",
    "quality_standards": "new quality insight"
}}

Only include fields with NEW information. Return empty object {{}} if no new insights.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"AI response content: {content}")
            
            # Clean up markdown code blocks if present
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            # Parse JSON response
            if content.startswith('{') and content.endswith('}'):
                insights = json.loads(content)
                logger.info(f"Parsed insights: {insights}")
                
                # Clean up empty values
                cleaned_insights = {}
                for key, value in insights.items():
                    if value and value != "":
                        if isinstance(value, list) and len(value) > 0:
                            cleaned_insights[key] = value
                        elif isinstance(value, str):
                            cleaned_insights[key] = value
                
                return cleaned_insights if cleaned_insights else None
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing conversation for memory: {e}")
            return None
    
    async def _merge_memory_insights(self, current_memory: Dict, new_insights: Dict) -> Dict:
        """
        Intelligently merge new insights with existing memory.
        """
        merged = current_memory.copy()
        
        # Add metadata
        merged["last_updated"] = datetime.utcnow().isoformat()
        merged["total_updates"] = merged.get("total_updates", 0) + 1
        
        for key, value in new_insights.items():
            if isinstance(value, list):
                # Merge lists, avoiding duplicates
                existing = merged.get(key, [])
                for item in value:
                    if item not in existing:
                        existing.append(item)
                merged[key] = existing
            else:
                # For strings, append or replace based on context
                if key in merged and isinstance(merged[key], str):
                    # Combine insights
                    merged[key] = f"{merged[key]}; {value}"
                else:
                    merged[key] = value
        
        return merged
    
    async def _save_contractor_memory(self, contractor_id: str, memory_data: Dict):
        """
        Save contractor memory to database.
        """
        try:
            # Check if memory record exists
            existing = self.db.client.table("contractor_ai_memory").select("id").eq(
                "contractor_id", contractor_id
            ).execute()
            
            data = {
                "contractor_id": contractor_id,
                "memory_data": memory_data,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if existing.data:
                # Update existing
                self.db.client.table("contractor_ai_memory").update(data).eq(
                    "contractor_id", contractor_id
                ).execute()
            else:
                # Create new
                data["id"] = str(uuid.uuid4())
                data["created_at"] = datetime.utcnow().isoformat()
                self.db.client.table("contractor_ai_memory").insert(data).execute()
            
            logger.info(f"Saved contractor AI memory for {contractor_id}")
            
        except Exception as e:
            logger.error(f"Error saving contractor memory: {e}")
    
    async def create_memory_table_if_not_exists(self):
        """
        Create contractor_ai_memory table if it doesn't exist.
        """
        try:
            # This would need to be run manually in Supabase SQL editor
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS contractor_ai_memory (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                contractor_id UUID NOT NULL REFERENCES contractors(id),
                memory_data JSONB NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(contractor_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_contractor_ai_memory_contractor_id 
            ON contractor_ai_memory(contractor_id);
            """
            
            logger.info("Table creation SQL:")
            logger.info(create_table_sql)
            
        except Exception as e:
            logger.error(f"Error creating memory table: {e}")
    
    async def get_contractor_personality_summary(self, contractor_id: str) -> str:
        """
        Get a natural language summary of contractor's personality and preferences.
        """
        memory = await self.get_contractor_memory(contractor_id)
        
        if not memory:
            return "No relationship history established yet."
        
        # Build natural summary
        summary_parts = []
        
        if memory.get("communication_style"):
            summary_parts.append(f"Communication style: {memory['communication_style']}")
        
        if memory.get("business_focus"):
            focus_areas = ", ".join(memory["business_focus"])
            summary_parts.append(f"Specializes in: {focus_areas}")
        
        if memory.get("personal_preferences"):
            prefs = ", ".join(memory["personal_preferences"][:3])  # Top 3
            summary_parts.append(f"Preferences: {prefs}")
        
        if memory.get("quality_standards"):
            summary_parts.append(f"Quality approach: {memory['quality_standards']}")
        
        if memory.get("customer_relationship_style"):
            summary_parts.append(f"Customer style: {memory['customer_relationship_style']}")
        
        updates = memory.get("total_updates", 0)
        last_updated = memory.get("last_updated", "Unknown")
        
        if summary_parts:
            summary = ". ".join(summary_parts)
            return f"{summary}. (Based on {updates} interactions, last updated: {last_updated[:10]})"
        
        return "Limited relationship history available."