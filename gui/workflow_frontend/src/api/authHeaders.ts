import { authService } from "../auth/authService";
import { getApiConfig, isDebugMode } from "./config";

export const createAuthHeaders = async (): Promise<Record<string, string>> => {
  const config = getApiConfig();
  const baseHeaders: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Internal-Secret": config.internalSecret,
  };

  try {
    const token = await authService.getAccessToken();
    if (token) {
      baseHeaders["Authorization"] = `Bearer ${token}`;
      if (isDebugMode()) {
        console.log("Auth token added to headers");
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

export const decodeJWT = (token: string) => {
  try {
    return JSON.parse(atob(token.split(".")[1]));
  } catch (error) {
    console.error("Invalid JWT token:", error);
    return null;
  }
};

export const isTokenExpired = (token: string): boolean => {
  const payload = decodeJWT(token);
  if (!payload || !payload.exp) return true;
  return payload.exp < Math.floor(Date.now() / 1000);
};

export const validateCurrentToken = async (): Promise<boolean> => {
  try {
    const token = await authService.getAccessToken();
    if (!token) return false;
    return !isTokenExpired(token);
  } catch {
    return false;
  }
};
