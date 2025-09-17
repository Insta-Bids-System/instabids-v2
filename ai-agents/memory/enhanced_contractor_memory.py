"""
Enhanced Multi-Table Contractor Memory System
Creates comprehensive contractor understanding across multiple dimensions
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from database import SupabaseDB
import uuid
from openai import AsyncOpenAI
import os
from .field_mappings import prepare_for_database_insert

logger = logging.getLogger(__name__)

class EnhancedContractorMemory:
    """
    Multi-dimensional contractor memory system that creates comprehensive
    understanding across relationship, project, communication, and business dimensions.
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
    
    async def update_all_contractor_memories(self, contractor_id: str, conversation_data: Dict) -> Dict:
        """
        Update all memory dimensions based on conversation data.
        
        This is the MAIN function that gets called after every conversation.
        It analyzes the conversation and updates multiple memory tables.
        """
        try:
            results = {}
            
            # 1. Update relationship memory (personality, preferences)
            relationship_memory = await self._update_relationship_memory(contractor_id, conversation_data)
            if relationship_memory:
                results["relationship"] = relationship_memory
            
            # 2. Update project memory (project patterns, quality standards)
            project_memory = await self._update_project_memory(contractor_id, conversation_data)
            if project_memory:
                results["project"] = project_memory
            
            # 3. Update communication memory (style, timing, channels)
            communication_memory = await self._update_communication_memory(contractor_id, conversation_data)
            if communication_memory:
                results["communication"] = communication_memory
            
            # 4. Update business memory (pricing, negotiations, processes)
            business_memory = await self._update_business_memory(contractor_id, conversation_data)
            if business_memory:
                results["business"] = business_memory
            
            # 5. Update pain points memory (challenges, opportunities, needs)
            pain_points_memory = await self._update_pain_points_memory(contractor_id, conversation_data)
            if pain_points_memory:
                results["pain_points"] = pain_points_memory
            
            logger.info(f"Updated {len(results)} memory dimensions for contractor {contractor_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error updating enhanced contractor memories: {e}")
            return {}
    
    async def get_complete_contractor_profile(self, contractor_id: str) -> str:
        """
        Get complete contractor understanding across all dimensions for system prompt injection.
        
        This creates the "shock value" comprehensive understanding you want.
        """
        try:
            # Load all memory dimensions - using correct table names
            relationship = await self._get_memory("contractor_relationship_memory", contractor_id)
            project = await self._get_memory("contractor_bidding_patterns", contractor_id)
            communication = await self._get_memory("contractor_information_needs", contractor_id)
            business = await self._get_memory("contractor_business_profile", contractor_id)
            pain_points = await self._get_memory("contractor_pain_points", contractor_id)
            
            # Load existing contractor profile data
            contractor_profile = await self._get_contractor_profile_data(contractor_id)
            
            # Build comprehensive profile
            profile_sections = []
            
            # Basic contractor info from contractors table
            if contractor_profile:
                basic_info = []
                if contractor_profile.get("company_name"):
                    basic_info.append(f"Company: {contractor_profile['company_name']}")
                if contractor_profile.get("years_in_business"):
                    basic_info.append(f"Experience: {contractor_profile['years_in_business']} years")
                if contractor_profile.get("specialties"):
                    basic_info.append(f"Specialties: {', '.join(contractor_profile['specialties'])}")
                if contractor_profile.get("lead_score"):
                    basic_info.append(f"Lead Quality Score: {contractor_profile['lead_score']}/100")
                
                if basic_info:
                    profile_sections.append("## Contractor Profile:\n" + "\n".join([f"- {info}" for info in basic_info]))
            
            # Relationship insights
            if relationship:
                rel_insights = []
                if relationship.get("personality_type"):
                    rel_insights.append(f"Personality: {relationship['personality_type']}")
                if relationship.get("work_style"):
                    rel_insights.append(f"Work Style: {relationship['work_style']}")
                if relationship.get("customer_approach"):
                    rel_insights.append(f"Customer Approach: {relationship['customer_approach']}")
                if relationship.get("decision_making_style"):
                    rel_insights.append(f"Decision Making: {relationship['decision_making_style']}")
                
                if rel_insights:
                    profile_sections.append("## Relationship Intelligence:\n" + "\n".join([f"- {insight}" for insight in rel_insights]))
            
            # Project patterns
            if project:
                proj_insights = []
                if project.get("preferred_project_types"):
                    proj_insights.append(f"Preferred Projects: {', '.join(project['preferred_project_types'])}")
                if project.get("quality_standards"):
                    proj_insights.append(f"Quality Standards: {project['quality_standards']}")
                if project.get("pricing_strategy"):
                    proj_insights.append(f"Pricing Strategy: {project['pricing_strategy']}")
                if project.get("timeline_preferences"):
                    proj_insights.append(f"Timeline Preferences: {project['timeline_preferences']}")
                
                if proj_insights:
                    profile_sections.append("## Project Intelligence:\n" + "\n".join([f"- {insight}" for insight in proj_insights]))
            
            # Communication patterns
            if communication:
                comm_insights = []
                if communication.get("preferred_channels"):
                    comm_insights.append(f"Preferred Communication: {', '.join(communication['preferred_channels'])}")
                if communication.get("response_timing"):
                    comm_insights.append(f"Response Timing: {communication['response_timing']}")
                if communication.get("documentation_style"):
                    comm_insights.append(f"Documentation Style: {communication['documentation_style']}")
                if communication.get("detail_level"):
                    comm_insights.append(f"Detail Level: {communication['detail_level']}")
                
                if comm_insights:
                    profile_sections.append("## Communication Intelligence:\n" + "\n".join([f"- {insight}" for insight in comm_insights]))
            
            # Business patterns
            if business:
                biz_insights = []
                if business.get("crm_system"):
                    biz_insights.append(f"CRM System: {business['crm_system']}")
                if business.get("employee_count"):
                    biz_insights.append(f"Employees: {business['employee_count']}")
                if business.get("growth_trajectory"):
                    biz_insights.append(f"Growth: {business['growth_trajectory']}")
                if business.get("technology_adoption"):
                    biz_insights.append(f"Tech Level: {business['technology_adoption']}")
                
                if biz_insights:
                    profile_sections.append("## Business Intelligence:\n" + "\n".join([f"- {insight}" for insight in biz_insights]))
            
            # Pain points & opportunities
            if pain_points:
                pain_insights = []
                if pain_points.get("operational_challenges"):
                    pain_insights.append(f"Challenges: {', '.join(pain_points['operational_challenges'])}")
                if pain_points.get("technology_gaps"):
                    pain_insights.append(f"Tech Gaps: {', '.join(pain_points['technology_gaps'])}")
                if pain_points.get("financial_pain_points"):
                    pain_insights.append(f"Financial Issues: {', '.join(pain_points['financial_pain_points'])}")
                if pain_points.get("immediate_needs"):
                    pain_insights.append(f"Immediate Needs: {', '.join(pain_points['immediate_needs'])}")
                
                if pain_insights:
                    profile_sections.append("## Pain Points & Opportunities:\n" + "\n".join([f"- {insight}" for insight in pain_insights]))
            
            # Calculate total insights
            total_insights = sum([
                len(relationship) if relationship else 0,
                len(project) if project else 0,
                len(communication) if communication else 0,
                len(business) if business else 0,
                len(pain_points) if pain_points else 0
            ])
            
            if profile_sections:
                header = f"\n\n## 🧠 COMPREHENSIVE CONTRACTOR INTELLIGENCE ({total_insights} insights across 5 dimensions):\n"
                return header + "\n\n".join(profile_sections)
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting complete contractor profile: {e}")
            return ""
    
    async def _update_relationship_memory(self, contractor_id: str, conversation_data: Dict) -> Optional[Dict]:
        """Update relationship memory (personality, preferences, work style)"""
        if not self.openai_client:
            return None
        
        try:
            current_memory = await self._get_memory("contractor_relationship_memory", contractor_id)
            
            analysis_prompt = f"""
Extract SPECIFIC PERSONAL/WORK DETAILS mentioned in this contractor conversation.

Contractor Input: "{conversation_data.get('input', '')}"
AI Response: "{conversation_data.get('response', '')}"
Project Context: {conversation_data.get('project_type', 'Unknown')}

Current Relationship Memory: {json.dumps(current_memory, indent=2)}

Extract ONLY specific details mentioned (do not infer personality types):
{{
    "communication_preferences": "exact preferences mentioned (e.g., email for non-urgent, text for emergencies)",
    "work_style": "specific work approach mentioned",
    "customer_approach": "specific customer service approach mentioned", 
    "specialties_mentioned": ["specific specializations mentioned"],
    "experience_details": "specific experience mentioned",
    "preferences_stated": "specific preferences or dislikes mentioned",
    "personal_details": "specific personal information shared",
    "business_philosophy": "specific business philosophy or approach mentioned"
}}

CRITICAL: Only include fields where contractor explicitly mentioned specific details. Do not categorize personality or infer traits. Return empty {{}} if no specific personal/work details mentioned.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=400,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up markdown
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            if content.startswith('{') and content.endswith('}'):
                insights = json.loads(content)
                
                if insights:
                    merged_memory = await self._merge_memory(current_memory, insights)
                    await self._save_memory("contractor_relationship_memory", contractor_id, merged_memory)
                    return merged_memory
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating relationship memory: {e}")
            return None
    
    async def _update_project_memory(self, contractor_id: str, conversation_data: Dict) -> Optional[Dict]:
        """Update project memory (project types, quality, pricing patterns)"""
        if not self.openai_client:
            return None
        
        try:
            current_memory = await self._get_memory("contractor_bidding_patterns", contractor_id)
            
            analysis_prompt = f"""
Extract SPECIFIC PROJECT FACTS mentioned in this contractor conversation.

Contractor Input: "{conversation_data.get('input', '')}"
AI Response: "{conversation_data.get('response', '')}"
Project Type: {conversation_data.get('project_type', 'Unknown')}
Bid Amount: {conversation_data.get('bid_amount', 'Not specified')}

Current Project Memory: {json.dumps(current_memory, indent=2)}

Extract ONLY specific project facts mentioned:
{{
    "preferred_project_types": ["specific project types mentioned"],
    "sweet_spot_projects": ["specific project ranges mentioned (e.g., bathroom and kitchen remodeling)"],
    "project_size_range": "specific size/budget range mentioned (e.g., $30k-$75k)",
    "specialization_areas": ["specific areas of expertise mentioned"],
    "pricing_strategy": "specific pricing approach mentioned",
    "markup_percentages": {{"materials": %, "labor": %}} if mentioned,
    "timeline_approach": "specific timeline preferences mentioned",
    "quality_standards": "specific quality approach mentioned",
    "licensing_details": "specific licenses or certifications mentioned",
    "equipment_capabilities": ["specific equipment or tools mentioned"],
    "subcontractor_relationships": ["specific subcontractor arrangements mentioned"]
}}

CRITICAL: Only include fields where contractor explicitly mentioned specific project details. Do not categorize or infer. Return empty {{}} if no specific project facts mentioned.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=400,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up and parse
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            if content.startswith('{') and content.endswith('}'):
                insights = json.loads(content)
                
                if insights:
                    merged_memory = await self._merge_memory(current_memory, insights)
                    await self._save_memory("contractor_bidding_patterns", contractor_id, merged_memory)
                    return merged_memory
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating project memory: {e}")
            return None
    
    async def _update_communication_memory(self, contractor_id: str, conversation_data: Dict) -> Optional[Dict]:
        """Update communication memory (style, timing, channels, documentation)"""
        if not self.openai_client:
            return None
        
        try:
            current_memory = await self._get_memory("contractor_information_needs", contractor_id)
            
            analysis_prompt = f"""
Extract SPECIFIC COMMUNICATION PREFERENCES mentioned in this contractor conversation.

Contractor Input: "{conversation_data.get('input', '')}"
AI Response: "{conversation_data.get('response', '')}"
Channel: {conversation_data.get('channel', 'BSA chat')}

Current Communication Memory: {json.dumps(current_memory, indent=2)}

Extract ONLY specific communication preferences mentioned:
{{
    "preferred_channels": ["specific channels mentioned (e.g., email for non-urgent, text for emergencies)"],
    "communication_style": "specific style preferences mentioned",
    "response_timing": "specific timing preferences mentioned",
    "documentation_preferences": "specific documentation needs mentioned (e.g., detailed proposals with material breakdowns)",
    "meeting_preferences": "specific meeting or interaction preferences mentioned",
    "contact_availability": "specific availability mentioned",
    "proposal_requirements": "specific proposal format requirements mentioned",
    "information_needs": "specific types of information requested or needed",
    "follow_up_preferences": "specific follow-up preferences mentioned"
}}

CRITICAL: Only include fields where contractor explicitly mentioned specific communication preferences. Do not infer style or categorize. Return empty {{}} if no specific preferences mentioned.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=400,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up and parse
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            if content.startswith('{') and content.endswith('}'):
                insights = json.loads(content)
                
                if insights:
                    merged_memory = await self._merge_memory(current_memory, insights)
                    await self._save_memory("contractor_information_needs", contractor_id, merged_memory)
                    return merged_memory
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating communication memory: {e}")
            return None
    
    async def _update_business_memory(self, contractor_id: str, conversation_data: Dict) -> Optional[Dict]:
        """Update business memory (pricing, negotiations, processes, payments)"""
        if not self.openai_client:
            return None
        
        try:
            current_memory = await self._get_memory("contractor_business_profile", contractor_id)
            
            analysis_prompt = f"""
Extract SPECIFIC BUSINESS FACTS mentioned in this contractor conversation.

Contractor Input: "{conversation_data.get('input', '')}"
AI Response: "{conversation_data.get('response', '')}"
Project Type: {conversation_data.get('project_type', 'Unknown')}

Current Business Memory: {json.dumps(current_memory, indent=2)}

Extract ONLY facts explicitly mentioned (do not infer or categorize):
{{
    "crm_system": "exact system name if mentioned (e.g., ServiceTitan, HubSpot)",
    "employee_count": specific number mentioned,
    "markup_percentages": {{"materials": %, "labor": %}} if specific percentages mentioned,
    "software_stack": ["exact software names mentioned"],
    "annual_revenue": "specific revenue if mentioned",
    "years_in_business": specific number if mentioned,
    "payment_terms": "exact terms mentioned (e.g., 30% down, 40% rough-in, 30% completion)",
    "project_size_range": "exact range mentioned (e.g., $30k-$75k)",
    "business_challenges": ["specific challenges mentioned"],
    "expansion_plans": "specific plans mentioned",
    "technology_adoption": "specific technology mentioned"
}}

CRITICAL: Only include fields where specific facts were mentioned. Do not categorize or infer. Return empty {{}} if no specific business facts mentioned.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=400,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up and parse
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            if content.startswith('{') and content.endswith('}'):
                insights = json.loads(content)
                
                if insights:
                    merged_memory = await self._merge_memory(current_memory, insights)
                    await self._save_memory("contractor_business_profile", contractor_id, merged_memory)
                    return merged_memory
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating business memory: {e}")
            return None
    
    async def _update_pain_points_memory(self, contractor_id: str, conversation_data: Dict) -> Optional[Dict]:
        """Update pain points memory (challenges, opportunities, needs)"""
        if not self.openai_client:
            return None
        
        try:
            current_memory = await self._get_memory("contractor_pain_points", contractor_id)
            
            analysis_prompt = f"""
Extract SPECIFIC CHALLENGES and PROBLEMS mentioned in this contractor conversation.

Contractor Input: "{conversation_data.get('input', '')}"
AI Response: "{conversation_data.get('response', '')}"
Project Context: {conversation_data.get('project_type', 'Unknown')}

Current Pain Points Memory: {json.dumps(current_memory, indent=2)}

Extract ONLY specific problems/challenges explicitly mentioned:
{{
    "operational_challenges": ["specific operational problems mentioned (e.g., managing electrical and HVAC subcontractors)"],
    "technology_gaps": ["specific technology issues mentioned"],
    "financial_pain_points": ["specific financial problems mentioned (e.g., cash flow tight when customers pay in 60+ days)"],
    "workflow_inefficiencies": ["specific workflow problems mentioned"],
    "scheduling_challenges": ["specific scheduling issues mentioned"],
    "material_issues": ["specific material or supply problems mentioned"],
    "staffing_challenges": ["specific staffing problems mentioned"],
    "customer_issues": ["specific customer-related challenges mentioned"],
    "growth_obstacles": ["specific barriers to growth mentioned"],
    "immediate_needs": ["specific urgent needs mentioned"],
    "future_goals": ["specific goals or expansion plans mentioned"]
}}

CRITICAL: Only include fields where contractor explicitly mentioned specific problems or challenges. Do not infer or categorize. Return empty {{}} if no specific challenges mentioned.
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=400,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up and parse
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            if content.startswith('{') and content.endswith('}'):
                insights = json.loads(content)
                
                if insights:
                    merged_memory = await self._merge_memory(current_memory, insights)
                    await self._save_memory("contractor_pain_points", contractor_id, merged_memory)
                    return merged_memory
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating pain points memory: {e}")
            return None
    
    async def _get_memory(self, table_name: str, contractor_id: str) -> Dict:
        """Get memory from specified table"""
        try:
            result = self.db.client.table(table_name).select("*").eq(
                "contractor_id", contractor_id
            ).execute()
            
            if result.data:
                # Return the full record, removing id and timestamps
                record = result.data[0].copy()
                record.pop('id', None)
                record.pop('created_at', None)
                record.pop('last_updated', None)
                return record
            return {}
            
        except Exception as e:
            logger.error(f"Error getting {table_name} memory: {e}")
            return {}
    
    async def _save_memory(self, table_name: str, contractor_id: str, memory_data: Dict):
        """Save memory to specified table"""
        try:
            # Map AI fields to database columns
            mapped_data = prepare_for_database_insert(table_name, memory_data, contractor_id)
            
            if not mapped_data or mapped_data.get("contractor_id") is None:
                logger.warning(f"No valid data to save for {table_name}")
                return
            
            # Check if record exists
            existing = self.db.client.table(table_name).select("id").eq(
                "contractor_id", contractor_id
            ).execute()
            
            if existing.data:
                # Update existing - remove contractor_id from update data
                update_data = {k: v for k, v in mapped_data.items() if k != "contractor_id"}
                self.db.client.table(table_name).update(update_data).eq(
                    "contractor_id", contractor_id
                ).execute()
            else:
                # Create new
                self.db.client.table(table_name).insert(mapped_data).execute()
            
            logger.info(f"Saved {table_name} memory for contractor {contractor_id}")
            
        except Exception as e:
            logger.error(f"Error saving {table_name} memory: {e}")
    
    async def _merge_memory(self, current: Dict, new_insights: Dict) -> Dict:
        """Merge new insights with existing memory"""
        merged = current.copy()
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
                merged[key] = value
        
        return merged
    
    async def _get_contractor_profile_data(self, contractor_id: str) -> Optional[Dict]:
        """Get basic contractor profile from contractors table"""
        try:
            result = self.db.client.table("contractors").select(
                "company_name, years_in_business, specialties, lead_score, enrichment_data, certifications"
            ).eq("id", contractor_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting contractor profile: {e}")
            return None
    
    async def create_memory_tables_if_not_exist(self):
        """Create all memory tables if they don't exist"""
        tables = [
            "contractor_relationship_memory",
            "contractor_project_memory", 
            "contractor_communication_memory",
            "contractor_business_memory"
        ]
        
        for table in tables:
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                contractor_id UUID NOT NULL REFERENCES contractors(id),
                memory_data JSONB NOT NULL DEFAULT '{{}}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(contractor_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_{table}_contractor_id 
            ON {table}(contractor_id);
            """
            
            logger.info(f"Memory table SQL for {table}:")
            logger.info(create_sql)