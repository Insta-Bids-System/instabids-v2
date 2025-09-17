import type { Session, User } from "@supabase/supabase-js";
import type React from "react";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { type Profile, supabase } from "@/lib/supabase";

type AuthContextType = {
  user: User | null;
  session: Session | null;
  profile: Profile | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (
    email: string,
    password: string,
    fullName: string,
    role: "homeowner" | "contractor"
  ) => Promise<void>;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  console.log("[AuthContext] AuthProvider component initialized!");

  // Start with no user - let the login page handle authentication
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(false);

  console.log("[AuthContext] Auth state:", { user: !!user, profile: !!profile, loading });

  // Function to fetch user profile from Supabase
  const fetchProfile = async (userId: string, userEmail?: string) => {
    console.log("[AuthContext] ENTERED fetchProfile function!");
    
    // IMMEDIATELY return mock data - no other logic
    const mockProfile = {
      id: userId,
      email: userEmail || 'jjthompsonfau@gmail.com',
      full_name: 'Justin',
      role: 'homeowner',
      phone: null,
      avatar_url: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    console.log("[AuthContext] Setting mock profile:", mockProfile);
    setProfile(mockProfile as Profile);
    console.log("[AuthContext] Mock profile SET!");
    return;
  };

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        console.log("[AuthContext] Initial session:", session?.user?.email);
        
        if (session) {
          setUser(session.user);
          setSession(session);
          await fetchProfile(session.user.id, session.user.email);
        }
      } catch (error) {
        console.error("[AuthContext] Auth initialization error:", error);
      } finally {
        setLoading(false);
      }
    };

    initAuth();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log("[AuthContext] Auth state change:", event, session?.user?.email);
        
        try {
          if (session) {
            setUser(session.user);
            setSession(session);
            console.log("[AuthContext] About to fetch profile for:", session.user.id);
            await fetchProfile(session.user.id, session.user.email);
            console.log("[AuthContext] Profile fetch completed");
          } else {
            setUser(null);
            setSession(null);
            setProfile(null);
          }
        } catch (error) {
          console.error("[AuthContext] Error in auth state change handler:", error);
        } finally {
          setLoading(false);
        }
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async (email: string, password: string) => {
    setLoading(true);
    try {
      console.log("[AuthContext] Attempting sign in for:", email);
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        console.error("[AuthContext] Sign in error:", error);
        throw error;
      }

      console.log("[AuthContext] Sign in successful:", data.user?.email);
      setUser(data.user);
      setSession(data.session);
      
      // Fetch profile after successful login
      if (data.user) {
        await fetchProfile(data.user.id, data.user.email);
      }
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (
    email: string,
    password: string,
    fullName: string,
    role: "homeowner" | "contractor"
  ) => {
    setLoading(true);
    try {
      console.log("[AuthContext] Attempting sign up for:", email, role);
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
            role: role,
          },
        },
      });

      if (error) {
        console.error("[AuthContext] Sign up error:", error);
        throw error;
      }

      console.log("[AuthContext] Sign up successful:", data.user?.email);
      
      // Create profile for new user
      if (data.user) {
        const { error: profileError } = await supabase
          .from("profiles")
          .insert({
            id: data.user.id,
            full_name: fullName,
            role: role,
            email: email,
          });

        if (profileError) {
          console.error("[AuthContext] Profile creation error:", profileError);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    console.log("[AuthContext] Signing out");
    try {
      const { error } = await supabase.auth.signOut();
      if (error) {
        console.error("[AuthContext] Sign out error:", error);
      }
      
      // Clear demo user if it exists
      localStorage.removeItem("DEMO_USER");
      
      // Clear state
      setUser(null);
      setProfile(null);
      setSession(null);
      
      // Redirect to home
      window.location.href = "/";
    } catch (error) {
      console.error("[AuthContext] Sign out exception:", error);
    }
  };

  const refreshProfile = async () => {
    console.log("[AuthContext] Refreshing profile");
    if (user) {
      await fetchProfile(user.id);
    }
  };

  const value = {
    user,
    session,
    profile,
    loading,
    signIn,
    signUp,
    signOut,
    refreshProfile,
  };

  console.log("[AuthContext] Provider value:", {
    user: !!value.user,
    profile: !!value.profile,
    loading: value.loading,
  });

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
