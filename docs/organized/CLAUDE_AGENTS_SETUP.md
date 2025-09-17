# Claude Multi-Agent Setup Guide

## Overview
This setup allows you to run multiple Claude agents simultaneously, each with:
- Their own identity and instructions
- Separate todo lists
- Persistent conversations
- Easy PowerShell aliases

## Setup Complete ✅

### 1. **PowerShell Functions Created**
You can now type in any PowerShell window:
- `claude1` - Frontend Flow Specialist
- `claude2` - Backend Core
- `claude3` - Homeowner UX
- `claude4` - Contractor UX
- `claude5` - Marketing Growth
- `claude6` - Codebase QA
- `claude` - Generic Claude (no specific agent)

### 2. **Conversation Persistence**
Each agent has a **fixed session ID** for continuity:
- Agent 1: `11111111-1111-1111-1111-111111111111`
- Agent 2: `22222222-2222-2222-2222-222222222222`
- Agent 3: `33333333-3333-3333-3333-333333333333`
- Agent 4: `44444444-4444-4444-4444-444444444444`
- Agent 5: `55555555-5555-5555-5555-555555555555`
- Agent 6: `66666666-6666-6666-6666-666666666666`

### 3. **Usage Examples**

#### Start a new conversation:
```powershell
claude1              # Starts Agent 1 with persistent session
```

#### Continue last conversation:
```powershell
claude1 -c           # Continue Agent 1's last conversation
```

#### Resume a specific conversation:
```powershell
claude1 -r           # Shows list of past conversations to resume
```

## How It Works

### 1. **Working Directory**
Each command automatically:
- Changes to the agent's folder (e.g., `instabids/agent1`)
- Claude reads the local `.claude/CLAUDE.md` for instructions
- Uses local `.claude/todo.md` for that agent's tasks

### 2. **Session Persistence**
- Each agent uses a **fixed UUID** for its session
- This means closing and reopening will maintain context
- The conversation persists across sessions
- Todo lists are separate per agent

### 3. **MCP Tools**
- All agents share the same MCP tools (Docker, Supabase, etc.)
- This is configured globally in your home `.claude` folder
- Each agent can use all tools but follows their role boundaries

## Important Notes

### PowerShell Profile
Your functions are saved in:
```
C:\Users\Not John Or Justin\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
```

To reload after changes:
```powershell
. $PROFILE
```

### Claude Version
Using Claude 1.0.63 with auto-updates disabled (as configured earlier)

### Folder Structure
```
instabids/
├── agent1/
│   ├── .claude/
│   │   ├── CLAUDE.md    # Agent 1 instructions
│   │   └── todo.md      # Agent 1 tasks
│   └── frontend.bat     # Alternative launcher
├── agent2/              # (Create as needed)
├── agent3/              # (Create as needed)
└── ...
```

## Next Steps

To set up agents 2-6:
1. Create their folders: `mkdir agent2\.claude`, etc.
2. Create their CLAUDE.md files with merged instructions
3. They're ready to use with `claude2`, `claude3`, etc.

## Tips

- **Multiple Windows**: You can run `claude1` in one PowerShell and `claude2` in another
- **Shared Code**: All agents work on the same `instabids` codebase
- **Coordination**: Use the main CLAUDE.md rules to avoid conflicts
- **Testing**: Each agent should create tests in `ai-agents/tests/agent[1-6]/`

## Troubleshooting

If PowerShell functions don't work:
1. Open new PowerShell window (profile loads on startup)
2. Or manually reload: `. $PROFILE`
3. Check Claude is in PATH: `claude --version`

If conversations don't persist:
- The session IDs are hardcoded for consistency
- Check `.claude` folder exists in agent directory
- Claude stores conversations in your home directory database