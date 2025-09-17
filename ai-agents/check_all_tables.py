import os
from dotenv import load_dotenv
from supabase import create_client

# Load root env
load_dotenv(r'C:\Users\Not John Or Justin\Documents\instabids\.env', override=True)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

print(f"URL: {url}")
print(f"Key: {key[:20]}...")

# Get all tables the CIA needs access to
supabase = create_client(url, key)

# Get all public tables
tables_result = supabase.table("bid_cards").select("*").limit(0).execute()
print("\nTesting table access...")

# List of tables CIA needs
cia_required_tables = [
    # Core tables
    "unified_conversations",
    "unified_messages", 
    "unified_conversation_memory",
    "unified_message_attachments",
    "unified_conversation_participants",
    
    # User/Project tables
    "homeowners",
    "projects",
    "properties",
    "bid_cards",
    "bid_card_items",
    "contractor_bids",
    
    # Memory tables
    "user_memories",
    "user_conversation_history",
    
    # RFI/Photo tables
    "rfi_requests",
    "rfi_responses",
    "project_images",
    
    # Messaging tables
    "messages",
    "message_filters",
    "contractor_aliases",
    
    # Session tables
    "user_sessions",
    "conversation_checkpoints"
]

print("\nTables CIA needs access to:")
for table in cia_required_tables:
    try:
        result = supabase.table(table).select("*").limit(0).execute()
        print(f"[OK] {table} - accessible")
    except Exception as e:
        print(f"[ERROR] {table} - {str(e)[:50]}")