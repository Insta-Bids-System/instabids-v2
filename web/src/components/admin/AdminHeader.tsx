import type React from "react";
import { useState } from "react";

interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  permissions: string[];
  created_at: string;
  last_login?: string;
  is_active: boolean;
}

interface AdminHeaderProps {
  adminUser: AdminUser | null;
  onLogout: () => void;
  connectionStatus: "connected" | "disconnected" | "connecting";
  alertCount: number;
}

const AdminHeader: React.FC<AdminHeaderProps> = ({
  adminUser,
  onLogout,
  connectionStatus,
  alertCount,
}) => {
  const [showUserMenu, setShowUserMenu] = useState(false);

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case "connected":
        return "bg-green-400";
      case "connecting":
        return "bg-yellow-400 animate-pulse";
      case "disconnected":
        return "bg-red-400";
      default:
        return "bg-gray-400";
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case "connected":
        return "Real-time connected";
      case "connecting":
        return "Connecting...";
      case "disconnected":
        return "Disconnected";
      default:
        return "Unknown";
    }
  };

  return (
    <>
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Left side - Logo and title */}
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-white"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h1 className="text-xl font-semibold text-gray-900">InstaBids Admin</h1>
                  <p className="text-xs text-gray-500">Live Dashboard</p>
                </div>
              </div>
            </div>

            {/* Center - Connection status */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center text-sm text-gray-600">
                <div className={`w-2 h-2 rounded-full mr-2 ${getConnectionStatusColor()}`}></div>
                <span>{getConnectionStatusText()}</span>
              </div>

              {/* Alert indicator */}
              {alertCount > 0 && (
                <div className="relative">
                  <div className="flex items-center text-sm text-orange-600">
                    <svg
                      className="w-4 h-4 mr-1"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 14.5c-.77.833.192 2.5 1.732 2.5z"
                      />
                    </svg>
                    <span>
                      {alertCount} Alert{alertCount !== 1 ? "s" : ""}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Right side - User menu */}
            <div className="flex items-center space-x-4">
              {adminUser ? (
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-gray-700">
                        {adminUser.email ? adminUser.email.charAt(0).toUpperCase() : "A"}
                      </span>
                    </div>
                    <div className="ml-3 text-left">
                      <p className="text-sm font-medium text-gray-700">
                        {adminUser.email || "Admin"}
                      </p>
                      <p className="text-xs text-gray-500">Administrator</p>
                    </div>
                    <svg
                      className="ml-2 h-4 w-4 text-gray-400"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </button>

                  {/* User dropdown menu */}
                  {showUserMenu && (
                    <div className="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
                      <div className="py-1">
                        <div className="px-4 py-2 text-xs text-gray-500 border-b border-gray-100">
                          <p>Signed in as</p>
                          <p className="font-medium text-gray-900">{adminUser.email}</p>
                        </div>

                        <div className="px-4 py-2 text-xs text-gray-500">
                          <p>Permissions:</p>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {adminUser.permissions.slice(0, 3).map((permission) => (
                              <span
                                key={permission}
                                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                              >
                                {permission.replace("_", " ")}
                              </span>
                            ))}
                            {adminUser.permissions.length > 3 && (
                              <span className="text-xs text-gray-500">
                                +{adminUser.permissions.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="border-t border-gray-100">
                          <button
                            type="button"
                            onClick={() => {
                              setShowUserMenu(false);
                              onLogout();
                            }}
                            className="block w-full text-left px-4 py-2 text-sm text-red-700 hover:bg-red-50 hover:text-red-900"
                          >
                            <div className="flex items-center">
                              <svg
                                className="mr-2 h-4 w-4"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path
                                  strokeLinecap="round"
                                  strokeLinejoin="round"
                                  strokeWidth={2}
                                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                                />
                              </svg>
                              Sign out
                            </div>
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center text-sm text-gray-500">
                  <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse"></div>
                  <div className="ml-3">
                    <div className="h-4 w-20 bg-gray-200 rounded animate-pulse"></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Click outside to close menu */}
      {showUserMenu && (
        <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
      )}
    </>
  );
};

export default AdminHeader;
