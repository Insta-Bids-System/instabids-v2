/**
 * Centralized API configuration
 * All API calls should use these constants instead of hardcoded URLs
 */

// Determine API URL based on environment
// In production, this should be set via environment variable
const getApiBaseUrl = () => {
  // If explicitly set, use that
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // In dev mode, use proxy (empty string means current origin)
  if (import.meta.env.DEV) {
    return '';
  }
  // In production, default to same origin
  return '';
};

// Use relative URLs with Vite proxy for development, absolute for production
export const API_BASE_URL = getApiBaseUrl();
export const WS_BASE_URL = '';

// API endpoints
export const API_ENDPOINTS = {
  // Admin endpoints
  ADMIN_BID_CARDS: '/api/admin/bid-cards-enhanced',
  ADMIN_RESTART_AGENT: '/api/admin/restart-agent',
  ADMIN_CAMPAIGNS: '/api/admin/campaigns',
  ADMIN_DASHBOARD_STATS: '/api/admin/dashboard-stats',
  
  // Bid card endpoints
  BID_CARDS: '/api/bid-cards',
  BID_CARD_SEARCH: '/api/bid-cards/search',
  BID_CARD_LIFECYCLE: (id: string) => `/api/bid-cards/${id}/lifecycle`,
  BID_CARD_IMAGES: (id: string) => `/api/bid-cards/${id}/images`,
  BID_CARD_CHANGE_HISTORY: (id: string) => `/api/bid-cards/${id}/change-history`,
  BID_CARD_APPROVE_CHANGE: (id: string, changeId: string) => `/api/bid-cards/${id}/approve-change/${changeId}`,
  
  // Contractor endpoints
  CONTRACTOR_MANAGEMENT: '/api/contractor-management/contractors',
  CONTRACTOR_PROPOSALS: '/api/contractor-proposals',
  CONTRACTOR_PROPOSAL_BY_BID: (bidId: string) => `/api/contractor-proposals/bid-card/${bidId}`,
  CONTRACTOR_PROPOSAL_STATUS: (id: string) => `/api/contractor-proposals/${id}/status`,
  
  // Campaign endpoints
  CAMPAIGN_MANAGEMENT: '/api/campaign-management/campaigns',
  CAMPAIGN_STATS: '/api/campaign-management/dashboard-stats',
  CAMPAIGN_DETAIL: (id: string) => `/api/campaign-management/campaigns/${id}`,
  CAMPAIGN_ASSIGN: (id: string) => `/api/campaign-management/campaigns/${id}/assign-contractors`,
  CAMPAIGN_STATUS: (id: string) => `/api/campaign-management/campaigns/${id}/status`,
  
  // IRIS endpoints
  IRIS_CHAT: '/api/iris/chat',
  IRIS_ACTIONS: {
    UPDATE_POTENTIAL_BID_CARD: '/api/iris/actions/update-potential-bid-card',
    UPDATE_BID_CARD: '/api/iris/actions/update-bid-card',
    ADD_REPAIR_ITEM: '/api/iris/actions/add-repair-item',
  },
  
  // Unified conversation
  UNIFIED_CONVERSATION: '/api/unified/conversation',
  
  // Property endpoints
  PROPERTY_PROJECTS: '/api/property-projects',
  PROPERTY_TRADES: '/api/property-projects/trades',
  PROPERTY_TRADE_GROUPS: (id: string) => `/api/property-projects/${id}/trade-groups`,
};

// WebSocket endpoints
export const WS_ENDPOINTS = {
  AGENT_ACTIVITY: '/ws/agent-activity',
  REALTIME: '/ws/realtime',
  CONTRACTOR: '/ws/contractor',
};

// Helper function to build full URL if needed
export function buildApiUrl(endpoint: string): string {
  return `${API_BASE_URL}${endpoint}`;
}

// Helper function to build WebSocket URL
export function buildWsUrl(endpoint: string, params?: Record<string, string>): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  
  // Determine WebSocket host
  let host: string;
  if (import.meta.env.VITE_WS_URL) {
    // If explicitly set, use that (remove protocol)
    // In production: VITE_WS_URL=wss://api.instabids.com
    host = import.meta.env.VITE_WS_URL.replace(/^wss?:\/\//, '');
  } else if (import.meta.env.DEV) {
    // Development: Use Vite dev server which proxies to backend
    // This works with Docker networking since Vite can resolve container names
    host = window.location.host; // Use Vite proxy (localhost:5173)
  } else {
    // Production: Use same host as the page (or could be api subdomain)
    // Assumes WebSocket endpoint is on same domain/subdomain
    host = window.location.host;
  }
  
  const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
  return `${protocol}//${host}${WS_BASE_URL}${endpoint}${queryString}`;
}

// Fetch with default options
export async function apiFetch(endpoint: string, options?: RequestInit): Promise<Response> {
  const url = buildApiUrl(endpoint);
  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
}