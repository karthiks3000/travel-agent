/**
 * Sign In Form component using Aceternity UI
 * Based on requirements 3.1, 3.2, 3.4
 */

import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Input, Button, Card, Label } from '../ui';
import { useAuthStore } from '../../stores/authStore';
import type { SignInFormData, FormValidation } from '../../types/auth';

export const SignInForm: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn, resetPassword, isLoading, error, clearError } = useAuthStore();
  
  const [formData, setFormData] = useState<SignInFormData>({
    email: '',
    password: '',
    rememberMe: false,
  });
  
  const [validation, setValidation] = useState<FormValidation>({
    isValid: false,
    errors: {},
  });
  
  const [showPasswordReset, setShowPasswordReset] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetSent, setResetSent] = useState(false);

  // Get success message from navigation state (e.g., from sign up confirmation)
  const successMessage = location.state?.message;

  // Real-time form validation
  const validateForm = (data: SignInFormData): FormValidation => {
    const errors: Record<string, string> = {};

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!data.email) {
      errors.email = 'Email is required';
    } else if (!emailRegex.test(data.email)) {
      errors.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!data.password) {
      errors.password = 'Password is required';
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors,
    };
  };

  // Handle input changes with real-time validation
  const handleInputChange = (field: keyof SignInFormData, value: string | boolean) => {
    const newFormData = { ...formData, [field]: value };
    setFormData(newFormData);
    
    // Clear any existing errors for this field
    clearError();
    
    // Validate form in real-time (only for string fields)
    if (typeof value === 'string') {
      const newValidation = validateForm(newFormData);
      setValidation(newValidation);
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const formValidation = validateForm(formData);
    setValidation(formValidation);
    
    if (!formValidation.isValid) {
      return;
    }

    try {
      await signIn(formData.email, formData.password);
      
      // Navigate to chat interface after successful sign in
      navigate('/chat', { replace: true });
    } catch (error) {
      // Error is handled by the store and displayed via error state
      console.error('Sign in failed:', error);
    }
  };

  // Handle password reset
  const handlePasswordReset = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!resetEmail.trim()) {
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(resetEmail)) {
      return;
    }

    try {
      await resetPassword(resetEmail);
      setResetSent(true);
    } catch (error) {
      console.error('Password reset failed:', error);
    }
  };

  // Render password reset form
  if (showPasswordReset) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
        <Card className="w-full max-w-md p-8 bg-white/10 backdrop-blur-lg border border-white/20">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-white mb-2">
              Reset Password
            </h2>
            {resetSent ? (
              <p className="text-gray-300 text-sm">
                Password reset instructions have been sent to your email.
              </p>
            ) : (
              <p className="text-gray-300 text-sm">
                Enter your email address and we'll send you a link to reset your password.
              </p>
            )}
          </div>

          {!resetSent ? (
            <form onSubmit={handlePasswordReset} className="space-y-6">
              <div>
                <Label htmlFor="resetEmail" className="text-white">
                  Email Address
                </Label>
                <Input
                  id="resetEmail"
                  type="email"
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="mt-1"
                  disabled={isLoading}
                  required
                />
              </div>

              {error && (
                <div className="text-red-400 text-sm text-center bg-red-500/10 p-3 rounded-lg border border-red-500/20">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={isLoading || !resetEmail.trim()}
              >
                {isLoading ? 'Sending...' : 'Send Reset Link'}
              </Button>
            </form>
          ) : (
            <div className="text-center">
              <div className="text-green-400 text-sm bg-green-500/10 p-3 rounded-lg border border-green-500/20 mb-6">
                Check your email for password reset instructions.
              </div>
            </div>
          )}

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => {
                setShowPasswordReset(false);
                setResetSent(false);
                setResetEmail('');
                clearError();
              }}
              className="text-purple-400 hover:text-purple-300 text-sm underline"
            >
              Back to Sign In
            </button>
          </div>
        </Card>
      </div>
    );
  }

  // Render sign in form
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
      <Card className="w-full max-w-md p-8 bg-white/10 backdrop-blur-lg border border-white/20">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-white mb-2">
            Welcome Back
          </h2>
          <p className="text-gray-300 text-sm">
            Sign in to continue planning your perfect trip
          </p>
        </div>

        {successMessage && (
          <div className="text-green-400 text-sm text-center bg-green-500/10 p-3 rounded-lg border border-green-500/20 mb-6">
            {successMessage}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <Label htmlFor="email" className="text-white">
              Email Address
            </Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              placeholder="Enter your email"
              className="mt-1"
              disabled={isLoading}
              required
            />
            {validation.errors.email && (
              <p className="text-red-400 text-sm mt-1">{validation.errors.email}</p>
            )}
          </div>

          <div>
            <Label htmlFor="password" className="text-white">
              Password
            </Label>
            <Input
              id="password"
              type="password"
              value={formData.password}
              onChange={(e) => handleInputChange('password', e.target.value)}
              placeholder="Enter your password"
              className="mt-1"
              disabled={isLoading}
              required
            />
            {validation.errors.password && (
              <p className="text-red-400 text-sm mt-1">{validation.errors.password}</p>
            )}
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="rememberMe"
                type="checkbox"
                checked={formData.rememberMe}
                onChange={(e) => handleInputChange('rememberMe', e.target.checked)}
                className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-white/20 rounded bg-white/5"
                disabled={isLoading}
              />
              <Label htmlFor="rememberMe" className="ml-2 text-sm text-gray-300">
                Remember me
              </Label>
            </div>

            <button
              type="button"
              onClick={() => setShowPasswordReset(true)}
              className="text-sm text-purple-400 hover:text-purple-300 underline"
              disabled={isLoading}
            >
              Forgot password?
            </button>
          </div>

          {error && (
            <div className="text-red-400 text-sm text-center bg-red-500/10 p-3 rounded-lg border border-red-500/20">
              {error}
            </div>
          )}

          <Button
            type="submit"
            className="w-full"
            disabled={isLoading || !validation.isValid}
          >
            {isLoading ? 'Signing In...' : 'Sign In'}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-300 text-sm">
            Don't have an account?{' '}
            <Link
              to="/signup"
              className="text-purple-400 hover:text-purple-300 underline"
            >
              Sign up here
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
};