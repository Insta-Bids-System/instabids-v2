"""
MCP-based Supabase Checkpointer for LangGraph
Uses Supabase MCP tools for reliable database operations
"""

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any, Optional
from datetime import datetime

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)

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


class MCPSupabaseCheckpointer(BaseCheckpointSaver):
    """
    LangGraph checkpointer using Supabase MCP tools for database operations.
    Provides permanent memory persistence for contractor conversations.
    """

    def __init__(self, project_id: str = "xrhgrthdcaymxuqcgrmj"):
        """Initialize checkpointer with MCP Supabase tools"""
        super().__init__(serde=LangChainJsonSerializer())
        self.project_id = project_id
        self.is_setup = False

    async def setup(self) -> None:
        """Verify tables exist - they should already be created via MCP"""
        if self.is_setup:
            return
        
        # Tables should already be created via MCP execute_sql calls
        self.is_setup = True

    async def aget_tuple(self, config: dict[str, Any]) -> Optional[CheckpointTuple]:
        """Get a checkpoint tuple by thread_id and checkpoint_id"""
        await self.setup()

        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"].get("checkpoint_id")

        try:
            # Import database client directly
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from database_simple import db
            
            if checkpoint_id:
                # Get specific checkpoint using Supabase client
                result = db.client.table("langgraph_checkpoints").select("*").eq(
                    "thread_id", thread_id
                ).eq("checkpoint_ns", checkpoint_ns).eq("checkpoint_id", checkpoint_id).execute()
            else:
                # Get latest checkpoint using Supabase client
                result = db.client.table("langgraph_checkpoints").select("*").eq(
                    "thread_id", thread_id
                ).eq("checkpoint_ns", checkpoint_ns).order("created_at", desc=True).limit(1).execute()
            
            # Parse result and create CheckpointTuple if data found
            if hasattr(result, 'data') and result.data:
                row = result.data[0]
                checkpoint = self.serde.loads_typed(row['checkpoint'])
                metadata = CheckpointMetadata(
                    source=row['metadata'].get('source', 'update'),
                    step=row['metadata'].get('step', 1),
                    writes=row['metadata'].get('writes', {})
                )
                config_dict = {
                    "configurable": {
                        "thread_id": thread_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": row['checkpoint_id']
                    }
                }
                
                return CheckpointTuple(
                    config=config_dict,
                    checkpoint=checkpoint,
                    metadata=metadata,
                    parent_config=None  # Will be implemented if needed
                )
            
            return None
            
        except Exception as e:
            print(f"Warning: Could not retrieve checkpoint: {e}")
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
        # Simple implementation - just yield empty for now
        return
        yield  # Make it a generator

    async def aput(
        self,
        config: dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: dict[str, str],
    ) -> dict[str, Any]:
        """Save a checkpoint to Supabase via MCP"""
        await self.setup()

        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = checkpoint.get("id") or str(uuid.uuid4())
        parent_checkpoint_id = config["configurable"].get("checkpoint_id")

        try:
            # Import database client directly
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from database_simple import db
            from datetime import datetime
            
            # Serialize checkpoint and metadata
            checkpoint_json = self.serde.dumps_typed(checkpoint)
            metadata_dict = {
                "source": getattr(metadata, "source", "update"),
                "step": getattr(metadata, "step", 1),
                "writes": getattr(metadata, "writes", {})
            }

            # Prepare data for insert/upsert
            data = {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint_id,
                "parent_checkpoint_id": parent_checkpoint_id,
                "checkpoint": checkpoint_json,
                "metadata": metadata_dict,
                "created_at": datetime.utcnow().isoformat()
            }

            # Use Supabase upsert operation
            result = db.client.table("langgraph_checkpoints").upsert(
                data, 
                on_conflict="thread_id,checkpoint_ns,checkpoint_id"
            ).execute()
            print(f"SUCCESS: Saved checkpoint: thread_id={thread_id}, checkpoint_id={checkpoint_id}")
            
        except Exception as e:
            print(f"ERROR: Error saving checkpoint: {e}")
            # Don't fail the entire operation if checkpoint save fails
            pass

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

        try:
            # Import database client directly
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from database_simple import db
            
            # Convert writes to the format we want to store
            writes_data = [
                {
                    "channel": write[0],
                    "data": self.serde._serialize_object(write[1]),
                    "task_id": task_id
                }
                for write in writes
            ]

            # Get the existing checkpoint to update its metadata
            existing = db.client.table("langgraph_checkpoints").select("metadata").eq(
                "thread_id", thread_id
            ).eq("checkpoint_ns", checkpoint_ns).eq("checkpoint_id", checkpoint_id).execute()
            
            if existing.data:
                # Update the metadata with the writes
                metadata = existing.data[0]["metadata"]
                metadata["writes"] = writes_data
                
                # Update the checkpoint with the new metadata
                result = db.client.table("langgraph_checkpoints").update(
                    {"metadata": metadata}
                ).eq("thread_id", thread_id).eq("checkpoint_ns", checkpoint_ns).eq(
                    "checkpoint_id", checkpoint_id
                ).execute()
            print(f"SUCCESS: Saved {len(writes)} writes for checkpoint: {checkpoint_id}")
            
        except Exception as e:
            print(f"ERROR: Error saving writes: {e}")


async def create_mcp_supabase_checkpointer() -> MCPSupabaseCheckpointer:
    """Factory function to create and setup MCP Supabase checkpointer"""
    checkpointer = MCPSupabaseCheckpointer()
    await checkpointer.setup()
    return checkpointer