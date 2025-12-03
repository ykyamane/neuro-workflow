import { supabase } from "../auth/supabase";
import { createAuthHeaders } from "./authHeaders";
import { isDebugMode } from "./config";

// Request Interceptors
export const onRequest = async (
  url: string,
  requestConfig: RequestInit
): Promise<RequestInit> => {
  // Get the latest token every time
  const freshHeaders = await createAuthHeaders();
  requestConfig.headers = {
    ...requestConfig.headers,
    ...freshHeaders,
  };

  // request log
  if (isDebugMode()) {
    console.log(`🚀 API Request: ${requestConfig.method || "GET"} ${url}`);
    console.log("Headers:", requestConfig.headers);
  }

  return requestConfig;
};

// Response Interceptors
export const onResponse = async (response: Response): Promise<Response> => {
  if (isDebugMode()) {
    console.log(`✅ API Response: ${response.status} ${response.url}`);
  }

  // 401 Error Handling (Authentication Failed)
  if (response.status === 401) {
    console.warn("🔒 Unauthorized - token may be expired");

    // automatic logout
    try {
      await supabase.auth.signOut();

      // Redirect to login page
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    } catch (error) {
      console.error("Error during automatic logout:", error);
    }
  }

  // 403 Error Handling (Insufficient Permissions)
  if (response.status === 403) {
    console.warn("🚫 Forbidden - insufficient permissions");

    // Notify users if necessary
    if (typeof window !== "undefined") {
      // Notify the user with a toast notification
      console.warn(
        "Access denied: You do not have permission to perform this action"
      );
    }
  }

  // 500 Error Handling (Server Error)
  if (response.status >= 500) {
    console.error("🔥 Server Error:", response.status);

    // Detailed logging for server errors
    if (isDebugMode()) {
      console.error("Response details:", {
        status: response.status,
        statusText: response.statusText,
        url: response.url,
      });
    }
  }

  return response;
};

// error handling
export const onError = (error: Error): never => {
  if (isDebugMode()) {
    console.error("❌ API Error:", error);
  }

  // network error
  if (error.name === "TypeError" && error.message.includes("fetch")) {
    console.error("🌐 Network error - server may be down");

    // Provides more detailed information in case of network errors
    const networkError = new Error(
      "Network connection failed. Please check your internet connection and try again."
    );
    networkError.name = "NetworkError";
    throw networkError;
  }

  // timeout error
  if (error.message.includes("timeout")) {
    const timeoutError = new Error("Request timed out. Please try again.");
    timeoutError.name = "TimeoutError";
    throw timeoutError;
  }

  throw error;
};

// Analysis of response data
export const parseResponse = async (response: Response): Promise<any> => {
  const contentType = response.headers.get("content-type");

  try {
    if (contentType?.includes("application/json")) {
      return await response.json();
    } else if (contentType?.includes("text/")) {
      return await response.text();
    } else {
      return await response.blob();
    }
  } catch (error) {
    console.error("Error parsing response:", error);
    throw new Error("Failed to parse response data");
  }
};
