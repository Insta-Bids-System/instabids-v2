# Complete Agent Flow Test Plan - Dream Image Generation

## The Problem
- Using placeholder/demo images instead of real AI generation
- Making direct API calls instead of using proper agent system
- No actual conversation between homeowner and Iris AI agent
- Missing the complete user experience flow

## The Solution: End-to-End Agent Testing

### Phase 1: Identify the Correct Agent
**Goal**: Find which agent handles dream image generation conversations

1. **Check existing agents in system**:
   - CIA (Customer Interface Agent) - Main homeowner conversation agent
   - Iris AI Agent - Specialized for inspiration/vision generation
   - JAA (Job Assessment Agent) - Creates bid cards
   - Check if there's a specific Vision/Dream Generation agent

2. **Verify agent capabilities**:
   - Agent has access to DALL-E generation tools
   - Agent has memory across conversations
   - Agent can reference board images and user preferences
   - Agent can save generated images back to board

### Phase 2: Test Agent Memory & Context
**Goal**: Verify agent remembers board context and user preferences

1. **Start conversation as Demo Homeowner**:
   - Agent should know about existing kitchen board
   - Agent should reference current space + inspiration images
   - Agent should ask clarifying questions about vision preferences

2. **Test memory persistence**:
   - Agent remembers board ID: `26cf972b-83e4-484c-98b6-a5d1a4affee3`
   - Agent knows current space is compact white kitchen
   - Agent knows inspiration is modern industrial with exposed brick

### Phase 3: Test Dream Generation Conversation
**Goal**: Have natural conversation that leads to image generation

1. **Homeowner initiates**: "I want to see what my kitchen would look like with the industrial inspiration"

2. **Agent should**:
   - Reference the specific images from the board
   - Ask clarifying questions about preferences
   - Confirm what elements to include in the vision
   - Generate the actual DALL-E image
   - Save it to the board with 'vision' tags
   - Show the user the result

3. **Expected conversation flow**:
   ```
   User: "Generate my dream kitchen"
   
   Iris: "I can see your current compact kitchen and the modern industrial 
          inspiration with exposed brick. For your dream transformation, 
          would you like me to:
          - Keep your current layout but add the exposed brick wall?
          - Include the pendant lighting from the inspiration?
          - Any specific color preferences?"
   
   User: "Yes, keep layout, add brick wall and pendant lights"
   
   Iris: "Perfect! Generating your dream kitchen now..."
   [Calls DALL-E API with proper prompt]
   
   Iris: "Here's your AI-generated dream kitchen! I've saved it to your 
          vision board. What do you think?"
   ```

### Phase 4: Verify Complete Integration
**Goal**: Confirm the generated image appears in UI

1. **Backend verification**:
   - Image saved to `inspiration_images` table with `vision` tag
   - Proper board_id and homeowner_id associations
   - AI analysis metadata included

2. **Frontend verification**:
   - Image appears in "My Vision" column
   - Image has proper tags and analysis
   - User can interact with the image (view, delete, etc.)

3. **Agent verification**:
   - Agent can reference the generated image in future conversations
   - Agent remembers this generation in conversation history
   - Agent can offer to generate variations or improvements

### Phase 5: Test Error Handling & Fallbacks
**Goal**: Ensure system works even when things go wrong

1. **DALL-E API failures**: Agent should explain and offer alternatives
2. **Database save failures**: Agent should retry or notify user
3. **Image loading failures**: Frontend should show appropriate messages

## Implementation Steps

### Step 1: Identify and Test the Agent
- [ ] Find the correct agent (likely CIA or Iris)
- [ ] Test agent startup and basic conversation
- [ ] Verify agent has access to board context
- [ ] Confirm agent has DALL-E generation tools

### Step 2: Test Agent Memory
- [ ] Start conversation with board context
- [ ] Verify agent knows about existing images
- [ ] Test memory persistence across multiple messages

### Step 3: Test Generation Flow
- [ ] Have natural conversation leading to generation request
- [ ] Verify agent asks clarifying questions
- [ ] Confirm actual DALL-E API call (not placeholder)
- [ ] Verify image is saved with proper tags

### Step 4: Test UI Integration
- [ ] Refresh board view after generation
- [ ] Verify 3rd image appears in "My Vision" column
- [ ] Test image interaction and metadata display

### Step 5: Test Complete User Journey
- [ ] Demo user logs in
- [ ] Opens existing board with 2 images
- [ ] Starts conversation with agent
- [ ] Requests dream generation
- [ ] Confirms preferences
- [ ] Sees real generated image
- [ ] Image persists in board

## Success Criteria

✅ **Real AI Generation**: Actual DALL-E API call creates unique image
✅ **Agent Conversation**: Natural dialogue with clarifying questions  
✅ **Memory Integration**: Agent remembers board and user context
✅ **Database Persistence**: Generated image saved with proper metadata
✅ **UI Display**: Image appears in "My Vision" column immediately
✅ **User Experience**: Complete flow from conversation to visual result

## Files to Test/Modify

### Backend Agent Files:
- `ai-agents/agents/cia/agent.py` - Main conversation agent
- `ai-agents/agents/iris/` - Check if Iris agent exists
- `ai-agents/memory/` - Memory and context management
- `ai-agents/api/image_generation.py` - Generation API endpoint

### Frontend Files:
- `web/src/components/inspiration/BoardView.tsx` - Board display
- `web/src/components/chat/` - Chat interface components
- `web/src/contexts/AuthContext.tsx` - Demo user authentication

### Test Files:
- Create: `test_complete_agent_conversation.py`
- Create: `test_iris_generation_flow.py`
- Update: `test_complete_flow_final.py`

## Next Actions

1. **Identify the correct agent** that should handle dream generation
2. **Test agent conversation** with proper board context
3. **Verify real DALL-E generation** (not placeholder images)
4. **Confirm UI integration** shows generated image
5. **Test complete user journey** end-to-end

This plan ensures we test the ACTUAL agent system as designed, not shortcuts or workarounds.