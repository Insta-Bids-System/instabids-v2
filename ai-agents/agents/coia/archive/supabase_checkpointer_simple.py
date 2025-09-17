"""
Simplified Supabase-based LangGraph Checkpointer using psycopg2
Works with psycopg2-binary for compatibility
"""

import json
import os
import uuid
from collections.abc import AsyncIterator
from typing import Any, Optional

import psycopg2
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)
from psycopg2.extras import Json, RealDictCursor


# Enhanced JSON serializer for LangChain objects
class LangChainJsonSerializer:
    def dumps_typed(self, obj):
        return json.dumps(obj, default=self._serialize_object)
    
    def loads_typed(self, data):
        if isinstance(data, str):
            return json.loads(data)
        return data
    
    def _serialize_object(self, obj):
        """Custom serializer for LangChain and other complex objects"""
        # Handle LangChain message objects
        if hasattr(obj, '__class__') and hasattr(obj, 'content'):
            # This is likely a LangChain message
            return {
                '__type__': obj.__class__.__name__,
                '__module__': getattr(obj.__class__, '__module__', ''),
                'content': obj.content if hasattr(obj, 'content') else str(obj),
                'type': getattr(obj, 'type', 'unknown'),
                # Include other common message fields
                'additional_kwargs': getattr(obj, 'additional_kwargs', {}),
                'response_metadata': getattr(obj, 'response_metadata', {}),
                'tool_calls': getattr(obj, 'tool_calls', []),
                'usage_metadata': getattr(obj, 'usage_metadata', {}),
                'id': getattr(obj, 'id', None),
            }
        
        # Handle datetime objects
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        
        # Handle UUID objects
        if hasattr(obj, 'hex'):
            return str(obj)
        
        # Handle other objects with dict representation
        if hasattr(obj, '__dict__'):
            try:
                return {
                    '__type__': obj.__class__.__name__,
                    '__module__': getattr(obj.__class__, '__module__', ''),
                    **obj.__dict__
                }
            except:
                pass
        
        # Fallback to string representation
        return str(obj)


class SupabaseCheckpointer(BaseCheckpointSaver):
    """
    Simplified LangGraph checkpointer using Supabase PostgreSQL as backend.
    Uses psycopg2-binary for compatibility.
    """

    def __init__(self, db_url: Optional[str] = None):
        """Initialize checkpointer with database connection"""
        super().__init__(serde=LangChainJsonSerializer())

        if db_url is None:
            db_url = os.getenv("SUPABASE_DB_URL")
            if not db_url:
                # Build PostgreSQL connection URL from Supabase environment variables
                supabase_url = os.getenv("SUPABASE_URL", "")
                supabase_key = os.getenv("SUPABASE_ANON_KEY", "")

                if supabase_url and "xrhgrthdcaymxuqcgrmj" in supabase_url:
                    # Get the actual Supabase service role key for database access
                    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
                    # Build proper Supabase PostgreSQL connection URL
                    db_url = f"postgresql://postgres.xrhgrthdcaymxuqcgrmj:{service_key}@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
                else:
                    # Fallback - use local development database if available
                    db_url = "postgresql://postgres:postgres@localhost:5432/postgres"

        self.db_url = db_url
        self.is_setup = False

    def get_connection(self):
        """Get a new database connection"""
        return psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)

    async def setup(self) -> None:
        """Create necessary tables in Supabase if they don't exist"""
        if self.is_setup:
            return

        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Create checkpoints table
                cur.execute("""
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

                # Create checkpoint writes table
                cur.execute("""
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

                # Create indexes
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id 
                    ON langgraph_checkpoints(thread_id);
                """)

                conn.commit()
                self.is_setup = True
        finally:
            conn.close()

    async def aget_tuple(self, config: dict[str, Any]) -> Optional[CheckpointTuple]:
        """Get a checkpoint tuple by thread_id and checkpoint_id"""
        await self.setup()

        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                if checkpoint_id:
                    # Get specific checkpoint
                    cur.execute("""
                        SELECT checkpoint, metadata, parent_checkpoint_id, created_at
                        FROM langgraph_checkpoints 
                        WHERE thread_id = %s AND checkpoint_ns = %s AND checkpoint_id = %s
                    """, (thread_id, checkpoint_ns, checkpoint_id))
                else:
                    # Get latest checkpoint
                    cur.execute("""
                        SELECT checkpoint, metadata, parent_checkpoint_id, created_at, checkpoint_id
                        FROM langgraph_checkpoints 
                        WHERE thread_id = %s AND checkpoint_ns = %s
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """, (thread_id, checkpoint_ns))

                row = cur.fetchone()
                if not row:
                    return None

                # Parse checkpoint data
                checkpoint = row["checkpoint"]
                if isinstance(checkpoint, str):
                    checkpoint = json.loads(checkpoint)

                metadata = row["metadata"] or {}
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)

                # Get pending writes
                checkpoint_id_for_writes = checkpoint_id or row.get("checkpoint_id")
                cur.execute("""
                    SELECT task_id, channel, value, type
                    FROM langgraph_checkpoint_writes
                    WHERE thread_id = %s AND checkpoint_ns = %s AND checkpoint_id = %s
                    ORDER BY task_id, idx
                """, (thread_id, checkpoint_ns, checkpoint_id_for_writes))

                writes_rows = cur.fetchall()
                pending_writes = []
                for write_row in writes_rows:
                    value = write_row["value"]
                    if isinstance(value, str):
                        value = json.loads(value)
                    pending_writes.append((write_row["task_id"], write_row["channel"], value))

                return CheckpointTuple(
                    config=config,
                    checkpoint=checkpoint,
                    metadata=CheckpointMetadata(**metadata),
                    pending_writes=pending_writes,
                    parent_config=None
                )
        finally:
            conn.close()

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

        # Simple implementation - just yield empty for now
        # This is enough to satisfy the interface requirement
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
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = checkpoint.get("id") or str(uuid.uuid4())
        parent_checkpoint_id = config["configurable"].get("checkpoint_id")

        # Convert to JSON-serializable format
        checkpoint_data = Json(checkpoint)
        metadata_dict = {
            "source": getattr(metadata, "source", "update"),
            "step": getattr(metadata, "step", 1),
            "writes": getattr(metadata, "writes", {})
        }
        metadata_data = Json(metadata_dict)

        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
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
                conn.commit()
        finally:
            conn.close()

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
        writes: list[tuple[str, Any]],
        task_id: str,
    ) -> None:
        """Save pending writes"""
        await self.setup()

        if not writes:
            return

        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]

        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                for idx, (channel, value) in enumerate(writes):
                    value_data = Json(value) if value is not None else None

                    cur.execute("""
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
                conn.commit()
        finally:
            conn.close()


async def create_supabase_checkpointer() -> SupabaseCheckpointer:
    """Factory function to create and setup Supabase checkpointer"""
    checkpointer = SupabaseCheckpointer()
    await checkpointer.setup()
    return checkpointer
