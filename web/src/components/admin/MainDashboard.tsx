import type React from "react";
import { useEffect, useState } from "react";
import { useAdminAuth } from "../../hooks/useAdminAuth";
import { useWebSocketContext } from "../../context/WebSocketContext";
import type {
  AdminDashboardData,
  AgentHealthStatus,
  SystemMetrics as SystemMetricsType,
} from "../../types";
import LoadingSpinner from "../ui/LoadingSpinner";
import AdminHeader from "./AdminHeader";
import AgentStatusPanel from "./AgentStatusPanel";
import AlertToast from "./AlertToast";
import BidCardMonitor from "./BidCardMonitor";
import BidCardTable from "./BidCardTable";
import DatabaseViewer from "./DatabaseViewer";
import SystemMetrics from "./SystemMetrics";
import EnhancedSearchPanel from "./EnhancedSearchPanel";
import ContractorManagement from "./ContractorManagement";
import CampaignManagement from "./CampaignManagement";
import EnhancedAgentMonitoring from "./EnhancedAgentMonitoring";
import ConnectionFeesManagement from "./ConnectionFeesManagement";
// import SubmittedProposalsTab from "./SubmittedProposalsTab";

interface DatabaseStats {
  total_tables: number;
  total_rows: number;
  database_size_mb: number;
  active_connections: number;
  slow_queries: number;
  cache_hit_ratio: number;
  recent_operations: DatabaseOperation[];
}

interface DatabaseOperation {
  id: string;
  operation_type: "SELECT" | "INSERT" | "UPDATE" | "DELETE";
  table_name: string;
  execution_time_ms: number;
  timestamp: string;
  rows_affected?: number;
}

interface WebSocketStats {
  total_connections: number;
  active_connections: number;
  messages_sent_today: number;
  messages_received_today: number;
  connection_errors: number;
  average_latency_ms: number;
}

interface AuthStats {
  active_sessions: number;
  failed_login_attempts: number;
  successful_logins_today: number;
  session_duration_avg_minutes: number;
  unique_users_today: number;
}

interface DashboardData {
  timestamp: string;
  system_metrics: SystemMetricsType;
  agent_statuses: Record<string, AgentHealthStatus>;
  database_stats: DatabaseStats;
  websocket_stats: WebSocketStats;
  auth_stats: AuthStats;
  monitoring_enabled: boolean;
}

interface Alert {
  id: string;
  type: string;
  message: string;
  severity: "info" | "warning" | "error";
  timestamp: string;
}

interface WebSocketMessage {
  type: string;
  data: unknown;
  timestamp: string;
}

interface SystemAlertData {
  alert_type: string;
  message: string;
  severity: "info" | "warning" | "error";
}

const MainDashboard: React.FC = () => {
  const { adminUser, logout, session } = useAdminAuth();
  const {
    isConnected,
    lastMessage
  } = useWebSocketContext();

  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState("overview");
  const [useEnhancedBidCards, setUseEnhancedBidCards] = useState(false);

  // Load real dashboard data from API
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // For now, set minimal real data structure
        const realData: DashboardData = {
          timestamp: new Date().toISOString(),
          system_metrics: {
            total_bid_cards: 0, // Will be updated by BidCardTable
            revenue_this_month: 0,
            bids_completed_today: 0,
            active_campaigns: 0,
            response_rate: 0,
            uptime_seconds: 0,
          },
          agent_statuses: {},
          database_stats: {
            total_tables: 41,
            total_rows: 0,
            database_size_mb: 0,
            active_connections: 0,
            slow_queries: 0,
            cache_hit_ratio: 0,
            recent_operations: [],
          },
          websocket_stats: {
            total_connections: 0,
            active_connections: 0,
            messages_sent_today: 0,
            messages_received_today: 0,
            connection_errors: 0,
            average_latency_ms: 0,
          },
          auth_stats: {
            active_sessions: 1,
            failed_login_attempts: 0,
            successful_logins_today: 1,
            session_duration_avg_minutes: 0,
            unique_users_today: 1,
          },
          monitoring_enabled: true,
        };

        setDashboardData(realData);
        setIsLoading(false);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [session?.session_id]);

  // Handle WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    const message = lastMessage as WebSocketMessage;

    switch (message.type) {
      case "system_overview":
        setDashboardData(message.data as DashboardData);
        break;

      case "system_alert": {
        const alertData = message.data as SystemAlertData;
        const alert: Alert = {
          id: Date.now().toString(),
          type: alertData.alert_type,
          message: alertData.message,
          severity: alertData.severity,
          timestamp: message.timestamp,
        };
        setAlerts((prev) => [alert, ...prev.slice(0, 9)]); // Keep last 10 alerts
        break;
      }

      case "bid_card_update":
      case "agent_status":
      case "database_operation":
        // These updates are handled by individual components
        break;

      default:
        console.log("Unhandled message type:", message.type);
    }
  }, [lastMessage]);

  const dismissAlert = (alertId: string) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
  };

  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-lg text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Dashboard Unavailable</h2>
          <p className="text-gray-600">
            Unable to load dashboard data. Please check the backend service.
          </p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: "overview", name: "Overview", icon: "📊" },
    { id: "bid-cards", name: "Bid Cards", icon: "📋" },
    { id: "submitted-proposals", name: "Submitted Proposals", icon: "📝" },
    { id: "connection-fees", name: "Connection Fees", icon: "💳" },
    { id: "campaigns", name: "Campaigns", icon: "🎯" },
    { id: "search", name: "Search", icon: "🔍" },
    { id: "agents", name: "Agents", icon: "🤖" },
    { id: "contractors", name: "Contractors", icon: "👷" },
    { id: "metrics", name: "Metrics", icon: "📈" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <AdminHeader
        adminUser={adminUser}
        onLogout={logout}
        connectionStatus={isConnected ? "connected" : "disconnected"}
        alertCount={alerts.length}
      />

      {/* Connection Status Bar - REMOVED: Redundant with header indicator */}

      {/* Alerts */}
      <div className="fixed top-20 right-4 z-50 space-y-2">
        {alerts.map((alert) => (
          <AlertToast key={alert.id} alert={alert} onDismiss={() => dismissAlert(alert.id)} />
        ))}
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* System Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600 font-semibold">📋</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Active Bid Cards</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {dashboardData.system_metrics.total_bid_cards}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 font-semibold">🤖</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Agents Online</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {
                    Object.values(dashboardData.agent_statuses).filter(
                      (a) => a.status === "healthy"
                    ).length
                  }
                  /{Object.keys(dashboardData.agent_statuses).length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <span className="text-purple-600 font-semibold">📧</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Revenue This Month</p>
                <p className="text-2xl font-semibold text-gray-900">
                  ${(dashboardData.system_metrics.revenue_this_month / 1000).toFixed(1)}k
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                  <span className="text-indigo-600 font-semibold">⏱️</span>
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Bids Completed Today</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {dashboardData.system_metrics.bids_completed_today}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                type="button"
                key={tab.id}
                onClick={() => setSelectedTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  selectedTab === tab.id
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

        {/* Tab Content */}
        <div className="space-y-8">
          {selectedTab === "overview" && (
            <div className="grid grid-cols-1 gap-8">
              <BidCardMonitor />
              <AgentStatusPanel agentStatuses={dashboardData.agent_statuses} />
            </div>
          )}

          {selectedTab === "bid-cards" && <BidCardMonitor />}

          {selectedTab === "submitted-proposals" && (
            <div className="p-6">
              <h3 className="text-lg font-semibold mb-4">Submitted Proposals</h3>
              <p>This section is temporarily disabled for troubleshooting.</p>
            </div>
          )}

          {selectedTab === "connection-fees" && <ConnectionFeesManagement />}

          {selectedTab === "campaigns" && <CampaignManagement />}

          {selectedTab === "search" && <EnhancedSearchPanel />}

          {selectedTab === "agents" && (
            <EnhancedAgentMonitoring />
          )}

          {selectedTab === "contractors" && (
            <ContractorManagement />
          )}

          {selectedTab === "metrics" && (
            <SystemMetrics
              metrics={dashboardData.system_metrics}
              websocketStats={dashboardData.websocket_stats}
              authStats={dashboardData.auth_stats}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default MainDashboard;
