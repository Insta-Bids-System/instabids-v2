"""Offline tests for the BSA DeepAgents streaming entry point."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List

import pytest

from agents.bsa.context_cache import bsa_context_cache
from agents.bsa import bsa_deepagents


@pytest.fixture(autouse=True)
def clear_bsa_cache():
    """Ensure cached contractor data does not leak between tests."""
    bsa_context_cache.clear()
    yield
    bsa_context_cache.clear()


@dataclass
class StubSupabaseDB:
    """Collects conversation saves performed by the agent."""

    saved: List[Dict[str, Any]]

    def __bool__(self) -> bool:  # pragma: no cover - trivial
        return True

    async def save_unified_conversation(self, payload: Dict[str, Any]) -> bool:
        self.saved.append(payload)
        return True


class StubMyBidsService:
    def __init__(self) -> None:
        self.tracked: List[Dict[str, Any]] = []

    async def load_full_my_bids_context(self, contractor_id: str) -> Dict[str, Any]:
        return {
            "total_my_bids": 1,
            "my_bids": [
                {
                    "bid_card_id": "BID-123",
                    "status": "viewed",
                    "last_interaction": "2025-01-01T00:00:00Z",
                    "messages": [],
                    "proposals": [],
                }
            ],
        }

    async def track_bid_interaction(
        self,
        contractor_id: str,
        bid_card_id: str,
        interaction_type: str,
        details: Dict[str, Any] | None = None,
    ) -> bool:
        self.tracked.append(
            {
                "contractor_id": contractor_id,
                "bid_card_id": bid_card_id,
                "interaction_type": interaction_type,
                "details": details,
            }
        )
        return True


class StubContractorContextAdapter:
    def get_contractor_context(self, contractor_id: str, session_id: str | None = None) -> Dict[str, Any]:
        return {
            "contractor_profile": {"name": "Stub Contractor", "id": contractor_id},
            "submitted_bids": [],
        }


class DirectResponseSingleton:
    """Singleton stub that returns a direct assistant message."""

    @classmethod
    async def get_instance(cls) -> "DirectResponseSingleton":
        return cls()

    @classmethod
    def get_thread_id(cls, contractor_id: str, session_id: str | None) -> str:
        return f"thread-{contractor_id}-{session_id}"

    async def invoke(self, state: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
        # Ensure injected context flowed into the state.
        assert state["contractor_context"]["contractor_profile"]["name"] == "Stub Contractor"
        assert state["my_bids_context"]["total_my_bids"] == 1
        return {
            "messages": [
                {"role": "assistant", "content": "Direct stub response"},
            ]
        }

    async def stream(self, state: Dict[str, Any], thread_id: str):  # pragma: no cover - not used in this test
        yield {}


class FallbackStreamingSingleton:
    """Singleton stub that forces the streaming fallback path."""

    @classmethod
    async def get_instance(cls) -> "FallbackStreamingSingleton":
        return cls()

    @classmethod
    def get_thread_id(cls, contractor_id: str, session_id: str | None) -> str:
        return "fallback-thread"

    async def invoke(self, state: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
        # Return an empty payload so the code falls back to streaming.
        return {"messages": []}

    async def stream(self, state: Dict[str, Any], thread_id: str):
        yield {"messages": [{"role": "assistant", "content": "Fallback stub response"}]}
        await asyncio.sleep(0)
        yield {"messages": [{"role": "assistant", "content": "Fallback stub response"}]}


@pytest.mark.asyncio
async def test_bsa_stream_direct_path(monkeypatch):
    """The direct invocation path should stream assistant text and persist via the helper."""

    saved_results: List[Dict[str, Any]] = []

    async def record_save(result_data, contractor_id, session_id, message, response_content):
        saved_results.append(
            {
                "result": result_data,
                "contractor_id": contractor_id,
                "session_id": session_id,
                "message": message,
                "response": response_content,
            }
        )

    monkeypatch.setattr("agents.bsa.bsa_singleton.BSASingleton", DirectResponseSingleton)
    monkeypatch.setattr(bsa_deepagents, "save_conversation_result", record_save)

    supabase = StubSupabaseDB(saved=[])
    my_bids = StubMyBidsService()
    contractor_adapter = StubContractorContextAdapter()

    chunks: List[Dict[str, Any]] = []
    async for chunk in bsa_deepagents.bsa_deepagent_stream(
        contractor_id="contractor-1",
        message="Hello there",
        conversation_history=[{"role": "user", "content": "Hi"}],
        session_id="session-1",
        supabase_db=supabase,
        contractor_context_adapter=contractor_adapter,
        my_bids_service=my_bids,
    ):
        chunks.append(chunk)

    assert chunks, "expected streamed chunks"
    assert chunks[-1].get("done") is True
    assert saved_results, "save_conversation_result should be invoked"
    assert saved_results[0]["response"] == "Direct stub response"


@pytest.mark.asyncio
async def test_bsa_stream_fallback_tracks_bid_and_saves(monkeypatch):
    """When the singleton cannot provide a direct response, the fallback stream should run."""

    monkeypatch.setattr("agents.bsa.bsa_singleton.BSASingleton", FallbackStreamingSingleton)

    async def noop_save(*_args, **_kwargs):
        return None

    monkeypatch.setattr(bsa_deepagents, "save_conversation_result", noop_save)

    supabase = StubSupabaseDB(saved=[])
    my_bids = StubMyBidsService()
    contractor_adapter = StubContractorContextAdapter()

    chunks: List[Dict[str, Any]] = []
    async for chunk in bsa_deepagents.bsa_deepagent_stream(
        contractor_id="contractor-2",
        message="Show me my bids",
        session_id="session-xyz",
        bid_card_id="bid-42",
        supabase_db=supabase,
        contractor_context_adapter=contractor_adapter,
        my_bids_service=my_bids,
    ):
        chunks.append(chunk)

    assert chunks, "expected streamed chunks"
    assert chunks[-1].get("done") is True
    assert any("Fallback stub response" in chunk["choices"][0]["delta"]["content"] for chunk in chunks if "choices" in chunk)
    assert supabase.saved, "conversation should be persisted via injected Supabase client"
    assert my_bids.tracked, "bid interaction should be tracked when bid_card_id provided"
