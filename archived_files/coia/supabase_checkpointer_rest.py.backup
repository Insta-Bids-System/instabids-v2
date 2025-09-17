"""
Supabase REST API based checkpointer for LangGraph
Uses Supabase REST API instead of direct PostgreSQL connection to avoid DNS issues
"""

import json
import os
import uuid
from collections.abc import AsyncIterator
from typing import Any, Optional
import asyncio
import httpx

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)


# Simple JSON serializer
class SimpleJsonSerializer:
    def dumps_typed(self, obj):
        return json.dumps(obj, default=str)
    def loads_typed(self, data):
        if isinstance(data, str):
            return json.loads(data)
        return data


class SupabaseRESTCheckpointer(BaseCheckpointSaver):
    """
    LangGraph checkpointer using Supabase REST API
    Avoids direct database connection issues
    """

    def __init__(self):
        """Initialize checkpointer with Supabase REST API"""
        super().__init__(serde=SimpleJsonSerializer())
        
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
        self.rest_url = f"{self.supabase_url}/rest/v1"
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        self.is_setup = False

    async def setup(self) -> None:
        """Setup is handled by Supabase automatically"""
        # Tables are created via Supabase migrations/dashboard
        # For now, we'll assume tables exist or create them manually
        self.is_setup = True

    async def aget_tuple(self, config: dict[str, Any]) -> Optional[CheckpointTuple]:
        """Get a checkpoint tuple by thread_id"""
        await self.setup()

        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("checkpoint_id")

        async with httpx.AsyncClient() as client:
            if checkpoint_id:
                # Get specific checkpoint
                url = f"{self.rest_url}/langgraph_checkpoints"
                params = {
                    "thread_id": f"eq.{thread_id}",
                    "checkpoint_id": f"eq.{checkpoint_id}",
                    "select": "checkpoint,metadata,parent_checkpoint_id,created_at,checkpoint_id"
                }
            else:
                # Get latest checkpoint
                url = f"{self.rest_url}/langgraph_checkpoints"
                params = {
                    "thread_id": f"eq.{thread_id}",
                    "select": "checkpoint,metadata,parent_checkpoint_id,created_at,checkpoint_id",
                    "order": "created_at.desc",
                    "limit": "1"
                }

            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                rows = response.json()
                
                if not rows:
                    return None

                row = rows[0]
                checkpoint = row["checkpoint"]
                metadata = row.get("metadata") or {}
                
                # Get pending writes
                writes_url = f"{self.rest_url}/langgraph_checkpoint_writes"
                writes_params = {
                    "thread_id": f"eq.{thread_id}",
                    "checkpoint_id": f"eq.{row['checkpoint_id']}",
                    "select": "task_id,channel,value,type",
                    "order": "task_id,idx"
                }
                
                writes_response = await client.get(writes_url, headers=self.headers, params=writes_params)
                writes_rows = writes_response.json() if writes_response.status_code == 200 else []
                
                pending_writes = []
                for write_row in writes_rows:
                    pending_writes.append((write_row["task_id"], write_row["channel"], write_row["value"]))

                return CheckpointTuple(
                    config=config,
                    checkpoint=checkpoint,
                    metadata=CheckpointMetadata(**metadata),
                    pending_writes=pending_writes,
                    parent_config=None
                )
            except Exception as e:
                print(f"Failed to get checkpoint: {e}")
                return None

    async def alist(
        self,
        config: Optional[dict[str, Any]] = None,
        *,
        filter: Optional[dict[str, Any]] = None,
        before: Optional[dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """List checkpoints with optional filtering"""
        await self.setup()
        # Simple implementation - just return empty for now
        return
        yield  # Make it a generator

    async def aput(
        self,
        config: dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict[str, str],
    ) -> dict[str, Any]:
        """Save a checkpoint"""
        await self.setup()

        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint.get("id") or str(uuid.uuid4())
        parent_checkpoint_id = config["configurable"].get("checkpoint_id")

        # Convert metadata to dict
        metadata_dict = {
            "source": getattr(metadata, "source", "update"),
            "step": getattr(metadata, "step", 1),
            "writes": getattr(metadata, "writes", {})
        }

        checkpoint_data = {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "parent_checkpoint_id": parent_checkpoint_id,
            "type": "checkpoint",
            "checkpoint": checkpoint,
            "metadata": metadata_dict
        }

        async with httpx.AsyncClient() as client:
            try:
                # Use upsert to insert or update
                url = f"{self.rest_url}/langgraph_checkpoints"
                headers = {**self.headers, "Prefer": "resolution=merge-duplicates"}
                
                response = await client.post(url, headers=headers, json=checkpoint_data)
                if response.status_code not in [200, 201]:
                    print(f"Failed to save checkpoint: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"Error saving checkpoint: {e}")

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id
            }
        }

    async def aput_writes(
        self,
        config: dict[str, Any],
        writes: list[tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Save pending writes"""
        await self.setup()

        if not writes:
            return

        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"]["checkpoint_id"]

        async with httpx.AsyncClient() as client:
            try:
                writes_data = []
                for idx, (channel, value) in enumerate(writes):
                    writes_data.append({
                        "thread_id": thread_id,
                        "checkpoint_id": checkpoint_id,
                        "task_id": task_id,
                        "idx": idx,
                        "channel": channel,
                        "type": "write",
                        "value": value
                    })

                url = f"{self.rest_url}/langgraph_checkpoint_writes"
                headers = {**self.headers, "Prefer": "resolution=merge-duplicates"}
                
                response = await client.post(url, headers=headers, json=writes_data)
                if response.status_code not in [200, 201]:
                    print(f"Failed to save writes: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"Error saving writes: {e}")


async def create_supabase_rest_checkpointer() -> SupabaseRESTCheckpointer:
    """Factory function to create REST-based checkpointer"""
    checkpointer = SupabaseRESTCheckpointer()
    await checkpointer.setup()
    return checkpointer