import {
  AlertCircle,
  ArrowLeft,
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
}

const HomeownerProjectWorkspaceFixed: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const user = { id: "11111111-1111-1111-1111-111111111111" }; // Hardcoded for testing - matches actual homeowner ID

  // State - all declared at top level to maintain hook order
  const [activeTab, setActiveTab] = useState<
    "overview" | "chat" | "contractors" | "documents" | "analytics"
  >("overview");
  const [bidCard, setBidCard] = useState<BidCardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const projectId = id;

  // Single useEffect for loading data
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
            console.log("Found bid card:", foundCard.bid_card_number, "Full card data:", foundCard);
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
              <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold border bg-green-100 text-green-800 border-green-200">
                {bidCard.status?.toUpperCase()}
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
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === "overview" && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Project Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Budget Range</h3>
                <p className="text-lg font-semibold text-gray-900">
                  ${bidCard.budget_min?.toLocaleString()} - ${bidCard.budget_max?.toLocaleString()}
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Contractors Needed</h3>
                <p className="text-lg font-semibold text-gray-900">
                  {bidCard.contractor_count_needed}
                </p>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="text-sm font-medium text-gray-600 mb-1">Timeline</h3>
                <p className="text-lg font-semibold text-gray-900">{bidCard.urgency_level}</p>
              </div>
            </div>
            <p className="text-gray-600">
              This is your project workspace. Use the tabs above to view contractor communications,
              project documents, and analytics.
            </p>
          </div>
        )}

        {activeTab === "contractors" && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            {(() => {
              console.log(
                "HomeownerProjectWorkspaceFixed: Passing bidCardId:",
                bidCard.id,
                "bidCard:",
                bidCard
              );
              return null;
            })()}
            <ContractorCommunicationHub
              bidCardId={bidCard.id}
              homeownerId={"11111111-1111-1111-1111-111111111111"}
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
      </div>
    </div>
  );
};

export default HomeownerProjectWorkspaceFixed;
