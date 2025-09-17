import { AlertCircle, ChevronDown, ChevronUp, Clock, Eye, Mail, Target, Users } from "lucide-react";
import type React from "react";
import { useState } from "react";

interface BidCardData {
  id: string;
  bid_card_number: string;
  project_type: string;
  status: string;

  // Homeowner info
  homeowner_name?: string;
  homeowner_email?: string;
  homeowner_phone?: string;

  // Project details
  urgency_level?: string;
  complexity_score?: number;
  budget_min?: number;
  budget_max?: number;
  timeline_weeks?: number;
  location_city?: string;
  location_state?: string;
  location_zip?: string;
  
  // Service complexity classification
  service_complexity?: "single-trade" | "multi-trade" | "complex-coordination";
  trade_count?: number;
  primary_trade?: string;
  secondary_trades?: string[];

  // Contractor targets
  contractor_count_needed?: number;
  bid_count?: number;
  interested_contractors?: number;
  bids_target_met?: boolean;

  // Campaign data
  campaign?: {
    max_contractors?: number;
    contractors_targeted?: number;
    contractors_responded?: number;
    status?: string;
  };

  // Outreach metrics
  outreach?: {
    email_sent?: number;
    forms_sent?: number;
    sms_sent?: number;
    total_attempts?: number;
    successful_deliveries?: number;
  };

  // Engagement
  views_count?: number;
  last_viewed?: string;

  // Timestamps
  created_at?: string;
  updated_at?: string;
  next_checkin?: string;
}

interface Props {
  bidCard: BidCardData;
  onStatusChange?: (bidCardId: string, newStatus: string) => void;
}

export function AdminBidCardEnhanced({ bidCard, onStatusChange }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Calculate progress percentage
  const progressPercentage = bidCard.contractor_count_needed
    ? ((bidCard.bid_count || 0) / bidCard.contractor_count_needed) * 100
    : 0;

  // Calculate time since creation
  const timeAgo = bidCard.created_at ? formatTimeAgo(new Date(bidCard.created_at)) : "Unknown";

  // Determine status color
  const statusColor = getStatusColor(bidCard.status);

  // Calculate deadline
  const deadline =
    bidCard.created_at && bidCard.timeline_weeks
      ? new Date(
          new Date(bidCard.created_at).getTime() + bidCard.timeline_weeks * 7 * 24 * 60 * 60 * 1000
        )
      : null;
  const daysUntilDeadline = deadline
    ? Math.ceil((deadline.getTime() - Date.now()) / (24 * 60 * 60 * 1000))
    : null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      {/* Header - Always Visible */}
      <div className="p-4 cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h4 className="font-semibold text-lg">
                {bidCard.project_type} ({bidCard.bid_card_number})
              </h4>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColor}`}>
                {bidCard.status}
              </span>
              {bidCard.urgency_level && (
                <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded-full text-xs">
                  {bidCard.urgency_level} urgency
                </span>
              )}
              {bidCard.service_complexity && (
                <span className={`px-2 py-1 rounded-full text-xs ${
                  bidCard.service_complexity === "single-trade" ? "bg-blue-100 text-blue-800" :
                  bidCard.service_complexity === "multi-trade" ? "bg-orange-100 text-orange-800" :
                  "bg-red-100 text-red-800"
                }`}>
                  {bidCard.service_complexity === "single-trade" && "Single Trade"}
                  {bidCard.service_complexity === "multi-trade" && "Multi Trade"} 
                  {bidCard.service_complexity === "complex-coordination" && "Complex"}
                </span>
              )}
              {bidCard.primary_trade && (
                <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs">
                  {bidCard.primary_trade}
                </span>
              )}
            </div>

            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {timeAgo}
              </span>
              {bidCard.location_city && (
                <span>
                  📍 {bidCard.location_city}, {bidCard.location_state}
                </span>
              )}
              {bidCard.homeowner_name && <span>🏠 {bidCard.homeowner_name}</span>}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {daysUntilDeadline !== null && daysUntilDeadline < 3 && (
              <AlertCircle
                className="w-5 h-5 text-red-500"
                title={`${daysUntilDeadline} days until deadline`}
              />
            )}{" "}
            {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-3">
          <div className="flex justify-between text-sm mb-1">
            <span>Bid Progress</span>
            <span className="font-medium">
              {bidCard.bid_count || 0} / {bidCard.contractor_count_needed || 0} bids
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${Math.min(progressPercentage, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-gray-200 p-4 space-y-4">
          {/* Key Metrics Row */}
          <div className="grid grid-cols-4 gap-4">
            <MetricCard
              icon={<Target className="w-5 h-5 text-blue-500" />}
              label="Target Contractors"
              value={bidCard.contractor_count_needed || 0}
              subtext={`${bidCard.interested_contractors || 0} interested`}
            />
            <MetricCard
              icon={<Users className="w-5 h-5 text-green-500" />}
              label="Outreach"
              value={bidCard.campaign?.contractors_targeted || 0}
              subtext={`${bidCard.campaign?.contractors_responded || 0} responded`}
            />
            <MetricCard
              icon={<Mail className="w-5 h-5 text-purple-500" />}
              label="Messages Sent"
              value={bidCard.outreach?.total_attempts || 0}
              subtext={`${bidCard.outreach?.successful_deliveries || 0} delivered`}
            />
            <MetricCard
              icon={<Eye className="w-5 h-5 text-orange-500" />}
              label="Views"
              value={bidCard.views_count || 0}
              subtext={
                bidCard.last_viewed
                  ? `Last: ${formatTimeAgo(new Date(bidCard.last_viewed))}`
                  : "No views yet"
              }
            />
          </div>

          {/* Project Details */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <h5 className="font-medium text-gray-700">Project Details</h5>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Budget Range:</span>
                  <span className="font-medium">
                    ${(bidCard.budget_min || 0).toLocaleString()} - $
                    {(bidCard.budget_max || 0).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Timeline:</span>
                  <span className="font-medium">{bidCard.timeline_weeks || 0} weeks</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Complexity:</span>
                  <span className="font-medium">{bidCard.complexity_score || 0}/10</span>
                </div>
                {bidCard.service_complexity && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Service Type:</span>
                    <span className="font-medium">
                      {bidCard.service_complexity === "single-trade" && "Single Trade"}
                      {bidCard.service_complexity === "multi-trade" && "Multi Trade"}
                      {bidCard.service_complexity === "complex-coordination" && "Complex"}
                      {bidCard.trade_count && ` (${bidCard.trade_count} trades)`}
                    </span>
                  </div>
                )}
                {bidCard.secondary_trades && bidCard.secondary_trades.length > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Secondary Trades:</span>
                    <span className="font-medium">+{bidCard.secondary_trades.length} more</span>
                  </div>
                )}
                {deadline && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Deadline:</span>
                    <span className={`font-medium ${daysUntilDeadline! < 3 ? "text-red-600" : ""}`}>
                      {daysUntilDeadline} days left
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-2">
              <h5 className="font-medium text-gray-700">Outreach Breakdown</h5>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Email:</span>
                  <span className="font-medium">{bidCard.outreach?.email_sent || 0} sent</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Forms:</span>
                  <span className="font-medium">{bidCard.outreach?.forms_sent || 0} submitted</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">SMS:</span>
                  <span className="font-medium">{bidCard.outreach?.sms_sent || 0} sent</span>
                </div>
                {bidCard.next_checkin && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Next Check-in:</span>
                    <span className="font-medium">
                      {formatTimeUntil(new Date(bidCard.next_checkin))}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              className="px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
            >
              View Details
            </button>
            <button
              type="button"
              className="px-3 py-1 text-sm bg-gray-50 text-gray-600 rounded hover:bg-gray-100"
            >
              View Timeline
            </button>
            {bidCard.status === "active" && (
              <button
                type="button"
                className="px-3 py-1 text-sm bg-green-50 text-green-600 rounded hover:bg-green-100"
              >
                Send Follow-up
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Helper Components
function MetricCard({
  icon,
  label,
  value,
  subtext,
}: {
  icon: React.ReactNode;
  label: string;
  value: number | string;
  subtext?: string;
}) {
  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        {icon}
        <span className="text-xs text-gray-600">{label}</span>
      </div>
      <div className="text-xl font-semibold">{value}</div>
      {subtext && <div className="text-xs text-gray-500">{subtext}</div>}
    </div>
  );
}

// Helper Functions
function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    generated: "bg-gray-100 text-gray-800",
    discovery: "bg-blue-100 text-blue-800",
    active: "bg-green-100 text-green-800",
    collecting_bids: "bg-purple-100 text-purple-800",
    bids_complete: "bg-indigo-100 text-indigo-800",
    pending_award: "bg-yellow-100 text-yellow-800",
    awarded: "bg-emerald-100 text-emerald-800",
    in_progress: "bg-orange-100 text-orange-800",
    completed: "bg-gray-100 text-gray-800",
    cancelled: "bg-red-100 text-red-800",
  };
  return colors[status] || "bg-gray-100 text-gray-800";
}
function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);

  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}

function formatTimeUntil(date: Date): string {
  const seconds = Math.floor((date.getTime() - Date.now()) / 1000);

  if (seconds < 0) return "Overdue";
  if (seconds < 60) return `in ${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `in ${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `in ${hours}h`;
  const days = Math.floor(hours / 24);
  return `in ${days}d`;
}
