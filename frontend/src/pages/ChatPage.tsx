/**
 * ChatPage component - Main chat interface page
 * Requirements: 4.1, 6.1
 */

import React, { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { useChatStore } from '@/stores/chatStore';
import { ChatLayout } from '@/components/chat/ChatLayout';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { ResultsPanel } from '@/components/chat/ResultsPanel';
import { Button } from '@/components/ui/button';
import { LogOut, RefreshCw } from 'lucide-react';

export const ChatPage: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading, signOut, user } = useAuthStore();
  const { startNewSession, clearSession, isSessionActive } = useChatStore();

  // Initialize session when component mounts
  useEffect(() => {
    if (isAuthenticated && !isSessionActive) {
      startNewSession();
    }
  }, [isAuthenticated, isSessionActive]);

  // Redirect to sign in if not authenticated
  if (!authLoading && !isAuthenticated) {
    return <Navigate to="/signin" replace />;
  }

  // Show loading state while checking authentication
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Handle sign out
  const handleSignOut = async () => {
    try {
      clearSession();
      await signOut();
    } catch (error) {
      console.error('Sign out failed:', error);
    }
  };

  // Handle new session
  const handleNewSession = () => {
    startNewSession();
  };

  // Chat header component
  const ChatHeader = () => (
    <div className="bg-white border-b border-gray-200 px-4 py-3 flex-shrink-0">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <h1 className="text-xl font-semibold text-gray-900">Travel Agent</h1>
        </div>
        
        <div className="flex items-center space-x-4">
          {user && (
            <span className="text-sm text-gray-500">
              Welcome {user.attributes.name}
            </span>
          )}
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleNewSession}
              className="flex items-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>New Session</span>
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleSignOut}
              className="flex items-center space-x-2"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Header */}
      <ChatHeader />
      
      {/* Chat Interface */}
      <div className="flex-1 min-h-0">
        <ChatLayout
          leftPanel={<ChatPanel />}
          rightPanel={<ResultsPanel />}
        />
      </div>
    </div>
  );
};
