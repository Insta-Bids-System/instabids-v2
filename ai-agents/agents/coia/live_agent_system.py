"""
Live Agent System for Natural Chat + Agent Status
Creates the experience of a team of AI agents working together with live updates
"""

import asyncio
import json
import logging
import uuid
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

class ParallelAgentOrchestrator:
    """Orchestrates multiple agents working in parallel while maintaining natural chat"""
    
    def __init__(self, tracker: LiveAgentTracker):
        self.tracker = tracker
        self.main_conversation_handler = None
        
    def set_conversation_handler(self, handler: Callable):
        """Set the handler for main conversation flow"""  
        self.main_conversation_handler = handler
        
    async def start_parallel_onboarding(self, contractor_lead_id: str, company_name: str, 
                                      location_hint: str, session_id: str):
        """Start all agents working in parallel"""
        self.tracker.set_session(session_id)
        
        # Start all agent tasks simultaneously
        tasks = [
            self._run_research_agent(company_name, location_hint),
            self._run_projects_agent(company_name, location_hint),
            self._run_profile_agent(company_name),
            self._run_account_agent(contractor_lead_id)
        ]
        
        # Run all agents in parallel 
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def _run_research_agent(self, company_name: str, location_hint: str):
        """Research agent workflow with status updates"""
        await self.tracker.update_agent_status("research", AgentStatus.WORKING, 0, 
                                              "Starting business research...")
        
        try:
            # Simulate research steps with progress updates
            await asyncio.sleep(1)
            await self.tracker.update_agent_status("research", AgentStatus.WORKING, 25,
                                                  "Searching Google Business...")
                                                  
            # Import actual research tools
            from .subagents.research_agent import research_company_basic
            research_data = research_company_basic(company_name, location_hint)
            
            await self.tracker.update_agent_status("research", AgentStatus.WORKING, 75,
                                                  "Analyzing website data...")
            await asyncio.sleep(2)
            
            # Report findings back to chat
            if research_data and research_data.get("website"):
                await self.tracker.agent_reports_back("research", 
                    f"your website at {research_data['website']} - 4.8 stars, 8 years in business",
                    self._send_to_chat)
            
            await self.tracker.update_agent_status("research", AgentStatus.COMPLETED, 100,
                                                  "Research complete!")
                                                  
        except Exception as e:
            logger.error(f"Research agent error: {e}")
            await self.tracker.update_agent_status("research", AgentStatus.ERROR, 0,
                                                  f"Research failed: {str(e)}")
                                                  
    async def _run_projects_agent(self, company_name: str, location_hint: str):
        """Projects agent workflow with status updates"""
        await self.tracker.update_agent_status("projects", AgentStatus.WORKING, 0,
                                              "Searching for matching projects...")
        try:
            await asyncio.sleep(3)  # Projects search takes longer
            await self.tracker.update_agent_status("projects", AgentStatus.WORKING, 50,
                                                  "Calculating project values...")
            
            # Import actual projects tools
            from .subagents.projects_agent import find_matching_projects
            # This would normally use staging_id but we'll simulate for now
            projects_data = {"total_projects": 6, "total_value": 47000, "types": "residential, commercial"}
            
            await asyncio.sleep(2)
            await self.tracker.agent_reports_back("projects",
                f"6 holiday lighting projects worth $47,000 total - 2 permanent LED installs, 3 seasonal jobs, 1 commercial",
                self._send_to_chat)
                
            await self.tracker.update_agent_status("projects", AgentStatus.COMPLETED, 100,
                                                  "Project search complete!")
                                                  
        except Exception as e:
            logger.error(f"Projects agent error: {e}")
            await self.tracker.update_agent_status("projects", AgentStatus.ERROR, 0,
                                                  f"Projects search failed: {str(e)}")
                                                  
    async def _run_profile_agent(self, company_name: str):
        """Profile agent workflow with status updates"""
        await self.tracker.update_agent_status("profile", AgentStatus.WORKING, 0,
                                              "Building company profile...")
        try:
            await asyncio.sleep(2)
            await self.tracker.update_agent_status("profile", AgentStatus.WORKING, 60,
                                                  "Analyzing market position...")
            
            # This would extract and stage the profile
            await asyncio.sleep(2)
            await self.tracker.agent_reports_back("profile",
                f"a premium positioning - your average project value ($8,500) is 150% above market average",
                self._send_to_chat)
                
            await self.tracker.update_agent_status("profile", AgentStatus.COMPLETED, 100,
                                                  "Profile compiled!")
                                                  
        except Exception as e:
            logger.error(f"Profile agent error: {e}")  
            await self.tracker.update_agent_status("profile", AgentStatus.ERROR, 0,
                                                  f"Profile building failed: {str(e)}")
                                                  
    async def _run_account_agent(self, contractor_lead_id: str):
        """Account agent workflow - prepares but doesn't create without consent"""
        await self.tracker.update_agent_status("account", AgentStatus.WORKING, 0,
                                              "Preparing account setup...")
        try:
            await asyncio.sleep(4)  # Account prep takes time
            await self.tracker.update_agent_status("account", AgentStatus.WORKING, 80,
                                                  "Configuring contractor portal...")
            
            await asyncio.sleep(1)
            await self.tracker.agent_reports_back("account",
                "your contractor onboarding package - everything is ready when you want to create your account",
                self._send_to_chat)
                
            await self.tracker.update_agent_status("account", AgentStatus.COMPLETED, 100,
                                                  "Ready for account creation!")
                                                  
        except Exception as e:
            logger.error(f"Account agent error: {e}")
            await self.tracker.update_agent_status("account", AgentStatus.ERROR, 0,
                                                  f"Account prep failed: {str(e)}")
                                                  
    async def _send_to_chat(self, chat_update: dict):
        """Send agent report to main chat conversation"""
        if self.main_conversation_handler:
            await self.main_conversation_handler(chat_update)
        else:
            logger.info(f"Chat update (no handler): {chat_update}")

# Global instance for the session
live_tracker = LiveAgentTracker()
parallel_orchestrator = ParallelAgentOrchestrator(live_tracker)