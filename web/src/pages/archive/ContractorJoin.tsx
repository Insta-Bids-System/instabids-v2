import { ArrowRight, CheckCircle, Clock, DollarSign, MapPin, Users } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

interface BidCard {
  id: string;
  public_token: string;
  project_type: string;
  urgency: string;
  budget_display: string;
  location: {
    city: string;
    state: string;
  };
  contractor_count: number;
  created_at: string;
}

const ContractorJoin: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [bidCard, setBidCard] = useState<BidCard | null>(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    company: "",
    trade: "",
    zipCode: "",
  });

  const bidToken = searchParams.get("bid");
  const source = searchParams.get("src") || "direct";

  useEffect(() => {
    // Track the click
    if (bidToken) {
      trackBidCardClick(bidToken, source);
      loadBidCard(bidToken);
    } else {
      setLoading(false);
    }
  }, [bidToken, source, loadBidCard, trackBidCardClick]);

  const trackBidCardClick = async (token: string, source: string) => {
    try {
      await fetch("/api/track/bid-card-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bid_token: token,
          source_channel: source,
          ip_address: "", // Will be captured server-side
          user_agent: navigator.userAgent,
        }),
      });
    } catch (error) {
      console.error("Failed to track click:", error);
    }
  };

  const loadBidCard = async (token: string) => {
    try {
      const response = await fetch(`/api/bid-cards/by-token/${token}`);
      if (response.ok) {
        const data = await response.json();
        setBidCard(data);
      }
    } catch (error) {
      console.error("Failed to load bid card:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // Create contractor account
      const response = await fetch("/api/contractors/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          source: source,
          bid_context: bidToken,
        }),
      });

      if (response.ok) {
        const contractor = await response.json();

        // Mark this click as converted
        await fetch("/api/track/bid-card-conversion", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            bid_token: bidToken,
            contractor_id: contractor.id,
          }),
        });

        // Redirect to welcome page
        navigate("/contractor/welcome");
      }
    } catch (error) {
      console.error("Signup failed:", error);
    }
  };

  const formatProjectType = (type: string) => {
    return type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case "emergency":
        return "bg-red-100 text-red-800 border-red-200";
      case "week":
        return "bg-orange-100 text-orange-800 border-orange-200";
      case "month":
        return "bg-blue-100 text-blue-800 border-blue-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getUrgencyText = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case "emergency":
        return "Urgent - ASAP";
      case "week":
        return "Within 7 Days";
      case "month":
        return "Within 30 Days";
      default:
        return "Flexible Timeline";
    }
  };

  const commonTrades = [
    "General Contractor",
    "Electrician",
    "Plumber",
    "HVAC",
    "Carpenter",
    "Painter",
    "Roofer",
    "Landscaper",
    "Handyman",
    "Other",
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading project details...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Join InstaBids - Submit Quotes for Free
          </h1>
          <p className="text-xl text-gray-600">No longer pay for leads, only jobs</p>
        </div>

        {/* Bid Card Context */}
        {bidCard && (
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 mb-8 border border-blue-100">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
              You're responding to this project:
            </h2>

            <div className="bg-white rounded-lg p-6 shadow-sm">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-2xl font-bold text-gray-900">
                  {formatProjectType(bidCard.project_type)}
                </h3>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium border ${getUrgencyColor(bidCard.urgency)}`}
                >
                  <Clock className="w-4 h-4 inline mr-1" />
                  {getUrgencyText(bidCard.urgency)}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-gray-600">
                <div className="flex items-center">
                  <MapPin className="w-5 h-5 mr-2 text-gray-400" />
                  {bidCard.location.city}, {bidCard.location.state}
                </div>
                <div className="flex items-center">
                  <DollarSign className="w-5 h-5 mr-2 text-gray-400" />
                  {bidCard.budget_display}
                </div>
                <div className="flex items-center">
                  <Users className="w-5 h-5 mr-2 text-gray-400" />
                  {bidCard.contractor_count} contractors needed
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Benefits Section */}
          <div className="bg-white rounded-xl shadow-sm p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Why Join InstaBids?</h2>

            <div className="space-y-4">
              <div className="flex items-start">
                <CheckCircle className="w-6 h-6 text-green-500 mr-3 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">No Lead Fees</h3>
                  <p className="text-gray-600">
                    Submit unlimited quotes for free. Pay only when you get the job.
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <CheckCircle className="w-6 h-6 text-green-500 mr-3 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">Pre-Qualified Leads</h3>
                  <p className="text-gray-600">
                    All homeowners have confirmed budgets and are ready to hire.
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <CheckCircle className="w-6 h-6 text-green-500 mr-3 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">Local Projects</h3>
                  <p className="text-gray-600">
                    Only get opportunities in your service area and trade.
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <CheckCircle className="w-6 h-6 text-green-500 mr-3 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900">Quick Setup</h3>
                  <p className="text-gray-600">
                    Get started in under 2 minutes. Start bidding immediately.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Signup Form */}
          <div className="bg-white rounded-xl shadow-sm p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Create Your Free Account</h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    First Name *
                  </label>
                  <input
                    type="text"
                    name="firstName"
                    required
                    value={formData.firstName}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Last Name *
                  </label>
                  <input
                    type="text"
                    name="lastName"
                    required
                    value={formData.lastName}
                    onChange={handleInputChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address *
                </label>
                <input
                  type="email"
                  name="email"
                  required
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Phone Number *
                </label>
                <input
                  type="tel"
                  name="phone"
                  required
                  value={formData.phone}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Company Name</label>
                <input
                  type="text"
                  name="company"
                  value={formData.company}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Primary Trade *
                </label>
                <select
                  name="trade"
                  required
                  value={formData.trade}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select your trade</option>
                  {commonTrades.map((trade) => (
                    <option key={trade} value={trade}>
                      {trade}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Service Area ZIP Code *
                </label>
                <input
                  type="text"
                  name="zipCode"
                  required
                  value={formData.zipCode}
                  onChange={handleInputChange}
                  placeholder="32904"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-4 px-6 rounded-lg font-semibold hover:bg-blue-700 transition text-lg flex items-center justify-center"
              >
                Join InstaBids - Start Bidding for Free
                <ArrowRight className="w-5 h-5 ml-2" />
              </button>

              <p className="text-xs text-gray-500 text-center">
                By signing up, you agree to our Terms of Service and Privacy Policy. You can
                unsubscribe at any time.
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContractorJoin;
