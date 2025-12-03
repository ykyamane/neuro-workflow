// lib/simpleApiClient.ts
import { ApiClientManager, withErrorHandling } from "./apiManager";
import { useState } from "react";

// HTTP Method type definition
export type HttpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";

// API call options
export interface ApiOptions {
  headers?: Record<string, string>;
  timeout?: number;
  params?: Record<string, any>; // query parameters
}

// API response type
export interface ApiResponse<T = any> {
  data: T | null;
  error: {
    status: number;
    message: string;
    details?: any;
  } | null;
  success: boolean;
}

// Mapping HTTP methods to Aspida method names
const HTTP_METHOD_MAP = {
  GET: "$get",
  POST: "$post",
  PUT: "$put",
  DELETE: "$delete",
  PATCH: "$patch",
} as const;

// Main API calling function
export const apiCall = async <T = any>(
  method: HttpMethod,
  path: string,
  data?: any,
  options?: ApiOptions
): Promise<ApiResponse<T>> => {
  try {
    const client = await ApiClientManager.getInstance();

    // Handling paths
    let processedPath = path.startsWith("/") ? path.substring(1) : path;

    // Handling paths with parameters (e.g.: users/123 -> users._id(123)）
    const pathParts = processedPath.split("/");
    let currentApi = client;

    for (let i = 0; i < pathParts.length; i++) {
      const part = pathParts[i];

      // For numeric or string IDs
      if (i > 0 && /^[a-zA-Z0-9-_]+$/.test(part) && !currentApi[part]) {
        // If the previous part is an array-like resource, treat it as an ID.
        const prevPart = pathParts[i - 1];
        if (currentApi[`_${prevPart.slice(0, -1)}`]) {
          // Attempts to convert plurals to singulars (e.g.: users -> user）
          currentApi = currentApi[`_${prevPart.slice(0, -1)}`](part);
          continue;
        } else if (currentApi._id) {
          // Use the generic _id method
          currentApi = currentApi._id(part);
          continue;
        }
      }

      if (currentApi[part]) {
        currentApi = currentApi[part];
      } else {
        throw new Error(`API path not found: ${path} (failed at: ${part})`);
      }
    }

    // Get the aspida method corresponding to the HTTP method
    const aspidaMethod = HTTP_METHOD_MAP[method];
    if (!currentApi[aspidaMethod]) {
      throw new Error(`Method ${method} not supported for path: ${path}`);
    }

    // Build aspida's call parameters
    const aspidaParams: any = {};

    if (options?.params && Object.keys(options.params).length > 0) {
      aspidaParams.query = options.params;
    }

    if (data && method !== "GET") {
      aspidaParams.body = data;
    }

    // API call execution
    const { data: responseData, error } = await withErrorHandling(async () => {
      return await currentApi[aspidaMethod](
        Object.keys(aspidaParams).length > 0 ? aspidaParams : undefined
      );
    });

    if (error) {
      return {
        data: null,
        error: {
          status: error.status || 500,
          message: error.message || "API request failed",
          details: error.details,
        },
        success: false,
      };
    }

    return {
      data: responseData,
      error: null,
      success: true,
    };
  } catch (err: any) {
    console.error(`API call failed: ${method} ${path}`, err);

    return {
      data: null,
      error: {
        status: 500,
        message: err.message || "Unexpected error occurred",
        details: err,
      },
      success: false,
    };
  }
};

// Useful Helper Functions
export const api = {
  get: <T = any>(path: string, options?: ApiOptions) =>
    apiCall<T>("GET", path, undefined, options),

  post: <T = any>(path: string, data?: any, options?: ApiOptions) =>
    apiCall<T>("POST", path, data, options),

  put: <T = any>(path: string, data?: any, options?: ApiOptions) =>
    apiCall<T>("PUT", path, data, options),

  patch: <T = any>(path: string, data?: any, options?: ApiOptions) =>
    apiCall<T>("PATCH", path, data, options),

  delete: <T = any>(path: string, options?: ApiOptions) =>
    apiCall<T>("DELETE", path, undefined, options),
};

// custom hooks
export const useApiCall = () => {
  const [loading, setLoading] = useState(false);

  const callApi = async <T = any>(
    method: HttpMethod,
    path: string,
    data?: any,
    options?: ApiOptions
  ): Promise<ApiResponse<T>> => {
    setLoading(true);
    try {
      return await apiCall<T>(method, path, data, options);
    } finally {
      setLoading(false);
    }
  };

  return { callApi, loading };
};

// Authentication-related helpers
export const authApi = {
  // Reset API client after token refresh
  refreshClient: async () => {
    ApiClientManager.resetInstance();
    return await ApiClientManager.getInstance();
  },

  // Force client update
  forceRefresh: async () => {
    return await ApiClientManager.forceRefresh();
  },

  // Check current client status
  hasClient: () => {
    return ApiClientManager.hasInstance();
  },
};
