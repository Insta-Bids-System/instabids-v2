import { CheckCircle, Clock, Home, Plus, XCircle } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";
import EnhancedBidCard from "@/components/bidcards/homeowner/EnhancedBidCard";
import PotentialBidCard from "@/components/bidcards/PotentialBidCard";
import ContractorCommunicationHub from "@/components/homeowner/ContractorCommunicationHub";
import RFINotifications from "@/components/homeowner/RFINotifications";
import InspirationDashboard from "@/components/inspiration/InspirationDashboard";
import PropertyDashboard from "@/components/property/PropertyDashboard";
import PopularServicesTab from "@/components/groupbidding/PopularServicesTab";
import { useAuth } from "@/contexts/AuthContext";
import { type Project, supabase } from "@/lib/supabase";

const DashboardPage: React.FC = () => {
  const { user, profile, signOut } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [bidCards, setBidCards] = useState<any[]>([]);
  const [potentialBidCards, setPotentialBidCards] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"projects" | "popular" | "inspiration" | "property">("projects");
  
  console.log("[DashboardPage] Current activeTab:", activeTab);

  const loadProjects = async () => {
    if (!user) return;

    try {
      const { data, error } = await supabase
        .from("projects")
        .select("*")
        .eq("user_id", user.id)
        .order("created_at", { ascending: false });

      if (error) throw error;
      setProjects(data || []);
    } catch (error) {
      console.error("Error loading projects:", error);
      toast.error("Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  const loadBidCards = async () => {
    if (!user) return;

    try {
      // Load bid cards from the backend API using the API service
      const response = await fetch(`/api/bid-cards/user/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        console.log("[Dashboard] Loaded bid cards:", data);
        setBidCards(data || []);
      } else {
        console.error("[Dashboard] API call failed - no fallback for security");
        // Don't show all bid cards as fallback - security risk
        setBidCards([]);
      }
    } catch (error) {
      console.error("[Dashboard] Error loading bid cards:", error);
      // Don't show error toast for bid cards since they might not exist yet
    }
  };

  const loadPotentialBidCards = async () => {
    if (!user) return;

    try {
      const response = await fetch(`/api/cia/user/${user.id}/potential-bid-cards`);
      if (response.ok) {
        const data = await response.json();
        console.log("[Dashboard] Loaded potential bid cards:", data);
        setPotentialBidCards(data.bid_cards || []);
      }
    } catch (error) {
      console.error("[Dashboard] Error loading potential bid cards:", error);
    }
  };

  const handleReviewPotentialBidCard = async (bidCard: any) => {
    // For now, trigger conversion directly
    // Later we can add a confirmation chat here
    try {
      const response = await fetch(
        `/api/cia/potential-bid-cards/${bidCard.id}/convert-to-bid-card`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (response.ok) {
        const result = await response.json();
        toast.success("Your project is now live! Finding contractors...");
        
        // Reload to show the new bid card
        await loadBidCards();
        await loadPotentialBidCards();
      } else {
        const error = await response.json();
        if (error.detail?.includes("authenticated")) {
          toast.error("Please sign in to get bids");
        } else {
          toast.error("Some details are missing. Please complete your project first.");
        }
      }
    } catch (error) {
      console.error("Error converting bid card:", error);
      toast.error("Failed to start finding contractors");
    }
  };

  const handleDeletePotentialBidCard = async (bidCardId: string) => {
    try {
      const response = await fetch(
        `/api/cia/potential-bid-cards/${bidCardId}`,
        {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
        }
      );

      if (response.ok) {
        toast.success("Draft bid card deleted");
        // Reload the potential bid cards list
        await loadPotentialBidCards();
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to delete bid card");
      }
    } catch (error) {
      console.error("Error deleting bid card:", error);
      toast.error("Failed to delete bid card");
    }
  };

  useEffect(() => {
    if (user) {
      loadProjects();
      loadBidCards();
      loadPotentialBidCards();
    }
  }, [user?.id]);

  const getStatusIcon = (status: Project["status"]) => {
    switch (status) {
      case "draft":
        return <Clock className="w-5 h-5 text-gray-500" />;
      case "posted":
      case "in_bidding":
        return <Clock className="w-5 h-5 text-blue-500" />;
      case "awarded":
      case "in_progress":
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "cancelled":
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = (status: Project["status"]) => {
    switch (status) {
      case "draft":
        return "Draft";
      case "posted":
        return "Posted";
      case "in_bidding":
        return "Receiving Bids";
      case "awarded":
        return "Awarded";
      case "in_progress":
        return "In Progress";
      case "completed":
        return "Completed";
      case "cancelled":
        return "Cancelled";
      default:
        return status;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <Link to="/" className="text-2xl font-bold text-primary-600">
              Instabids
            </Link>
            <div className="flex items-center gap-4">
              <span className="text-gray-600">{profile?.full_name || user?.email}</span>
              <button
                type="button"
                onClick={signOut}
                className="text-gray-700 hover:text-primary-600"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            <button
              type="button"
              onClick={() => setActiveTab("projects")}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === "projects"
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              My Projects
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("popular")}
              className={`py-2 px-1 border-b-2 font-medium text-sm relative ${
                activeTab === "popular"
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Popular Services
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Save 15-25%!
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("inspiration")}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === "inspiration"
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Inspiration Board
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("property")}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === "property"
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              My Property
            </button>
          </nav>
        </div>

        {/* Conditional Content */}
        {activeTab === "projects" ? (
          <>
            {/* RFI Notifications Section */}
            {user && <RFINotifications homeownerId={user.id} />}
            
            <div className="mb-8 flex justify-between items-center">
              <h1 className="text-3xl font-bold text-gray-900">My Projects</h1>
              <Link
                to="/chat"
                className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
                New Project
              </Link>
            </div>

            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              </div>
            ) : projects.length === 0 && bidCards.length === 0 && potentialBidCards.length === 0 ? (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <Home className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-gray-900 mb-2">No projects yet</h2>
                <p className="text-gray-600 mb-6">
                  Start by describing your first project to our AI assistant
                </p>
                <Link
                  to="/chat"
                  className="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors"
                >
                  <Plus className="w-5 h-5" />
                  Create Your First Project
                </Link>
              </div>
            ) : (
              <div className="space-y-8">
                {/* Potential Bid Cards Section - Show FIRST */}
                {potentialBidCards.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h2 className="text-2xl font-semibold text-gray-900">
                          Projects Ready for Bids
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">
                          Complete your project details to start finding contractors
                        </p>
                      </div>
                      <span className="text-sm text-gray-500">{potentialBidCards.length} draft{potentialBidCards.length > 1 ? 's' : ''}</span>
                    </div>
                    <div className="grid gap-6 lg:grid-cols-2">
                      {potentialBidCards.map((bidCard) => (
                        <PotentialBidCard
                          key={bidCard.id}
                          bidCard={bidCard}
                          onReview={handleReviewPotentialBidCard}
                          onDelete={handleDeletePotentialBidCard}
                          onBidCardUpdate={() => {
                            loadBidCards();
                            loadPotentialBidCards();
                          }}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Active Bid Cards Section */}
                {bidCards.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-2xl font-semibold text-gray-900">
                        AI-Generated Bid Cards
                      </h2>
                      <span className="text-sm text-gray-500">{bidCards.length} active</span>
                    </div>
                    <div className="grid gap-6 lg:grid-cols-2">
                      {bidCards.map((bidCard) => (
                        <div
                          key={bidCard.id}
                          className="cursor-pointer"
                          onClick={() => {
                            // Fixed navigation - use correct route path
                            navigate(`/bid-cards/${bidCard.id}`);
                          }}
                        >
                          <EnhancedBidCard
                            bidCard={bidCard}
                            onContinueChat={(e) => {
                              e?.stopPropagation();
                              navigate("/chat", {
                                state: {
                                  projectContext: bidCard,
                                  initialMessage: `I want to continue working on my ${bidCard.project_type} project (${bidCard.bid_card_number})`,
                                },
                              });
                            }}
                            onViewAnalytics={(e) => {
                              e?.stopPropagation();
                              toast.success("Analytics coming soon!");
                            }}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Regular Projects Section */}
                {projects.length > 0 && (
                  <div>
                    <div className="flex items-center justify-between mb-6">
                      <h2 className="text-2xl font-semibold text-gray-900">Regular Projects</h2>
                      <span className="text-sm text-gray-500">{projects.length} projects</span>
                    </div>
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                      {projects.map((project) => (
                        <div
                          key={project.id}
                          className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
                          onClick={() => navigate(`/projects/${project.id}`)}
                        >
                          <div className="p-6">
                            <div className="flex items-start justify-between mb-4">
                              <h3 className="text-lg font-semibold text-gray-900 line-clamp-1">
                                {project.title}
                              </h3>
                              {getStatusIcon(project.status)}
                            </div>
                            <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                              {project.description}
                            </p>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-500">{project.category}</span>
                              <span
                                className={`font-medium ${
                                  project.status === "completed"
                                    ? "text-green-600"
                                    : project.status === "cancelled"
                                      ? "text-red-600"
                                      : "text-blue-600"
                                }`}
                              >
                                {getStatusText(project.status)}
                              </span>
                            </div>
                            {project.budget_range && (
                              <div className="mt-3 text-sm text-gray-600">
                                Budget: ${project.budget_range.min.toLocaleString()} - $
                                {project.budget_range.max.toLocaleString()}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        ) : activeTab === "popular" ? (
          <PopularServicesTab />
        ) : activeTab === "inspiration" ? (
          <InspirationDashboard />
        ) : activeTab === "property" ? (
          (() => {
            console.log("[DashboardPage] Rendering PropertyDashboard for activeTab:", activeTab);
            return <PropertyDashboard />;
          })()
        ) : (
          (() => {
            console.log("[DashboardPage] Default fallback case - activeTab:", activeTab);
            return <PropertyDashboard />;
          })()
        )}
      </main>
    </div>
  );
};

export default DashboardPage;
