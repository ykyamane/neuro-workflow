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

  // Loading ...
  if (loading) {
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

  // If unauthenticated, redirect to login page
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If authenticated, display child component
  return <>{children}</>;
};

export default ProtectedRoute;
