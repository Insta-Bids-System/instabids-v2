import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Debug environment variables
console.log("[Supabase Debug] URL:", supabaseUrl);
console.log("[Supabase Debug] Key:", supabaseAnonKey ? `${supabaseAnonKey.substring(0, 20)}...` : 'undefined');
console.log("[Supabase Debug] All env vars:", import.meta.env);

if (!supabaseUrl || !supabaseAnonKey) {
  console.error("[Supabase Debug] Missing environment variables!");
  console.error("[Supabase Debug] URL exists:", !!supabaseUrl);
  console.error("[Supabase Debug] Key exists:", !!supabaseAnonKey);
  throw new Error("Missing Supabase environment variables");
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
});

// Database types
export type Profile = {
  id: string;
  role: "homeowner" | "contractor" | "admin";
  full_name: string;
  phone?: string;
  created_at: string;
  updated_at: string;
};

export type Project = {
  id: string;
  user_id: string;
  title: string;
  description: string;
  category: string;
  urgency?: string;
  budget_range?: { min: number; max: number };
  location?: {
    address?: string;
    city?: string;
    state?: string;
    zip_code?: string;
  };
  status: "draft" | "posted" | "in_bidding" | "awarded" | "in_progress" | "completed" | "cancelled";
  images?: string[];
  documents?: string[];
  cia_conversation_id?: string;
  job_assessment?: any;
  created_at: string;
  updated_at: string;
  posted_at?: string;
  completed_at?: string;
};

export type Bid = {
  id: string;
  project_id: string;
  contractor_id: string;
  amount: number;
  timeline_days: number;
  proposal: string;
  status: "pending" | "accepted" | "rejected" | "withdrawn";
  created_at: string;
  updated_at: string;
};

export type Message = {
  id: string;
  project_id: string;
  sender_id: string;
  recipient_id: string;
  message_type: "text" | "image" | "document" | "system";
  content: string;
  metadata?: any;
  read_at?: string;
  created_at: string;
};
