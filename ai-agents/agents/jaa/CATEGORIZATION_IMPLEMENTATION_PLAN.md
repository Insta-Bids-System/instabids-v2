# JAA Agent Categorization Implementation Plan
**Created**: January 13, 2025
**Purpose**: Add intelligent categorization to JAA Agent for normalizing bid card data

## 🎯 **WHAT JAA WILL CATEGORIZE**

### **The 3 Key Fields JAA Will Populate:**

1. **service_category** (enum - work type)
   - One of 14 options: installation, repair, replacement, renovation, maintenance, ongoing, emergency, labor_only, consultation, events, rentals, lifestyle_wellness, professional_digital, ai_solutions

2. **project_type** (normalized string) 
   - Examples: "artificial_turf", "kitchen_renovation", "roof_repair"
   - Normalized from variations like "fake grass" → "artificial_turf"

3. **project_description** (AI-generated intelligent writeup)
   - Professional, detailed description of the project
   - Combines user's raw input with structured understanding
   - Example: "Complete artificial turf installation for 2,500 sq ft backyard including ground preparation, drainage system, and premium synthetic grass material"

## 📊 **WHAT JAA HAS ACCESS TO FOR CATEGORIZATION**

### **JAA Gets the FULL Context:**
```python
# JAA receives in process_conversation():
conversation_data = {
    "state": {
        "messages": [
            # FULL conversation history
            {"role": "user", "content": "I need my artificial grass repaired"},
            {"role": "assistant", "content": "I can help with that..."},
            {"role": "user", "content": "It's torn in multiple spots..."}
        ],
        "collected_info": {
            # CIA's extracted data
            "project_type": "artificial grass repair",  # Raw, not normalized
            "budget_range": "$5000-$10000",
            "urgency": "ASAP"
        }
    }
}
```

### **JAA's Categorization Inputs:**
1. ✅ **Full Conversation History** - All messages between user and CIA
2. ✅ **CIA's Collected Info** - Extracted project details (raw, unnormalized)
3. ✅ **Claude Opus 4 Analysis** - JAA's own AI understanding of the project
4. ✅ **Extracted Data** - JAA's structured extraction (budget, timeline, location, etc.)

## 🏗️ **IMPLEMENTATION ARCHITECTURE**

### **Step 1: Add Categorization Module to JAA**
```python
# New file: agents/jaa/categorization.py
class ProjectCategorizer:
    """Intelligent project categorization for bid cards"""
    
    def __init__(self):
        # Pre-built mappings
        self.project_type_mappings = {
            # Artificial turf variations
            "artificial grass": "artificial_turf",
            "fake grass": "artificial_turf",
            "synthetic turf": "artificial_turf",
            "synthetic grass": "artificial_turf",
            "astroturf": "artificial_turf",
            "fake lawn": "artificial_turf",
            
            # Kitchen variations
            "kitchen remodel": "kitchen_renovation",
            "kitchen renovation": "kitchen_renovation",
            "kitchen makeover": "kitchen_renovation",
            "kitchen update": "kitchen_renovation",
            
            # More mappings...
        }
        
        # Service category detection patterns
        self.service_patterns = {
            "repair": ["fix", "repair", "broken", "damaged", "torn", "leak"],
            "installation": ["install", "new", "add", "put in", "setup"],
            "replacement": ["replace", "swap", "change out", "new for old"],
            "renovation": ["remodel", "renovation", "makeover", "update", "renovate"],
            "maintenance": ["maintain", "service", "tune up", "clean", "inspect"],
            "emergency": ["urgent", "asap", "emergency", "immediately", "today"]
        }
    
    async def categorize(self, conversation_data: dict, extracted_data: dict, llm) -> dict:
        """
        Main categorization method
        
        Args:
            conversation_data: Full conversation from CIA
            extracted_data: JAA's extracted project data
            llm: Claude Opus 4 instance for intelligent analysis
        
        Returns:
            Categorized project data with normalized fields
        """
        # Step 1: Normalize project_type
        project_type = self._normalize_project_type(extracted_data)
        
        # Step 2: Determine service_category
        service_category = await self._determine_service_category(
            conversation_data, extracted_data, llm
        )
        
        # Step 3: Generate intelligent project description
        project_description = await self._generate_project_description(
            conversation_data, extracted_data, project_type, service_category, llm
        )
        
        return {
            "service_category": service_category,
            "project_type": project_type,
            "project_description": project_description,
            "categorization_confidence": self._calculate_confidence(...)
        }
```

### **Step 2: Integrate with JAA's Workflow**
```python
# In agents/jaa/agent.py

def _build_workflow(self) -> StateGraph:
    """Build the LangGraph workflow for intelligent bid card generation"""
    
    workflow = StateGraph(IntelligentJAAState)
    
    # Add nodes
    workflow.add_node("analyze_conversation", self._analyze_conversation)
    workflow.add_node("extract_project_data", self._extract_project_data)
    workflow.add_node("extract_dates", self._extract_dates)
    workflow.add_node("categorize_project", self._categorize_project)  # NEW NODE
    workflow.add_node("validate_extraction", self._validate_extraction)
    workflow.add_node("generate_bid_card", self._generate_bid_card)
    
    # Add edges
    workflow.add_edge(START, "analyze_conversation")
    workflow.add_edge("analyze_conversation", "extract_project_data")
    workflow.add_edge("extract_project_data", "extract_dates")
    workflow.add_edge("extract_dates", "categorize_project")  # NEW FLOW
    workflow.add_edge("categorize_project", "validate_extraction")
    workflow.add_edge("validate_extraction", "generate_bid_card")
    workflow.add_edge("generate_bid_card", END)
    
    return workflow.compile()

def _categorize_project(self, state: IntelligentJAAState) -> IntelligentJAAState:
    """NEW: Categorize project with normalized taxonomy"""
    print("[INTELLIGENT JAA] Stage 3: Categorizing project with normalized taxonomy...")
    
    # Initialize categorizer
    from .categorization import ProjectCategorizer
    categorizer = ProjectCategorizer()
    
    # Run categorization with full context
    categorization_result = await categorizer.categorize(
        conversation_data=state["conversation_data"],
        extracted_data=state["extracted_data"],
        llm=self.llm
    )
    
    # Add to state
    state["extracted_data"]["categorization"] = categorization_result
    
    print(f"[INTELLIGENT JAA] Categorized as: {categorization_result['service_category']} - {categorization_result['project_type']}")
    
    return state
```

### **Step 3: Update Bid Card Creation**
```python
# In agents/jaa/agent.py - modify _generate_bid_card method

def _generate_bid_card(self, state: IntelligentJAAState) -> IntelligentJAAState:
    """Step 4: Generate final bid card with categorized data"""
    
    extracted = state["extracted_data"]
    categorization = extracted.get("categorization", {})
    
    bid_card_data = {
        # NEW CATEGORIZED FIELDS
        "service_category": categorization.get("service_category"),
        "project_type": categorization.get("project_type"),  # NORMALIZED
        "project_description": categorization.get("project_description"),
        
        # EXISTING FIELDS
        "budget_min": extracted.get("budget_min"),
        "budget_max": extracted.get("budget_max"),
        "urgency_level": extracted.get("urgency_level"),
        # ... rest of fields
    }
```

## 📋 **CATEGORIZATION LOGIC EXAMPLES**

### **Example 1: Artificial Turf Repair**
```python
Input Conversation:
User: "I need my artificial grass fixed"
CIA: "What seems to be the problem?"
User: "It's torn in several spots and lifting at the edges"

JAA Categorization Process:
1. Detect "artificial grass" → Normalize to "artificial_turf"
2. Detect "fixed", "torn" → service_category = "repair"
3. Generate description: "Repair existing artificial turf installation including patching torn sections and re-securing lifted edges to restore lawn appearance and functionality"

Output:
{
    "service_category": "repair",
    "project_type": "artificial_turf",
    "project_description": "Repair existing artificial turf installation..."
}
```

### **Example 2: Kitchen Renovation**
```python
Input Conversation:
User: "Looking to do a complete kitchen makeover"
CIA: "What's your vision?"
User: "New cabinets, countertops, backsplash, everything"

JAA Categorization Process:
1. Detect "kitchen makeover" → Normalize to "kitchen_renovation"
2. Detect "complete", "makeover", "new everything" → service_category = "renovation"
3. Generate description: "Complete kitchen renovation including cabinet replacement, new countertops, backsplash installation, and comprehensive updates to transform the entire kitchen space"

Output:
{
    "service_category": "renovation",
    "project_type": "kitchen_renovation",
    "project_description": "Complete kitchen renovation including..."
}
```

## 🔧 **IMPLEMENTATION PHASES**

### **Phase 1: Basic Categorization (Week 1)**
- [ ] Create categorization.py with basic mappings
- [ ] Add 100 most common project_type normalizations
- [ ] Implement service_category detection logic
- [ ] Add categorization node to JAA workflow

### **Phase 2: AI-Enhanced Description (Week 2)**
- [ ] Implement Claude-powered project description generation
- [ ] Add confidence scoring system
- [ ] Create fallback logic for unknown project types

### **Phase 3: Testing & Refinement (Week 3)**
- [ ] Test with existing potential_bid_cards
- [ ] Refine mappings based on real data
- [ ] Add logging for new project type discovery
- [ ] Create admin review workflow for new types

### **Phase 4: Production Rollout (Week 4)**
- [ ] Deploy to production JAA agent
- [ ] Monitor categorization accuracy
- [ ] Weekly review of new project types
- [ ] Continuous improvement based on usage

## 📊 **SUCCESS METRICS**

### **Immediate Goals:**
- ✅ 100% of new bid cards have service_category populated
- ✅ 100% of new bid cards have normalized project_type
- ✅ 100% of new bid cards have AI-generated project_description

### **Quality Metrics:**
- 📊 95% categorization confidence for common projects
- 📊 80% confidence for edge cases
- 📊 <5% require manual admin review

### **Business Impact:**
- 🎯 Perfect bid card → contractor matching
- 🎯 Accurate group bidding clusters
- 🎯 Clean analytics and reporting
- 🎯 Better contractor discovery

## 🚨 **CRITICAL CONSIDERATIONS**

### **What NOT to Change:**
- ❌ Don't modify potential_bid_cards structure (keep messy on purpose)
- ❌ Don't change CIA Agent's extraction (raw data is fine)
- ❌ Don't create new tables (use existing fields)

### **What TO Focus On:**
- ✅ JAA as single point of categorization
- ✅ Clean, normalized bid_cards table
- ✅ Learning system for continuous improvement
- ✅ Admin oversight for quality control

## 💡 **KEY INSIGHT**

**JAA has EVERYTHING it needs:**
- Full conversation history to understand context
- CIA's extracted info for initial categorization hints
- Claude Opus 4 for intelligent analysis
- Complete control over bid card creation

**This makes JAA the PERFECT place for categorization - it has maximum context and is the gateway to the bid_cards table.**

---

## 🎯 **NEXT STEPS**

1. **Review this plan** - Does this match your vision?
2. **Approve categorization mappings** - Are the project_type normalizations correct?
3. **Confirm service categories** - Are the 14 categories final?
4. **Start implementation** - Begin with Phase 1 basic categorization

**JAA Agent Directory**: `C:\Users\Not John Or Justin\Documents\instabids\ai-agents\agents\jaa\`
**This Plan Location**: `CATEGORIZATION_IMPLEMENTATION_PLAN.md`