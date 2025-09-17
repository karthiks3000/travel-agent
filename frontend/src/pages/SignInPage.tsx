/**
 * Sign In Page component
 * Based on requirements 3.1, 3.2, 3.4
 */

import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { SignInForm } from '../components/auth/SignInForm';
import { useAuthStore } from '../stores/authStore';

export const SignInPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  // Redirect authenticated users to chat interface
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/chat', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Don't render the form if user is already authenticated
  if (isAuthenticated) {
    return null;
  }

  return <SignInForm />;
};