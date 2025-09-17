/**
 * Sign Up Page component
 * Based on requirements 2.1, 2.2, 2.5
 */

import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { SignUpForm } from '../components/auth/SignUpForm';
import { useAuthStore } from '../stores/authStore';

export const SignUpPage: React.FC = () => {
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

  return <SignUpForm />;
};