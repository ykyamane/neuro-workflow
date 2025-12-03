import { supabase } from "../auth/supabase";
import { getApiConfig, isDebugMode } from "./config";

// Authentication header generation
export const createAuthHeaders = async (): Promise<Record<string, string>> => {
  const config = getApiConfig();
  const baseHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Internal-Secret": config.internalSecret,
  };

  try {
    // Get your tokens from Supabase
    const {
      data: { session },
      error,
    } = await supabase.auth.getSession();

    if (error) {
      if (isDebugMode()) {
        console.warn("Failed to get session:", error.message);
      }
      return baseHeaders;
    }

    if (session?.access_token) {
      baseHeaders["Authorization"] = `Bearer ${session.access_token}`;

      if (isDebugMode()) {
        console.log("🔑 Auth token added to headers");
      }
    }

    return baseHeaders;
  } catch (error) {
    if (isDebugMode()) {
      console.error("Error creating auth headers:", error);
    }
    return baseHeaders;
  }
};

// Decoding a JWT Token
export const decodeJWT = (token: string) => {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload;
  } catch (error) {
    console.error("Invalid JWT token:", error);
    return null;
  }
};

// Token expiration check
export const isTokenExpired = (token: string): boolean => {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) return true;

  const currentTime = Math.floor(Date.now() / 1000);
  return payload.exp < currentTime;
};

// Token Validation
export const validateCurrentToken = async (): Promise<boolean> => {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session?.access_token) return false;

    return !isTokenExpired(session.access_token);
  } catch {
    return false;
  }
};
