import {
  AlertCircle,
  ArrowLeft,
  CheckCircle,
  Clock,
  DollarSign,
  MapPin,
  MessageSquare,
  Users,
} from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { supabase } from "@/lib/supabase";

interface Project {
  id: string;
  title: string;
  description: string;
  status: string;
  budget_min: number;
  budget_max: number;
  timeline: string;
  location: string;
  created_at: string;
  job_details: any;
  homeowner: {
    id: string;
    email: string;
    full_name: string;
  };
}

interface BidCard {
  id: string;
  project_id: string;
  contractor_id: string;
  status: string;
  bid_amount: number;
  timeline_days: number;
  message: string;
  created_at: string;
  contractor: {
    id: string;
    company_name: string;
    contact_name: string;
    email: string;
    phone: string;
    rating: number;
    verified: boolean;
  };
}

const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [bidCards, setBidCards] = useState<BidCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedBid, setSelectedBid] = useState<string | null>(null);

  const fetchProjectDetails = async () => {
    try {
      const { data, error } = await supabase
        .from("projects")
        .select(`
          *,
          homeowner:homeowners!projects_user_id_fkey(
            id,
            email,
            full_name
          )
        `)
        .eq("id", id)
        .single();

      if (error) throw error;
      setProject(data);
    } catch (error) {
      console.error("Error fetching project:", error);
      toast.error("Failed to load project details");
    }
  };

  const fetchBidCards = async () => {
    try {
      const { data, error } = await supabase
        .from("bid_cards")
        .select(`
          *,
          contractor:contractors!bid_cards_contractor_id_fkey(
            id,
            company_name,
            contact_name,
            email,
            phone,
            rating,
            verified
          )
        `)
        .eq("project_id", id)
        .order("created_at", { ascending: false });

      if (error) throw error;
      setBidCards(data || []);
    } catch (error) {
      console.error("Error fetching bid cards:", error);
      toast.error("Failed to load bids");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchProjectDetails();
      fetchBidCards();
    }
  }, [id]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-green-100 text-green-800";
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      case "completed":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getBidStatusColor = (status: string) => {
    switch (status) {
      case "submitted":
        return "text-blue-600";
      case "viewed":
        return "text-purple-600";
      case "accepted":
        return "text-green-600";
      case "rejected":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Project Not Found</h2>
          <p className="text-gray-600 mb-4">
            This project doesn't exist or you don't have access to it.
          </p>
          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">{project.title}</h1>
                <p className="text-sm text-gray-600">
                  Created {new Date(project.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(project.status)}`}
            >
              {project.status.charAt(0).toUpperCase() + project.status.slice(1)}
            </span>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Project Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Description */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Project Description</h2>
              <p className="text-gray-600 whitespace-pre-wrap">{project.description}</p>
            </div>

            {/* Bid Cards */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-gray-900">Contractor Bids</h2>
                <span className="text-sm text-gray-500">{bidCards.length} bids received</span>
              </div>

              {bidCards.length === 0 ? (
                <div className="text-center py-12">
                  <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 mb-2">No bids yet</p>
                  <p className="text-sm text-gray-400">
                    We're reaching out to qualified contractors
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {bidCards.map((bid) => (
                    <div
                      key={bid.id}
                      className={`border rounded-lg p-4 cursor-pointer transition-all ${
                        selectedBid === bid.id
                          ? "border-primary-500 bg-primary-50"
                          : "border-gray-200 hover:border-gray-300"
                      }`}
                      onClick={() => setSelectedBid(bid.id === selectedBid ? null : bid.id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h3 className="font-medium text-gray-900">
                              {bid.contractor.company_name}
                            </h3>
                            {bid.contractor.verified && (
                              <CheckCircle
                                className="w-4 h-4 text-green-500"
                                title="Verified Contractor"
                              />
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mb-2">
                            {bid.contractor.contact_name}
                          </p>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="font-medium text-gray-900">
                              ${bid.bid_amount.toLocaleString()}
                            </span>
                            <span className="text-gray-500">•</span>
                            <span className="text-gray-600">{bid.timeline_days} days</span>
                            <span className="text-gray-500">•</span>
                            <span className={getBidStatusColor(bid.status)}>{bid.status}</span>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => console.log("Click")}
                          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                          <MessageSquare className="w-5 h-5 text-gray-600" />
                        </button>
                      </div>

                      {selectedBid === bid.id && (
                        <div className="mt-4 pt-4 border-t border-gray-200">
                          <p className="text-sm text-gray-600 mb-3">{bid.message}</p>
                          <div className="flex gap-3">
                            <button
                              type="button"
                              onClick={() => console.log("Click")}
                              className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors text-sm font-medium"
                            >
                              Contact Contractor
                            </button>
                            <button
                              type="button"
                              onClick={() => window.open(`tel:${bid.contractor.phone}`, "_self")}
                              className="flex-1 border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
                            >
                              Call {bid.contractor.phone}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Project Info */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Project Details</h3>
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <DollarSign className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Budget</p>
                    <p className="text-sm text-gray-600">
                      ${project.budget_min.toLocaleString()} - $
                      {project.budget_max.toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Clock className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Timeline</p>
                    <p className="text-sm text-gray-600">{project.timeline}</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">Location</p>
                    <p className="text-sm text-gray-600">{project.location}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button
                  type="button"
                  onClick={() => navigate("/chat")}
                  className="w-full flex items-center justify-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors"
                >
                  <MessageSquare className="w-4 h-4" />
                  Continue with CIA
                </button>
                <button
                  type="button"
                  onClick={() => navigate(`/projects/${id}/edit`)}
                  className="w-full flex items-center justify-center gap-2 border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Edit Project
                </button>
              </div>
            </div>

            {/* Help */}
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex gap-3">
                <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-blue-900 mb-1">Need help?</p>
                  <p className="text-sm text-blue-700">
                    Our AI assistant can help you compare bids and make the best choice for your
                    project.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetailPage;
