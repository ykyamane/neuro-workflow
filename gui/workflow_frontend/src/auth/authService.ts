import { supabase, AuthError } from "./supabase";
import { getKeycloak, isKeycloakConfigured } from "./keycloak";

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

/**
 * Unified auth facade: delegates to Keycloak when configured,
 * otherwise falls back to Supabase.
 */
class AuthService {
  // ── Keycloak init (called once in AuthProvider) ──────────────────────
  async initKeycloak(): Promise<boolean> {
    if (!isKeycloakConfigured) return false;
    const kc = getKeycloak();
    try {
      const authenticated = await kc.init({
        onLoad: "login-required",
        checkLoginIframe: false,
      });
      return authenticated;
    } catch (err) {
      console.error("Keycloak init failed:", err);
      return false;
    }
  }

  // ── Sign-up (Keycloak delegates to its own registration page) ───────
  async signUp({ email, password, name }: SignUpData): Promise<AuthResult> {
    if (isKeycloakConfigured) {
      const kc = getKeycloak();
      kc.register();
      return { success: true };
    }
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { name, full_name: name } },
      });
      if (error)
        return {
          success: false,
          error: { message: this.getErrorMessage(error.message), status: error.status },
        };
      return { success: true, data: data.user };
    } catch {
      return { success: false, error: { message: "Unexpected sign-up error" } };
    }
  }

  // ── Sign-in ─────────────────────────────────────────────────────────
  async signIn(_data?: SignInData): Promise<AuthResult> {
    if (isKeycloakConfigured) {
      const kc = getKeycloak();
      await kc.login();
      return { success: true };
    }
    if (!_data) return { success: false, error: { message: "No credentials" } };
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: _data.email,
        password: _data.password,
      });
      if (error)
        return {
          success: false,
          error: { message: this.getErrorMessage(error.message), status: error.status },
        };
      return { success: true, data: data.user };
    } catch {
      return { success: false, error: { message: "Unexpected sign-in error" } };
    }
  }

  // ── Sign-out ────────────────────────────────────────────────────────
  async signOut(): Promise<AuthResult> {
    if (isKeycloakConfigured) {
      const kc = getKeycloak();
      await kc.logout({ redirectUri: window.location.origin });
      return { success: true };
    }
    try {
      const { error } = await supabase.auth.signOut();
      if (error)
        return { success: false, error: { message: this.getErrorMessage(error.message) } };
      return { success: true };
    } catch {
      return { success: false, error: { message: "Unexpected sign-out error" } };
    }
  }

  // ── Password reset (Supabase only; Keycloak has its own UI) ─────────
  async resetPassword(email: string): Promise<AuthResult> {
    if (isKeycloakConfigured) {
      return {
        success: false,
        error: { message: "Password reset is handled by the identity provider." },
      };
    }
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/auth/reset-password`,
      });
      if (error)
        return { success: false, error: { message: this.getErrorMessage(error.message) } };
      return { success: true };
    } catch {
      return { success: false, error: { message: "Unexpected error" } };
    }
  }

  // ── Get current user ────────────────────────────────────────────────
  async getCurrentUser() {
    if (isKeycloakConfigured) {
      const kc = getKeycloak();
      if (!kc.authenticated || !kc.tokenParsed) return null;
      return {
        id: kc.tokenParsed.sub,
        email: kc.tokenParsed.email ?? "",
        user_metadata: {
          name: kc.tokenParsed.preferred_username,
          full_name: `${kc.tokenParsed.given_name ?? ""} ${kc.tokenParsed.family_name ?? ""}`.trim(),
        },
      };
    }
    try {
      const {
        data: { user },
      } = await supabase.auth.getUser();
      return user ?? null;
    } catch {
      return null;
    }
  }

  // ── Get access token ────────────────────────────────────────────────
  async getAccessToken(): Promise<string | null> {
    if (isKeycloakConfigured) {
      const kc = getKeycloak();
      if (!kc.authenticated) return null;
      try {
        await kc.updateToken(30);
      } catch {
        kc.login();
        return null;
      }
      return kc.token ?? null;
    }
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      return session?.access_token ?? null;
    } catch {
      return null;
    }
  }

  // ── Auth state change listener ──────────────────────────────────────
  onAuthStateChange(callback: (event: string, session: any) => void) {
    if (isKeycloakConfigured) {
      const kc = getKeycloak();
      kc.onAuthSuccess = () => callback("SIGNED_IN", { user: this.getCurrentUser() });
      kc.onAuthLogout = () => callback("SIGNED_OUT", null);
      kc.onTokenExpired = () => {
        kc.updateToken(30).catch(() => callback("SIGNED_OUT", null));
      };
      return { data: { subscription: { unsubscribe: () => {} } } };
    }
    return supabase.auth.onAuthStateChange(callback);
  }

  private getErrorMessage(msg: string): string {
    const map: Record<string, string> = {
      "Invalid login credentials": "Incorrect email address or password",
      "User already registered": "This email address is already registered",
      "Email not confirmed": "Email address not verified",
      "Signup requires a valid password": "Invalid password",
      "Password should be at least 6 characters": "Please enter a password of at least 6 characters",
      "Invalid email": "Email address format is incorrect",
      "Email rate limit exceeded": "Email sending limit reached. Please wait a while and try again",
    };
    return map[msg] || msg;
  }
}

export const authService = new AuthService();
