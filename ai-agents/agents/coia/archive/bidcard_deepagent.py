"""
Bid-Card Signup DeepAgent for COIA

Creates a DeepAgents-powered agent focused on the authenticated email link flow:
- Preload full contractor context (profile, bid history, available projects) via adapter
- Offer relevant actions (view opportunities, complete profile, create account with consent)
- Optionally perform additional research on request
- Enforce strict consent before account creation
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from deepagents import create_deep_agent
except Exception as _e:  # Do not crash import-time
    create_deep_agent = None  # type: ignore

from .deepagents_tools import (
    get_contractor_context,
    search_bid_cards,
    create_contractor_account,
    research_business,  # optional on request
)

logger = logging.getLogger(__name__)

_agent = None  # cached instance


def _instructions() -> str:
    """
    System prompt for Bid-Card Agent.
    """
    return """
You are COIA (BidCard Email Link), the Contractor Onboarding & Bidding Assistant.

Context:
- The contractor reached us via a secure email link for a specific bid/project.
- Their context (profile, bid history, available projects) is available via get_contractor_context.

Your job:
- First preload the contractor context using get_contractor_context(lead_id, session_id) if not already provided.
- Use the profile and available_projects to recommend next steps:
  - Show or filter relevant projects (use search_bid_cards as needed)
  - Help complete the profile if critical fields are missing
  - Only if the user explicitly consents, create an account (use create_contractor_account)

Rules:
- NEVER create an account without explicit consent. Ask clearly for permission first.
- Prefer known contractor data from context rather than re-researching; do research_business only if the user asks.
- Stay concise and specific. Avoid hallucinations; if unknown, state it honestly.

Outputs:
- Summarize key profile status (e.g., completeness, missing fields)
- Provide project recommendations when relevant
- If user requests, guide through account creation steps and only then call create_contractor_account
"""


def get_agent() -> Any:
    """
    Returns a cached DeepAgents agent instance for the bid-card flow.
    Safe to call repeatedly.
    """
    global _agent
    if _agent is not None:
        return _agent

    if create_deep_agent is None:
        raise RuntimeError(
            "deepagents is not installed or import failed. "
            "Install with `pip install deepagents` and ensure environment is configured."
        )

    tools = [
        get_contractor_context,
        search_bid_cards,
        create_contractor_account,
        research_business,  # optional enrichment on explicit user request
    ]

    # Specialized subagent for bidding guidance (optional)
    bid_subagent = {
        "name": "bid-agent",
        "description": "Helps contractors evaluate projects and prepare to bid.",
        "prompt": (
            "You are a bidding guidance agent. Use get_contractor_context first if needed. "
            "Help the contractor find relevant projects (search_bid_cards) and guide them with clear steps. "
            "Do not create accounts without explicit consent."
        ),
    }

    _agent = create_deep_agent(
        tools=tools,
        instructions=_instructions(),
        subagents=[bid_subagent],
    )
    logger.info("BidCard DeepAgent created")
    return _agent


# Usage example (caller responsibility):
# agent = get_agent()
# ctx = get_contractor_context("lead-uuid", "sess-123")
# result = agent.invoke({
#   "messages": [{"role": "user", "content": "I'm interested in that turf project from the email"}],
#   "context": ctx
# })
# The router should pass contractor_lead_id/session_id and optionally merge ctx into the agent input.
