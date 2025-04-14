
import React from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Navigate } from 'react-router-dom';
import Landing from '@/components/Landing';

const Index = () => {
  const { isAuthenticated } = useAuth();

  return isAuthenticated ? <Navigate to="/chat/new" replace /> : <Landing />;
};

export default Index;
