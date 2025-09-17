import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

# Provide a stub database module before importing the agent so the real Supabase client isn't created
if "database_simple" not in sys.modules:
    stub_database_simple = types.ModuleType("database_simple")
    stub_database_simple.db = None
    sys.modules["database_simple"] = stub_database_simple

# Ensure the ai-agents package root is importable when running pytest from repository root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from agents.cia import agent as agent_module  # noqa: E402
from agents.cia.agent import CustomerInterfaceAgent  # noqa: E402


class StubResponse:
    """Container that mimics the minimal OpenAI response structure used by the agent."""

    def __init__(self, *, content: str | None, tool_calls: list[SimpleNamespace] | None):
        message = SimpleNamespace(content=content, tool_calls=tool_calls)
        self.choices = [SimpleNamespace(message=message)]


@pytest.fixture
def stub_async_openai(monkeypatch):
    """Patch the AsyncOpenAI client so no real API calls are attempted."""

    responses: list[StubResponse] = []
    calls: list[dict] = []

    class StubCompletions:
        async def create(self, **kwargs):
            calls.append(kwargs)
            if not responses:
                raise AssertionError("No stubbed OpenAI responses configured")
            return responses.pop(0)

    class StubChat:
        def __init__(self):
            self.completions = StubCompletions()

    class StubAsyncOpenAI:
        def __init__(self, *args, **kwargs):
            self.chat = StubChat()

    monkeypatch.setattr(agent_module, "AsyncOpenAI", StubAsyncOpenAI)

    def configure(new_responses: list[StubResponse]):
        responses[:] = list(new_responses)
        calls.clear()
        return calls

    return configure


@pytest.fixture
def stub_db(monkeypatch):
    class StubDB:
        def __init__(self):
            self.state_to_return = None
            self.loaded_threads: list[str] = []
            self.saved_calls: list[dict] = []

        async def load_conversation_state(self, thread_id: str):
            self.loaded_threads.append(thread_id)
            return self.state_to_return

        async def save_conversation_state(self, *, user_id: str, thread_id: str, agent_type: str, state: dict):
            self.saved_calls.append(
                {
                    "user_id": user_id,
                    "thread_id": thread_id,
                    "agent_type": agent_type,
                    "state": state,
                }
            )
            return {"state": state}

    stub = StubDB()
    monkeypatch.setattr(agent_module, "db", stub)
    return stub


@pytest.fixture
def stub_store(monkeypatch):
    instances = []

    class StubCIAStore:
        def __init__(self):
            self.contexts: dict[str, dict] = {}
            self.saved_turns: list[dict] = []

        async def get_user_context(self, user_id: str):
            return self.contexts.get(user_id, {"new_user": True})

        async def save_conversation_turn(self, *args, **kwargs):
            self.saved_turns.append({"args": args, "kwargs": kwargs})

    def factory():
        store = StubCIAStore()
        instances.append(store)
        return store

    monkeypatch.setattr(agent_module, "CIAStore", factory)
    return instances


@pytest.fixture
def stub_bid_card_manager(monkeypatch):
    instances = []

    class StubPotentialBidCardManager:
        def __init__(self):
            self.created_calls: list[dict] = []
            self.updated_fields: list[dict] = []
            self.status_queries: list[str] = []

        async def create_potential_bid_card(self, *, conversation_id: str, session_id: str, user_id: str | None):
            self.created_calls.append(
                {
                    "conversation_id": conversation_id,
                    "session_id": session_id,
                    "user_id": user_id,
                }
            )
            return "test-bid-card"

        async def update_bid_card_field(self, *, bid_card_id: str, field_name: str, field_value, confidence: float):
            self.updated_fields.append(
                {
                    "bid_card_id": bid_card_id,
                    "field_name": field_name,
                    "field_value": field_value,
                    "confidence": confidence,
                }
            )
            return True

        async def get_bid_card_status(self, bid_card_id: str):
            self.status_queries.append(bid_card_id)
            return {"id": bid_card_id, "completion_percentage": 64}

    def factory():
        manager = StubPotentialBidCardManager()
        instances.append(manager)
        return manager

    monkeypatch.setattr(agent_module, "PotentialBidCardManager", factory)
    return instances


@pytest.fixture
def stub_categorization(monkeypatch):
    calls: list[dict] = []

    async def fake_handle(tool_call_args: dict, bid_card_id: str):
        calls.append({"args": tool_call_args, "bid_card_id": bid_card_id})
        return {"status": "ok", "category": "kitchen", "bid_card_id": bid_card_id}

    def fake_response(result: dict) -> str:
        return f"Categorized as {result['category']}"

    def fake_tool() -> dict:
        return {"type": "function", "function": {"name": "categorize_project"}}

    monkeypatch.setattr(agent_module, "handle_categorization_tool_call", fake_handle)
    monkeypatch.setattr(agent_module, "get_categorization_response", fake_response)
    monkeypatch.setattr(agent_module, "get_categorization_tool", fake_tool)
    return calls


def make_tool_call(name: str, arguments: dict) -> SimpleNamespace:
    return SimpleNamespace(function=SimpleNamespace(name=name, arguments=json.dumps(arguments)))


@pytest.mark.asyncio
async def test_handle_conversation_landing_profile(
    stub_async_openai, stub_db, stub_store, stub_bid_card_manager, stub_categorization
):
    extracted_payload = {
        "title": "Kitchen Remodel",
        "description": "Full kitchen gut and upgrade",
        "location_zip": "90210",
        "urgency_level": "urgent",
        "contractor_count_needed": 3,
        "materials_specified": ["quartz", "maple"],
        "eligible_for_group_bidding": False,
    }

    tool_call = make_tool_call("update_bid_card", extracted_payload)
    openai_calls = stub_async_openai([StubResponse(content="Let's get started!", tool_calls=[tool_call])])

    stub_db.state_to_return = {"messages": [{"role": "assistant", "content": "Earlier reply"}]}

    agent = CustomerInterfaceAgent(api_key="test-key")
    manager = agent.bid_cards

    result = await agent.handle_conversation(
        user_id=None,
        message="I want to redo my kitchen this month.",
        session_id="session-landing",
        profile="landing",
    )

    assert result["success"] is True
    assert result["profile_used"] == "landing"
    assert result["bid_card_id"] == "test-bid-card"
    assert result["extracted_data"] == extracted_payload
    assert result["completion_percentage"] == 64
    assert result["bid_card_status"] == {"id": "test-bid-card", "completion_percentage": 64}

    assert manager.created_calls[0]["user_id"] is None
    updated_field_names = {entry["field_name"] for entry in manager.updated_fields}
    assert {"title", "description", "location_zip", "urgency_level", "contractor_count_needed"}.issubset(
        updated_field_names
    )

    assert stub_db.saved_calls[0]["user_id"] == "anonymous"
    saved_state = stub_db.saved_calls[0]["state"]
    assert saved_state["profile"] == "landing"
    assert saved_state["messages"][-2]["content"] == "I want to redo my kitchen this month."
    assert saved_state["messages"][-1]["role"] == "assistant"
    assert saved_state["messages"][-1]["content"].startswith("Let's get started!")

    assert len(stub_categorization) == 1
    assert openai_calls[0]["model"] == "gpt-4o"
    assert openai_calls[0]["messages"][-1]["role"] == "user"
    assert "redo my kitchen" in openai_calls[0]["messages"][-1]["content"]


@pytest.mark.asyncio
async def test_handle_conversation_app_profile(
    stub_async_openai, stub_db, stub_store, stub_bid_card_manager, stub_categorization
):
    extracted_payload = {
        "title": "Backyard Upgrade",
        "description": "Add a pergola and new lighting",
        "location_zip": "73301",
        "urgency_level": "month",
        "contractor_count_needed": 2,
        "service_type": "outdoor_living",
    }

    tool_calls = [
        make_tool_call("update_bid_card", extracted_payload),
        make_tool_call(
            "categorize_project",
            {"description": "Add a pergola and new lighting", "context": "outdoor_living"},
        ),
    ]
    openai_calls = stub_async_openai([StubResponse(content="That sounds exciting!", tool_calls=tool_calls)])

    stub_db.state_to_return = {"messages": [{"role": "user", "content": "Previous details"}]}

    agent = CustomerInterfaceAgent(api_key="test-key")
    store_instance = agent.store
    store_instance.contexts["user-123"] = {"new_user": False, "preferred_contractor": "regional"}
    manager = agent.bid_cards

    result = await agent.handle_conversation(
        user_id="user-123",
        message="Help me plan the next steps.",
        session_id="session-app",
        profile="app",
    )

    assert result["success"] is True
    assert result["profile_used"] == "app"
    assert result["bid_card_id"] == "test-bid-card"
    assert result["extracted_data"] == extracted_payload
    assert result["categorization_result"] == {
        "status": "ok",
        "category": "kitchen",
        "bid_card_id": "test-bid-card",
    }

    assert manager.created_calls[0]["user_id"] == "user-123"
    assert any(entry["field_name"] == "service_type" for entry in manager.updated_fields)

    assert stub_db.saved_calls[0]["user_id"] == "user-123"
    saved_state = stub_db.saved_calls[0]["state"]
    assert saved_state["profile"] == "app"
    assert saved_state["user_id"] == "user-123"
    assert saved_state["messages"][-2]["content"] == "Help me plan the next steps."
    assert saved_state["messages"][-1]["role"] == "assistant"
    assert saved_state["messages"][-1]["content"].startswith("That sounds exciting!")

    # Two categorization calls: automatic follow-up + explicit tool call
    assert len(stub_categorization) == 2
    assert openai_calls[0]["model"] == "gpt-4o"
    assert openai_calls[0]["messages"][-1]["role"] == "user"
    assert "Help me plan the next steps" in openai_calls[0]["messages"][-1]["content"]
