import type React from "react";
import { useState } from "react";
import LLMCostDashboard from "./LLMCostDashboard";

interface SystemMetricsData {
  bid_cards_active: number;
  campaigns_running: number;
  contractors_total: number;
  emails_sent_today: number;
  forms_filled_today: number;
  database_operations_today: number;
  average_response_time?: number;
  error_rate?: number;
  uptime_seconds: number;
}

interface WebSocketStats {
  active_connections: number;
  total_connections: number;
  messages_sent: number;
  queue_size: number;
  connections: Array<{
    client_id: string;
    admin_user_id: string;
    connected_at: string;
    last_ping: number;
    subscriptions: string[];
  }>;
}

interface AuthStats {
  total_admin_users: number;
  active_admin_users: number;
  active_sessions: number;
  total_sessions_created: number;
  session_duration_hours: number;
  remember_me_duration_days: number;
}

interface SystemMetricsProps {
  metrics: SystemMetricsData;
  websocketStats: WebSocketStats;
  authStats: AuthStats;
}

const SystemMetrics: React.FC<SystemMetricsProps> = ({ metrics, websocketStats, authStats }) => {
  const [selectedMetric, setSelectedMetric] = useState<string>("overview");

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const formatResponseTime = (time: number | undefined): string => {
    if (time === undefined || time === null || isNaN(time)) return "N/A";
    if (time < 1) return `${Math.round(time * 1000)}ms`;
    return `${time.toFixed(2)}s`;
  };

  const formatPercentage = (rate: number | undefined): string => {
    if (rate === undefined || rate === null || isNaN(rate)) return "N/A";
    return `${(rate * 100).toFixed(2)}%`;
  };

  const getPerformanceColor = (value: number | undefined, thresholds: { good: number; warning: number }) => {
    if (value === undefined || value === null || isNaN(value)) return "text-gray-500";
    if (value <= thresholds.good) return "text-green-600";
    if (value <= thresholds.warning) return "text-yellow-600";
    return "text-red-600";
  };

  const metricTabs = [
    { id: "overview", label: "Overview", icon: "📊" },
    { id: "performance", label: "Performance", icon: "⚡" },
    { id: "websockets", label: "WebSockets", icon: "🔗" },
    { id: "authentication", label: "Auth", icon: "🔐" },
    { id: "costs", label: "LLM Costs", icon: "💰" },
  ];

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">📈 System Performance Metrics</h3>
        <p className="text-sm text-gray-500 mt-1">
          Detailed system performance and usage statistics
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {metricTabs.map((tab) => (
            <button
              type="button"
              key={tab.id}
              onClick={() => setSelectedMetric(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                selectedMetric === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="p-6">
        {/* Overview Tab */}
        {selectedMetric === "overview" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <span className="text-3xl">📋</span>
                  </div>
                  <div className="ml-3">
                    <p className="text-2xl font-semibold text-blue-900">
                      {metrics.bid_cards_active}
                    </p>
                    <p className="text-sm text-blue-700">Active Bid Cards</p>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <span className="text-3xl">📧</span>
                  </div>
                  <div className="ml-3">
                    <p className="text-2xl font-semibold text-green-900">
                      {metrics.emails_sent_today}
                    </p>
                    <p className="text-sm text-green-700">Emails Today</p>
                  </div>
                </div>
              </div>

              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <span className="text-3xl">👷</span>
                  </div>
                  <div className="ml-3">
                    <p className="text-2xl font-semibold text-purple-900">
                      {metrics.contractors_total}
                    </p>
                    <p className="text-sm text-purple-700">Total Contractors</p>
                  </div>
                </div>
              </div>

              <div className="bg-indigo-50 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <span className="text-3xl">⏱️</span>
                  </div>
                  <div className="ml-3">
                    <p className="text-2xl font-semibold text-indigo-900">
                      {formatUptime(metrics.uptime_seconds)}
                    </p>
                    <p className="text-sm text-indigo-700">System Uptime</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Daily Activity</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Campaigns Running:</span>
                    <span className="text-sm font-medium">{metrics.campaigns_running}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Forms Filled:</span>
                    <span className="text-sm font-medium">{metrics.forms_filled_today}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">DB Operations:</span>
                    <span className="text-sm font-medium">{metrics.database_operations_today}</span>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Performance</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Avg Response:</span>
                    <span
                      className={`text-sm font-medium ${getPerformanceColor(metrics.average_response_time, { good: 1, warning: 3 })}`}
                    >
                      {formatResponseTime(metrics.average_response_time)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Error Rate:</span>
                    <span
                      className={`text-sm font-medium ${getPerformanceColor(metrics.error_rate, { good: 0.01, warning: 0.05 })}`}
                    >
                      {formatPercentage(metrics.error_rate)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Connections</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Active WebSocket:</span>
                    <span className="text-sm font-medium">{websocketStats.active_connections}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Admin Sessions:</span>
                    <span className="text-sm font-medium">{authStats.active_sessions}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Performance Tab */}
        {selectedMetric === "performance" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Response Time</h4>
                <div className="flex items-end justify-center h-32">
                  <div className="text-center">
                    <div
                      className={`text-4xl font-bold ${getPerformanceColor(metrics.average_response_time, { good: 1, warning: 3 })}`}
                    >
                      {formatResponseTime(metrics.average_response_time)}
                    </div>
                    <p className="text-sm text-gray-600 mt-2">Average Response Time</p>
                  </div>
                </div>
                <div className="mt-4 flex justify-between text-xs text-gray-500">
                  <span>Target: &lt;1s</span>
                  <span>Warning: &gt;3s</span>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Error Rate</h4>
                <div className="flex items-end justify-center h-32">
                  <div className="text-center">
                    <div
                      className={`text-4xl font-bold ${getPerformanceColor(metrics.error_rate, { good: 0.01, warning: 0.05 })}`}
                    >
                      {formatPercentage(metrics.error_rate)}
                    </div>
                    <p className="text-sm text-gray-600 mt-2">System Error Rate</p>
                  </div>
                </div>
                <div className="mt-4 flex justify-between text-xs text-gray-500">
                  <span>Target: &lt;1%</span>
                  <span>Warning: &gt;5%</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-lg font-medium text-gray-900 mb-4">System Health Indicators</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl mb-2">
                    {metrics.uptime_seconds > 86400
                      ? "🟢"
                      : metrics.uptime_seconds > 3600
                        ? "🟡"
                        : "🔴"}
                  </div>
                  <p className="text-sm font-medium">Uptime</p>
                  <p className="text-xs text-gray-600">{formatUptime(metrics.uptime_seconds)}</p>
                </div>
                <div className="text-center">
                  <div className="text-2xl mb-2">
                    {metrics.error_rate === undefined || metrics.error_rate === null ? "⚪" :
                     metrics.error_rate < 0.01 ? "🟢" : metrics.error_rate < 0.05 ? "🟡" : "🔴"}
                  </div>
                  <p className="text-sm font-medium">Reliability</p>
                  <p className="text-xs text-gray-600">
                    {metrics.error_rate !== undefined ? formatPercentage(1 - metrics.error_rate) : "N/A"} uptime
                  </p>
                </div>
                <div className="text-center">
                  <div className="text-2xl mb-2">
                    {metrics.average_response_time === undefined || metrics.average_response_time === null ? "⚪" :
                     metrics.average_response_time < 1
                      ? "🟢"
                      : metrics.average_response_time < 3
                        ? "🟡"
                        : "🔴"}
                  </div>
                  <p className="text-sm font-medium">Performance</p>
                  <p className="text-xs text-gray-600">
                    {formatResponseTime(metrics.average_response_time)} avg
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* WebSockets Tab */}
        {selectedMetric === "websockets" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-blue-900">
                  {websocketStats.active_connections}
                </div>
                <div className="text-sm text-blue-700">Active Connections</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-green-900">
                  {websocketStats.total_connections}
                </div>
                <div className="text-sm text-green-700">Total Connections</div>
              </div>
              <div className="bg-purple-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-purple-900">
                  {websocketStats.messages_sent}
                </div>
                <div className="text-sm text-purple-700">Messages Sent</div>
              </div>
              <div className="bg-orange-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-orange-900">
                  {websocketStats.queue_size}
                </div>
                <div className="text-sm text-orange-700">Queue Size</div>
              </div>
            </div>

            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Active Connections</h4>
              <div className="space-y-2">
                {websocketStats.connections.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">No active connections</p>
                ) : (
                  websocketStats.connections.map((conn) => (
                    <div
                      key={conn.client_id}
                      className="flex items-center justify-between p-3 bg-white rounded border"
                    >
                      <div>
                        <p className="font-medium text-sm">{conn.admin_user_id}</p>
                        <p className="text-xs text-gray-600">
                          Connected: {new Date(conn.connected_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-xs text-gray-500">
                          Subscriptions: {conn.subscriptions.length}
                        </div>
                        <div className="text-xs text-gray-400">
                          Last ping: {Math.floor((Date.now() - conn.last_ping * 1000) / 1000)}s ago
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Authentication Tab */}
        {selectedMetric === "authentication" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-blue-900">
                  {authStats.active_admin_users}
                </div>
                <div className="text-sm text-blue-700">Active Admin Users</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-green-900">{authStats.active_sessions}</div>
                <div className="text-sm text-green-700">Active Sessions</div>
              </div>
              <div className="bg-purple-50 rounded-lg p-4 text-center">
                <div className="text-2xl font-bold text-purple-900">
                  {authStats.total_sessions_created}
                </div>
                <div className="text-sm text-purple-700">Total Sessions Created</div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Session Configuration</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Session Duration:</span>
                    <span className="text-sm font-medium">{authStats.session_duration_hours}h</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Remember Me Duration:</span>
                    <span className="text-sm font-medium">
                      {authStats.remember_me_duration_days}d
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Admin Users:</span>
                    <span className="text-sm font-medium">{authStats.total_admin_users}</span>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Security Status</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Multi-admin Support:</span>
                    <span className="text-green-600">✅ Enabled</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Session Management:</span>
                    <span className="text-green-600">✅ Active</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Permission System:</span>
                    <span className="text-green-600">✅ Enforced</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {/* LLM Costs Tab */}
        {selectedMetric === "costs" && (
          <div className="overflow-hidden">
            <LLMCostDashboard />
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemMetrics;
