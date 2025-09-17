# Cipher MCP Tool Setup Guide for InstaBids Multi-Agent System

## 🚀 Quick Setup (Already Added to Your Config!)

I've already added Cipher to your Claude Desktop config. You just need to:

1. **Add your API keys** to the config:
   ```json
   "env": {
     "OPENAI_API_KEY": "your-actual-openai-key",
     "ANTHROPIC_API_KEY": "your-actual-anthropic-key"
   }
   ```

2. **Restart Claude Desktop** to load the new MCP server

3. **Test Cipher** is working:
   - Look for "cipher" in your available tools
   - You should see `ask_cipher` tool available

## 🛠️ Alternative Setup Methods

### Option 1: Global Installation (For All Projects)
```bash
# Install globally
npm install -g @byterover/cipher

# Run standalone server
cipher --mode mcp --mcp-transport-type sse --mcp-port 4000
```

### Option 2: Docker Setup (For Team Sharing)
```bash
# Clone and setup
git clone https://github.com/campfirein/cipher.git
cd cipher
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

### Option 3: Advanced Aggregator Mode
This exposes ALL tools from Cipher, not just `ask_cipher`:

```json
{
  "cipher-aggregator": {
    "command": "npx",
    "args": ["-y", "@byterover/cipher", "--mode", "mcp"],
    "env": {
      "MCP_SERVER_MODE": "aggregator",
      "OPENAI_API_KEY": "your-key",
      "ANTHROPIC_API_KEY": "your-key"
    }
  }
}
```

## 🔧 Configuration Options

### Environment Variables
- `CIPHER_MEMORY_DIR`: Where to store memories (default: `~/.cipher/memories`)
- `CIPHER_VECTOR_STORE`: Vector database type (default: `chromadb`)
- `CIPHER_EMBEDDING_MODEL`: Model for embeddings (default: `text-embedding-3-small`)
- `CIPHER_LLM_PROVIDER`: LLM provider (default: `openai`)

### Memory Types
1. **Workspace Memory**: Project-specific context
2. **Reasoning Memory**: Code generation decisions
3. **Team Memory**: Shared across all developers

## 🎯 How to Use Cipher in Your Agents

### For Your Database Consultant
```python
# Store discovered schema
async def store_database_knowledge(self):
    await ask_cipher(
        "Store this database schema discovery: " + 
        json.dumps(self.discovered_schema)
    )

# Retrieve on next run
async def load_previous_knowledge(self):
    knowledge = await ask_cipher(
        "What do we know about the Supabase database schema?"
    )
    return knowledge
```

### For Agent Coordination
```python
# Agent 1 stores work done
await ask_cipher("Agent 1 completed: Built messaging system with tables X, Y, Z")

# Agent 6 checks what's been done
completed_work = await ask_cipher("What features have other agents completed?")
```

### For Test Results
```python
# Store test results
await ask_cipher(f"Test results for {feature}: {test_results}")

# Check historical test data
history = await ask_cipher(f"Show all test results for {feature}")
```

## 🔍 Cipher vs Your Current Memory Attempts

| Feature | Your JSON Files | Cipher |
|---------|----------------|---------|
| Persistence | ✅ Manual | ✅ Automatic |
| Search | ❌ None | ✅ Vector search |
| Multi-agent | ❌ File conflicts | ✅ Shared memory |
| Versioning | ❌ None | ✅ Built-in |
| Team sharing | ❌ Git only | ✅ Real-time |
| Context size | ❌ Limited | ✅ Unlimited |

## 🚨 Important Notes

1. **API Keys Required**: Cipher needs OpenAI or Anthropic keys for embeddings
2. **Storage Location**: Memories stored locally by default (can configure)
3. **Team Sharing**: Use Docker setup for multi-developer teams
4. **Privacy**: All memories stored locally unless you configure cloud storage

## 📝 Example Use Cases for InstaBids

### 1. Database Discovery Persistence
```
User: "What tables are related to bid cards?"
Agent: *asks cipher for stored schema knowledge*
Cipher: "From previous discovery: 15 tables directly related..."
```

### 2. Cross-Session Context
```
Session 1: "Built complete messaging system"
*Close Claude*
Session 2: "What did we build yesterday?"
Agent: *asks cipher*
Cipher: "Yesterday you built a messaging system with..."
```

### 3. Multi-Agent Coordination
```
Agent 1: *stores* "Completed frontend messaging UI"
Agent 2: *queries* "What frontend components exist?"
Cipher: "Agent 1 completed messaging UI components..."
```

## 🎉 You're Ready!

Just restart Claude Desktop and you'll have persistent memory across all your agents!

**Next Steps**:
1. Add your actual API keys to the config
2. Restart Claude Desktop
3. Test with: "Store a test memory in Cipher"
4. Start using in your database consultant!