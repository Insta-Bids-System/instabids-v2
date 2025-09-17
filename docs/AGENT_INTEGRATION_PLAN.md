# Agent Integration & Monitoring Plan
**Created**: August 8, 2025
**Purpose**: Connect backend agents to UI for real-time monitoring, testing, and audit trails

## 🎯 CRITICAL BACKEND AGENTS REQUIRING UI VISIBILITY

### **1. CIA (Customer Interface Agent)**
- **Purpose**: Extracts project details from homeowner conversations
- **What to Monitor**: 
  - Conversation flow and extraction success
  - Project data extracted (budget, timeline, urgency)
  - Bid card creation trigger
- **UI Features Needed**:
  - View conversation history
  - See extracted project data
  - Manual retry/correction options

### **2. JAA (Job Assessment Agent)**
- **Purpose**: Creates bid cards from CIA data
- **What to Monitor**:
  - Bid card generation success/failure
  - Data validation errors
  - Database save status
- **UI Features Needed**:
  - View bid card creation logs
  - Edit/retry failed bid cards
  - See validation errors

### **3. CDA (Contractor Discovery Agent)**
- **Purpose**: Finds contractors for projects
- **What to Monitor**:
  - Discovery run status
  - Number of contractors found per tier
  - Match quality scores
- **UI Features Needed**:
  - Trigger manual discovery
  - View discovery results
  - Filter/sort contractors by match score

### **4. EAA (Email Acquisition Agent)** ⭐ CRITICAL
- **Purpose**: Sends emails to contractors
- **What to Monitor**:
  - Email generation (personalized content)
  - Send status (success/failure)
  - Delivery tracking
- **UI Features Needed**:
  - Preview generated emails
  - Manual send trigger
  - View sent email history
  - Delivery status tracking

### **5. WFA (Website Form Agent)** ⭐ CRITICAL
- **Purpose**: Fills contractor website forms
- **What to Monitor**:
  - Form detection success
  - Field mapping accuracy
  - Submission confirmation
- **UI Features Needed**:
  - Preview form data
  - Manual form fill trigger
  - Screenshot of filled forms
  - Submission confirmation logs

## 🔧 IMPLEMENTATION PHASES

### **Phase 1: Hook Up Campaign Assignment to Agents** (IMMEDIATE)

#### Step 1: Create Agent Trigger Service
```python
# ai-agents/services/agent_orchestrator.py
class AgentOrchestrator:
    def __init__(self):
        self.eaa = EAAAgent()
        self.wfa = WFAAgent()
        
    async def trigger_contractor_outreach(
        self, 
        contractor_id: str, 
        campaign_id: str,
        channel: str = "auto"
    ):
        """Trigger appropriate agent based on contractor data"""
        contractor = await get_contractor_details(contractor_id)
        campaign = await get_campaign_details(campaign_id)
        
        results = {
            "contractor_id": contractor_id,
            "campaign_id": campaign_id,
            "actions": []
        }
        
        # Email outreach
        if contractor.email and channel in ["auto", "email"]:
            email_result = await self.eaa.send_campaign_email(
                contractor, 
                campaign
            )
            results["actions"].append({
                "type": "email",
                "status": email_result.status,
                "details": email_result.details,
                "timestamp": datetime.now()
            })
            
        # Website form outreach
        if contractor.website and channel in ["auto", "form"]:
            form_result = await self.wfa.fill_contractor_form(
                contractor,
                campaign
            )
            results["actions"].append({
                "type": "form",
                "status": form_result.status,
                "screenshot": form_result.screenshot_url,
                "timestamp": datetime.now()
            })
            
        # Store results for audit
        await store_agent_action_log(results)
        
        return results
```

#### Step 2: Modify Campaign Assignment Endpoint
```python
# Update campaign_management_api.py
@router.post("/campaigns/{campaign_id}/assign-contractors")
async def assign_contractors_to_campaign(
    campaign_id: str,
    contractor_data: dict
):
    # ... existing assignment code ...
    
    # NEW: Trigger agent outreach
    orchestrator = AgentOrchestrator()
    for contractor_id in contractor_ids:
        try:
            outreach_result = await orchestrator.trigger_contractor_outreach(
                contractor_id,
                campaign_id
            )
            # Store result in database
            await store_outreach_result(outreach_result)
        except Exception as e:
            logger.error(f"Failed to trigger outreach for {contractor_id}: {e}")
            
    return response
```

### **Phase 2: Build Agent Monitoring Dashboard**

#### Component Structure:
```typescript
// web/src/components/admin/AgentMonitoring.tsx
interface AgentStatus {
  id: string;
  name: string;
  status: 'idle' | 'running' | 'error';
  lastAction: Date;
  successRate: number;
  currentTask?: {
    type: string;
    contractor: string;
    campaign: string;
    progress: number;
  };
}

const AgentMonitoring = () => {
  // Real-time WebSocket connection for updates
  const agents = useWebSocket('/ws/agents');
  
  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Agent Status Cards */}
      <AgentStatusCard agent="EAA" />
      <AgentStatusCard agent="WFA" />
      <AgentStatusCard agent="CDA" />
      <AgentStatusCard agent="CIA" />
      
      {/* Agent Action Log */}
      <AgentActionLog />
      
      {/* Manual Trigger Panel */}
      <ManualAgentTrigger />
    </div>
  );
};
```

### **Phase 3: Agent Decision Logging**

#### Create Decision Log Table:
```sql
CREATE TABLE agent_decision_logs (
    id UUID PRIMARY KEY,
    agent_type VARCHAR(10),  -- CIA, JAA, CDA, EAA, WFA
    campaign_id UUID,
    contractor_id UUID,
    decision_type VARCHAR(50),  -- email_template_selection, form_field_mapping, etc
    reasoning TEXT,  -- AI reasoning from Claude/GPT
    input_data JSONB,
    output_data JSONB,
    confidence_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Log Agent Decisions:
```python
# In each agent, add decision logging
async def log_agent_decision(
    agent_type: str,
    decision_type: str,
    reasoning: str,
    input_data: dict,
    output_data: dict,
    confidence: float = 0.0
):
    await db.client.table("agent_decision_logs").insert({
        "id": str(uuid4()),
        "agent_type": agent_type,
        "decision_type": decision_type,
        "reasoning": reasoning,
        "input_data": input_data,
        "output_data": output_data,
        "confidence_score": confidence,
        "created_at": datetime.now().isoformat()
    }).execute()
```

### **Phase 4: Manual Agent Testing Interface**

#### Test Panel Component:
```typescript
// web/src/components/admin/AgentTestPanel.tsx
const AgentTestPanel = () => {
  const [selectedAgent, setSelectedAgent] = useState('EAA');
  const [testData, setTestData] = useState({});
  const [results, setResults] = useState(null);
  
  const runAgentTest = async () => {
    const response = await fetch(`/api/agents/${selectedAgent}/test`, {
      method: 'POST',
      body: JSON.stringify(testData)
    });
    setResults(await response.json());
  };
  
  return (
    <div>
      {/* Agent Selection */}
      <AgentSelector value={selectedAgent} onChange={setSelectedAgent} />
      
      {/* Test Data Input */}
      <TestDataForm agent={selectedAgent} onChange={setTestData} />
      
      {/* Run Test Button */}
      <button onClick={runAgentTest}>Run Agent Test</button>
      
      {/* Results Display */}
      {results && <AgentTestResults results={results} />}
    </div>
  );
};
```

### **Phase 5: Audit Trail & Proof of Work**

#### Audit Display Component:
```typescript
// web/src/components/admin/AgentAuditTrail.tsx
const AgentAuditTrail = ({ campaignId }) => {
  const [auditLogs, setAuditLogs] = useState([]);
  
  return (
    <div className="space-y-4">
      {auditLogs.map(log => (
        <div key={log.id} className="border p-4 rounded">
          <div className="flex justify-between">
            <span>{log.agent_type}</span>
            <span>{log.timestamp}</span>
          </div>
          
          {/* Email Proof */}
          {log.type === 'email' && (
            <div>
              <p>Email sent to: {log.recipient}</p>
              <button onClick={() => viewEmail(log.email_id)}>
                View Email Content
              </button>
              <span className={log.delivered ? 'text-green' : 'text-red'}>
                {log.delivered ? 'Delivered' : 'Failed'}
              </span>
            </div>
          )}
          
          {/* Form Proof */}
          {log.type === 'form' && (
            <div>
              <p>Form filled at: {log.website}</p>
              <img src={log.screenshot} alt="Form screenshot" />
              <span className={log.submitted ? 'text-green' : 'text-red'}>
                {log.submitted ? 'Submitted' : 'Failed'}
              </span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
```

## 🧪 TESTING WORKFLOW

### **1. Manual Agent Test**
```bash
# Test EAA Email Agent
curl -X POST http://localhost:8008/api/agents/eaa/test \
  -H "Content-Type: application/json" \
  -d '{
    "contractor_id": "xxx",
    "campaign_id": "yyy",
    "action": "send_email"
  }'

# Test WFA Form Agent
curl -X POST http://localhost:8008/api/agents/wfa/test \
  -H "Content-Type: application/json" \
  -d '{
    "contractor_id": "xxx",
    "website": "https://contractor-site.com",
    "action": "fill_form"
  }'
```

### **2. End-to-End Campaign Test**
1. Create campaign in UI
2. Assign contractors
3. Watch Agent Monitoring dashboard
4. Verify emails sent (check MailHog)
5. Verify forms filled (check screenshots)
6. View audit trail

### **3. Agent Decision Verification**
- View reasoning logs in UI
- Check confidence scores
- Review input/output data
- Manually override if needed

## 📊 SUCCESS METRICS

### **What Success Looks Like:**
- ✅ Click "Assign Contractor" → Email automatically sent
- ✅ Agent dashboard shows real-time status
- ✅ Audit trail proves actions completed
- ✅ Manual test triggers work reliably
- ✅ Decision logs explain agent reasoning

### **Key Performance Indicators:**
- Email delivery rate > 95%
- Form submission success > 80%
- Agent response time < 5 seconds
- Decision confidence > 0.7
- Zero duplicate outreach

## 🚀 NEXT STEPS

1. **Immediate**: Implement Phase 1 (Hook up campaign assignment)
2. **Today**: Build basic agent monitoring UI
3. **Tomorrow**: Add decision logging
4. **This Week**: Complete audit trail
5. **Next Week**: Full testing suite

This plan provides complete visibility into backend agent operations with the ability to monitor, test, and audit every action.