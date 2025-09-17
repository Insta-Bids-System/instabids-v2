import type React from "react";
import { useEffect, useState } from "react";
import { useAdminAuth } from "../../hooks/useAdminAuth";
import LoadingSpinner from "../ui/LoadingSpinner";
import LLMCostDashboard from "./LLMCostDashboard";

interface AgentStatus {
  agent_id: string;
  agent_name: string;
  status: "idle" | "running" | "error" | "offline";
  last_action?: string;
  last_action_time?: string;
  success_rate: number;
  total_actions: number;
  successful_actions: number;
}

interface AgentTestRequest {
  agent_type: string;
  test_data: Record<string, any>;
  action: "test" | "execute";
}

interface AgentTestResult {
  agent: string;
  test_type: string;
  status: string;
  result?: string;
  error?: string;
  preview?: Record<string, any>;
}

interface AuditTrailEntry {
  id: string;
  timestamp: string;
  contractor: string;
  channel: string;
  status: string;
  agent: string;
  details: Record<string, any>;
  proof?: {
    type: string;
    verified: boolean;
    recipient?: string;
    website?: string;
  };
}

interface DecisionLogEntry {
  id: string;
  agent_type: string;
  timestamp: string;
  decision_type: string;
  reasoning: string;
  confidence_score: number;
  input_data: Record<string, any>;
  output_data: Record<string, any>;
}

const EnhancedAgentMonitoring: React.FC = () => {
  const { session } = useAdminAuth();
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<AgentTestResult | null>(null);
  const [auditTrail, setAuditTrail] = useState<AuditTrailEntry[]>([]);
  const [decisionLogs, setDecisionLogs] = useState<DecisionLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isTesting, setIsTesting] = useState(false);
  const [testData, setTestData] = useState<Record<string, any>>({});
  const [selectedCampaign, setSelectedCampaign] = useState<string>("");
  const [selectedView, setSelectedView] = useState<"overview" | "testing" | "audit" | "decisions" | "costs">("overview");

  // Load agent statuses
  useEffect(() => {
    fetchAgentStatuses();
    // Polling disabled for performance - use manual refresh instead
    // const interval = setInterval(fetchAgentStatuses, 30000); // Refresh every 30 seconds
    // return () => clearInterval(interval);
  }, [session]);

  const fetchAgentStatuses = async () => {
    try {
      const response = await fetch("/api/agents/status", {
        headers: {
          Authorization: `Bearer ${session?.session_id}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setAgents(data);
      } else {
        console.error("Failed to fetch agent statuses");
      }
    } catch (error) {
      console.error("Error fetching agent statuses:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const testAgent = async (agentType: string, action: "test" | "execute") => {
    setIsTesting(true);
    setTestResult(null);

    const request: AgentTestRequest = {
      agent_type: agentType,
      action: action,
      test_data: getTestDataForAgent(agentType)
    };

    try {
      const response = await fetch(`/api/agents/test/${agentType.toLowerCase()}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session?.session_id}`,
        },
        body: JSON.stringify(request),
      });

      if (response.ok) {
        const result = await response.json();
        setTestResult(result);
      } else {
        const error = await response.json();
        setTestResult({
          agent: agentType,
          test_type: "error",
          status: "error",
          error: error.detail || "Test failed"
        });
      }
    } catch (error) {
      console.error("Error testing agent:", error);
      setTestResult({
        agent: agentType,
        test_type: "error", 
        status: "error",
        error: "Network error"
      });
    } finally {
      setIsTesting(false);
    }
  };

  const fetchAuditTrail = async (campaignId: string) => {
    if (!campaignId) return;

    try {
      const response = await fetch(`/api/agents/audit-trail/${campaignId}`, {
        headers: {
          Authorization: `Bearer ${session?.session_id}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAuditTrail(data);
      }
    } catch (error) {
      console.error("Error fetching audit trail:", error);
    }
  };

  const fetchDecisionLogs = async (agentType?: string, campaignId?: string) => {
    try {
      const params = new URLSearchParams();
      if (agentType) params.append("agent_type", agentType);
      if (campaignId) params.append("campaign_id", campaignId);
      params.append("limit", "20");

      const response = await fetch(`/api/agents/decision-logs?${params}`, {
        headers: {
          Authorization: `Bearer ${session?.session_id}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setDecisionLogs(data);
      }
    } catch (error) {
      console.error("Error fetching decision logs:", error);
    }
  };

  const getTestDataForAgent = (agentType: string): Record<string, any> => {
    switch (agentType.toLowerCase()) {
      case "eaa":
        return {
          email: "test@contractor.com",
          name: "Test Contractor",
          project: {
            project_type: "kitchen_remodel",
            urgency: "standard",
            location: "Test City, ST",
            budget_range: "$10,000 - $20,000"
          }
        };
      case "wfa":
        return {
          website: "https://example.com/contact",
          form_data: {
            project_type: "bathroom_remodel",
            budget: "$5,000 - $10,000",
            timeline: "urgent"
          }
        };
      default:
        return {};
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "idle":
        return "bg-green-100 text-green-800 border-green-200";
      case "running":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "error":
        return "bg-red-100 text-red-800 border-red-200";
      case "offline":
        return "bg-gray-100 text-gray-800 border-gray-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "idle":
        return "✅";
      case "running":
        return "🔄";
      case "error":
        return "❌";
      case "offline":
        return "⭕";
      default:
        return "❓";
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-gray-600">Loading agent monitoring data...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">🤖 Backend Agent Monitoring</h3>
          <p className="text-sm text-gray-500 mt-1">
            Real-time status, testing, audit trail, and decision logs for all backend agents
          </p>
          
          {/* Tab Navigation */}
          <div className="mt-4 border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: "overview", name: "Agent Status", icon: "📊" },
                { id: "testing", name: "Testing", icon: "🧪" },
                { id: "audit", name: "Audit Trail", icon: "📋" },
                { id: "decisions", name: "Decision Logs", icon: "🧠" },
                { id: "costs", name: "LLM Costs", icon: "💰" }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setSelectedView(tab.id as any)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    selectedView === tab.id
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Overview Tab */}
        {selectedView === "overview" && (

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {agents.map((agent) => (
              <div
                key={agent.agent_id}
                className={`border rounded-lg p-4 transition-all duration-200 cursor-pointer ${
                  selectedAgent === agent.agent_id
                    ? "border-blue-500 bg-blue-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
                onClick={() => setSelectedAgent(selectedAgent === agent.agent_id ? null : agent.agent_id)}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-xl">{getStatusIcon(agent.status)}</span>
                    <h4 className="font-medium text-gray-900">{agent.agent_name}</h4>
                  </div>
                  <div
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(agent.status)}`}
                  >
                    {agent.status}
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Success Rate:</span>
                    <span className={`font-medium ${agent.success_rate >= 80 ? "text-green-600" : agent.success_rate >= 60 ? "text-yellow-600" : "text-red-600"}`}>
                      {agent.success_rate.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Actions:</span>
                    <span className="font-medium text-gray-900">{agent.total_actions}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Successful:</span>
                    <span className="font-medium text-green-600">{agent.successful_actions}</span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="mt-3">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${agent.success_rate >= 80 ? "bg-green-500" : agent.success_rate >= 60 ? "bg-yellow-500" : "bg-red-500"}`}
                      style={{ width: `${Math.min(agent.success_rate, 100)}%` }}
                    ></div>
                  </div>
                </div>

                {agent.last_action && (
                  <div className="mt-2 text-xs text-gray-500">
                    Last: {agent.last_action} ({new Date(agent.last_action_time || "").toLocaleTimeString()})
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
        )}

        {/* Testing Tab */}
        {selectedView === "testing" && (

        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Test Controls */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Agent to Test
                </label>
                <select
                  value={selectedAgent || ""}
                  onChange={(e) => setSelectedAgent(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Choose an agent...</option>
                  {agents.map((agent) => (
                    <option key={agent.agent_id} value={agent.agent_id}>
                      {agent.agent_name}
                    </option>
                  ))}
                </select>
              </div>

              {selectedAgent && (
                <div className="space-y-3">
                  <button
                    onClick={() => testAgent(selectedAgent, "test")}
                    disabled={isTesting}
                    className="w-full px-4 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isTesting ? "Testing..." : "Preview Test (Safe)"}
                  </button>
                  
                  <button
                    onClick={() => testAgent(selectedAgent, "execute")}
                    disabled={isTesting}
                    className="w-full px-4 py-2 bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isTesting ? "Executing..." : "Execute Test (Real Action)"}
                  </button>
                </div>
              )}
            </div>

            {/* Test Results */}
            <div className="border border-gray-200 rounded-lg p-4 min-h-[200px]">
              <h4 className="font-medium text-gray-900 mb-3">Test Results</h4>
              
              {isTesting && (
                <div className="flex items-center space-x-2">
                  <LoadingSpinner size="sm" />
                  <span className="text-gray-600">Running agent test...</span>
                </div>
              )}

              {testResult && (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      testResult.status === "success" ? "bg-green-100 text-green-800" :
                      testResult.status === "preview" ? "bg-blue-100 text-blue-800" :
                      "bg-red-100 text-red-800"
                    }`}>
                      {testResult.status}
                    </span>
                    <span className="text-sm font-medium">{testResult.agent}</span>
                  </div>

                  {testResult.preview && (
                    <div className="bg-blue-50 border border-blue-200 rounded p-3">
                      <h5 className="font-medium text-blue-900 mb-2">Preview:</h5>
                      <pre className="text-xs text-blue-800 overflow-x-auto">
                        {JSON.stringify(testResult.preview, null, 2)}
                      </pre>
                    </div>
                  )}

                  {testResult.result && (
                    <div className="bg-green-50 border border-green-200 rounded p-3">
                      <h5 className="font-medium text-green-900 mb-2">Result:</h5>
                      <p className="text-sm text-green-800">{testResult.result}</p>
                    </div>
                  )}

                  {testResult.error && (
                    <div className="bg-red-50 border border-red-200 rounded p-3">
                      <h5 className="font-medium text-red-900 mb-2">Error:</h5>
                      <p className="text-sm text-red-800">{testResult.error}</p>
                    </div>
                  )}
                </div>
              )}

              {!testResult && !isTesting && (
                <p className="text-gray-500 text-sm">
                  Select an agent and run a test to see results here.
                </p>
              )}
            </div>
          </div>
        </div>
        )}

        {/* Audit Trail Tab */}
        {selectedView === "audit" && (

        <div className="p-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Campaign ID (for audit trail)
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={selectedCampaign}
                onChange={(e) => setSelectedCampaign(e.target.value)}
                placeholder="Enter campaign ID..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={() => fetchAuditTrail(selectedCampaign)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Load Audit Trail
              </button>
            </div>
          </div>

          {auditTrail.length > 0 && (
            <div className="space-y-3">
              {auditTrail.map((entry) => (
                <div key={entry.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        entry.agent === "EAA" ? "bg-purple-100 text-purple-800" : "bg-orange-100 text-orange-800"
                      }`}>
                        {entry.agent}
                      </span>
                      <span className="text-sm font-medium">{entry.contractor}</span>
                      <span className="text-sm text-gray-600">via {entry.channel}</span>
                    </div>
                    <div className="text-sm text-gray-500">
                      {new Date(entry.timestamp).toLocaleString()}
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className={`px-2 py-1 rounded text-xs font-medium ${
                      entry.status === "sent" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                    }`}>
                      {entry.status}
                    </div>
                    
                    {entry.proof && (
                      <div className={`flex items-center space-x-1 text-xs ${
                        entry.proof.verified ? "text-green-600" : "text-gray-600"
                      }`}>
                        <span>{entry.proof.verified ? "✅" : "⏳"}</span>
                        <span>
                          {entry.proof.type === "email_sent" && `Email to ${entry.proof.recipient}`}
                          {entry.proof.type === "form_submitted" && `Form at ${entry.proof.website}`}
                        </span>
                      </div>
                    )}
                  </div>

                  {entry.details.message && (
                    <div className="mt-2 text-sm text-gray-600 truncate">
                      {entry.details.message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {auditTrail.length === 0 && selectedCampaign && (
            <p className="text-gray-500 text-center py-8">
              No audit trail found for campaign "{selectedCampaign}". 
              Make sure the campaign ID is correct and has agent activity.
            </p>
          )}
        </div>
        )}

        {/* Decision Logs Tab */}
        {selectedView === "decisions" && (
        <div className="p-6">
          <div className="mb-4 flex space-x-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Filter by Agent Type
              </label>
              <select
                value={selectedAgent || ""}
                onChange={(e) => {
                  setSelectedAgent(e.target.value);
                  fetchDecisionLogs(e.target.value);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All agents</option>
                {agents.map((agent) => (
                  <option key={agent.agent_id} value={agent.agent_id}>
                    {agent.agent_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Campaign ID (optional)
              </label>
              <input
                type="text"
                value={selectedCampaign}
                onChange={(e) => setSelectedCampaign(e.target.value)}
                placeholder="Enter campaign ID..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={() => fetchDecisionLogs(selectedAgent || undefined, selectedCampaign || undefined)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Load Decision Logs
              </button>
            </div>
          </div>

          {decisionLogs.length > 0 && (
            <div className="space-y-4">
              {decisionLogs.map((log) => (
                <div key={log.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        log.agent_type === "EAA" ? "bg-purple-100 text-purple-800" :
                        log.agent_type === "WFA" ? "bg-orange-100 text-orange-800" :
                        log.agent_type === "CDA" ? "bg-blue-100 text-blue-800" :
                        "bg-gray-100 text-gray-800"
                      }`}>
                        {log.agent_type}
                      </span>
                      <span className="text-sm font-medium">{log.decision_type.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</span>
                      <div className="flex items-center space-x-1">
                        <span className="text-xs text-gray-500">Confidence:</span>
                        <span className={`text-xs font-medium ${
                          log.confidence_score >= 0.8 ? "text-green-600" :
                          log.confidence_score >= 0.6 ? "text-yellow-600" :
                          "text-red-600"
                        }`}>
                          {(log.confidence_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      {new Date(log.timestamp).toLocaleString()}
                    </div>
                  </div>

                  <div className="mb-3">
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Agent Reasoning:</h4>
                    <p className="text-sm text-gray-600 bg-gray-50 rounded p-2">
                      {log.reasoning}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Input Data:</h4>
                      <pre className="text-xs bg-blue-50 border border-blue-200 rounded p-2 overflow-x-auto">
                        {JSON.stringify(log.input_data, null, 2)}
                      </pre>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Output Data:</h4>
                      <pre className="text-xs bg-green-50 border border-green-200 rounded p-2 overflow-x-auto">
                        {JSON.stringify(log.output_data, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {decisionLogs.length === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-500 mb-2">No decision logs found.</p>
              <p className="text-sm text-gray-400">
                Select filters above and click "Load Decision Logs" to see agent decision making process.
              </p>
            </div>
          )}
        </div>
        )}

        {/* LLM Costs Tab */}
        {selectedView === "costs" && (
        <div className="p-6">
          <div className="overflow-hidden">
            <LLMCostDashboard />
          </div>
        </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedAgentMonitoring;