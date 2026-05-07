export interface User {
  id: string;
  email: string;
  user_metadata?: {
    name?: string;
    full_name?: string;
  };
}

export interface AuthError {
  message: string;
  status?: number;
}

export interface AuthResult {
  success: boolean;
  data?: unknown;
  error?: AuthError;
}
