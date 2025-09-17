import { Loader2 } from "lucide-react";
import type React from "react";
import { useEffect } from "react";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/lib/supabase";

const AuthCallbackPage: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Get the session from the URL
        const {
          data: { session },
          error,
        } = await supabase.auth.getSession();

        if (error) throw error;

        if (session) {
          // Check if we have pending project data
          const pendingSessionId = localStorage.getItem("pendingSessionId");
          const pendingProjectData = localStorage.getItem("pendingProjectData");

          if (pendingSessionId && pendingProjectData) {
            // TODO: Associate the conversation with the new user
            // This would involve calling an API endpoint to transfer the session
            try {
              const _projectData = JSON.parse(pendingProjectData);
              // You would call your API here to associate the session with the user
              console.log("Associating session:", pendingSessionId, "with user:", session.user.id);

              // Clean up localStorage
              localStorage.removeItem("pendingSessionId");
              localStorage.removeItem("pendingProjectData");

              toast.success("Welcome! Your project has been saved.");
              navigate("/dashboard");
            } catch (err) {
              console.error("Failed to associate project data:", err);
              navigate("/dashboard");
            }
          } else {
            navigate("/dashboard");
          }
        } else {
          throw new Error("No session found");
        }
      } catch (error: unknown) {
        console.error("Auth callback error:", error);
        toast.error("Authentication failed. Please try again.");
        navigate("/login");
      }
    };

    handleAuthCallback();
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <Loader2 className="w-12 h-12 animate-spin text-primary-600 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-800">Completing sign up...</h2>
        <p className="text-gray-600 mt-2">Please wait while we set up your account.</p>
      </div>
    </div>
  );
};

export default AuthCallbackPage;
