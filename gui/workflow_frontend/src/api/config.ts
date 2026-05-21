interface ApiConfig {
  baseURL: string;
  internalSecret: string;
  timeout: number;
}

const DEFAULT_TIMEOUT_MS = 30000;

const parseTimeout = (raw: string | undefined): number => {
  if (!raw) return DEFAULT_TIMEOUT_MS;
  const parsed = Number(raw);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_TIMEOUT_MS;
};

export const getApiConfig = (): ApiConfig => {
  const isDev = (import.meta.env.MODE || "development") === "development";
  return {
    baseURL: import.meta.env.VITE_API_BASE_URL,
    internalSecret:
      import.meta.env.VITE_INTERNAL_SECRET || (isDev ? "dev-secret" : ""),
    timeout: parseTimeout(import.meta.env.VITE_API_TIMEOUT),
  };
};

export interface ApiError {
  status: number;
  message: string;
  details?: any;
}

// debug settings
export const isDebugMode = () => {
  return (
    import.meta.env.VITE_DEBUG_API === "true" ||
    import.meta.env.MODE === "development"
  );
};
