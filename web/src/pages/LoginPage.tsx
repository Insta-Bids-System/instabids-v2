import { Lock, Mail } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { signIn, profile, user } = useAuth();
  const navigate = useNavigate();

  // Redirect based on profile role after successful login
  useEffect(() => {
    console.log("LoginPage useEffect:", { user: !!user, profile, loading });
    
    // Clear any demo user data to prevent auto-redirect
    localStorage.removeItem("DEMO_USER");
    
    // Normal auth redirect logic - navigate immediately if user is authenticated
    if (user && !loading) {
      console.log("User authenticated, navigating to dashboard");
      // Default to homeowner dashboard if profile is not loaded yet
      const targetPath = profile?.role === "contractor" ? "/contractor/dashboard" : "/dashboard";
      console.log("Navigating to:", targetPath);
      navigate(targetPath);
    }
  }, [user, profile, loading, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await signIn(email, password);
      toast.success("Welcome back!");
      // The useEffect above will handle the redirect once profile loads
      setLoading(false);
    } catch (error: unknown) {
      toast.error(error.message || "Failed to sign in");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <Link to="/" className="flex justify-center">
            <h1 className="text-3xl font-bold text-primary-600">Instabids</h1>
          </Link>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Or{" "}
            <Link to="/signup" className="font-medium text-primary-600 hover:text-primary-500">
              create a new account
            </Link>
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none rounded-none relative block w-full px-10 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                  placeholder="Email address"
                />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none rounded-none relative block w-full px-10 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-primary-500 focus:border-primary-500 focus:z-10 sm:text-sm"
                  placeholder="Password"
                />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                Remember me
              </label>
            </div>

            <div className="text-sm">
              <a href="#" className="font-medium text-primary-600 hover:text-primary-500">
                Forgot your password?
              </a>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </div>

          <div className="relative mt-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-50 text-gray-500">or</span>
            </div>
          </div>

          <div>
            <button
              type="button"
              onClick={() => {
                // Set demo credentials for homeowner (using real UUID)
                localStorage.setItem(
                  "DEMO_USER",
                  JSON.stringify({
                    id: "550e8400-e29b-41d4-a716-446655440001",
                    email: "demo.homeowner@instabids.com",
                    role: "homeowner",
                    full_name: "Demo Homeowner",
                  })
                );
                navigate("/dashboard");
              }}
              className="group relative w-full flex justify-center py-3 px-4 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-gray-50 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Demo Homeowner Access
            </button>
          </div>

          <div>
            <button
              type="button"
              onClick={() => {
                // Set demo credentials for contractor (using real JM Holiday Lighting UUID)
                localStorage.setItem(
                  "DEMO_USER",
                  JSON.stringify({
                    id: "c24d60b5-5469-4207-a364-f20363422d8a",
                    email: "info@jmholidaylighting.com",
                    role: "contractor",
                    full_name: "JM Holiday Lighting, Inc.",
                  })
                );
                navigate("/contractor/dashboard");
              }}
              className="group relative w-full flex justify-center py-3 px-4 border border-orange-500 text-sm font-medium rounded-md text-orange-700 bg-orange-50 hover:bg-orange-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
            >
              Demo Contractor Access (JM Holiday Lighting)
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
