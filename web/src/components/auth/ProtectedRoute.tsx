import type React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: "homeowner" | "contractor" | "admin";
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRole }) => {
  const { user, profile, loading } = useAuth();

  // Check for demo user
  const demoUser = localStorage.getItem("DEMO_USER");
  const isDemoUser = !!demoUser;

  if (loading && !isDemoUser) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!user && !isDemoUser) {
    return <Navigate to="/login" replace />;
  }

  // Handle demo user role
  if (isDemoUser) {
    const demoData = JSON.parse(demoUser);
    if (requiredRole && demoData.role !== requiredRole) {
      if (demoData.role === "contractor") {
        return <Navigate to="/contractor/dashboard" replace />;
      } else if (demoData.role === "homeowner") {
        return <Navigate to="/dashboard" replace />;
      }
    }
    // Demo user is authorized
    return <>{children}</>;
  }

  // Check role if required for real users
  if (requiredRole && profile?.role !== requiredRole) {
    // Redirect to appropriate dashboard based on user's actual role
    if (profile?.role === "contractor") {
      return <Navigate to="/contractor/dashboard" replace />;
    } else if (profile?.role === "homeowner") {
      return <Navigate to="/dashboard" replace />;
    } else {
      return <Navigate to="/" replace />;
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;
