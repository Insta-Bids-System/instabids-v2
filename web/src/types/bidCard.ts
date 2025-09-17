// Enhanced Bid Card Types for InstaBids
// Supports multiple UI variants: homeowner editing, contractor bidding, public marketplace, group bidding

export interface BidCard {
  id: string;
  project_id: string;
  user_id: string;

  // Core bid card data
  title: string;
  description: string;
  budget_range: {
    min: number;
    max: number;
  };
  timeline: {
    start_date: string;
    end_date: string;
    flexibility: "flexible" | "strict" | "asap";
  };

  // Location data for matching
  location: {
    address?: string;
    city: string;
    state: string;
    zip_code: string;
    coordinates?: {
      lat: number;
      lng: number;
    };
  };

  // Categories and requirements
  project_type: string;
  categories: string[];
  requirements: string[];
  preferred_schedule: string[];

  // Service complexity classification
  service_complexity?: "single-trade" | "multi-trade" | "complex-coordination";
  trade_count?: number;
  primary_trade?: string;
  secondary_trades?: string[];

  // Media attachments
  images: BidCardImage[];
  documents: BidCardDocument[];

  // Status and visibility
  status: "draft" | "active" | "collecting_bids" | "bids_complete" | "in_progress" | "completed";
  visibility: "private" | "public" | "invited_only";

  // Group bidding
  group_bid_eligible: boolean;
  group_bid_id?: string;

  // Bid management
  bid_count: number;
  interested_contractors: number;
  bid_deadline?: string;
  auto_close_after_bids?: number;

  // Messaging flags
  allows_questions: boolean;
  requires_bid_before_message: boolean;

  // Timestamps
  created_at: string;
  updated_at: string;
  published_at?: string;

  // Additional metadata
  metadata?: Record<string, any>;
}

export interface BidCardImage {
  id: string;
  url: string;
  thumbnail_url?: string;
  caption?: string;
  is_primary: boolean;
  upload_date: string;
}

export interface BidCardDocument {
  id: string;
  name: string;
  url: string;
  type: string;
  size: number;
  upload_date: string;
}

export interface ContractorBid {
  id: string;
  bid_card_id: string;
  contractor_id: string;

  // Bid details
  amount: number;
  timeline: {
    start_date: string;
    end_date: string;
    milestones?: BidMilestone[];
  };

  // Proposal
  proposal: string;
  approach: string;
  materials_included: boolean;
  warranty_details?: string;

  // Status
  status: "draft" | "submitted" | "under_review" | "accepted" | "rejected" | "withdrawn";

  // Messaging
  allows_messages: boolean;
  last_message_at?: string;

  // Timestamps
  submitted_at?: string;
  updated_at: string;
  created_at: string;
}

export interface BidMilestone {
  id: string;
  title: string;
  description: string;
  amount: number;
  estimated_completion: string;
}

export interface BidCardMessage {
  id: string;
  bid_card_id: string;
  conversation_id?: string;

  // Participants
  sender_id: string;
  sender_type: "homeowner" | "contractor";
  recipient_id?: string;
  recipient_type?: "homeowner" | "contractor";

  // Message content
  content: string;
  original_content?: string; // Original content before filtering
  content_filtered?: boolean; // Was content filtered?
  filter_reasons?: Array<{
    pattern: string;
    category: string;
    severity: string;
    matched_text: string;
  }>;
  attachments?: MessageAttachment[];

  // Status
  is_read?: boolean;
  read_at?: string | null;

  // Threading
  thread_id?: string;
  reply_to_id?: string;

  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface MessageAttachment {
  id: string;
  type: "image" | "document" | "bid_update";
  url: string;
  name: string;
  size?: number;
}

export interface GroupBid {
  id: string;
  name: string;
  description: string;

  // Location for grouping
  location: {
    city: string;
    state: string;
    zip_codes: string[];
    radius_miles: number;
  };

  // Bid cards in group
  bid_card_ids: string[];
  total_budget_range: {
    min: number;
    max: number;
  };

  // Savings and incentives
  estimated_savings_percentage: number;
  bulk_discount_available: boolean;

  // Management
  coordinator_id?: string;
  status: "forming" | "active" | "closed";
  min_participants: number;
  current_participants: number;

  // Deadlines
  join_deadline: string;
  bid_deadline: string;

  // Timestamps
  created_at: string;
  updated_at: string;
}

// View models for different UI contexts
export interface HomeownerBidCardView extends BidCard {
  can_edit: boolean;
  can_delete: boolean;
  can_publish: boolean;
  unread_messages_count: number;
  pending_questions: number;
}

export interface ContractorBidCardView extends BidCard {
  can_bid: boolean;
  has_bid: boolean;
  my_bid?: ContractorBid;
  distance_miles?: number;
  match_score?: number;
}

export interface MarketplaceBidCardView extends Omit<BidCard, "user_id"> {
  homeowner_verified: boolean;
  response_time_hours?: number;
  success_rate?: number;
  is_featured: boolean;
  is_urgent: boolean;
}

// Filter and search types
export interface BidCardFilters {
  status?: BidCard["status"][];
  project_types?: string[];
  categories?: string[];
  location?: {
    city?: string;
    state?: string;
    zip_code?: string;
    radius_miles?: number;
  };
  budget?: {
    min?: number;
    max?: number;
  };
  timeline?: {
    start_after?: string;
    start_before?: string;
  };
  group_bid_eligible?: boolean;
  sort_by?: "created_at" | "bid_deadline" | "budget" | "distance" | "bid_count";
  sort_order?: "asc" | "desc";
}

// API response types
export interface BidCardListResponse {
  bid_cards: MarketplaceBidCardView[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface BidSubmissionRequest {
  bid_card_id: string;
  amount: number;
  timeline: {
    start_date: string;
    end_date: string;
  };
  proposal: string;
  approach: string;
  materials_included: boolean;
  warranty_details?: string;
  milestones?: Omit<BidMilestone, "id">[];
  attachments?: Array<{
    name: string;
    type: string;
    size: number;
    url: string;
    file: File;
  }>;
}

export interface MessageSendRequest {
  bidCardId: string;
  conversationId?: string;
  content: string;
  attachments?: Array<{
    file: File;
    fileName: string;
    fileType: string;
    fileSize: number;
  }>;
}
