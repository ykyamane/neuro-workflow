import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, Spinner } from '@chakra-ui/react';
import { useAuth } from './auth/authContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  // Development mode: bypass authentication if Supabase is not configured
  const isDevelopmentMode = !import.meta.env.VITE_SUPABASE_URL || 
                          import.meta.env.VITE_SUPABASE_URL.includes('<your') ||
                          import.meta.env.VITE_SUPABASE_URL.includes('your_');

  // ローディング中
  if (loading && !isDevelopmentMode) {
    return (
      <Box
        minH="100vh"
        display="flex"
        alignItems="center"
        justifyContent="center"
      >
        <Spinner size="xl" color="brand.500" />
      </Box>
    );
  }

  // Development mode: allow access without authentication
  if (isDevelopmentMode) {
    return <>{children}</>;
  }

  // 未認証の場合はログインページにリダイレクト
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // 認証済みの場合は子コンポーネントを表示
  return <>{children}</>;
};

export default ProtectedRoute;
