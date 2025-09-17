/**
 * Sign Up Form component using Aceternity UI
 * Based on requirements 2.1, 2.2, 2.5
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Input, Button, Card, Label } from '../ui';
import { useAuthStore } from '../../stores/authStore';
import type { SignUpFormData, FormValidation } from '../../types/auth';

export const SignUpForm: React.FC = () => {
  const navigate = useNavigate();
  const { signUp, confirmSignUp, resendConfirmationCode, isLoading, error, clearError } = useAuthStore();
  
  const [formData, setFormData] = useState<SignUpFormData>({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
  });
  
  const [validation, setValidation] = useState<FormValidation>({
    isValid: false,
    errors: {},
  });
  
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [confirmationCode, setConfirmationCode] = useState('');
  const [pendingEmail, setPendingEmail] = useState('');

  // Real-time form validation
  const validateForm = (data: SignUpFormData): FormValidation => {
    const errors: Record<string, string> = {};

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!data.email) {
      errors.email = 'Email is required';
    } else if (!emailRegex.test(data.email)) {
      errors.email = 'Please enter a valid email address';
    }

    // Name validation
    if (!data.name.trim()) {
      errors.name = 'Name is required';
    } else if (data.name.trim().length < 2) {
      errors.name = 'Name must be at least 2 characters';
    }

    // Password validation
    if (!data.password) {
      errors.password = 'Password is required';
    } else if (data.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(data.password)) {
      errors.password = 'Password must contain uppercase, lowercase, and number';
    }

    // Confirm password validation
    if (!data.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (data.password !== data.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors,
    };
  };

  // Handle input changes with real-time validation
  const handleInputChange = (field: keyof SignUpFormData, value: string) => {
    const newFormData = { ...formData, [field]: value };
    setFormData(newFormData);
    
    // Clear any existing errors for this field
    clearError();
    
    // Validate form in real-time
    const newValidation = validateForm(newFormData);
    setValidation(newValidation);
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
      await signUp(formData.email, formData.password, formData.name);
      
      // Show confirmation step for email verification
      setPendingEmail(formData.email);
      setShowConfirmation(true);
    } catch (error) {
      // Error is handled by the store and displayed via error state
      console.error('Sign up failed:', error);
    }
  };

  // Handle email confirmation
  const handleConfirmation = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!confirmationCode.trim()) {
      return;
    }

    try {
      await confirmSignUp(pendingEmail, confirmationCode);
      
      // Navigate to sign in page after successful confirmation
      navigate('/signin', { 
        state: { message: 'Account confirmed! Please sign in.' }
      });
    } catch (error) {
      // Error is handled by the store and displayed via error state
      console.error('Confirmation failed:', error);
    }
  };

  // Handle resend confirmation code
  const handleResendCode = async () => {
    try {
      await resendConfirmationCode(pendingEmail);
    } catch (error) {
      console.error('Failed to resend code:', error);
    }
  };

  // Render confirmation step
  if (showConfirmation) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
        <Card className="w-full max-w-md p-8 bg-white/10 backdrop-blur-lg border border-white/20">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold text-white mb-2">
              Verify Your Email
            </h2>
            <p className="text-gray-300 text-sm">
              We've sent a verification code to {pendingEmail}
            </p>
          </div>

          <form onSubmit={handleConfirmation} className="space-y-6">
            <div>
              <Label htmlFor="confirmationCode" className="text-white">
                Verification Code
              </Label>
              <Input
                id="confirmationCode"
                type="text"
                value={confirmationCode}
                onChange={(e) => setConfirmationCode(e.target.value)}
                placeholder="Enter 6-digit code"
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
              disabled={isLoading || !confirmationCode.trim()}
            >
              {isLoading ? 'Verifying...' : 'Verify Email'}
            </Button>

            <div className="text-center">
              <button
                type="button"
                onClick={handleResendCode}
                disabled={isLoading}
                className="text-purple-400 hover:text-purple-300 text-sm underline"
              >
                Didn't receive the code? Resend
              </button>
            </div>
          </form>
        </Card>
      </div>
    );
  }

  // Render sign up form
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
      <Card className="w-full max-w-md p-8 bg-white/10 backdrop-blur-lg border border-white/20">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-white mb-2">
            Create Your Account
          </h2>
          <p className="text-gray-300 text-sm">
            Join us to start planning your perfect trip
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <Label htmlFor="name" className="text-white">
              Full Name
            </Label>
            <Input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="Enter your full name"
              className="mt-1"
              disabled={isLoading}
              required
            />
            {validation.errors.name && (
              <p className="text-red-400 text-sm mt-1">{validation.errors.name}</p>
            )}
          </div>

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
              placeholder="Create a strong password"
              className="mt-1"
              disabled={isLoading}
              required
            />
            {validation.errors.password && (
              <p className="text-red-400 text-sm mt-1">{validation.errors.password}</p>
            )}
          </div>

          <div>
            <Label htmlFor="confirmPassword" className="text-white">
              Confirm Password
            </Label>
            <Input
              id="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
              placeholder="Confirm your password"
              className="mt-1"
              disabled={isLoading}
              required
            />
            {validation.errors.confirmPassword && (
              <p className="text-red-400 text-sm mt-1">{validation.errors.confirmPassword}</p>
            )}
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
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-gray-300 text-sm">
            Already have an account?{' '}
            <Link
              to="/signin"
              className="text-purple-400 hover:text-purple-300 underline"
            >
              Sign in here
            </Link>
          </p>
        </div>
      </Card>
    </div>
  );
};