import React, { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

type SUser = {
  id: string;
  email?: string;
  name?: string;
  avatar_url?: string;
};

function extract(u: any): SUser {
  const m = u?.user_metadata ?? {};
  return {
    id: u?.id,
    email: u?.email ?? m.email,
    name: m.full_name ?? m.name,
    avatar_url: m.avatar_url ?? m.picture,
  };
}

const GoogleIcon = () => (
  <img
    src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
    width={18}
    height={18}
    alt=""
  />
);

export default function AuthStatus() {
  const [user, setUser] = useState<SUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      const u = data.session?.user;
      setUser(u ? extract(u) : null);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ? extract(session.user) : null);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (loading) return null;

  if (!user) {
    const signIn = async () => {
      const { error } = await supabase.auth.signInWithOAuth({ provider: "google" });
      if (error) console.error("Google sign-in error:", error);
    };
    return (
      <button
        onClick={signIn}
        className="inline-flex items-center gap-2 rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        aria-label="Continue with Google"
      >
        <GoogleIcon />
        Continue with Google
      </button>
    );
  }

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  return (
    <div className="flex items-center gap-3">
      {user.avatar_url && (
        <img
          src={user.avatar_url}
          alt="avatar"
          width={28}
          height={28}
          className="rounded-full"
        />
      )}
      <div className="leading-tight">
        <div className="text-sm font-medium text-gray-900">{user.name ?? "Signed in"}</div>
        <div className="text-xs text-gray-600">{user.email}</div>
      </div>
      <button
        onClick={signOut}
        className="ml-1 inline-flex items-center rounded-md border border-gray-300 px-2.5 py-1.5 text-xs text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
      >
        Sign out
      </button>
    </div>
  );
}
