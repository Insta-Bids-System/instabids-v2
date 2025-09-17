import { createContext, type ReactNode, useContext, useEffect, useState } from "react";

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

interface AdminSession {
  session_id: string;
  admin_user_id: string;
  email: string;
  created_at: string;
  expires_at: string;
  last_activity: string;
  ip_address?: string;
  user_agent?: string;
  is_active: boolean;
}

interface AdminLoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

interface AdminAuthContextType {
  adminUser: AdminUser | null;
  session: AdminSession | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: AdminLoginRequest) => Promise<boolean>;
  logout: () => Promise<void>;
  checkPermission: (permission: string) => boolean;
  refreshSession: () => Promise<boolean>;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

export const AdminAuthProvider = ({ children }: { children: ReactNode }) => {
  const [adminUser, setAdminUser] = useState<AdminUser | null>(null);
  const [session, setSession] = useState<AdminSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = adminUser !== null && session !== null;

  // Check for existing session on startup
  useEffect(() => {
    const checkExistingSession = async () => {
      try {
        // Try to get current session from backend
        const response = await fetch(`/api/admin/session`, {
          method: "GET",
          credentials: "include", // Include cookies
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const data = await response.json();
          if (data.success && data.admin_user && data.session) {
            setAdminUser(data.admin_user);
            setSession(data.session);
          }
        }
      } catch (error) {
        console.error("Error checking session:", error);
      } finally {
        setIsLoading(false);
      }
    };

    checkExistingSession();
  }, []);

  // Store session ID in a variable accessible within the provider
  const _getSessionId = () => session?.session_id || "";

  const login = async (credentials: AdminLoginRequest): Promise<boolean> => {
    setIsLoading(true);

    try {
      const response = await fetch(`/api/admin/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(credentials),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Login response data:", data); // Debug log

        // Check if login was successful
        if (!data.success) {
          throw new Error(data.error || "Login failed");
        }

        const { session, admin_user } = data;

        if (!session || !admin_user) {
          console.error("Invalid response structure:", data);
          throw new Error("Invalid server response");
        }

        setSession(session);
        setAdminUser(admin_user);

        // Store session ID in localStorage for API calls
        localStorage.setItem("admin_session_id", session.session_id);

        return true;
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Login failed");
      }
    } catch (error) {
      console.error("Login error:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      if (session) {
        await fetch(`/api/admin/logout`, {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-Session-ID": session.session_id,
          },
          body: JSON.stringify({ session_id: session.session_id }),
        });
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // Clear local state and localStorage - session removed from Supabase
      localStorage.removeItem("admin_session_id");
      setAdminUser(null);
      setSession(null);
    }
  };

  const checkPermission = (permission: string): boolean => {
    return adminUser?.permissions?.includes(permission) || false;
  };

  const refreshSession = async (): Promise<boolean> => {
    if (!session) return false;

    try {
      const response = await fetch(`/api/admin/refresh-session`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          "X-Session-ID": session.session_id,
        },
        body: JSON.stringify({ session_id: session.session_id }),
      });

      if (response.ok) {
        const data = await response.json();
        setSession(data.session);
        return true;
      }

      return false;
    } catch (error) {
      console.error("Session refresh error:", error);
      return false;
    }
  };

  // Auto-refresh session every 30 minutes
  useEffect(() => {
    if (!isAuthenticated) return;

    const interval = setInterval(
      async () => {
        const success = await refreshSession();
        if (!success) {
          await logout();
        }
      },
      30 * 60 * 1000
    ); // 30 minutes

    return () => clearInterval(interval);
  }, [isAuthenticated, logout, refreshSession]);

  const contextValue: AdminAuthContextType = {
    adminUser,
    session,
    isLoading,
    isAuthenticated,
    login,
    logout,
    checkPermission,
    refreshSession,
  };

  return <AdminAuthContext.Provider value={contextValue}>{children}</AdminAuthContext.Provider>;
};

export const useAdminAuth = (): AdminAuthContextType => {
  const context = useContext(AdminAuthContext);
  if (context === undefined) {
    throw new Error("useAdminAuth must be used within an AdminAuthProvider");
  }
  return context;
};

export default useAdminAuth;
