import React from "react";
import { useNavigate } from "react-router-dom";

const QuickTestDashboard: React.FC = () => {
  const navigate = useNavigate();
  
  // Bypass all auth - just show a working dashboard
  const mockUser = {
    id: "01087874-747b-4159-8735-5ebb8715ff84",
    email: "jjthompsonfau@gmail.com",
    name: "Justin"
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Dashboard (Auth Bypassed for Testing)</h1>
        
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">User Info</h2>
          <p>Email: {mockUser.email}</p>
          <p>Name: {mockUser.name}</p>
          <p>ID: {mockUser.id}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <button
            onClick={() => navigate("/dashboard")}
            className="p-6 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Go to Real Dashboard
          </button>
          
          <button
            onClick={() => navigate("/")}
            className="p-6 bg-green-500 text-white rounded-lg hover:bg-green-600"
          >
            Go to Home
          </button>
          
          <button
            onClick={() => {
              // Force set auth in localStorage
              localStorage.setItem("test_auth", JSON.stringify(mockUser));
              alert("Auth data saved to localStorage");
            }}
            className="p-6 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
          >
            Save Auth to LocalStorage
          </button>
        </div>

        <div className="mt-8 p-6 bg-yellow-100 rounded-lg">
          <h3 className="font-bold mb-2">Testing Notes:</h3>
          <p>This dashboard bypasses all authentication to test if the app works at all.</p>
          <p>If this page loads, the React app is working.</p>
          <p>If clicking buttons works, routing is working.</p>
        </div>
      </div>
    </div>
  );
};

export default QuickTestDashboard;