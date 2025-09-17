"""
Live Agent Orchestrator for COIA - Separate from DeepAgent
Handles parallel agent coordination and WebSocket status updates
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"  
    COMPLETED = "completed"
    ERROR = "error"

class AgentPersonality:
    """Defines how each agent presents itself and reports back"""
    
    RESEARCH_AGENT = {
        "name": "Research Agent",
        "emoji": "🔍",
        "personality": "detective",
        "working_messages": [
            "Investigating your business...",
            "Searching Google Business listings...",
            "Analyzing company website...",
            "Cross-referencing business data..."
        ],
        "report_templates": [
            "I discovered {finding}",
            "My investigation shows {finding}",
            "I found evidence that {finding}",
            "Research confirms {finding}"
        ]
    }
    
    PROJECTS_AGENT = {
        "name": "Projects Agent", 
        "emoji": "🎯",
        "personality": "opportunity_hunter",
        "working_messages": [
            "Hunting for matching projects...",
            "Scanning available opportunities...", 
            "Calculating project values...",
            "Mapping project locations..."
        ],
        "report_templates": [
            "I located {finding}",
            "I spotted {finding}",
            "There's potential for {finding}",
            "I identified {finding}"
        ]
    }
    
    PROFILE_AGENT = {
        "name": "Profile Agent",
        "emoji": "📊", 
        "personality": "data_organizer",
        "working_messages": [
            "Compiling business profile...",
            "Organizing company data...",
            "Calculating market position...",
            "Building competitive analysis..."
        ],
        "report_templates": [
            "I've compiled {finding}",
            "Your profile shows {finding}",
            "The data indicates {finding}",
            "Analysis reveals {finding}"
        ]
    }
    
    ACCOUNT_AGENT = {
        "name": "Account Agent",
        "emoji": "💼",
        "personality": "onboarding_specialist", 
        "working_messages": [
            "Preparing onboarding setup...",
            "Configuring account options...",
            "Setting up contractor portal...",
            "Finalizing registration details..."
        ],
        "report_templates": [
            "I've prepared {finding}",
            "Your setup includes {finding}",
            "I recommend {finding}",
            "Ready to activate {finding}"
        ]
    }

class LiveAgentTracker:
    """Tracks status of all agents and broadcasts updates"""
    
    def __init__(self):
        self.agents = {
            "research": {"status": AgentStatus.IDLE, "progress": 0, "message": "", "results": []},
            "projects": {"status": AgentStatus.IDLE, "progress": 0, "message": "", "results": []},  
            "profile": {"status": AgentStatus.IDLE, "progress": 0, "message": "", "results": []},
            "account": {"status": AgentStatus.IDLE, "progress": 0, "message": "", "results": []}
        }
        self.session_id = None
        self.update_callbacks = []
        
    def add_update_callback(self, callback: Callable):
        """Add callback function to receive status updates"""
        self.update_callbacks.append(callback)
        
    def set_session(self, session_id: str):
        """Set the session ID for this tracking instance"""
        self.session_id = session_id
        
    async def update_agent_status(self, agent_name: str, status: AgentStatus, 
                                progress: int = None, message: str = None, result: dict = None):
        """Update an agent's status and broadcast to callbacks"""
        if agent_name not in self.agents:
            return
            
        agent = self.agents[agent_name]
        agent["status"] = status
        
        if progress is not None:
            agent["progress"] = progress
        if message is not None:
            agent["message"] = message
        if result is not None:
            agent["results"].append(result)
            
        # Broadcast update
        update = {
            "type": "agent_status_update",
            "session_id": self.session_id,
            "agent": agent_name,
            "status": status.value,
            "progress": agent["progress"], 
            "message": agent["message"],
            "timestamp": datetime.now().isoformat()
        }
        
        for callback in self.update_callbacks:
            try:
                await callback(update)
            except Exception as e:
                logger.error(f"Error in update callback: {e}")
                
    async def agent_reports_back(self, agent_name: str, finding: str, chat_callback: Callable):
        """Agent reports discovery back to main chat"""
        if agent_name not in self.agents:
            return
            
        personality = getattr(AgentPersonality, f"{agent_name.upper()}_AGENT")
        emoji = personality["emoji"]
        name = personality["name"] 
        templates = personality["report_templates"]
        
        # Pick random report template
        import random
        template = random.choice(templates)
        report_message = f"{emoji} {name}: \"{template.format(finding=finding)}\""
        
        # Send to main chat
        chat_update = {
            "type": "agent_report",
            "session_id": self.session_id,
            "agent": agent_name,
            "message": report_message,
            "finding": finding,
            "timestamp": datetime.now().isoformat()
        }
        
        await chat_callback(chat_update)
        
    def get_status_summary(self) -> dict:
        """Get current status of all agents"""
        return {
            "session_id": self.session_id,
            "agents": self.agents,
            "timestamp": datetime.now().isoformat()
        }

# Global live tracker instance
live_tracker = LiveAgentTracker()

# Placeholder for chat broadcast function
_broadcast_to_chat = None

async def trigger_parallel_agents(company_name: str, location_hint: str, session_id: str, staging_id: str = None):
    """Trigger parallel agent processing with proper error handling"""
    
    live_tracker.set_session(session_id)
    
    # Wrapper for safe execution
    async def safe_run_agent(agent_func, agent_name, *args):
        try:
            logger.info(f"Starting {agent_name}...")
            result = await agent_func(*args)
            logger.info(f"{agent_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{agent_name} failed: {e}")
            # Update tracker with error status
            live_tracker.update_agent_status(
                agent_name.lower().replace(" ", "_"),
                AgentStatus.ERROR,
                0,
                f"Error: {str(e)}"
            )
            return {"error": str(e), "agent": agent_name}
    
    # Start all agents with error handling
    tasks = [
        safe_run_agent(_run_research_agent_live, "Research Agent", company_name, location_hint),
        safe_run_agent(_run_projects_agent_live, "Projects Agent", staging_id, company_name, location_hint),
        safe_run_agent(_run_profile_agent_live, "Profile Agent", company_name),
        safe_run_agent(_run_account_agent_live, "Account Agent", staging_id)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=False)
    
    # Log summary
    successful = [r for r in results if not isinstance(r, dict) or "error" not in r]
    failed = [r for r in results if isinstance(r, dict) and "error" in r]
    
    logger.info(f"Parallel agents completed: {len(successful)} successful, {len(failed)} failed")
    
    return results
    

async def _run_research_agent_live(company_name: str, location_hint: str):
    """Research agent with live status updates using DeepAgents tools"""
    await live_tracker.update_agent_status("research", AgentStatus.WORKING, 0, 
                                          "Starting business research...")
    
    try:
        from .subagents.identity_agent import extract_company_info, validate_company_exists
        from .subagents.research_agent import research_company_basic, extract_contractor_profile
        
        # Step 1: Extract company info
        await live_tracker.update_agent_status("research", AgentStatus.WORKING, 20,
                                              "Extracting company information...")
        company_info = extract_company_info(f"{company_name} in {location_hint}")
        
        # Step 2: Validate company exists
        await live_tracker.update_agent_status("research", AgentStatus.WORKING, 40,
                                              "Validating business existence...")
        validation = validate_company_exists(company_name, location_hint)
        
        # Step 3: Research company basic data
        await live_tracker.update_agent_status("research", AgentStatus.WORKING, 60,
                                              "Researching company details...")
        research_data = research_company_basic(company_name, location_hint)
        
        # Step 4: Report findings back
        await live_tracker.update_agent_status("research", AgentStatus.WORKING, 95,
                                              "Finalizing research...")
        
        if research_data and research_data.get("website"):
            finding = f"verified {company_name} - website {research_data['website']}"
            if _broadcast_to_chat:
                await live_tracker.agent_reports_back("research", finding, _broadcast_to_chat)
        
        await live_tracker.update_agent_status("research", AgentStatus.COMPLETED, 100,
                                              "Research complete!")
                                              
    except Exception as e:
        logger.error(f"Research agent error: {e}")
        await live_tracker.update_agent_status("research", AgentStatus.ERROR, 0,
                                              f"Research failed: {str(e)}")

async def _run_projects_agent_live(staging_id: str, company_name: str, location_hint: str):
    """Projects agent with live status updates using DeepAgents tools"""
    await live_tracker.update_agent_status("projects", AgentStatus.WORKING, 0,
                                          "Searching for matching projects...")
    try:
        from .subagents.projects_agent import find_matching_projects
        
        # Call actual projects search if staging_id available
        if staging_id:
            projects_data = find_matching_projects(staging_id)
            
            await live_tracker.update_agent_status("projects", AgentStatus.WORKING, 70,
                                                  "Calculating project values...")
            
            # Extract project insights
            if projects_data and isinstance(projects_data, dict):
                total_projects = projects_data.get("total_projects", 0)
                total_value = projects_data.get("total_value", 0)
                
                if total_projects > 0:
                    finding = f"{total_projects} matching projects worth ${total_value:,.0f} total"
                    if _broadcast_to_chat:
                        await live_tracker.agent_reports_back("projects", finding, _broadcast_to_chat)
        else:
            finding = "profile setup needed first - I'll search once we have your service details"
            if _broadcast_to_chat:
                await live_tracker.agent_reports_back("projects", finding, _broadcast_to_chat)
        
        await live_tracker.update_agent_status("projects", AgentStatus.COMPLETED, 100,
                                              "Project search complete!")
                                              
    except Exception as e:
        logger.error(f"Projects agent error: {e}")
        await live_tracker.update_agent_status("projects", AgentStatus.ERROR, 0,
                                              f"Projects search failed: {str(e)}")

async def _run_profile_agent_live(company_name: str):
    """Profile agent with live status updates using DeepAgents tools"""
    await live_tracker.update_agent_status("profile", AgentStatus.WORKING, 0,
                                          "Building company profile...")
    try:
        from .subagents.research_agent import research_company_basic, extract_contractor_profile, stage_profile
        
        # Step 1: Research company data
        await live_tracker.update_agent_status("profile", AgentStatus.WORKING, 25,
                                              "Gathering company data...")
        research_data = research_company_basic(company_name, "")
        
        # Step 2: Extract contractor profile with AI
        await live_tracker.update_agent_status("profile", AgentStatus.WORKING, 50,
                                              "AI profile extraction...")
        profile_data = extract_contractor_profile(research_data, company_name)
        
        # Step 3: Stage the profile
        await live_tracker.update_agent_status("profile", AgentStatus.WORKING, 75,
                                              "Staging profile data...")
        staging_result = stage_profile(profile_data, company_name)
        
        # Step 4: Report profile insights
        await live_tracker.update_agent_status("profile", AgentStatus.WORKING, 90,
                                              "Analyzing market position...")
        
        if staging_result and staging_result.get("staging_id"):
            services = profile_data.get("services", [])
            service_count = len(services) if isinstance(services, list) else 0
            
            finding = f"staged profile with {service_count} services - ready for project matching"
            if _broadcast_to_chat:
                await live_tracker.agent_reports_back("profile", finding, _broadcast_to_chat)
        
        await live_tracker.update_agent_status("profile", AgentStatus.COMPLETED, 100,
                                              "Profile compiled!")
                                              
    except Exception as e:
        logger.error(f"Profile agent error: {e}")  
        await live_tracker.update_agent_status("profile", AgentStatus.ERROR, 0,
                                              f"Profile building failed: {str(e)}")

async def _run_account_agent_live(staging_id: str):
    """Account agent with live status updates - prepares but waits for consent"""
    await live_tracker.update_agent_status("account", AgentStatus.WORKING, 0,
                                          "Preparing account setup...")
    try:
        if staging_id:
            # Profile exists - prepare account options
            await live_tracker.update_agent_status("account", AgentStatus.WORKING, 60,
                                                  "Preparing contractor portal...")
            
            await live_tracker.update_agent_status("account", AgentStatus.WORKING, 90,
                                                  "Finalizing setup package...")
            
            finding = "your contractor account package ready - just say the word and I'll activate it instantly"
            if _broadcast_to_chat:
                await live_tracker.agent_reports_back("account", finding, _broadcast_to_chat)
        else:
            finding = "waiting for profile completion before preparing your account"
            if _broadcast_to_chat:
                await live_tracker.agent_reports_back("account", finding, _broadcast_to_chat)
        
        await live_tracker.update_agent_status("account", AgentStatus.COMPLETED, 100,
                                              "Ready for account creation!")
                                              
    except Exception as e:
        logger.error(f"Account agent error: {e}")
        await live_tracker.update_agent_status("account", AgentStatus.ERROR, 0,
                                              f"Account prep failed: {str(e)}")

def set_broadcast_callback(callback: Callable):
    """Set the broadcast callback for agent reports"""
    global _broadcast_to_chat
    _broadcast_to_chat = callback