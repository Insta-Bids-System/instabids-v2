# CIPHER PERMANENT MEMORY SETUP

## QUICK START - USE THIS DAILY

### Option 1: Windows Batch File (EASIEST)
```batch
cd C:\Users\Not John Or Justin\Documents\instabids
start-cipher-permanent.bat
```

### Option 2: Docker (MOST RELIABLE)
```bash
docker-compose -f docker-compose.cipher.yml up -d
```

### Option 3: Node.js Script
```bash
node cipher-permanent-fix.js
```

## YOUR MEMORY DATA LOCATIONS

### Primary Database (Your Original History)
- **Path**: `C:\Users\Not John Or Justin\data\cipher-sessions.db`
- **Content**: 11 records with InstaBids conversations
- **Status**: PRESERVED

### Permanent Location (New Safe Location)
- **Path**: `C:\Users\Not John Or Justin\cipher-permanent\cipher-sessions.db`
- **Content**: Migrated data + new memories
- **Status**: ACTIVE

### Docker Volume (If using Docker)
- **Path**: `C:\Users\Not John Or Justin\Documents\instabids\cipher-data\`
- **Content**: Persistent Docker storage
- **Status**: PERSISTENT

## WHY YOUR MEMORY "DISAPPEARED"

1. **Configuration Format Changed**: Cipher.yml structure changed between versions
2. **Database Path Changed**: Cipher looked in `instabids/data/` instead of `data/`
3. **Vector Embeddings Lost**: Search index disconnected from text
4. **Multiple Processes**: Zombie Node processes created confusion

## THE PERMANENT FIX

### 1. FIXED DATA PATHS
```javascript
const CIPHER_ROOT = 'C:/Users/Not John Or Justin/cipher-permanent';
const CIPHER_DB = `${CIPHER_ROOT}/cipher-sessions.db`;
```
These paths NEVER change, regardless of configuration.

### 2. DOCKER VOLUMES
```yaml
volumes:
  - ./cipher-data:/data        # Database
  - ./cipher-chroma:/chroma    # Vector embeddings
```
Docker ensures data persists even if container restarts.

### 3. AUTOMATIC MIGRATION
The scripts automatically copy existing data to permanent location.

## DAILY BACKUP ROUTINE

### Weekly Backup Command
```batch
copy "C:\Users\Not John Or Justin\cipher-permanent\cipher-sessions.db" "C:\Users\Not John Or Justin\backups\cipher-%date:~10,4%%date:~4,2%%date:~7,2%.db"
```

### Check Data Integrity
```bash
node check_db.js
```

## TROUBLESHOOTING

### If Memory Disappears Again

1. **Check Process Status**
```bash
tasklist | findstr cipher
```

2. **Verify Database Location**
```bash
dir C:\Users\Not John Or Justin\cipher-permanent\*.db
```

3. **Check Docker Status**
```bash
docker ps | findstr cipher
```

### Kill Zombie Processes
```batch
taskkill //F //IM node.exe //FI "COMMANDLINE eq *cipher*"
```

### Restore From Backup
```batch
copy "C:\Users\Not John Or Justin\backups\cipher-latest.db" "C:\Users\Not John Or Justin\cipher-permanent\cipher-sessions.db"
```

## INTEGRATION WITH INSTABIDS

### MCP Configuration
The Cipher MCP tool is available in Claude Code at:
- **Tool Name**: `cipher`
- **Available Functions**: 
  - `ask_cipher` - Query and store memories
  - `store_memory` - Save information
  - `search_memory` - Search past conversations

### Docker Network
Cipher runs on the same Docker network as InstaBids:
- Network: `instabids_instabids-network`
- Can communicate with all InstaBids containers

## NEVER DO THIS AGAIN

❌ **DON'T** modify cipher.yml directly
❌ **DON'T** run multiple Cipher instances
❌ **DON'T** change database paths
❌ **DON'T** delete the cipher-permanent folder
❌ **DON'T** run without the permanent scripts

## ALWAYS DO THIS

✅ **DO** use start-cipher-permanent.bat
✅ **DO** make weekly backups
✅ **DO** check integrity monthly
✅ **DO** use Docker for production
✅ **DO** keep the permanent folder safe

## TECHNICAL DETAILS

### What We Fixed
1. Configuration locked to specific paths
2. Database migration automated
3. Vector store made persistent
4. Docker volumes for data safety
5. Automatic process cleanup

### Architecture
```
Cipher MCP Server
├── SQLite Database (conversations)
├── ChromaDB (vector embeddings)
├── OpenAI API (embeddings generation)
└── MCP Interface (Claude Code connection)
```

### Data Flow
1. Claude Code → MCP Tool → Cipher Server
2. Cipher → OpenAI (create embeddings)
3. Embeddings → ChromaDB (persistent storage)
4. Conversations → SQLite (permanent database)

## YOUR DATA IS SAFE

- Original data: PRESERVED in `C:\Users\Not John Or Justin\data\`
- Permanent copy: ACTIVE in `cipher-permanent\`
- Docker volume: PERSISTENT in `cipher-data\`
- Backups: CREATE WEEKLY in `backups\`

## SUPPORT

If issues persist:
1. Run `node extract_memory.js` to see raw data
2. Check `cipher-mcp.log` for errors
3. Verify OpenAI API key is valid
4. Ensure Docker is running (if using Docker)

---

**Remember**: Your conversations were NEVER lost. They were just in a different location. This setup ensures that NEVER happens again.