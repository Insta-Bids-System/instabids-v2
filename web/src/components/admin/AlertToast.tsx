import type React from "react";
import { useEffect, useState } from "react";

interface Alert {
  id: string;
  type: string;
  message: string;
  severity: "info" | "warning" | "error";
  timestamp: string;
}

interface AlertToastProps {
  alert: Alert;
  onDismiss: () => void;
  autoHide?: boolean;
  duration?: number;
}

const AlertToast: React.FC<AlertToastProps> = ({
  alert,
  onDismiss,
  autoHide = true,
  duration = 8000,
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    if (!autoHide) return;

    const interval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev - 100 / (duration / 100);
        if (newProgress <= 0) {
          handleDismiss();
          return 0;
        }
        return newProgress;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [autoHide, duration, handleDismiss]);

  const handleDismiss = () => {
    setIsVisible(false);
    setTimeout(onDismiss, 300); // Wait for fade out animation
  };

  const getSeverityStyles = () => {
    switch (alert.severity) {
      case "error":
        return {
          container: "bg-red-50 border border-red-200",
          icon: "text-red-600",
          title: "text-red-800",
          message: "text-red-700",
          progress: "bg-red-500",
          iconPath:
            "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 14.5c-.77.833.192 2.5 1.732 2.5z",
        };
      case "warning":
        return {
          container: "bg-yellow-50 border border-yellow-200",
          icon: "text-yellow-600",
          title: "text-yellow-800",
          message: "text-yellow-700",
          progress: "bg-yellow-500",
          iconPath:
            "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 14.5c-.77.833.192 2.5 1.732 2.5z",
        };
      default:
        return {
          container: "bg-blue-50 border border-blue-200",
          icon: "text-blue-600",
          title: "text-blue-800",
          message: "text-blue-700",
          progress: "bg-blue-500",
          iconPath: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
        };
    }
  };

  const styles = getSeverityStyles();

  const formatTime = (timestamp: string) => {
    const time = new Date(timestamp);
    return time.toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const getAlertTypeIcon = () => {
    switch (alert.type) {
      case "agent_failure":
      case "agent_offline":
        return "🤖";
      case "high_error_rate":
        return "⚠️";
      case "slow_response":
        return "🐌";
      case "database_error":
        return "💾";
      case "email_failure":
        return "📧";
      case "form_failure":
        return "📝";
      case "agent_restart":
        return "🔄";
      default:
        return "🔔";
    }
  };

  return (
    <div
      className={`max-w-sm w-full shadow-lg rounded-lg pointer-events-auto transition-all duration-300 transform ${
        isVisible ? "translate-x-0 opacity-100" : "translate-x-full opacity-0"
      } ${styles.container}`}
      role="alert"
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <div className="flex items-center justify-center w-8 h-8">
              <span className="text-lg">{getAlertTypeIcon()}</span>
            </div>
          </div>

          <div className="ml-3 w-0 flex-1">
            <div className="flex items-center justify-between">
              <p className={`text-sm font-medium ${styles.title}`}>
                {alert.type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
              </p>
              <p className="text-xs text-gray-500">{formatTime(alert.timestamp)}</p>
            </div>

            <p className={`mt-1 text-sm ${styles.message}`}>{alert.message}</p>
          </div>

          <div className="ml-4 flex-shrink-0 flex">
            <button
              type="button"
              onClick={handleDismiss}
              className={`inline-flex text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600 transition ease-in-out duration-150`}
            >
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      {autoHide && (
        <div className="h-1 bg-gray-200 rounded-b-lg overflow-hidden">
          <div
            className={`h-full transition-all duration-100 ease-linear ${styles.progress}`}
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
};

export default AlertToast;
