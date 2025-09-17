import types
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agents.cia.agent import CustomerInterfaceAgent
from routers import cia_routes_unified


class _DummyResponse:
    def __init__(self, content: str = "Test response", tool_calls=None):
        message = types.SimpleNamespace(content=content, tool_calls=tool_calls)
        choice = types.SimpleNamespace(message=message)
        self.choices = [choice]


class _DummyChatClient:
    def __init__(self):
        self.calls = []
        completions = types.SimpleNamespace()

        async def _create(**kwargs):
            self.calls.append(kwargs)
            return _DummyResponse()

        completions.create = _create
        self.chat = types.SimpleNamespace(completions=completions)


class _DummyBidCards:
    async def create_potential_bid_card(self, **_kwargs):
        return "bid-123"

    async def get_bid_card_status(self, *_args, **_kwargs):
        return {"completion_percentage": 75}


class _DummyDB:
    def __init__(self):
        self.saved_state = None

    async def load_conversation_state(self, _session_id):
        return {"messages": [{"role": "assistant", "content": "Earlier"}]}

    async def save_conversation_state(self, **kwargs):
        self.saved_state = kwargs["state"]
        return {"state": kwargs["state"]}


@pytest.mark.asyncio
async def test_handle_conversation_app_profile_loads_user_context(monkeypatch):
    """The app profile should pull user context and persist profile metadata."""

    monkeypatch.setattr("agents.cia.agent.AsyncOpenAI", lambda *args, **kwargs: _DummyChatClient())

    agent = CustomerInterfaceAgent(api_key="test")

    dummy_store_calls = []

    async def _get_user_context(user_id: str):
        dummy_store_calls.append(user_id)
        return {"new_user": False, "context": "loaded"}

    agent.store.get_user_context = _get_user_context  # type: ignore[assignment]
    agent.bid_cards = _DummyBidCards()
    dummy_db = _DummyDB()
    agent.db = dummy_db  # type: ignore[assignment]
    agent.client = _DummyChatClient()  # type: ignore[assignment]

    result = await agent.handle_conversation(
        user_id="user-123",
        message="Hi there",
        session_id="session-1",
        profile="app",
        conversation_id="conv-1",
    )

    assert dummy_store_calls == ["user-123"]
    assert dummy_db.saved_state is not None
    assert dummy_db.saved_state.get("profile") == "app"
    assert result["profile_used"] == "app"
    assert agent.client.calls, "OpenAI client should be called"
    app_tools = {tool["function"]["name"] for tool in agent.client.calls[-1]["tools"]}
    assert app_tools == {"update_bid_card", "categorize_project"}


@pytest.mark.asyncio
async def test_handle_conversation_landing_profile_skips_user_context(monkeypatch):
    """Landing profile should not attempt to load authenticated user context."""

    monkeypatch.setattr("agents.cia.agent.AsyncOpenAI", lambda *args, **kwargs: _DummyChatClient())

    agent = CustomerInterfaceAgent(api_key="test")

    async def _get_user_context(_user_id: str):  # pragma: no cover - should not run
        raise AssertionError("Landing profile should not request user context")

    agent.store.get_user_context = _get_user_context  # type: ignore[assignment]
    agent.bid_cards = _DummyBidCards()
    dummy_db = _DummyDB()
    agent.db = dummy_db  # type: ignore[assignment]
    agent.client = _DummyChatClient()  # type: ignore[assignment]

    result = await agent.handle_conversation(
        user_id=None,
        message="Hi there",
        session_id="session-landing",
        profile="landing",
        conversation_id="conv-landing",
    )

    assert dummy_db.saved_state is not None
    assert dummy_db.saved_state.get("profile") == "landing"
    assert result["profile_used"] == "landing"
    assert agent.client.calls, "OpenAI client should be called"
    landing_tools = {tool["function"]["name"] for tool in agent.client.calls[-1]["tools"]}
    assert landing_tools == {"update_bid_card"}


def test_get_system_prompt_varies_by_profile(monkeypatch):
    """System prompt should include profile-specific guidance."""

    monkeypatch.setattr("agents.cia.agent.AsyncOpenAI", lambda *args, **kwargs: _DummyChatClient())

    agent = CustomerInterfaceAgent(api_key="test")

    landing_prompt = agent._get_system_prompt({}, profile="landing")
    app_prompt = agent._get_system_prompt({}, profile="app")

    assert "LANDING PROFILE INSTRUCTIONS" in landing_prompt
    assert "APP PROFILE INSTRUCTIONS" in app_prompt
    assert "ANONYMOUS" in landing_prompt
    assert "LOGGED IN" in app_prompt


def test_router_profile_endpoints(monkeypatch):
    """Landing and app endpoints should enforce the expected profiles."""

    async def _load_state(_session_id):
        return None

    dummy_agent_calls = []

    class _DummyAgent:
        async def handle_conversation(self, **kwargs):
            dummy_agent_calls.append(kwargs)
            return {"response": "hello", "tool_calls": [], "bid_card_id": None}

    class _AsyncOpenAI:
        def __init__(self, *args, **kwargs):
            pass

    async def _sleep(_delay):
        return None

    async def _wait_for(coro, *_args, **_kwargs):
        return await coro

    dummy_cost_tracker = types.SimpleNamespace(track_llm_call_sync=lambda *a, **k: None)

    monkeypatch.setattr(cia_routes_unified.db, "load_conversation_state", _load_state)
    monkeypatch.setattr(cia_routes_unified, "AsyncOpenAI", _AsyncOpenAI, raising=False)
    monkeypatch.setattr(cia_routes_unified.asyncio, "sleep", _sleep)
    monkeypatch.setattr(cia_routes_unified.asyncio, "wait_for", _wait_for)
    monkeypatch.setattr(cia_routes_unified, "cia_agent", _DummyAgent())
    monkeypatch.setattr(cia_routes_unified, "cost_tracker", dummy_cost_tracker)

    app = FastAPI()
    app.include_router(cia_routes_unified.router, prefix="/api/cia")

    payload = {
        "messages": [{"role": "user", "content": "hello"}],
        "conversation_id": "conv-1",
        "user_id": "user-abc",
    }

    with TestClient(app) as client:
        with client.stream("POST", "/api/cia/app/stream", json=payload) as response:
            body = "".join(list(response.iter_text()))
            assert response.status_code == 200
            assert "[DONE]" in body

        landing_payload = {**payload, "user_id": "00000000-0000-0000-0000-000000000000"}
        with client.stream("POST", "/api/cia/landing/stream", json=landing_payload) as response:
            body = "".join(list(response.iter_text()))
            assert response.status_code == 200
            assert "[DONE]" in body

    profiles = [call["profile"] for call in dummy_agent_calls]
    assert profiles == ["app", "landing"]


def test_app_stream_requires_user_id(monkeypatch):
    """Authenticated endpoint should reject missing user identifiers."""

    dummy_agent = types.SimpleNamespace(handle_conversation=AsyncMock())
    monkeypatch.setattr(cia_routes_unified, "cia_agent", dummy_agent)

    app = FastAPI()
    app.include_router(cia_routes_unified.router, prefix="/api/cia")

    payload = {
        "messages": [{"role": "user", "content": "hi"}],
        "conversation_id": "conv-2",
        "user_id": "00000000-0000-0000-0000-000000000000",
    }

    with TestClient(app) as client:
        response = client.post("/api/cia/app/stream", json=payload)
        assert response.status_code == 400
        assert "user_id" in response.json()["detail"]
