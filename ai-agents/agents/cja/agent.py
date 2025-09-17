"""
Contractor Job Agent (CJA) - Helps contractors find relevant jobs in their area
Uses LLM for natural conversation and radius-based job search
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import requests
from dotenv import load_dotenv
from openai import OpenAI


# Load environment variables from .env file
load_dotenv(override=True)

logger = logging.getLogger(__name__)

@dataclass
class JobSearchCriteria:
    """Criteria for job search extracted from conversation"""
    zip_code: str
    radius_miles: int = 25
    project_types: Optional[list[str]] = None
    min_budget: Optional[int] = None
    max_budget: Optional[int] = None
    keywords: Optional[str] = None

class ContractorJobAgent:
    """Agent that helps contractors find relevant jobs through conversation"""

    def __init__(self, api_key: str = None):
        """Initialize with OpenAI for intelligent conversation"""
        # Use provided key or get from environment
        openai_key = api_key or os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=openai_key)
        
        # Use environment variable or config module for base URL
        try:
            from config.service_urls import get_backend_url
            self.api_base_url = get_backend_url()
        except ImportError:
            import os
            self.api_base_url = os.getenv("BACKEND_URL", get_backend_url())
        
        logger.info(f"Contractor Job Agent initialized with backend at {self.api_base_url}")

        # Conversation memory
        self.conversations = {}

    async def process_message(self, contractor_id: str, message: str,
                            contractor_info: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Process contractor message and help find relevant jobs"""

        logger.info(f"CJA processing message from contractor {contractor_id}: {message}")

        # Get or create conversation history
        if contractor_id not in self.conversations:
            self.conversations[contractor_id] = {
                "messages": [],
                "contractor_info": contractor_info or {},
                "last_search": None
            }

        conversation = self.conversations[contractor_id]
        conversation["messages"].append({"role": "user", "content": message})

        # Use LLM to understand intent and extract search criteria
        understanding = await self._understand_message(message, conversation)

        if understanding["intent"] == "job_search":
            # Perform job search based on extracted criteria
            search_results = await self._search_jobs(understanding["criteria"])

            # Generate response with job recommendations
            response = await self._generate_job_recommendations(
                search_results,
                understanding["criteria"],
                conversation
            )

            # Save search for context
            conversation["last_search"] = {
                "criteria": understanding["criteria"],
                "results": search_results,
                "timestamp": datetime.now().isoformat()
            }

        elif understanding["intent"] == "job_details":
            # Provide more details about a specific job
            response = await self._provide_job_details(
                understanding["job_id"],
                conversation
            )

        elif understanding["intent"] == "refine_search":
            # Refine previous search with new criteria
            response = await self._refine_search(
                understanding["refinements"],
                conversation
            )

        else:
            # General conversation about job hunting
            response = await self._general_conversation(message, conversation)

        # Save assistant response
        conversation["messages"].append({"role": "assistant", "content": response["message"]})

        return {
            "response": response["message"],
            "jobs_found": response.get("jobs", []),
            "search_criteria": response.get("criteria", {}),
            "intent": understanding["intent"],
            "conversation_id": contractor_id
        }

    async def _understand_message(self, message: str, conversation: dict) -> dict[str, Any]:
        """Use LLM to understand contractor's intent and extract search criteria"""

        # Build conversation context
        history = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation["messages"][-5:]  # Last 5 messages
        ])

        contractor_info = conversation.get("contractor_info", {})

        system_prompt = """You are an AI assistant helping contractors find relevant construction jobs.
Analyze the contractor's message and determine their intent and extract job search criteria.

Contractor Information:
- Location: {location}
- Services: {services}
- Experience: {experience}

Previous conversation:
{history}

Determine the intent:
1. "job_search" - Looking for jobs (extract: zip_code, radius_miles, project_types, budget range, keywords)
2. "job_details" - Asking about a specific job (extract: job_id)
3. "refine_search" - Modifying previous search (extract: refinements)
4. "general" - General conversation about job hunting

Return a JSON object with:
{{
    "intent": "job_search|job_details|refine_search|general",
    "criteria": {{
        "zip_code": "contractor's zip code",
        "radius_miles": 25,
        "project_types": ["kitchen", "bathroom"],
        "min_budget": 10000,
        "max_budget": 50000,
        "keywords": "specific keywords mentioned"
    }},
    "job_id": "specific job ID if asking about details",
    "refinements": {{
        "field": "new value"
    }}
}}""".format(
            location=contractor_info.get("location", "Unknown"),
            services=contractor_info.get("services", ["general"]),
            experience=contractor_info.get("years_experience", "Unknown"),
            history=history
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Current message: {message}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )

            result = json.loads(response.choices[0].message.content)
            logger.info(f"CJA Understanding: {result}")
            return result

        except Exception as e:
            logger.error(f"Error understanding message: {e}")
            return {
                "intent": "general",
                "criteria": {},
                "error": str(e)
            }

    async def _search_jobs(self, criteria: dict[str, Any]) -> dict[str, Any]:
        """Search for jobs using the contractor job search API"""

        try:
            # Call the contractor job search API
            params = {
                "zip_code": criteria.get("zip_code", "90210"),
                "radius_miles": criteria.get("radius_miles", 25),
                "page": 1,
                "page_size": 10
            }

            if criteria.get("project_types"):
                params["project_types"] = criteria["project_types"]
            if criteria.get("min_budget"):
                params["min_budget"] = criteria["min_budget"]
            if criteria.get("max_budget"):
                params["max_budget"] = criteria["max_budget"]

            logger.info(f"Searching jobs with params: {params}")

            response = requests.get(
                f"{self.api_base_url}/api/contractor-jobs/search",
                params=params
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Job search failed: {response.status_code} - {response.text}")
                return {"job_opportunities": [], "total": 0, "error": "Search failed"}

        except Exception as e:
            logger.error(f"Error searching jobs: {e}")
            return {"job_opportunities": [], "total": 0, "error": str(e)}

    async def _generate_job_recommendations(self, search_results: dict, criteria: dict,
                                          conversation: dict) -> dict[str, Any]:
        """Generate natural language response with job recommendations"""

        jobs = search_results.get("job_opportunities", [])
        total = search_results.get("total", 0)

        if not jobs:
            return {
                "message": f"I couldn't find any jobs within {criteria.get('radius_miles', 25)} miles of {criteria.get('zip_code', 'your area')}. Would you like me to expand the search radius or look for different project types?",
                "jobs": [],
                "criteria": criteria
            }

        # Format job details for LLM
        job_summaries = []
        for i, job in enumerate(jobs[:5], 1):
            summary = f"""
{i}. {job.get('title', 'Untitled Project')}
   Location: {job['location']['city']}, {job['location']['state']} ({job['distance_miles']:.1f} miles away)
   Budget: ${job['budget_range']['min']:,} - ${job['budget_range']['max']:,}
   Type: {job['project_type']}
   Timeline: {job['timeline']['start_date']} to {job['timeline']['end_date']}
   Description: {job.get('description', 'No description')[:150]}...
"""
            job_summaries.append(summary)

        system_prompt = """You are a helpful contractor's assistant. Generate a natural, conversational response 
about the job opportunities found. Be encouraging and highlight the most relevant aspects based on the 
contractor's search criteria. Keep the response concise but informative."""

        user_prompt = f"""Found {total} jobs within {criteria.get('radius_miles', 25)} miles of {criteria.get('zip_code', 'the area')}.

Here are the top matches:
{''.join(job_summaries)}

Search criteria used:
- Location: {criteria.get('zip_code', 'Not specified')}
- Radius: {criteria.get('radius_miles', 25)} miles
- Project types: {criteria.get('project_types', 'All types')}
- Budget range: ${criteria.get('min_budget', 0):,} - ${criteria.get('max_budget', 'No limit')}

Generate a helpful response that:
1. Summarizes what was found
2. Highlights the most promising opportunities
3. Suggests next steps (view details, submit bids, refine search)"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return {
                "message": response.choices[0].message.content,
                "jobs": jobs[:5],
                "criteria": criteria,
                "total_found": total
            }

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            # Fallback response
            return {
                "message": f"I found {total} jobs in your area! The closest one is {jobs[0]['title']} in {jobs[0]['location']['city']}, just {jobs[0]['distance_miles']:.1f} miles away with a budget of ${jobs[0]['budget_range']['min']:,}-${jobs[0]['budget_range']['max']:,}. Would you like to see more details or submit a bid?",
                "jobs": jobs[:5],
                "criteria": criteria,
                "total_found": total
            }

    async def _provide_job_details(self, job_id: str, conversation: dict) -> dict[str, Any]:
        """Provide detailed information about a specific job"""

        # Check if we have the job in recent search results
        last_search = conversation.get("last_search", {})
        jobs = last_search.get("results", {}).get("job_opportunities", [])

        job = None
        for j in jobs:
            if j.get("id") == job_id or j.get("bid_card_number") == job_id:
                job = j
                break

        if not job:
            return {
                "message": "I don't have information about that specific job. Could you tell me more about which job you're interested in?",
                "jobs": []
            }

        # Generate detailed response about the job
        detailed_message = f"""Here are the complete details for this project:

**{job.get('title', 'Untitled Project')}**

📍 **Location**: {job['location']['city']}, {job['location']['state']} {job['location']['zip_code']}
📏 **Distance**: {job.get('distance_miles', 'Unknown'):.1f} miles from your location

💰 **Budget**: ${job['budget_range']['min']:,} - ${job['budget_range']['max']:,}
📅 **Timeline**: {job['timeline']['start_date']} to {job['timeline']['end_date']}
🔨 **Project Type**: {job['project_type']}
🏷️ **Categories**: {', '.join(job.get('categories', []))}

**Description**:
{job.get('description', 'No description available')}

**Additional Details**:
- Contractors needed: {job.get('contractor_count_needed', 'Unknown')}
- Current bids: {job.get('bid_count', 0)}
- Group bid eligible: {'Yes' if job.get('group_bid_eligible') else 'No'}

Would you like to submit a bid for this project? I can help you prepare a competitive proposal."""

        return {
            "message": detailed_message,
            "jobs": [job]
        }

    async def _refine_search(self, refinements: dict, conversation: dict) -> dict[str, Any]:
        """Refine the previous search with new criteria"""

        last_search = conversation.get("last_search", {})
        if not last_search:
            return {
                "message": "I don't have a previous search to refine. What kind of jobs are you looking for?",
                "jobs": []
            }

        # Update criteria with refinements
        criteria = last_search.get("criteria", {})
        criteria.update(refinements)

        # Perform new search
        search_results = await self._search_jobs(criteria)

        # Generate response
        return await self._generate_job_recommendations(search_results, criteria, conversation)

    async def _general_conversation(self, message: str, conversation: dict) -> dict[str, Any]:
        """Handle general conversation about job hunting"""

        system_prompt = """You are a helpful contractor's assistant specializing in helping contractors 
find construction jobs. Provide helpful advice about job hunting, bidding strategies, and using the 
InstaBids platform effectively. Keep responses concise and actionable."""

        # Include recent conversation context
        recent_messages = conversation["messages"][-3:]
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Recent conversation:\n{context}\n\nCurrent message: {message}"}
                ],
                temperature=0.7,
                max_tokens=300
            )

            return {
                "message": response.choices[0].message.content,
                "jobs": []
            }

        except Exception as e:
            logger.error(f"Error in general conversation: {e}")
            return {
                "message": "I'm here to help you find construction jobs in your area. What type of projects are you looking for?",
                "jobs": []
            }
