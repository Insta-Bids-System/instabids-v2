import json
import sys
import uuid
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import importlib.util

module_path = Path(__file__).resolve().parents[2] / "agents" / "cia" / "potential_bid_card_integration.py"
spec = importlib.util.spec_from_file_location("potential_bid_card_integration", module_path)
potential_bid_card_integration = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(potential_bid_card_integration)

PotentialBidCardManager = potential_bid_card_integration.PotentialBidCardManager


@pytest.mark.asyncio
async def test_http_client_path_updates_and_status():
    """Ensure the manager can use an injected HTTP client for all operations."""

    cards = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "POST" and path == "/api/cia/potential-bid-cards":
            payload = json.loads(request.content.decode())
            bid_card_id = f"http-{len(cards) + 1}"
            cards[bid_card_id] = {
                "payload": payload,
                "fields": {},
                "status": "pending",
                "completion_percentage": 0,
            }
            return httpx.Response(200, json={"id": bid_card_id})

        if request.method == "PUT" and path.startswith("/api/cia/potential-bid-cards/") and path.endswith("/field"):
            bid_card_id = path.split("/")[4]
            body = json.loads(request.content.decode())
            cards[bid_card_id]["fields"][body["field_name"]] = body["field_value"]
            cards[bid_card_id]["completion_percentage"] = 50
            return httpx.Response(200, json={"success": True})

        if request.method == "GET" and path.startswith("/api/cia/potential-bid-cards/"):
            bid_card_id = path.split("/")[4]
            card = cards[bid_card_id]
            return httpx.Response(
                200,
                json={
                    "id": bid_card_id,
                    "status": card["status"],
                    "completion_percentage": card["completion_percentage"],
                    "fields": card["fields"],
                },
            )

        if request.method == "POST" and path.endswith("/convert-to-bid-card"):
            bid_card_id = path.split("/")[4]
            official_id = f"official-{bid_card_id}"
            cards[bid_card_id]["official_bid_card_id"] = official_id
            cards[bid_card_id]["status"] = "converted"
            return httpx.Response(200, json={"official_bid_card_id": official_id})

        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        manager = PotentialBidCardManager(
            base_url="http://testserver/api/cia/potential-bid-cards",
            client=client,
        )

        bid_card_id = await manager.create_potential_bid_card(
            conversation_id=str(uuid.uuid4()),
            session_id="session-123",
            user_id="user-456",
        )
        assert bid_card_id in cards

        updated = await manager.update_bid_card_field(bid_card_id, "title", "Test Project", confidence=0.8)
        assert updated is True

        status = await manager.get_bid_card_status(bid_card_id)
        assert status is not None
        assert status["id"] == bid_card_id
        assert status["fields"]["title"] == "Test Project"

        official_id = await manager.convert_to_official_bid_card(bid_card_id, "user-456")
        assert official_id == f"official-{bid_card_id}"
        assert cards[bid_card_id]["status"] == "converted"


@pytest.mark.asyncio
async def test_in_memory_fallback_operations():
    """The fallback store should allow tests to run without HTTP services."""

    manager = PotentialBidCardManager(use_fallback=True)

    bid_card_id = await manager.create_potential_bid_card(
        conversation_id="conv-1",
        session_id="session-1",
        user_id=None,
    )
    assert bid_card_id is not None

    await manager.update_bid_card_field(bid_card_id, "project_description", "A backyard remodel")
    await manager.update_from_collected_info(
        bid_card_id,
        {"budget_min": 1000, "budget_max": 5000, "zip_code": "94107"},
    )

    status = await manager.get_bid_card_status(bid_card_id)
    assert status is not None
    assert status["fields"]["description"] == "A backyard remodel"
    assert status["fields"]["budget_min"] == 1000
    assert status["fields"]["zip_code"] == "94107"

    official_id = await manager.convert_to_official_bid_card(bid_card_id, "user-789")
    assert official_id is not None
    assert official_id != ""
