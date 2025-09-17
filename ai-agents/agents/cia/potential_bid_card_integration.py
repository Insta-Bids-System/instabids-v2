"""Utilities for managing Potential Bid Cards during CIA conversations."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional

import httpx

from config.service_urls import ServiceEndpoints

logger = logging.getLogger(__name__)


class _InMemoryPotentialBidCardStore:
    """Simple in-memory store used as a fallback when HTTP service is unavailable."""

    def __init__(self) -> None:
        self._cards: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def create(self, payload: Dict[str, Any]) -> str:
        async with self._lock:
            bid_card_id = str(uuid.uuid4())
            self._cards[bid_card_id] = {
                "id": bid_card_id,
                "conversation_id": payload.get("conversation_id"),
                "session_id": payload.get("session_id"),
                "user_id": payload.get("user_id"),
                "anonymous_user_id": payload.get("anonymous_user_id"),
                "title": payload.get("title", "New Project"),
                "fields": {},
                "status": "pending",
                "completion_percentage": 0,
            }
            return bid_card_id

    async def update_field(
        self,
        bid_card_id: str,
        field_name: str,
        field_value: Any,
        confidence: float,
    ) -> bool:
        async with self._lock:
            card = self._cards.get(bid_card_id)
            if not card:
                return False

            fields = card.setdefault("fields", {})
            fields[field_name] = {
                "value": field_value,
                "confidence": confidence,
            }

            non_empty = len([f for f in fields.values() if f["value"] not in (None, "")])
            card["completion_percentage"] = min(non_empty * 10, 100)
            return True

    async def get_status(self, bid_card_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            card = self._cards.get(bid_card_id)
            if not card:
                return None
            return {
                "id": card["id"],
                "status": card.get("status", "pending"),
                "completion_percentage": card.get("completion_percentage", 0),
                "fields": {name: info["value"] for name, info in card.get("fields", {}).items()},
            }

    async def convert(self, bid_card_id: str, payload: Dict[str, Any]) -> Optional[str]:
        async with self._lock:
            card = self._cards.get(bid_card_id)
            if not card:
                return None
            official_id = payload.get("official_bid_card_id") or str(uuid.uuid4())
            card["official_bid_card_id"] = official_id
            card["status"] = "converted"
            return official_id


class PotentialBidCardManager:
    """Manages potential bid card creation and updates during CIA conversations."""

    FIELD_MAPPING: Dict[str, str] = {
        # Core project fields (FIXED)
        "project_type": "project_type",
        "project_description": "description",
        "title": "title",

        # Location fields (FIXED)
        "location_zip": "location_zip",
        "zip_code": "zip_code",
        "zip": "zip_code",
        "room_location": "room_location",
        "property_area": "property_area",

        # Budget fields (FIXED)
        "budget_min": "budget_min",
        "budget_max": "budget_max",
        "budget_context": "budget_context",

        # Timeline fields
        "timeline": "estimated_timeline",
        "urgency": "urgency_level",
        "timeline_flexibility": "timeline_flexibility",

        # Contractor preferences
        "contractor_size": "contractor_size_preference",
        "quality_expectations": "quality_expectations",

        # Materials and specifications
        "materials": "materials_specified",
        "special_requirements": "special_requirements",

        # Service and complexity
        "service_type": "service_type",
        "project_complexity": "project_complexity",
        "component_type": "component_type",
        "service_complexity": "service_complexity",
        "trade_count": "trade_count",
        "primary_trade": "primary_trade",
        "secondary_trades": "secondary_trades",

        # Date fields
        "bid_collection_deadline": "bid_collection_deadline",
        "project_completion_deadline": "project_completion_deadline",
        "deadline_hard": "deadline_hard",
        "deadline_context": "deadline_context",

        # Email/contact
        "email_address": "email_address",
    }

    IGNORED_FIELDS = {
        "property_type",
        "property_size",
        "current_condition",
        "location",
        "location_context",
        "contractor_requirements",
        "urgency_reason",
        "timeline_details",
        "uploaded_photos",
        "photo_analyses",
        "phone_number",
    }

    def __init__(
        self,
        base_url: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
        use_fallback: bool = False,
        fallback_store: Optional[_InMemoryPotentialBidCardStore] = None,
    ) -> None:
        api_base = base_url or ServiceEndpoints.CIA_POTENTIAL_BID_CARDS
        self.api_endpoint = api_base.rstrip("/")
        self._client = client
        self._fallback = fallback_store if use_fallback else None
        if use_fallback and self._fallback is None:
            self._fallback = _InMemoryPotentialBidCardStore()

    async def create_potential_bid_card(
        self,
        conversation_id: str,
        session_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[str]:
        """Create a new potential bid card for the conversation."""
        try:
            payload = {
                "conversation_id": conversation_id,
                "session_id": session_id,
                "user_id": user_id,
                "anonymous_user_id": user_id if user_id == "00000000-0000-0000-0000-000000000000" else None,
                "title": "New Project",
            }

            if self._fallback:
                bid_card_id = await self._fallback.create(payload)
                logger.info(f"[CIA] Created potential bid card via fallback: {bid_card_id}")
                return bid_card_id

            response = await self._post(self.api_endpoint, payload)
            if response and response.status_code == 200:
                data = response.json()
                bid_card_id = data.get("id")
                logger.info(f"[CIA] Created potential bid card: {bid_card_id}")
                return bid_card_id

            status = response.status_code if response else "no-response"
            logger.error(f"[CIA] Failed to create potential bid card: {status}")
            return None

        except Exception as exc:
            logger.error(f"[CIA] Error creating potential bid card: {exc}")
            return None

    async def update_bid_card_field(
        self,
        bid_card_id: str,
        field_name: str,
        field_value: Any,
        confidence: float = 1.0,
    ) -> bool:
        """Update a specific field in the potential bid card."""
        try:
            if field_name in self.IGNORED_FIELDS:
                logger.info(f"[CIA] Skipping ignored field: {field_name}")
                return True

            mapped_field = self.FIELD_MAPPING.get(field_name, field_name)
            payload = {
                "field_name": mapped_field,
                "field_value": field_value,
                "confidence": confidence,
                "source": "conversation",
            }

            if self._fallback:
                success = await self._fallback.update_field(bid_card_id, mapped_field, field_value, confidence)
                if success:
                    logger.info(f"[CIA] Updated bid card field via fallback {mapped_field}: {field_value}")
                else:
                    logger.error(f"[CIA] Failed to update field via fallback {mapped_field}: {bid_card_id}")
                return success

            url = f"{self.api_endpoint}/{bid_card_id}/field"
            response = await self._put(url, payload)

            if response and response.status_code == 200:
                logger.info(f"[CIA] Updated bid card field {mapped_field}: {field_value}")
                return True

            status = response.status_code if response else "no-response"
            logger.error(f"[CIA] Failed to update field {mapped_field}: {status}")
            return False

        except Exception as exc:
            logger.error(f"[CIA] Error updating bid card field: {exc}")
            return False

    async def update_from_collected_info(
        self,
        bid_card_id: str,
        collected_info: Dict[str, Any],
    ) -> int:
        """Update multiple fields from CIA's collected_info."""
        if not bid_card_id or not collected_info:
            return 0

        updated_count = 0

        for field_name, field_value in collected_info.items():
            if field_value not in (None, ""):
                success = await self.update_bid_card_field(
                    bid_card_id,
                    field_name,
                    field_value,
                )
                if success:
                    updated_count += 1

        logger.info(f"[CIA] Updated {updated_count} fields in potential bid card")
        return updated_count

    async def get_bid_card_status(self, bid_card_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a potential bid card."""
        try:
            if self._fallback:
                return await self._fallback.get_status(bid_card_id)

            url = f"{self.api_endpoint}/{bid_card_id}"
            response = await self._get(url)

            if response and response.status_code == 200:
                return response.json()

            status = response.status_code if response else "no-response"
            logger.error(f"[CIA] Failed to get bid card status: {status}")
            return None

        except Exception as exc:
            logger.error(f"[CIA] Error getting bid card status: {exc}")
            return None

    async def convert_to_official_bid_card(
        self,
        bid_card_id: str,
        user_id: str,
    ) -> Optional[str]:
        """Convert potential bid card to official bid card after signup."""
        try:
            payload = {"user_id": user_id}

            if self._fallback:
                return await self._fallback.convert(bid_card_id, payload)

            url = f"{self.api_endpoint}/{bid_card_id}/convert-to-bid-card"
            response = await self._post(url, payload)

            if response and response.status_code == 200:
                data = response.json()
                official_bid_card_id = data.get("official_bid_card_id")
                logger.info(f"[CIA] Converted to official bid card: {official_bid_card_id}")
                return official_bid_card_id

            status = response.status_code if response else "no-response"
            logger.error(f"[CIA] Failed to convert bid card: {status}")
            return None

        except Exception as exc:
            logger.error(f"[CIA] Error converting bid card: {exc}")
            return None

    async def _post(self, url: str, payload: Dict[str, Any]) -> Optional[httpx.Response]:
        try:
            if self._client:
                return await self._client.post(url, json=payload)
            async with httpx.AsyncClient() as client:
                return await client.post(url, json=payload)
        except Exception as exc:
            logger.error(f"[CIA] POST request failed for {url}: {exc}")
            return None

    async def _put(self, url: str, payload: Dict[str, Any]) -> Optional[httpx.Response]:
        try:
            if self._client:
                return await self._client.put(url, json=payload)
            async with httpx.AsyncClient() as client:
                return await client.put(url, json=payload)
        except Exception as exc:
            logger.error(f"[CIA] PUT request failed for {url}: {exc}")
            return None

    async def _get(self, url: str) -> Optional[httpx.Response]:
        try:
            if self._client:
                return await self._client.get(url)
            async with httpx.AsyncClient() as client:
                return await client.get(url)
        except Exception as exc:
            logger.error(f"[CIA] GET request failed for {url}: {exc}")
            return None
