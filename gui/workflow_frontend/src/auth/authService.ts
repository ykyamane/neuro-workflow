import { supabase, AuthError } from "./supabase";

export interface SignUpData {
  email: string;
  password: string;
  name: string;
}

export interface SignInData {
  email: string;
  password: string;
}

export interface AuthResult {
  success: boolean;
  data?: any;
  error?: AuthError;
}

class AuthService {
  // sign up
  async signUp({ email, password, name }: SignUpData): Promise<AuthResult> {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            name,
            full_name: name,
          },
        },
      });

      if (error) {
        return {
          success: false,
          error: {
            message: this.getErrorMessage(error.message),
            status: error.status,
          },
        };
      }

      return {
        success: true,
        data: data.user,
      };
    } catch (error) {
      return {
        success: false,
        error: {
          message: "An unexpected error occurred during sign up",
        },
      };
    }
  }

  // Sign in
  async signIn({ email, password }: SignInData): Promise<AuthResult> {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) {
        return {
          success: false,
          error: {
            message: this.getErrorMessage(error.message),
            status: error.status,
          },
        };
      }

      return {
        success: true,
        data: data.user,
      };
    } catch (error) {
      return {
        success: false,
        error: {
          message: "An unexpected error occurred during sign in",
        },
      };
    }
  }

  // sign out
  async signOut(): Promise<AuthResult> {
    try {
      const { error } = await supabase.auth.signOut();

      if (error) {
        return {
          success: false,
          error: {
            message: this.getErrorMessage(error.message),
          },
        };
      }

      return {
        success: true,
      };
    } catch (error) {
      return {
        success: false,
        error: {
          message: "An unexpected error occurred during sign out",
        },
      };
    }
  }

  // password reset
  async resetPassword(email: string): Promise<AuthResult> {
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`,
      });

      if (error) {
        return {
          success: false,
          error: {
            message: this.getErrorMessage(error.message),
          },
        };
      }

      return {
        success: true,
      };
    } catch (error) {
      return {
        success: false,
        error: {
          message: "An unexpected error occurred during password reset",
        },
      };
    }
  }

  // Password update
  async updatePassword(password: string): Promise<AuthResult> {
    try {
      const { error } = await supabase.auth.updateUser({
        password,
      });

      if (error) {
        return {
          success: false,
          error: {
            message: this.getErrorMessage(error.message),
          },
        };
      }

      return {
        success: true,
      };
    } catch (error) {
      return {
        success: false,
        error: {
          message: "An unexpected error occurred during password update",
        },
      };
    }
  }

  // Get current user
  async getCurrentUser() {
    try {
      const {
        data: { user },
        error,
      } = await supabase.auth.getUser();

      if (error) {
        return null;
      }

      return user;
    } catch (error) {
      return null;
    }
  }

  // Authentication status monitoring
  onAuthStateChange(callback: (event: string, session: any) => void) {
    return supabase.auth.onAuthStateChange(callback);
  }

  // Error message translation
  private getErrorMessage(errorMessage: string): string {
    const errorMessages: { [key: string]: string } = {
      "Invalid login credentials":
        "Incorrect email address or password",
      "User already registered": "This email address is already registered",
      "Email not confirmed": "Email address not verified",
      "Signup requires a valid password": "Invalid password",
      "Password should be at least 6 characters":
        "Please enter a password of at least 6 characters",
      "Invalid email": "Email address format is incorrect",
      "Email rate limit exceeded":
        "Email sending limit reached. Please wait a while and try again",
    };

    return errorMessages[errorMessage] || errorMessage;
  }
}

export const authService = new AuthService();
