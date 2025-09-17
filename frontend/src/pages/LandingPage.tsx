import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { HeroSection } from '@/components/landing/HeroSection';
import { FeaturesGrid } from '@/components/landing/FeaturesGrid';
import { CTASection } from '@/components/landing/CTASection';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    // Redirect authenticated users to chat interface (Requirement 1.6)
    if (isAuthenticated) {
      navigate('/chat');
    }
  }, [isAuthenticated, navigate]);

  // Don't render the landing page if user is authenticated
  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen">
      <HeroSection />
      <FeaturesGrid />
      <CTASection />
    </div>
  );
};