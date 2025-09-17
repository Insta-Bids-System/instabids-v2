import type React from "react";
import { useEffect, useState } from "react";
import { useWebSocketContext } from "../../context/WebSocketContext";

interface DatabaseStats {
  monitoring_enabled: boolean;
  changes_processed: number;
  errors_count: number;
  last_change_time: string | null;
  subscriptions_active: number;
  table_counts: {
    bid_cards: number;
    outreach_campaigns: number;
    contractor_leads: number;
    contractor_outreach_attempts: number;
  };
}

interface DatabaseOperation {
  id: string;
  timestamp: string;
  operation: string;
  table: string;
  record_id: string;
  additional_data?: any;
}

interface DatabaseViewerProps {
  databaseStats: DatabaseStats;
}

const DatabaseViewer: React.FC<DatabaseViewerProps> = ({ databaseStats: initialStats }) => {
  const [databaseStats, setDatabaseStats] = useState(initialStats);
  const [recentOperations, setRecentOperations] = useState<DatabaseOperation[]>([]);
  const [selectedTable, setSelectedTable] = useState<string>("all");

  const { lastMessage, subscribe } = useWebSocketContext();

  // Subscribe to database operation updates
  useEffect(() => {
    const unsubscribe = subscribe("database_operations", () => {});
    return () => {
      if (typeof unsubscribe === 'function') {
        unsubscribe();
      }
    };
  }, [subscribe]);

  // Handle WebSocket updates
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === "database_operation") {
      const operation: DatabaseOperation = {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        ...lastMessage.data,
      };

      setRecentOperations((prev) => [operation, ...prev.slice(0, 49)]); // Keep last 50 operations
    }

    if (
      lastMessage.type === "performance_metric" &&
      lastMessage.data.metric_type === "database_stats"
    ) {
      setDatabaseStats(lastMessage.data.data);
    }
  }, [lastMessage]);

  const getOperationColor = (operation: string) => {
    switch (operation.toUpperCase()) {
      case "INSERT":
        return "bg-green-100 text-green-800";
      case "UPDATE":
        return "bg-blue-100 text-blue-800";
      case "DELETE":
        return "bg-red-100 text-red-800";
      case "SELECT":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-purple-100 text-purple-800";
    }
  };

  const getOperationIcon = (operation: string) => {
    switch (operation.toUpperCase()) {
      case "INSERT":
        return "➕";
      case "UPDATE":
        return "✏️";
      case "DELETE":
        return "🗑️";
      case "SELECT":
        return "👁️";
      default:
        return "🔧";
    }
  };

  const getTableIcon = (table: string) => {
    switch (table) {
      case "bid_cards":
        return "📋";
      case "outreach_campaigns":
        return "📧";
      case "contractor_leads":
        return "👷";
      case "contractor_outreach_attempts":
        return "📞";
      default:
        return "💾";
    }
  };

  const formatTableName = (table: string) => {
    return table.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - time.getTime()) / 1000);

    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  const filteredOperations =
    selectedTable === "all"
      ? recentOperations
      : recentOperations.filter((op) => op.table === selectedTable);

  const tableOptions = [
    { value: "all", label: "All Tables", icon: "🗄️" },
    { value: "bid_cards", label: "Bid Cards", icon: "📋" },
    { value: "outreach_campaigns", label: "Campaigns", icon: "📧" },
    { value: "contractor_leads", label: "Contractors", icon: "👷" },
    { value: "contractor_outreach_attempts", label: "Outreach", icon: "📞" },
  ];

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">💾 Database Operations Monitor</h3>
            <p className="text-sm text-gray-500 mt-1">Real-time database changes and statistics</p>
          </div>
          <div className="flex items-center space-x-2">
            <div
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                databaseStats.monitoring_enabled
                  ? "bg-green-100 text-green-800"
                  : "bg-red-100 text-red-800"
              }`}
            >
              {databaseStats.monitoring_enabled ? "🟢 Monitoring Active" : "🔴 Monitoring Disabled"}
            </div>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Database Statistics */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Database Statistics</h4>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center">
                <span className="text-2xl mr-2">📊</span>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {databaseStats.changes_processed}
                  </p>
                  <p className="text-xs text-gray-600">Changes Processed</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center">
                <span className="text-2xl mr-2">⚠️</span>
                <div>
                  <p className="text-sm font-medium text-gray-900">{databaseStats.errors_count}</p>
                  <p className="text-xs text-gray-600">Errors</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center">
                <span className="text-2xl mr-2">🔗</span>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {databaseStats.subscriptions_active}
                  </p>
                  <p className="text-xs text-gray-600">Active Subscriptions</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center">
                <span className="text-2xl mr-2">🕒</span>
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {databaseStats.last_change_time
                      ? formatTimeAgo(databaseStats.last_change_time)
                      : "Never"}
                  </p>
                  <p className="text-xs text-gray-600">Last Change</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Table Counts */}
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Table Record Counts</h4>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(databaseStats.table_counts).map(([table, count]) => (
              <div key={table} className="bg-blue-50 rounded-lg p-3">
                <div className="flex items-center">
                  <span className="text-2xl mr-2">{getTableIcon(table)}</span>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{count}</p>
                    <p className="text-xs text-gray-600">{formatTableName(table)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Operations */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-900">Recent Operations</h4>
            <select
              value={selectedTable}
              onChange={(e) => setSelectedTable(e.target.value)}
              className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {tableOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.icon} {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2 max-h-96 overflow-y-auto">
            {filteredOperations.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-gray-400 text-4xl mb-2">📊</div>
                <p className="text-gray-500">No database operations yet</p>
                <p className="text-sm text-gray-400 mt-1">
                  Operations will appear here as they happen
                </p>
              </div>
            ) : (
              filteredOperations.map((operation) => (
                <div
                  key={operation.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-lg">{getOperationIcon(operation.operation)}</span>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getOperationColor(operation.operation)}`}
                        >
                          {operation.operation}
                        </span>
                        <span className="text-sm font-medium text-gray-900">
                          {getTableIcon(operation.table)} {formatTableName(operation.table)}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 font-mono mt-1">
                        Record: {operation.record_id.substring(0, 8)}...
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">{formatTimeAgo(operation.timestamp)}</p>
                    <p className="text-xs text-gray-400">
                      {new Date(operation.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DatabaseViewer;
