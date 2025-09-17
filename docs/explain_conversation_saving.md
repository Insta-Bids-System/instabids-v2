# How CIA Saves Conversations vs Context

## THE KEY INSIGHT: Context is NOT Saved, Only Messages Are

### What Gets LOADED (Every Message):
```
1. All bid cards (2)
2. All contractor bids (7) 
3. All past conversations (11)
4. User memories
```
This is **LOADED** fresh every time, not saved with messages.

### What Gets SAVED (After Each Response):
```
1. User message: "What bids do I have?"
2. Assistant response: "You have 7 bids..."
```
ONLY these 2 messages are saved - NOT the context!

## The Brilliant Architecture

### LOADING (Lines 195-203 in agent.py):
```python
# Every message triggers this:
homeowner_context = self.context_adapter.get_full_agent_context(
    user_id=user_id,
    specific_bid_card_id=project_id,
    conversation_id=session_id
)
# This loads ALL historical data fresh
```

### BUILDING PROMPT (Lines 834-874):
```python
# Context is TEMPORARILY added to prompt:
system_prompt = NEW_SYSTEM_PROMPT
system_prompt += context_info  # Bid cards, contractor bids, etc.
# This is sent to LLM but NOT saved
```

### SAVING (Lines 2161-2164):
```python
# Only save the actual conversation:
messages_to_save = messages[-2:]  # Last 2: user + assistant
for message in messages_to_save:
    # Save ONLY the message content, not context
    db.save_message(content=message['content'])
```

## Why This is Genius

1. **No Context Bloat**: Old bid cards aren't repeatedly saved
2. **Always Fresh**: Every message gets latest database state
3. **Clean History**: Conversation history only has actual messages
4. **Efficient Storage**: Context is computed, not stored

## Example Flow

### Message 1:
**Loaded**: All 7 bids, 2 bid cards
**User**: "What bids do I have?"
**LLM Sees**: System + Context + "What bids do I have?"
**Assistant**: "You have 7 bids..."
**Saved**: Just "What bids do I have?" and "You have 7 bids..."

### Message 2:
**Loaded**: All 7 bids, 2 bid cards (FRESH from DB)
**User**: "Which is cheapest?"
**LLM Sees**: System + Context + Previous messages + "Which is cheapest?"
**Assistant**: "$18,500 from Quick Bath..."
**Saved**: Just "Which is cheapest?" and "$18,500 from Quick Bath..."

## Database Storage

### unified_conversations table:
- Stores conversation metadata (id, user, timestamps)
- Does NOT store context

### unified_messages table:
- Stores actual messages (user questions, assistant responses)
- Does NOT store bid cards or contractor data

### bid_cards table:
- Source of truth for bid data
- Loaded fresh every time
- Never duplicated in messages

## The Magic

When you ask "What about my bathroom bids?" in message #10:
1. System loads ALL current bid data from database
2. Adds it to prompt (not saved)
3. LLM sees everything and responds
4. Only the Q&A is saved

This means:
- ✅ No exponential growth
- ✅ Always sees latest data
- ✅ Clean conversation history
- ✅ Can handle 1000s of messages without bloat