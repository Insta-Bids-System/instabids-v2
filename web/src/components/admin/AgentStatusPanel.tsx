import type React from "react";
import { useEffect, useState } from "react";
import { useAdminAuth } from "../../hooks/useAdminAuth";
import { useWebSocketContext } from "../../context/WebSocketContext";

interface AgentStatus {
  status: string;
  health_score: number;
  response_time: number;
  last_seen: string;
  error_count?: number;
  success_count?: number;
}

interface AgentStatusPanelProps {
  agentStatuses: Record<string, AgentStatus>;
}

const AgentStatusPanel: React.FC<AgentStatusPanelProps> = ({ agentStatuses: initialStatuses }) => {
  const [agentStatuses, setAgentStatuses] = useState(initialStatuses);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [isRestarting, setIsRestarting] = useState<string | null>(null);

  const { lastMessage, subscribe } = useWebSocketContext();
  const { session, checkPermission } = useAdminAuth();

  // Subscribe to agent status updates
  useEffect(() => {
    const unsubscribe = subscribe("agent_status", () => {});
    return () => {
      if (typeof unsubscribe === 'function') {
        unsubscribe();
      }
    };
  }, [subscribe]);

  // Handle WebSocket updates
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === "agent_status") {
      const { agent, status, response_time, health_score, error_count, success_count } =
        lastMessage.data;

      setAgentStatuses((prev) => ({
        ...prev,
        [agent]: {
          status,
          response_time,
          health_score,
          last_seen: lastMessage.timestamp,
          error_count,
          success_count,
        },
      }));
    }
  }, [lastMessage]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "online":
        return "bg-green-100 text-green-800 border-green-200";
      case "error":
        return "bg-red-100 text-red-800 border-red-200";
      case "offline":
        return "bg-gray-100 text-gray-800 border-gray-200";
      case "warning":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "online":
        return "✅";
      case "error":
        return "❌";
      case "offline":
        return "⭕";
      case "warning":
        return "⚠️";
      default:
        return "❓";
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    if (score >= 40) return "text-orange-600";
    return "text-red-600";
  };

  const getAgentDescription = (agentName: string) => {
    const descriptions = {
      CIA: "Customer Interface Agent - Handles homeowner conversations",
      JAA: "Job Assessment Agent - Creates bid cards from conversations",
      CDA: "Contractor Discovery Agent - Finds qualified contractors",
      EAA: "External Acquisition Agent - Manages email outreach",
      WFA: "Website Form Automation - Fills contractor forms",
    };
    return (
      descriptions[agentName as keyof typeof descriptions] || "Agent description not available"
    );
  };

  const formatResponseTime = (time: number) => {
    if (time < 1) return `${Math.round(time * 1000)}ms`;
    if (time < 60) return `${time.toFixed(1)}s`;
    return `${Math.floor(time / 60)}m ${Math.round(time % 60)}s`;
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60));

    if (diffInMinutes < 1) return "Just now";
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return `${Math.floor(diffInMinutes / 1440)}d ago`;
  };

  const handleRestartAgent = async (agentName: string) => {
    if (!checkPermission("manage_system")) {
      alert("You do not have permission to restart agents");
      return;
    }

    if (!confirm(`Are you sure you want to restart the ${agentName} agent?`)) {
      return;
    }

    setIsRestarting(agentName);

    try {
      const response = await fetch(`/api/admin/restart-agent`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session?.session_id}`,
        },
        body: JSON.stringify({
          agent_name: agentName,
          session_id: session?.session_id,
        }),
      });

      if (response.ok) {
        // Update agent status optimistically
        setAgentStatuses((prev) => ({
          ...prev,
          [agentName]: {
            ...prev[agentName],
            status: "online",
            health_score: 100,
            last_seen: new Date().toISOString(),
          },
        }));
      } else {
        const error = await response.json();
        alert(`Failed to restart agent: ${error.detail}`);
      }
    } catch (error) {
      console.error("Error restarting agent:", error);
      alert("Failed to restart agent due to network error");
    } finally {
      setIsRestarting(null);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">🤖 Agent Status Monitor</h3>
        <p className="text-sm text-gray-500 mt-1">
          Real-time health monitoring for all InstaBids agents
        </p>
      </div>

      <div className="p-6">
        <div className="grid grid-cols-1 gap-4">
          {Object.entries(agentStatuses).map(([agentName, status]) => (
            <div
              key={agentName}
              className={`border rounded-lg p-4 transition-all duration-200 cursor-pointer ${
                selectedAgent === agentName
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
              onClick={() => setSelectedAgent(selectedAgent === agentName ? null : agentName)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">{getStatusIcon(status.status)}</div>
                  <div>
                    <h4 className="font-medium text-gray-900">{agentName}</h4>
                    <p className="text-sm text-gray-600">{getAgentDescription(agentName)}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(status.status)}`}
                    >
                      {status.status}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {formatTimeAgo(status.last_seen)}
                    </div>
                  </div>

                  <div className="text-right">
                    <div
                      className={`text-sm font-medium ${getHealthScoreColor(status.health_score)}`}
                    >
                      {status.health_score.toFixed(0)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatResponseTime(status.response_time)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Health Score Bar */}
              <div className="mt-3">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-gray-600">Health Score</span>
                  <span className={`font-medium ${getHealthScoreColor(status.health_score)}`}>
                    {status.health_score.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      status.health_score >= 80
                        ? "bg-green-500"
                        : status.health_score >= 60
                          ? "bg-yellow-500"
                          : status.health_score >= 40
                            ? "bg-orange-500"
                            : "bg-red-500"
                    }`}
                    style={{ width: `${Math.min(status.health_score, 100)}%` }}
                  ></div>
                </div>
              </div>

              {/* Expanded Details */}
              {selectedAgent === agentName && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Response Time:</span>
                      <span className="ml-2 text-gray-600">
                        {formatResponseTime(status.response_time)}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Last Seen:</span>
                      <span className="ml-2 text-gray-600">
                        {new Date(status.last_seen).toLocaleString()}
                      </span>
                    </div>
                    {status.success_count !== undefined && (
                      <div>
                        <span className="font-medium text-gray-700">Success Count:</span>
                        <span className="ml-2 text-green-600">{status.success_count}</span>
                      </div>
                    )}
                    {status.error_count !== undefined && (
                      <div>
                        <span className="font-medium text-gray-700">Error Count:</span>
                        <span className="ml-2 text-red-600">{status.error_count}</span>
                      </div>
                    )}
                  </div>

                  {/* Action Buttons */}
                  <div className="mt-4 flex space-x-2">
                    <button
                      type="button"
                      className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                    >
                      View Logs
                    </button>
                    <button
                      type="button"
                      className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                    >
                      Test Connection
                    </button>
                    {status.status !== "online" && checkPermission("manage_system") && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRestartAgent(agentName);
                        }}
                        disabled={isRestarting === agentName}
                        className="px-3 py-1 text-xs bg-orange-100 text-orange-700 rounded hover:bg-orange-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isRestarting === agentName ? "Restarting..." : "Restart Agent"}
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Summary Statistics */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-green-600">
                {Object.values(agentStatuses).filter((a) => a.status === "online").length}
              </div>
              <div className="text-sm text-gray-600">Online</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">
                {Object.values(agentStatuses).filter((a) => a.status === "error").length}
              </div>
              <div className="text-sm text-gray-600">Errors</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">
                {(
                  Object.values(agentStatuses).reduce((sum, a) => sum + a.health_score, 0) /
                  Object.values(agentStatuses).length
                ).toFixed(0)}
                %
              </div>
              <div className="text-sm text-gray-600">Avg Health</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">
                {formatResponseTime(
                  Object.values(agentStatuses).reduce((sum, a) => sum + a.response_time, 0) /
                    Object.values(agentStatuses).length
                )}
              </div>
              <div className="text-sm text-gray-600">Avg Response</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentStatusPanel;
