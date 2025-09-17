import { ArrowLeft, FileText, Home, MessageSquare, TrendingUp, Users } from "lucide-react";
import type React from "react";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

interface BidCardData {
  id: string;
  bid_card_number: string;
  project_type: string;
  status: string;
}

const HomeownerProjectWorkspaceSimple: React.FC = () => {
  const { id } = useParams();
  const user = { id: "test-homeowner-id" };
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<
    "overview" | "chat" | "contractors" | "documents" | "analytics"
  >("overview");

  // Mock bid card data to avoid API call
  const bidCard: BidCardData = {
    id: id || "",
    bid_card_number: id || "",
    project_type: "kitchen_remodel",
    status: "active",
  };

  const handleTabClick = (
    tabName: "overview" | "chat" | "contractors" | "documents" | "analytics"
  ) => {
    setActiveTab(tabName);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={() => navigate("/dashboard")}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Dashboard
              </button>
              <div className="h-6 w-px bg-gray-300" />
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Kitchen Remodel</h1>
                <p className="text-sm text-gray-500">{bidCard.bid_card_number}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-1 py-3">
            <button
              type="button"
              onClick={() => handleTabClick("overview")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "overview"
                  ? "bg-blue-600 text-white"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              }`}
            >
              <Home className="w-4 h-4" />
              Overview
            </button>
            <button
              type="button"
              onClick={() => handleTabClick("contractors")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "contractors"
                  ? "bg-blue-600 text-white"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              }`}
            >
              <Users className="w-4 h-4" />
              Contractors
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === "overview" && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">Project Overview</h2>
            <p>This is a simplified version to test basic functionality.</p>
          </div>
        )}

        {activeTab === "contractors" && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold mb-4">Contractor Communications</h2>
            <p>Contractor communications would appear here.</p>
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                Tab switching is working! This content only appears when the Contractors tab is
                active.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomeownerProjectWorkspaceSimple;
