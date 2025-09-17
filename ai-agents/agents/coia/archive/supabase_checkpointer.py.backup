"""
Supabase-based LangGraph Checkpointer for Unified COIA Agent
Provides persistent state management using Supabase PostgreSQL backend
"""

import asyncio
import json
import os
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool


try:
    from langgraph.checkpoint.base.serde.jsonplus import JsonPlusSerializer
except ImportError:
    try:
        from langgraph.checkpoint.serde import JsonPlusSerializer
    except ImportError:
        # Create message-aware JSON serializer fallback
        import json
        from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
        
        class MessageAwareSerializer:
            def dumps_typed(self, obj):
                return json.dumps(obj, default=self._serialize_message)
            
            def loads_typed(self, data):
                return json.loads(data, object_hook=self._deserialize_message)
            
            def _serialize_message(self, obj):
                if isinstance(obj, BaseMessage):
                    return {
                        "__type": obj.__class__.__name__,
                        "content": obj.content,
                        "additional_kwargs": getattr(obj, 'additional_kwargs', {}),
                        "response_metadata": getattr(obj, 'response_metadata', {})
                    }
                return str(obj)
            
            def _deserialize_message(self, obj):
                if isinstance(obj, dict) and "__type" in obj:
                    msg_type = obj["__type"]
                    if msg_type == "HumanMessage":
                        return HumanMessage(
                            content=obj["content"],
                            additional_kwargs=obj.get("additional_kwargs", {}),
                            response_metadata=obj.get("response_metadata", {})
                        )
                    elif msg_type == "AIMessage":
                        return AIMessage(
                            content=obj["content"],
                            additional_kwargs=obj.get("additional_kwargs", {}),
                            response_metadata=obj.get("response_metadata", {})
                        )
                return obj
        
        JsonPlusSerializer = MessageAwareSerializer

from .unified_state import UnifiedCoIAState


class SupabaseCheckpointer(BaseCheckpointSaver):
    """
    LangGraph checkpointer using Supabase PostgreSQL as backend.
    Provides persistent state management for unified COIA agent across multiple interfaces.
    """

    def __init__(self, pool: Optional[AsyncConnectionPool] = None):
        """Initialize checkpointer with connection pool"""
        super().__init__(serde=JsonPlusSerializer())

        if pool is None:
            # Create connection pool from environment variables
            db_url = os.getenv("SUPABASE_DB_URL")
            if not db_url:
                raise ValueError("SUPABASE_DB_URL environment variable required")

            self.pool = AsyncConnectionPool(
                conninfo=db_url,
                min_size=2,
                max_size=10,
                kwargs={
                    "sslmode": "require",
                    "connect_timeout": 10,
                    "row_factory": dict_row
                }
            )
        else:
            self.pool = pool

        self.is_setup = False

    async def setup(self) -> None:
        """Create necessary tables in Supabase if they don't exist"""
        if self.is_setup:
            return

        async with self.pool.connection() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS langgraph_checkpoints (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    parent_checkpoint_id TEXT,
                    type TEXT,
                    checkpoint JSONB NOT NULL,
                    metadata JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS langgraph_checkpoint_blobs (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    channel TEXT NOT NULL,
                    version TEXT NOT NULL,
                    type TEXT NOT NULL,
                    blob BYTEA,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS langgraph_checkpoint_writes (
                    thread_id TEXT NOT NULL,
                    checkpoint_ns TEXT NOT NULL DEFAULT '',
                    checkpoint_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    idx INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    type TEXT,
                    value JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                );
            """)

            # Create indexes for better performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id 
                ON langgraph_checkpoints(thread_id);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at 
                ON langgraph_checkpoints(created_at DESC);
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_checkpoint_writes_thread_id 
                ON langgraph_checkpoint_writes(thread_id);
            """)

        self.is_setup = True

    async def aget_tuple(self, config: dict[str, Any]) -> Optional[CheckpointTuple]:
        """Get a checkpoint tuple by thread_id and checkpoint_id"""
        await self.setup()

        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        if checkpoint_id:
            # Get specific checkpoint
            query = """
                SELECT checkpoint, metadata, parent_checkpoint_id, created_at
                FROM langgraph_checkpoints 
                WHERE thread_id = %s AND checkpoint_ns = %s AND checkpoint_id = %s
            """
            params = (thread_id, checkpoint_ns, checkpoint_id)
        else:
            # Get latest checkpoint
            query = """
                SELECT checkpoint, metadata, parent_checkpoint_id, created_at, checkpoint_id
                FROM langgraph_checkpoints 
                WHERE thread_id = %s AND checkpoint_ns = %s
                ORDER BY created_at DESC 
                LIMIT 1
            """
            params = (thread_id, checkpoint_ns)

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                row = await cur.fetchone()

                if not row:
                    return None

                # Deserialize checkpoint
                checkpoint = self.serde.loads_typed(row["checkpoint"])
                metadata = CheckpointMetadata(**row["metadata"])

                # Get pending writes
                writes_query = """
                    SELECT task_id, channel, value, type
                    FROM langgraph_checkpoint_writes
                    WHERE thread_id = %s AND checkpoint_ns = %s AND checkpoint_id = %s
                    ORDER BY task_id, idx
                """
                checkpoint_id_for_writes = checkpoint_id or row.get("checkpoint_id")
                await cur.execute(writes_query, (thread_id, checkpoint_ns, checkpoint_id_for_writes))
                writes_rows = await cur.fetchall()

                pending_writes = []
                for write_row in writes_rows:
                    value = self.serde.loads_typed(write_row["value"]) if write_row["value"] else None
                    pending_writes.append((write_row["task_id"], write_row["channel"], value))

                return CheckpointTuple(
                    config=config,
                    checkpoint=checkpoint,
                    metadata=metadata,
                    pending_writes=pending_writes,
                    parent_config=None  # TODO: implement parent config lookup if needed
                )

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

        query_parts = ["SELECT checkpoint, metadata, checkpoint_id, thread_id, checkpoint_ns, created_at"]
        query_parts.append("FROM langgraph_checkpoints")

        conditions = []
        params = []

        # Apply config filtering
        if config:
            thread_id = config["configurable"].get("thread_id")
            if thread_id:
                conditions.append("thread_id = %s")
                params.append(thread_id)

            checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
            conditions.append("checkpoint_ns = %s")
            params.append(checkpoint_ns)

        # Apply additional filters
        if filter:
            for key, value in filter.items():
                if key in ["thread_id", "checkpoint_ns", "type"]:
                    conditions.append(f"{key} = %s")
                    params.append(value)

        # Apply before filter
        if before and "created_at" in before:
            conditions.append("created_at < %s")
            params.append(before["created_at"])

        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))

        query_parts.append("ORDER BY created_at DESC")

        if limit:
            query_parts.append(f"LIMIT {limit}")

        query = " ".join(query_parts)

        async with self.pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)

                async for row in cur:
                    checkpoint = self.serde.loads_typed(row["checkpoint"])
                    metadata = CheckpointMetadata(**row["metadata"])

                    config_dict = {
                        "configurable": {
                            "thread_id": row["thread_id"],
                            "checkpoint_ns": row["checkpoint_ns"],
                            "checkpoint_id": row["checkpoint_id"]
                        }
                    }

                    yield CheckpointTuple(
                        config=config_dict,
                        checkpoint=checkpoint,
                        metadata=metadata,
                        pending_writes=[],  # Not loading writes for list view
                        parent_config=None
                    )

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
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = checkpoint["id"]
        parent_checkpoint_id = config["configurable"].get("checkpoint_id")

        # Serialize checkpoint and metadata
        checkpoint_data = self.serde.dumps_typed(checkpoint)
        metadata_data = self.serde.dumps_typed(metadata)

        async with self.pool.connection() as conn:
            # Insert checkpoint
            await conn.execute("""
                INSERT INTO langgraph_checkpoints 
                (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (thread_id, checkpoint_ns, checkpoint_id) 
                DO UPDATE SET 
                    checkpoint = EXCLUDED.checkpoint,
                    metadata = EXCLUDED.metadata,
                    created_at = NOW()
            """, (
                thread_id,
                checkpoint_ns,
                checkpoint_id,
                parent_checkpoint_id,
                "checkpoint",
                checkpoint_data,
                metadata_data
            ))

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id
            }
        }

    async def aput_writes(
        self,
        config: dict[str, Any],
        writes: list[tuple[str, str, Any]],
        task_id: str,
    ) -> None:
        """Save pending writes"""
        await self.setup()

        if not writes:
            return

        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]

        async with self.pool.connection() as conn:
            for idx, (channel, value) in enumerate(writes):
                value_data = self.serde.dumps_typed(value) if value is not None else None

                await conn.execute("""
                    INSERT INTO langgraph_checkpoint_writes
                    (thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, type, value)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                    DO UPDATE SET 
                        channel = EXCLUDED.channel,
                        type = EXCLUDED.type,
                        value = EXCLUDED.value,
                        created_at = NOW()
                """, (
                    thread_id,
                    checkpoint_ns,
                    checkpoint_id,
                    task_id,
                    idx,
                    channel,
                    "write",
                    value_data
                ))


async def create_supabase_checkpointer() -> SupabaseCheckpointer:
    """Factory function to create and setup Supabase checkpointer"""
    checkpointer = SupabaseCheckpointer()
    await checkpointer.setup()
    return checkpointer


# Utility functions for COIA-specific state management
async def save_coia_state(
    checkpointer: SupabaseCheckpointer,
    thread_id: str,
    state: UnifiedCoIAState,
    session_id: str,
    interface: str = "chat"
) -> str:
    """
    Helper function to save COIA state with proper configuration
    Returns the checkpoint ID
    """
    checkpoint_id = str(uuid4())

    config = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_id": checkpoint_id,
            "checkpoint_ns": f"coia_{interface}"  # Namespace by interface
        }
    }

    # Create checkpoint with COIA-specific metadata
    checkpoint = Checkpoint(
        v=1,
        id=checkpoint_id,
        ts=datetime.now().isoformat(),
        channel_values={"__root__": state},
        channel_versions={"__root__": checkpoint_id},
        versions_seen={"__root__": {checkpoint_id}}
    )

    metadata = CheckpointMetadata(
        source="update",
        step=1,
        writes={"__root__": state},
        session_id=session_id,
        interface=interface,
        mode=state.get("current_mode", "conversation"),
        contractor_id=state.get("contractor_id"),
        last_updated=datetime.now().isoformat()
    )

    await checkpointer.aput(config, checkpoint, metadata, {"__root__": checkpoint_id})
    return checkpoint_id


async def load_coia_state(
    checkpointer: SupabaseCheckpointer,
    thread_id: str,
    interface: str = "chat",
    checkpoint_id: Optional[str] = None
) -> Optional[UnifiedCoIAState]:
    """
    Helper function to load COIA state by thread ID
    Returns None if no state found
    """
    config = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": f"coia_{interface}"
        }
    }

    if checkpoint_id:
        config["configurable"]["checkpoint_id"] = checkpoint_id

    tuple_result = await checkpointer.aget_tuple(config)
    if not tuple_result:
        return None

    # Extract state from checkpoint
    channel_values = tuple_result.checkpoint.get("channel_values", {})
    return channel_values.get("__root__")


if __name__ == "__main__":
    """Test the checkpointer functionality"""
    async def test_checkpointer():
        # Test basic functionality
        checkpointer = await create_supabase_checkpointer()

        # Create test state
        test_state: UnifiedCoIAState = {
            "messages": [],
            "session_id": "test_session_123",
            "user_id": "user_456",
            "contractor_lead_id": None,
            "contractor_id": None,
            "interface": "chat",
            "current_mode": "conversation",
            "previous_mode": None,
            "mode_confidence": 1.0,
            "transition_reason": None,
            "last_updated": datetime.now().isoformat(),
            "contractor_profile": {},
            "profile_completeness": 0.0,
            "company_name": "Test Company",
            "company_website": None,
            "business_info": None,
            "research_completed": False,
            "research_confirmed": False,
            "research_findings": None,
            "website_research_status": "pending",
            "intelligence_data": None,
            "google_places_data": None,
            "returning_contractor_id": None,
            "persistent_memory_loaded": False,
            "available_capabilities": ["conversation"],
            "active_tools": [],
            "tool_results": None,
            "next_action": None,
            "completion_ready": False,
            "contractor_created": False,
            "conversion_successful": False,
            "error_state": None,
            "original_project_id": None,
            "source_channel": "chat",
            "matching_projects_count": 0
        }

        # Save state
        thread_id = f"test_thread_{uuid4()}"
        checkpoint_id = await save_coia_state(
            checkpointer,
            thread_id,
            test_state,
            "test_session_123",
            "chat"
        )

        print(f"Saved state with checkpoint ID: {checkpoint_id}")

        # Load state back
        loaded_state = await load_coia_state(checkpointer, thread_id, "chat")

        if loaded_state:
            print("Successfully loaded state!")
            print(f"Session ID: {loaded_state['session_id']}")
            print(f"Current mode: {loaded_state['current_mode']}")
            print(f"Company name: {loaded_state['company_name']}")
        else:
            print("Failed to load state")

    # Run test
    asyncio.run(test_checkpointer())
