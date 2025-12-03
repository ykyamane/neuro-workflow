import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

// Only create client if we have valid credentials (not placeholders)
const isValidUrl = (url: string): boolean => {
  if (!url || url.includes('<your') || url.includes('your_')) {
    return false;
  }
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

const isValidKey = (key: string): boolean => {
  if (!key || key.includes('<your') || key.includes('your_')) {
    return false;
  }
  return true;
};

// Create a mock client if Supabase isn't configured
const createMockClient = () => {
  return {
    auth: {
      getSession: async () => ({ data: { session: null }, error: null }),
      onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
      signInWithPassword: async () => ({ data: null, error: { message: 'Supabase not configured' } }),
      signUp: async () => ({ data: null, error: { message: 'Supabase not configured' } }),
      signOut: async () => ({ error: null }),
      resetPasswordForEmail: async () => ({ error: null }),
    },
  } as any;
};

export const supabase = (isValidUrl(supabaseUrl) && isValidKey(supabaseAnonKey))
  ? createClient(supabaseUrl, supabaseAnonKey)
  : createMockClient();

// 型定義
export interface User {
  id: string;
  email: string;
  email_confirmed_at?: string;
  user_metadata?: {
    name?: string;
    full_name?: string;
  };
}

export interface AuthError {
  message: string;
  status?: number;
}
