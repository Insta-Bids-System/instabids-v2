"""Compatibility wrappers for legacy BSA tooling imports."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .bsa_deepagents import search_bid_cards_original


async def search_available_bid_cards_async(
    *,
    contractor_zip: str,
    radius_miles: int = 30,
    project_keywords: Optional[str] = None,
    contractor_type_ids: Optional[list[int]] = None,
    contractor_size: int = 3,
) -> Dict[str, Any]:
    """Async helper that forwards to :func:`search_bid_cards_original`."""

    return await search_bid_cards_original(
        contractor_zip=contractor_zip,
        radius_miles=radius_miles,
        project_type=project_keywords,
        contractor_type_ids=contractor_type_ids or [],
        contractor_size=contractor_size,
    )


class _SearchAvailableBidCardsTool:
    async def invoke(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return await search_available_bid_cards_async(**params)


search_available_bid_cards = _SearchAvailableBidCardsTool()

__all__ = ["search_available_bid_cards", "search_available_bid_cards_async"]
