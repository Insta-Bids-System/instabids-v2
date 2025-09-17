import type React from "react";
import { useEffect, useState } from "react";
import LoadingSpinner from "../ui/LoadingSpinner";

interface CostSummary {
  date: string;
  total_cost_usd: number;
  total_calls: number;
  total_tokens: number;
  average_cost_per_call: number;
}

interface AgentCostBreakdown {
  [agent: string]: {
    cost: number;
    calls: number;
    tokens: number;
    models: {
      [model: string]: {
        cost: number;
        calls: number;
      };
    };
  };
}

interface TrendData {
  date: string;
  daily_cost: number;
  daily_calls: number;
  daily_tokens: number;
}

interface ModelComparison {
  provider: string;
  model: string;
  total_calls: number;
  total_cost: number;
  total_tokens: number;
  avg_cost_per_call: number;
  avg_tokens_per_call: number;
  cost_per_1k_tokens: number;
}

interface ExpensiveSession {
  session_id: string;
  user_id: string;
  agents_used: number;
  session_cost: number;
  total_calls: number;
  total_tokens: number;
  session_start: string;
  session_end: string;
  duration_minutes: number;
}

interface CostAlert {
  type: "CRITICAL" | "WARNING";
  message: string;
  threshold: string;
}

interface CostDashboardData {
  summary: CostSummary;
  agent_breakdown: AgentCostBreakdown;
  trend_7_days: TrendData[];
  details_by_model: any[];
}

const LLMCostDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<CostDashboardData | null>(null);
  const [modelComparison, setModelComparison] = useState<ModelComparison[]>([]);
  const [expensiveSessions, setExpensiveSessions] = useState<ExpensiveSession[]>([]);
  const [alerts, setAlerts] = useState<CostAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<string>("all");
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>("daily");
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      const response = await fetch(`/api/llm-costs/dashboard?time_range=${selectedTimeRange}`);
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error("Failed to fetch cost dashboard:", error);
    }
  };

  // Fetch model comparison
  const fetchModelComparison = async () => {
    try {
      const response = await fetch("/api/llm-costs/models/comparison");
      if (response.ok) {
        const data = await response.json();
        setModelComparison(data.model_comparison || []);
      }
    } catch (error) {
      console.error("Failed to fetch model comparison:", error);
    }
  };

  // Fetch expensive sessions
  const fetchExpensiveSessions = async () => {
    try {
      const response = await fetch("/api/llm-costs/sessions/expensive?limit=5&min_cost=0.5");
      if (response.ok) {
        const data = await response.json();
        setExpensiveSessions(data.expensive_sessions || []);
      }
    } catch (error) {
      console.error("Failed to fetch expensive sessions:", error);
    }
  };

  // Fetch cost alerts
  const fetchAlerts = async () => {
    try {
      const response = await fetch("/api/llm-costs/alerts/status");
      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts || []);
      }
    } catch (error) {
      console.error("Failed to fetch cost alerts:", error);
    }
  };

  // Initial data load
  useEffect(() => {
    const loadAllData = async () => {
      setIsLoading(true);
      await Promise.all([
        fetchDashboardData(),
        fetchModelComparison(),
        fetchExpensiveSessions(),
        fetchAlerts()
      ]);
      setIsLoading(false);
    };
    loadAllData();
  }, [selectedTimeRange]); // Reload when time range changes

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchDashboardData();
      fetchAlerts();
    }, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat("en-US").format(num);
  };

  const getAgentColor = (agent: string) => {
    const colors: { [key: string]: string } = {
      CIA: "bg-blue-100 text-blue-800",
      JAA: "bg-green-100 text-green-800",
      IRIS: "bg-purple-100 text-purple-800",
      CDA: "bg-yellow-100 text-yellow-800",
      EAA: "bg-red-100 text-red-800",
      WFA: "bg-indigo-100 text-indigo-800",
      COIA: "bg-pink-100 text-pink-800",
    };
    return colors[agent] || "bg-gray-100 text-gray-800";
  };

  if (isLoading || !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-medium text-gray-900">💰 LLM Cost Monitoring</h3>
            <p className="text-sm text-gray-500">Track API usage and costs across all agents</p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => {
                fetchDashboardData();
                fetchAlerts();
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Refresh
            </button>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-600">Auto-refresh</span>
            </label>
          </div>
        </div>

        {/* Time Range Selector */}
        <div className="mb-4">
          <div className="flex space-x-2">
            {[
              { key: "hourly", label: "Last 24 Hours" },
              { key: "daily", label: "Today" },
              { key: "weekly", label: "Last 7 Days" },
              { key: "monthly", label: "Last 30 Days" }
            ].map((range) => (
              <button
                key={range.key}
                onClick={() => setSelectedTimeRange(range.key)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedTimeRange === range.key
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>

        {/* Cost Alerts */}
        {alerts && alerts.length > 0 && (
          <div className="mb-4 space-y-2">
            {alerts.map((alert, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg ${
                  alert.type === "CRITICAL" 
                    ? "bg-red-50 border border-red-200 text-red-800"
                    : "bg-yellow-50 border border-yellow-200 text-yellow-800"
                }`}
              >
                <span className="font-medium">{alert.type}: </span>
                {alert.message}
              </div>
            ))}
          </div>
        )}

        {/* Summary Cards */}
        {dashboardData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">
                {selectedTimeRange === "hourly" ? "Last 24 Hours" :
                 selectedTimeRange === "daily" ? "Today's Cost" :
                 selectedTimeRange === "weekly" ? "Last 7 Days" :
                 "Last 30 Days"}
              </p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(dashboardData?.summary?.total_cost_usd || 0)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {formatNumber(dashboardData?.summary?.total_calls || 0)} calls
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Total Tokens</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatNumber(dashboardData?.summary?.total_tokens || 0)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Avg {formatCurrency(dashboardData?.summary?.average_cost_per_call || 0)}/call
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Active Agents</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardData?.agent_breakdown ? Object.keys(dashboardData.agent_breakdown).length : 0}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Making API calls today
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500">Cost Trend</p>
              <p className="text-2xl font-bold text-gray-900">
                {dashboardData?.trend_7_days && dashboardData.trend_7_days.length > 1 ? (
                  <>
                    {((dashboardData.trend_7_days[0].daily_cost - 
                      dashboardData.trend_7_days[1].daily_cost) / 
                      dashboardData.trend_7_days[1].daily_cost * 100).toFixed(1)}%
                  </>
                ) : "N/A"}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                vs {selectedTimeRange === "hourly" ? "previous hour" :
                     selectedTimeRange === "daily" ? "yesterday" :
                     selectedTimeRange === "weekly" ? "previous week" :
                     "previous period"}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Agent Breakdown */}
      {dashboardData && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h4 className="text-md font-medium text-gray-900">Cost by Agent</h4>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {Object.entries(dashboardData.agent_breakdown).map(([agent, data]) => (
                <div key={agent} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getAgentColor(agent)}`}>
                      {agent}
                    </span>
                    <div>
                      <p className="text-sm text-gray-600">
                        {formatNumber(data.calls)} calls • {formatNumber(data.tokens)} tokens
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">{formatCurrency(data.cost)}</p>
                    <div className="text-xs text-gray-500">
                      {Object.entries(data.models).map(([model, modelData]) => (
                        <div key={model}>
                          {model}: {modelData.calls} calls
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Model Comparison */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h4 className="text-md font-medium text-gray-900">Model Performance & Cost</h4>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Provider</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Calls</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Cost</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cost/1K Tokens</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {modelComparison.map((model, idx) => (
                <tr key={idx}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {model.model}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`px-2 py-1 rounded ${
                      model.provider === 'openai' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                    }`}>
                      {model.provider}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatNumber(model.total_calls)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(model.total_cost)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(model.cost_per_1k_tokens)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Expensive Sessions */}
      {expensiveSessions && expensiveSessions.length > 0 && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h4 className="text-md font-medium text-gray-900">High-Cost Sessions</h4>
          </div>
          <div className="p-6">
            <div className="space-y-3">
              {expensiveSessions.map((session) => (
                <div key={session.session_id} className="p-3 bg-red-50 rounded-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Session: {session.session_id.substring(0, 8)}...
                      </p>
                      <p className="text-xs text-gray-500">
                        {session.agents_used} agents • {session.total_calls} calls • {Math.round(session.duration_minutes)} min
                      </p>
                    </div>
                    <p className="text-lg font-bold text-red-600">
                      {formatCurrency(session.session_cost)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LLMCostDashboard;