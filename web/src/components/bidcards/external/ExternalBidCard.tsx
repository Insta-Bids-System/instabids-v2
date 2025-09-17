import { ArrowRight, Camera, MapPin, Users, Zap } from "lucide-react";
import type React from "react";
import { useState } from "react";

interface ExternalBidCardProps {
  bidCard: {
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
    photo_urls?: string[];
    project_details?: {
      scope_of_work?: string[];
    };
  };
  variant?: "email" | "sms" | "web_embed";
  source?: string;
}

const ExternalBidCard: React.FC<ExternalBidCardProps> = ({
  bidCard,
  variant = "web_embed",
  source = "web",
}) => {
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);

  const formatProjectType = (type: string) => {
    return type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case "emergency":
        return "bg-red-500 text-white";
      case "week":
        return "bg-orange-500 text-white";
      case "month":
        return "bg-blue-500 text-white";
      default:
        return "bg-gray-500 text-white";
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

  const getLandingUrl = () => {
    return `/contractor?bid=${bidCard.public_token}&src=${source}`;
  };

  // SMS Version - Ultra compact
  if (variant === "sms") {
    return (
      <div className="text-sm space-y-1">
        <div className="font-bold text-gray-900">
          🏠 New {formatProjectType(bidCard.project_type)} Job
        </div>
        <div className="text-gray-700">
          📍 {bidCard.location.city}, {bidCard.location.state}
        </div>
        <div className="text-gray-700">
          💰 {bidCard.budget_display} • ⏰ {getUrgencyText(bidCard.urgency)}
        </div>
        <div className="text-gray-700">👥 {bidCard.contractor_count} contractors needed</div>
        {bidCard.photo_urls && bidCard.photo_urls.length > 0 && (
          <div className="text-gray-600">📸 {bidCard.photo_urls.length} photos included</div>
        )}
        <div className="pt-2">
          <a href={getLandingUrl()} className="text-blue-600 font-semibold underline">
            Join InstaBids to bid - FREE signup ➜
          </a>
        </div>
      </div>
    );
  }

  // Email Version - HTML email safe
  if (variant === "email") {
    return (
      <div
        style={{
          maxWidth: "600px",
          margin: "0 auto",
          backgroundColor: "#ffffff",
          borderRadius: "16px",
          overflow: "hidden",
          boxShadow: "0 10px 25px rgba(0,0,0,0.1)",
          border: "1px solid #e5e7eb",
          fontFamily: "-apple-system, BlinkMacSystemFont, sans-serif",
        }}
      >
        {/* Header with urgency badge */}
        <div
          style={{
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            padding: "20px",
            position: "relative",
            color: "white",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: "16px",
              right: "16px",
              backgroundColor: "rgba(255,255,255,0.2)",
              backdropFilter: "blur(10px)",
              padding: "6px 12px",
              borderRadius: "20px",
              fontSize: "12px",
              fontWeight: "600",
            }}
          >
            🔥 NEW PROJECT
          </div>

          <h2
            style={{
              fontSize: "28px",
              fontWeight: "bold",
              margin: "0 0 8px 0",
              lineHeight: "1.2",
            }}
          >
            {formatProjectType(bidCard.project_type)}
          </h2>

          <div
            style={{
              fontSize: "16px",
              opacity: "0.9",
              margin: "0",
            }}
          >
            {bidCard.location.city}, {bidCard.location.state}
          </div>
        </div>

        {/* Photo Section */}
        {bidCard.photo_urls && bidCard.photo_urls.length > 0 && (
          <div style={{ position: "relative", height: "250px", overflow: "hidden" }}>
            <img
              src={bidCard.photo_urls[0]}
              alt="Project photo"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
              }}
            />
            {bidCard.photo_urls.length > 1 && (
              <div
                style={{
                  position: "absolute",
                  bottom: "12px",
                  right: "12px",
                  backgroundColor: "rgba(0,0,0,0.7)",
                  color: "white",
                  padding: "6px 10px",
                  borderRadius: "16px",
                  fontSize: "14px",
                  fontWeight: "500",
                }}
              >
                📸 {bidCard.photo_urls.length} photos
              </div>
            )}
          </div>
        )}

        {/* Content */}
        <div style={{ padding: "24px" }}>
          {/* Key Details */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
              gap: "16px",
              marginBottom: "20px",
            }}
          >
            <div
              style={{
                textAlign: "center",
                padding: "12px",
                backgroundColor: "#f8fafc",
                borderRadius: "8px",
              }}
            >
              <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>BUDGET</div>
              <div style={{ fontSize: "16px", fontWeight: "bold", color: "#0f172a" }}>
                {bidCard.budget_display}
              </div>
            </div>

            <div
              style={{
                textAlign: "center",
                padding: "12px",
                backgroundColor: "#f8fafc",
                borderRadius: "8px",
              }}
            >
              <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>
                TIMELINE
              </div>
              <div style={{ fontSize: "16px", fontWeight: "bold", color: "#0f172a" }}>
                {getUrgencyText(bidCard.urgency)}
              </div>
            </div>

            <div
              style={{
                textAlign: "center",
                padding: "12px",
                backgroundColor: "#f8fafc",
                borderRadius: "8px",
              }}
            >
              <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>
                CONTRACTORS NEEDED
              </div>
              <div style={{ fontSize: "16px", fontWeight: "bold", color: "#0f172a" }}>
                {bidCard.contractor_count}
              </div>
            </div>
          </div>

          {/* Project Scope */}
          {bidCard.project_details?.scope_of_work && (
            <div style={{ marginBottom: "24px" }}>
              <h3
                style={{
                  fontSize: "16px",
                  fontWeight: "600",
                  color: "#374151",
                  marginBottom: "12px",
                }}
              >
                Project Includes:
              </h3>
              <ul style={{ margin: "0", paddingLeft: "20px", color: "#6b7280" }}>
                {bidCard.project_details.scope_of_work.slice(0, 3).map((item, index) => (
                  <li key={index} style={{ marginBottom: "4px" }}>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Value Proposition */}
          <div
            style={{
              background: "linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 100%)",
              padding: "20px",
              borderRadius: "12px",
              marginBottom: "24px",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontSize: "18px",
                fontWeight: "bold",
                color: "#0c4a6e",
                marginBottom: "8px",
              }}
            >
              🎯 Why InstaBids?
            </div>
            <div style={{ fontSize: "14px", color: "#075985", lineHeight: "1.5" }}>
              ✅ Zero lead fees - pay only when you win
              <br />✅ Pre-qualified homeowners ready to hire
              <br />✅ Higher win rates than other platforms
            </div>
          </div>

          {/* CTA Button */}
          <div style={{ textAlign: "center" }}>
            <a
              href={getLandingUrl()}
              style={{
                display: "inline-block",
                background: "linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)",
                color: "white",
                padding: "16px 32px",
                borderRadius: "12px",
                textDecoration: "none",
                fontWeight: "bold",
                fontSize: "18px",
                boxShadow: "0 4px 15px rgba(59, 130, 246, 0.3)",
              }}
            >
              Join InstaBids - Submit Quote FREE ➜
            </a>

            <div
              style={{
                fontSize: "12px",
                color: "#9ca3af",
                marginTop: "12px",
                lineHeight: "1.4",
              }}
            >
              No longer pay for leads, only jobs
              <br />
              Takes 2 minutes • Start bidding immediately
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Web Embed Version - Interactive
  return (
    <div className="max-w-md mx-auto bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 hover:shadow-2xl transition-all duration-300">
      {/* Animated Header */}
      <div className="relative bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-600 p-6 text-white">
        <div className="absolute top-3 right-3">
          <div className="flex items-center gap-1 bg-white/20 backdrop-blur-sm rounded-full px-3 py-1 text-xs font-semibold">
            <Zap className="w-3 h-3" />
            NEW
          </div>
        </div>

        <h3 className="text-xl font-bold mb-2 pr-16">{formatProjectType(bidCard.project_type)}</h3>

        <div className="flex items-center gap-2 text-white/90">
          <MapPin className="w-4 h-4" />
          <span className="text-sm">
            {bidCard.location.city}, {bidCard.location.state}
          </span>
        </div>
      </div>

      {/* Photo Carousel */}
      {bidCard.photo_urls && bidCard.photo_urls.length > 0 && (
        <div className="relative h-48 bg-gray-100">
          <img
            src={bidCard.photo_urls[currentPhotoIndex]}
            alt="Project photo"
            className="w-full h-full object-cover"
          />

          {bidCard.photo_urls.length > 1 && (
            <>
              <div className="absolute bottom-3 left-1/2 transform -translate-x-1/2 flex gap-1">
                {bidCard.photo_urls.map((_, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => setCurrentPhotoIndex(index)}
                    className={`w-2 h-2 rounded-full transition-all ${
                      index === currentPhotoIndex ? "bg-white" : "bg-white/50"
                    }`}
                  />
                ))}
              </div>

              <div className="absolute top-3 right-3 bg-black/50 backdrop-blur-sm rounded-full px-2 py-1 flex items-center gap-1">
                <Camera className="w-3 h-3 text-white" />
                <span className="text-white text-xs">{bidCard.photo_urls.length}</span>
              </div>
            </>
          )}
        </div>
      )}

      {/* Content */}
      <div className="p-6">
        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">Budget</div>
            <div className="text-sm font-semibold text-gray-900">{bidCard.budget_display}</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">Timeline</div>
            <div
              className={`text-xs font-semibold px-2 py-1 rounded-full ${getUrgencyColor(bidCard.urgency)}`}
            >
              {getUrgencyText(bidCard.urgency)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-500 mb-1">Needed</div>
            <div className="text-sm font-semibold text-gray-900 flex items-center justify-center gap-1">
              <Users className="w-3 h-3" />
              {bidCard.contractor_count}
            </div>
          </div>
        </div>

        {/* Project Scope Preview */}
        {bidCard.project_details?.scope_of_work && (
          <div className="mb-6">
            <div className="text-sm font-medium text-gray-900 mb-2">Project includes:</div>
            <ul className="text-xs text-gray-600 space-y-1">
              {bidCard.project_details.scope_of_work.slice(0, 2).map((item, index) => (
                <li key={index} className="flex items-start gap-2">
                  <div className="w-1 h-1 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                  <span>{item}</span>
                </li>
              ))}
              {bidCard.project_details.scope_of_work.length > 2 && (
                <li className="text-blue-600 font-medium">+ more details</li>
              )}
            </ul>
          </div>
        )}

        {/* Value Props */}
        <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4 mb-6">
          <div className="text-sm font-semibold text-gray-900 mb-2">🎯 Why InstaBids?</div>
          <div className="text-xs text-gray-700 space-y-1">
            <div>✅ No lead fees - pay only when you win</div>
            <div>✅ Pre-qualified homeowner ready to hire</div>
            <div>✅ Higher win rates than competitors</div>
          </div>
        </div>

        {/* CTA */}
        <a
          href={getLandingUrl()}
          className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-4 rounded-xl font-semibold text-center block hover:from-blue-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl"
        >
          <div className="flex items-center justify-center gap-2">
            Join InstaBids - Quote FREE
            <ArrowRight className="w-4 h-4" />
          </div>
        </a>

        <div className="text-center mt-3">
          <div className="text-xs text-gray-500">No longer pay for leads, only jobs</div>
        </div>
      </div>
    </div>
  );
};

export default ExternalBidCard;
