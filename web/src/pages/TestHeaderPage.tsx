import React from "react";
import AuthStatus from "@/components/AuthStatus";
import { useAuth } from "@/contexts/AuthContext";

const TestHeaderPage: React.FC = () => {
  const { user, profile } = useAuth();
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Test AppLayout header */}
      <div className="bg-yellow-100 p-4 border-b-2 border-yellow-400">
        <h2 className="text-lg font-bold mb-2">Test: AppLayout Header (Should show on /dashboard)</h2>
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <div className="text-2xl font-bold text-primary-600">
                  InstaBids
                </div>
              </div>
              <div className="flex items-center">
                <AuthStatus />
              </div>
            </div>
          </div>
        </header>
      </div>

      {/* Debug info */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-bold mb-4">Auth Debug Info</h3>
          
          <div className="space-y-4">
            <div>
              <h4 className="font-semibold text-gray-700">AuthContext (useAuth):</h4>
              <pre className="bg-gray-100 p-2 rounded text-xs">
                {JSON.stringify({ 
                  userExists: !!user, 
                  userId: user?.id,
                  userEmail: user?.email,
                  profileExists: !!profile,
                  profileName: profile?.full_name
                }, null, 2)}
              </pre>
            </div>

            <div>
              <h4 className="font-semibold text-gray-700">Current location:</h4>
              <p className="text-gray-600">{window.location.pathname}</p>
            </div>

            <div>
              <h4 className="font-semibold text-gray-700">Expected behavior:</h4>
              <ul className="list-disc ml-5 text-gray-600">
                <li>When logged in with Google, AuthStatus should show your Google profile</li>
                <li>The header above should be visible at the top of /dashboard</li>
                <li>This is what AppLayout should render</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestHeaderPage;