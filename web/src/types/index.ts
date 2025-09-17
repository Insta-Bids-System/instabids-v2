// TypeScript Definitions for InstaBids Platform
// Agent 6 - Code Quality Improvements
// Replaces all 'any' types with proper interfaces

// ===== CORE BID CARD TYPES =====

export interface BidCard {
  id: string;
  bid_card_number: string;
  project_type: string;
  project_description: string;
  status: BidCardStatus;
  urgency_level: UrgencyLevel;
  complexity_score: number;
  contractor_count_needed: number;
  budget_min?: number;
  budget_max?: number;
  timeline_days?: number;
  created_at: string;
  updated_at: string;
  user_id: string;
  cia_thread_id?: string;
  location_city?: string;
  location_state?: string;
  project_photos?: string[];
  bid_document: BidDocument;
}

export interface BidDocument {
  submitted_bids?: SubmittedBid[];
  bids_received_count: number;
  bids_target_met: boolean;
  additional_notes?: string;
}

export interface SubmittedBid {
  id: string;
  contractor_id: string;
  contractor_name: string;
  bid_amount: number;
  timeline_estimate: string;
  proposal_details: string;
  submitted_at: string;
  submission_method: "api" | "portal" | "email";
  materials_cost?: number;
  labor_cost?: number;
  includes_permits: boolean;
  warranty_offered?: string;
  start_date_available?: string;
}

export type BidCardStatus =
  | "generated"
  | "discovery_in_progress"
  | "contractors_found"
  | "outreach_initiated"
  | "collecting_bids"
  | "bids_complete"
  | "contractor_selected"
  | "project_completed";

export type UrgencyLevel = "emergency" | "urgent" | "standard" | "group" | "flexible";

// ===== CAMPAIGN & OUTREACH TYPES =====

export interface OutreachCampaign {
  id: string;
  bid_card_id: string;
  campaign_name: string;
  max_contractors: number;
  contractors_targeted: number;
  responses_received: number;
  created_at: string;
  updated_at: string;
  status: CampaignStatus;
}

export type CampaignStatus = "planning" | "active" | "paused" | "completed" | "cancelled";

export interface CampaignCheckIn {
  id: string;
  campaign_id: string;
  check_in_time: string;
  target_percentage: number;
  actual_responses: number;
  expected_responses: number;
  action_taken?: string;
}

export interface ContractorOutreachAttempt {
  id: string;
  bid_card_id: string;
  campaign_id: string;
  contractor_lead_id: string;
  channel: OutreachChannel;
  status: OutreachStatus;
  sent_at: string;
  message_template_id?: string;
  response_received_at?: string;
}

export type OutreachChannel = "email" | "form" | "sms" | "phone";
export type OutreachStatus =
  | "pending"
  | "sent"
  | "delivered"
  | "opened"
  | "clicked"
  | "responded"
  | "failed";

// ===== CONTRACTOR TYPES =====

export interface Contractor {
  id: string;
  business_name: string;
  contact_name: string;
  email: string;
  phone: string;
  website?: string;
  specialties: string[];
  tier: ContractorTier;
  response_rate: number;
  rating: number;
  location_city: string;
  location_state: string;
  license_number?: string;
  insurance_verified: boolean;
  years_in_business?: number;
}

export type ContractorTier = "tier1" | "tier2" | "tier3";

export interface ContractorLead {
  id: string;
  business_name: string;
  contact_email: string;
  phone?: string;
  website?: string;
  discovery_run_id: string;
  lead_score: number;
  tier: ContractorTier;
  specialties: string[];
  location: string;
  status: LeadStatus;
}

export type LeadStatus =
  | "discovered"
  | "validated"
  | "contacted"
  | "responded"
  | "converted"
  | "rejected";

export interface DiscoveryRun {
  id: string;
  bid_card_id: string;
  search_criteria: DiscoverySearchCriteria;
  contractors_found: number;
  execution_time_ms: number;
  started_at: string;
  completed_at: string;
  status: DiscoveryStatus;
}

export interface DiscoverySearchCriteria {
  project_type: string;
  location: string;
  budget_range?: [number, number];
  urgency_level: UrgencyLevel;
  required_specialties: string[];
}

export type DiscoveryStatus = "pending" | "running" | "completed" | "failed";

// ===== HOMEOWNER & PROJECT TYPES =====

export interface Homeowner {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  address?: Address;
  preferred_contact_method: ContactMethod;
  total_projects: number;
  created_at: string;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
}

export type ContactMethod = "email" | "phone" | "text" | "app";

export interface Project {
  id: string;
  user_id: string;
  title: string;
  description: string;
  project_type: string;
  status: ProjectStatus;
  budget_range?: [number, number];
  desired_start_date?: string;
  estimated_duration?: string;
  created_at: string;
  updated_at: string;
  cia_conversation_id?: string;
}

export type ProjectStatus =
  | "planning"
  | "quotes_requested"
  | "comparing_bids"
  | "contractor_selected"
  | "in_progress"
  | "completed"
  | "cancelled";

// ===== MESSAGING TYPES =====

export interface Message {
  id: string;
  thread_id: string;
  sender_id: string;
  sender_type: SenderType;
  recipient_id: string;
  recipient_type: RecipientType;
  content: string;
  message_type: MessageType;
  sent_at: string;
  read_at?: string;
  bid_card_id?: string;
  project_id?: string;
}

export type SenderType = "homeowner" | "contractor" | "system" | "agent";
export type RecipientType = "homeowner" | "contractor" | "system";
export type MessageType = "text" | "bid_submission" | "project_update" | "system_notification";

export interface MessageThread {
  id: string;
  bid_card_id?: string;
  project_id?: string;
  participants: ThreadParticipant[];
  last_message_at: string;
  created_at: string;
  status: ThreadStatus;
}

export interface ThreadParticipant {
  user_id: string;
  user_type: SenderType;
  joined_at: string;
  last_read_at?: string;
}

export type ThreadStatus = "active" | "archived" | "closed";

// ===== ADMIN DASHBOARD TYPES =====

export interface AdminDashboardData {
  system_metrics: SystemMetrics;
  recent_bid_cards: BidCard[];
  active_campaigns: OutreachCampaign[];
  contractor_stats: ContractorStats;
  agent_health: AgentHealthStatus[];
}

export interface SystemMetrics {
  total_bid_cards: number;
  active_campaigns: number;
  total_contractors: number;
  response_rate_avg: number;
  bids_completed_today: number;
  revenue_this_month: number;
}

export interface ContractorStats {
  total_registered: number;
  active_this_week: number;
  tier1_count: number;
  tier2_count: number;
  tier3_count: number;
  avg_response_time: string;
}

export interface AgentHealthStatus {
  agent_name: string;
  status: AgentStatus;
  last_activity: string;
  success_rate: number;
  error_count: number;
  performance_score: number;
}

export type AgentStatus = "healthy" | "warning" | "error" | "offline";

// ===== ENGAGEMENT & ANALYTICS TYPES =====

export interface BidCardView {
  id: string;
  bid_card_id: string;
  contractor_id?: string;
  viewer_type: ViewerType;
  view_duration?: number;
  viewed_at: string;
  ip_address?: string;
  user_agent?: string;
}

export type ViewerType = "contractor" | "homeowner" | "admin" | "anonymous";

export interface EngagementEvent {
  id: string;
  bid_card_id: string;
  contractor_id?: string;
  event_type: EngagementEventType;
  event_data?: Record<string, unknown>;
  occurred_at: string;
}

export type EngagementEventType =
  | "view"
  | "download"
  | "email_open"
  | "email_click"
  | "form_submit"
  | "bid_submit"
  | "message_send";

// ===== FORM & UI TYPES =====

export interface FormValidationError {
  field: string;
  message: string;
  code?: string;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  code?: string;
}

export interface PaginationParams {
  page: number;
  limit: number;
  sort_by?: string;
  sort_order?: SortOrder;
}

export type SortOrder = "asc" | "desc";

export interface FilterOptions {
  status?: BidCardStatus[];
  project_type?: string[];
  urgency_level?: UrgencyLevel[];
  date_range?: DateRange;
  location?: string;
  budget_range?: [number, number];
}

export interface DateRange {
  start_date: string;
  end_date: string;
}

// ===== NOTIFICATION TYPES =====

export interface Notification {
  id: string;
  user_id: string;
  type: NotificationType;
  title: string;
  message: string;
  data?: Record<string, unknown>;
  read: boolean;
  created_at: string;
  expires_at?: string;
}

export type NotificationType =
  | "bid_received"
  | "campaign_complete"
  | "contractor_response"
  | "system_alert"
  | "payment_reminder";

// ===== INSPIRATION & IRIS TYPES =====

export interface InspirationBoard {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  project_type: string;
  images: InspirationImage[];
  created_at: string;
  updated_at: string;
}

export interface InspirationImage {
  id: string;
  url: string;
  title?: string;
  description?: string;
  source?: string;
  tags: string[];
  uploaded_at: string;
}

export interface GeneratedDreamSpace {
  id: string;
  user_id: string;
  project_type: string;
  style_preferences: string[];
  generated_image_url: string;
  prompt_used: string;
  created_at: string;
}

// ===== AUTHENTICATION TYPES =====

export interface User {
  id: string;
  email: string;
  role: UserRole;
  profile: UserProfile;
  created_at: string;
  last_login_at?: string;
}

export type UserRole = "homeowner" | "contractor" | "admin" | "agent";

export interface UserProfile {
  first_name: string;
  last_name: string;
  phone?: string;
  avatar_url?: string;
  preferences: UserPreferences;
}

export interface UserPreferences {
  notifications_enabled: boolean;
  email_frequency: EmailFrequency;
  communication_style: CommunicationStyle;
  timezone: string;
}

export type EmailFrequency = "immediate" | "daily" | "weekly" | "never";
export type CommunicationStyle = "professional" | "casual" | "detailed" | "concise";

// ===== AGENT CONVERSATION TYPES =====

export interface AgentConversation {
  id: string;
  thread_id: string;
  agent_type: AgentType;
  user_id: string;
  project_id?: string;
  conversation_state: ConversationState;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, unknown>;
}

export type AgentType = "CIA" | "JAA" | "CDA" | "EAA" | "WFA" | "HMA" | "CMA" | "COIA";

export interface ConversationState {
  current_step: string;
  collected_data: Record<string, unknown>;
  next_actions: string[];
  confidence_score: number;
}

// Types are already exported above as interfaces - no need for duplicate export
