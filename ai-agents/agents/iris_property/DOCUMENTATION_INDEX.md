# IRIS Property Agent - Documentation Index
**Last Updated**: August 29, 2025  
**Purpose**: Quick reference to all documentation for the iris_property agent

## 📚 Active Documentation

### Core Documentation
1. **[README.md](README.md)** - Main documentation
   - Complete system architecture
   - Conversational flow explanation
   - Component descriptions
   - API endpoints
   - Usage examples

2. **[ACTUAL_FUNCTIONALITY_ANALYSIS.md](ACTUAL_FUNCTIONALITY_ANALYSIS.md)** - Implementation status
   - What's supposed to work vs what actually works
   - Component status tracking
   - Recent implementation updates

3. **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing documentation
   - Quick test commands
   - Conversation flow testing scenarios
   - Component testing examples
   - End-to-end test scripts

4. **[MEMORY_SYSTEM_DEEP_DIVE.md](MEMORY_SYSTEM_DEEP_DIVE.md)** - Technical reference
   - Three-tier memory architecture
   - Database table relationships
   - Memory persistence details

## 📁 Code Structure

```
iris_property/
├── agent.py                    # Main orchestrator
├── models/                     # Data models
│   ├── database.py            # PropertyTask, PropertyRoom, PotentialBidCard
│   ├── requests.py            # API request models
│   └── responses.py           # API response models
├── services/                   # Core services
│   ├── conversation_manager.py # State management
│   ├── task_manager.py        # Task CRUD operations
│   ├── vision_analyzer.py     # OpenAI Vision integration
│   ├── room_detector.py       # Room identification
│   ├── photo_manager.py       # Photo storage
│   ├── memory_manager.py      # Memory persistence
│   └── context_builder.py     # Context aggregation
├── workflows/                  # Conversation flows
│   ├── conversational_flow.py # Main state machine
│   ├── image_workflow.py      # Image processing
│   └── consultation_workflow.py # General consultation
├── routes.py                   # API endpoints
└── utils/
    └── supabase_client.py     # Database connection
```

## 🗂️ Archived Documentation

Old/outdated documentation has been moved to `archive_outdated_docs/`:
- Pre-conversational implementation plans
- Outdated fix plans
- Historical audit reports
- Completed implementation plans

## 🔑 Key Concepts

### Conversational State Machine
The agent uses a 7-state conversation flow:
1. `INITIAL` - Starting state
2. `AWAITING_ROOM` - Waiting for room identification
3. `CONFIRMING_ROOM` - Confirming detected room
4. `ROOM_DOCUMENTED` - Photos stored
5. `SUGGESTING_TASKS` - Proposing maintenance tasks
6. `AWAITING_TASK_CONFIRM` - Waiting for approval
7. `TASKS_CREATED` - Tasks created

### Core Innovation
- **Conversational, not automated** - Engages in dialogue
- **Room-aware photo storage** - Links photos to specific rooms
- **Task suggestion with confirmation** - User approves before creation
- **State persistence** - Maintains context across messages

## 🚀 Quick Start

1. **Import the agent**:
   ```python
   from agents.iris_property.agent import IRISAgent
   agent = IRISAgent()
   ```

2. **Handle a conversation**:
   ```python
   response = await agent.handle_unified_chat(request)
   ```

3. **Test room detection**:
   ```python
   from agents.iris_property.services.room_detector import RoomDetector
   detector = RoomDetector()
   result = detector.detect_room_from_message("kitchen leak")
   ```

## 📈 Current Status

- **Production Readiness**: 95% Complete
- **Core Features**: ✅ All implemented
- **Remaining Work**: Redis integration, WebSocket support, rate limiting

---

*This index provides quick navigation to all iris_property documentation. Start with README.md for complete system understanding.*