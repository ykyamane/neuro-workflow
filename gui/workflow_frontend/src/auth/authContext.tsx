import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User } from './supabase';
import { authService } from './authService';
import { isKeycloakConfigured } from './keycloak';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signUp: (data: { email: string; password: string; name: string }) => Promise<any>;
  signIn: (data: { email: string; password: string }) => Promise<any>;
  signOut: () => Promise<any>;
  resetPassword: (email: string) => Promise<any>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const AUTH_INIT_TIMEOUT_MS = 5000;

    const init = async () => {
      try {
        if (isKeycloakConfigured) {
          const authenticated = await authService.initKeycloak();
          if (authenticated) {
            const u = await authService.getCurrentUser();
            if (u) setUser(u as User);
          }
        } else {
          const result = await Promise.race([
            authService.getCurrentUser(),
            new Promise<null>(resolve =>
              setTimeout(() => resolve(null), AUTH_INIT_TIMEOUT_MS)
            ),
          ]);
          if (result) setUser(result as User);
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
      } finally {
        setLoading(false);
      }
    };

    init();

    const { data: { subscription } } = authService.onAuthStateChange(
      async (event, session) => {
        if (event === 'SIGNED_IN' && session?.user) {
          setUser(session.user as User);
        } else if (event === 'SIGNED_OUT') {
          setUser(null);
        } else if (event === 'TOKEN_REFRESHED' && session?.user) {
          setUser(session.user as User);
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const signUp = async (data: { email: string; password: string; name: string }) => {
    setLoading(true);
    try {
      return await authService.signUp(data);
    } finally {
      setLoading(false);
    }
  };

  const signIn = async (data: { email: string; password: string }) => {
    setLoading(true);
    try {
      return await authService.signIn(data);
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    setLoading(true);
    try {
      return await authService.signOut();
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (email: string) => {
    return await authService.resetPassword(email);
  };

  const value = { user, loading, signUp, signIn, signOut, resetPassword };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
