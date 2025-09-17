#!/usr/bin/env python3
"""
Check what's in the unified tables vs old tables
"""

import database_simple
import json
from datetime import datetime, timedelta

db = database_simple.get_client()

print("\n" + "="*60)
print("CHECKING CONVERSATION STORAGE TABLES")
print("="*60)

# Check old agent_conversations table
print("\n--- OLD agent_conversations TABLE ---")
old_result = db.table("agent_conversations").select("*").order("created_at", desc=True).limit(5).execute()

if old_result.data:
    print(f"Found {len(old_result.data)} recent records:")
    for conv in old_result.data:
        created = conv.get("created_at", "")[:19] if conv.get("created_at") else "Unknown"
        print(f"  - {conv['agent_type']}: {conv['thread_id'][:30]}... (created: {created})")
else:
    print("✅ No records found (table is empty or unused)")

# Check unified_conversations table
print("\n--- NEW unified_conversations TABLE ---")
unified_result = db.table("unified_conversations").select("*").order("created_at", desc=True).limit(5).execute()

if unified_result.data:
    print(f"Found {len(unified_result.data)} recent records:")
    for conv in unified_result.data:
        metadata = conv.get("metadata", {})
        agent_type = metadata.get("agent_type", "Unknown")
        session_id = metadata.get("session_id", "No session")[:30]
        created = conv.get("created_at", "")[:19] if conv.get("created_at") else "Unknown"
        print(f"  - {agent_type}: {session_id}... (created: {created})")
        print(f"    Title: {conv.get('title', 'Untitled')}")
else:
    print("❌ No records found")

# Check unified_messages table
print("\n--- unified_messages TABLE ---")
messages_result = db.table("unified_messages").select("*").order("created_at", desc=True).limit(5).execute()

if messages_result.data:
    print(f"Found {len(messages_result.data)} recent messages:")
    for msg in messages_result.data:
        sender = msg.get("sender_type", "Unknown")
        content_preview = msg.get("content", "")[:50] if msg.get("content") else "Empty"
        created = msg.get("created_at", "")[:19] if msg.get("created_at") else "Unknown"
        print(f"  - {sender}: {content_preview}... (created: {created})")
else:
    print("❌ No messages found")

# Check unified_conversation_memory table
print("\n--- unified_conversation_memory TABLE ---")
memory_result = db.table("unified_conversation_memory").select("*").order("created_at", desc=True).limit(5).execute()

if memory_result.data:
    print(f"Found {len(memory_result.data)} recent memory entries:")
    for mem in memory_result.data:
        mem_type = mem.get("memory_type", "Unknown")
        mem_key = mem.get("memory_key", "Unknown")
        created = mem.get("created_at", "")[:19] if mem.get("created_at") else "Unknown"
        print(f"  - {mem_type}: {mem_key} (created: {created})")
else:
    print("❌ No memory entries found")

# Summary
print("\n" + "="*60)
print("MIGRATION STATUS SUMMARY")
print("="*60)

# Count records from today
today = datetime.now().date().isoformat()

old_today = db.table("agent_conversations").select("count").gte("created_at", today).execute()
old_today_count = old_today.data[0]["count"] if old_today.data else 0

unified_today = db.table("unified_conversations").select("count").gte("created_at", today).execute()
unified_today_count = unified_today.data[0]["count"] if unified_today.data else 0

print(f"\nRecords created today ({today}):")
print(f"  Old agent_conversations: {old_today_count}")
print(f"  New unified_conversations: {unified_today_count}")

if unified_today_count > 0 and old_today_count == 0:
    print("\n✅ MIGRATION SUCCESSFUL!")
    print("   System is using unified tables exclusively")
elif unified_today_count > 0 and old_today_count > 0:
    print("\n⚠️ PARTIAL MIGRATION")
    print("   Both old and new systems are being used")
elif old_today_count > 0:
    print("\n❌ MIGRATION NOT WORKING")
    print("   System is still using old tables")
else:
    print("\n❓ NO RECENT ACTIVITY")
    print("   Cannot determine migration status")

# Check which agents are using which system
print("\n--- AGENT USAGE ANALYSIS ---")

# Check CIA usage
cia_old = db.table("agent_conversations").select("count").eq("agent_type", "CIA").execute()
cia_old_count = cia_old.data[0]["count"] if cia_old.data else 0

cia_new = db.table("unified_conversations").select("count").ilike("metadata->>agent_type", "CIA").execute()
cia_new_count = cia_new.data[0]["count"] if cia_new.data else 0

print(f"CIA Agent:")
print(f"  Old system: {cia_old_count} conversations")
print(f"  New system: {cia_new_count} conversations")

# Check IRIS usage
iris_new = db.table("unified_conversations").select("count").ilike("metadata->>agent_type", "IRIS").execute()
iris_new_count = iris_new.data[0]["count"] if iris_new.data else 0

print(f"IRIS Agent:")
print(f"  Old system: 0 conversations (never used old system)")
print(f"  New system: {iris_new_count} conversations")

# Check COIA usage
coia_old = db.table("agent_conversations").select("count").eq("agent_type", "COIA").execute()
coia_old_count = coia_old.data[0]["count"] if coia_old.data else 0

coia_new = db.table("unified_conversations").select("count").ilike("metadata->>agent_type", "COIA").execute()
coia_new_count = coia_new.data[0]["count"] if coia_new.data else 0

print(f"COIA Agent:")
print(f"  Old system: {coia_old_count} conversations")
print(f"  New system: {coia_new_count} conversations")

print("\n" + "="*60)