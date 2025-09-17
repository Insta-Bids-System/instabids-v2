"""Compatibility wrappers exposing the legacy BSA agent API."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional

from .bsa_deepagents import bsa_deepagent_stream


async def process_contractor_input_streaming(
    *,
    contractor_id: str,
    input_data: str,
    input_type: str = "text",
    session_id: Optional[str] = None,
    bid_card_id: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    **kwargs: Any,
) -> AsyncIterator[Dict[str, Any]]:
    """Stream responses using the DeepAgents-powered BSA entry point.

    The original implementation accepted ``input_type`` and ``input_data`` arguments.
    Only text input is currently supported, so we forward ``input_data`` directly
    to :func:`bsa_deepagent_stream` while passing through any injected dependencies
    via ``kwargs``.
    """

    if input_type != "text":  # pragma: no cover - defensive branch
        raise ValueError(f"Unsupported input_type: {input_type}")

    async for chunk in bsa_deepagent_stream(
        contractor_id=contractor_id,
        message=input_data,
        conversation_history=conversation_history,
        session_id=session_id,
        bid_card_id=bid_card_id,
        **kwargs,
    ):
        yield chunk


__all__ = ["process_contractor_input_streaming"]
