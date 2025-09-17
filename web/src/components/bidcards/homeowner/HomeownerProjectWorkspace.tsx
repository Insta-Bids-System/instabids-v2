import {
  AlertCircle,
  ArrowLeft,
  Clock,
  DollarSign,
  Edit3,
  FileText,
  Home,
  MessageSquare,
  TrendingUp,
  Users,
} from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ContractorCommunicationHub from "@/components/homeowner/ContractorCommunicationHub";

interface BidCardData {
  id: string;
  bid_card_number: string;
  project_type: string;
  status: string;
  budget_min: number;
  budget_max: number;
  contractor_count_needed: number;
  urgency_level: string;
  created_at: string;
  bid_document?: {
    all_extracted_data?: {
      location?: {
        city?: string;
        state?: string;
        address?: string;
        zip_code?: string;
        full_location?: string;
      };
      project_description?: string;
      service_type?: string;
      timeline_urgency?: string;
      material_preferences?: string[];
      special_requirements?: string[];
      contractor_requirements?: {
        contractor_count?: number;
        equipment_needed?: string[];
        licenses_required?: string[];
        specialties_required?: string[];
      };
      property_details?: {
        type?: string;
      };
      images?: string[];
      intention_score?: number;
      group_bidding_potential?: boolean;
    };
  };
  view_count?: number;
  click_count?: number;
  contractor_signups?: number;
}

const HomeownerProjectWorkspace: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const user = { id: "test-homeowner-id" }; // Hardcoded for testing

  // All state hooks declared at top level to maintain consistent order
  const [activeTab, setActiveTab] = useState<
    "overview" | "chat" | "contractors" | "documents" | "analytics"
  >("overview");
  const [bidCard, setBidCard] = useState<BidCardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [chatMessage, setChatMessage] = useState("");

  const projectId = id;

  // Single useEffect for all data loading - no conditional effects
  useEffect(() => {
    const loadBidCard = async () => {
      if (!projectId) {
        setError("No project ID provided");
        setLoading(false);
        return;
      }

      try {
        console.log("Loading bid card with ID:", projectId);
        const response = await fetch(`/api/bid-cards/homeowner/${user.id}`);

        if (response.ok) {
          const allCards = await response.json();
          console.log("API response received:", allCards.length, "cards");

          const foundCard = allCards.find(
            (card: BidCardData) => card.id === projectId || card.bid_card_number === projectId
          );

          if (foundCard) {
            console.log("Found bid card:", foundCard.bid_card_number);
            setBidCard(foundCard);
          } else {
            setError("Bid card not found");
          }
        } else {
          setError("Failed to load bid card");
        }
      } catch (error) {
        console.error("Error loading bid card:", error);
        setError("Error loading bid card");
      } finally {
        setLoading(false);
      }
    };

    loadBidCard();
  }, [projectId, user.id]);

  const handleTabClick = (
    tabName: "overview" | "chat" | "contractors" | "documents" | "analytics"
  ) => {
    setActiveTab(tabName);
  };

  const formatProjectType = (type: string) => {
    return type?.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()) || "Home Project";
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "active":
        return "bg-green-100 text-green-800 border-green-200";
      case "pending":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "completed":
        return "bg-blue-100 text-blue-800 border-blue-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !bidCard) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            {error || "Project Not Found"}
          </h2>
          <p className="text-gray-600 mb-6">
            The project you're looking for doesn't exist or you don't have access to it.
          </p>
          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const extractedData = bidCard?.bid_document?.all_extracted_data || {};
  const photos = extractedData.images || [];

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
                <h1 className="text-xl font-semibold text-gray-900">
                  {formatProjectType(bidCard.project_type)}
                </h1>
                <p className="text-sm text-gray-500">{bidCard.bid_card_number}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(bidCard.status)}`}
              >
                {bidCard.status?.toUpperCase()}
              </div>
              <button
                type="button"
                onClick={() => navigate("/dashboard")}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
              >
                <Edit3 className="w-4 h-4" />
                Modify Project
              </button>
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
              onClick={() => handleTabClick("chat")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "chat"
                  ? "bg-blue-600 text-white"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              Project Chat
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
            <button
              type="button"
              onClick={() => handleTabClick("documents")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "documents"
                  ? "bg-blue-600 text-white"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              }`}
            >
              <FileText className="w-4 h-4" />
              Documents
            </button>
            <button
              type="button"
              onClick={() => handleTabClick("analytics")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === "analytics"
                  ? "bg-blue-600 text-white"
                  : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              Analytics
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === "overview" && (
          <div className="space-y-8">
            {/* Project Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <div className="flex items-center gap-3 mb-2">
                  <DollarSign className="w-5 h-5 text-green-600" />
                  <span className="text-sm font-medium text-gray-600">Budget Range</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  ${bidCard.budget_min?.toLocaleString()} - ${bidCard.budget_max?.toLocaleString()}
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <div className="flex items-center gap-3 mb-2">
                  <Users className="w-5 h-5 text-blue-600" />
                  <span className="text-sm font-medium text-gray-600">Contractors Needed</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {bidCard.contractor_count_needed}
                </div>
              </div>

              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <div className="flex items-center gap-3 mb-2">
                  <Clock className="w-5 h-5 text-orange-600" />
                  <span className="text-sm font-medium text-gray-600">Timeline</span>
                </div>
                <div className="text-2xl font-bold text-gray-900">
                  {extractedData.timeline_urgency || bidCard.urgency_level}
                </div>
              </div>
            </div>

            {/* Project Description */}
            {extractedData.project_description && (
              <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Project Description
                </h3>
                <p className="text-gray-700 leading-relaxed">{extractedData.project_description}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === "chat" && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Project Modifications</h2>
              <p className="text-gray-600 mt-1">
                Make changes to your project requirements, budget, timeline, or other details.
              </p>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    What would you like to modify about your project?
                  </label>
                  <textarea
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    placeholder="I want to increase the budget to $50,000 and add premium appliances..."
                    className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => navigate("/dashboard")}
                    disabled={!chatMessage.trim()}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <MessageSquare className="w-4 h-4" />
                    Start Modification Chat
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "contractors" && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <ContractorCommunicationHub
              bidCardId={projectId || ""}
              homeownerId={user.id || "test-homeowner-id"}
            />
          </div>
        )}

        {activeTab === "documents" && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Project Documents</h2>
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Coming Soon</h3>
              <p className="text-gray-600">
                Document management features will be available in a future update.
              </p>
            </div>
          </div>
        )}

        {activeTab === "analytics" && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Project Analytics</h2>
            <div className="text-center py-12">
              <TrendingUp className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Coming Soon</h3>
              <p className="text-gray-600">
                Advanced analytics and reporting features will be available in a future update.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomeownerProjectWorkspace;
