/**
 * MessageInput component - Text input with send functionality
 * Requirements: 4.2, 4.6
 */

import React, { useState, useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useChatStore } from '@/stores/chatStore';
import { useAuthStore } from '@/stores/authStore';
import { Send, Loader2 } from 'lucide-react';

interface MessageInputProps {
  className?: string;
  placeholder?: string;
  maxLength?: number;
}

export const MessageInput: React.FC<MessageInputProps> = ({
  className,
  placeholder = "Type your message...",
  maxLength = 1000
}) => {
  const [message, setMessage] = useState('');
  const [isComposing, setIsComposing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  
  const { sendMessage, isSending, error, clearError } = useChatStore();
  const { isAuthenticated } = useAuthStore();

  // Handle message sending
  const handleSend = useCallback(async () => {
    const trimmedMessage = message.trim();
    
    if (!trimmedMessage || isSending || !isAuthenticated) {
      return;
    }

    // Validate message length
    if (trimmedMessage.length > maxLength) {
      return;
    }

    // Clear any previous errors
    if (error) {
      clearError();
    }

    try {
      await sendMessage(trimmedMessage);
      setMessage('');
      
      // Focus back to input after sending
      if (inputRef.current) {
        inputRef.current.focus();
      }
    } catch (err) {
      // Error is handled by the store
      console.error('Failed to send message:', err);
    }
  }, [message, isSending, isAuthenticated, maxLength, error, sendMessage, clearError]);

  // Handle form submission
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    handleSend();
  }, [handleSend]);

  // Handle key press
  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend, isComposing]);

  // Handle input change
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    
    // Enforce character limit
    if (value.length <= maxLength) {
      setMessage(value);
    }
  }, [maxLength]);

  // Handle composition events (for IME input)
  const handleCompositionStart = useCallback(() => {
    setIsComposing(true);
  }, []);

  const handleCompositionEnd = useCallback(() => {
    setIsComposing(false);
  }, []);

  const isDisabled = !isAuthenticated || isSending;
  const canSend = message.trim().length > 0 && !isDisabled;
  const characterCount = message.length;
  const isNearLimit = characterCount > maxLength * 0.8;

  return (
    <form onSubmit={handleSubmit} className={cn("space-y-2", className)}>
      {/* Input container */}
      <div className="flex space-x-2">
        <div className="flex-1 relative">
          <Input
            ref={inputRef}
            type="text"
            value={message}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            onCompositionStart={handleCompositionStart}
            onCompositionEnd={handleCompositionEnd}
            placeholder={isAuthenticated ? placeholder : "Please sign in to send messages"}
            disabled={isDisabled}
            className={cn(
              "pr-12 resize-none",
              error && "border-red-300 focus:border-red-500 focus:ring-red-500"
            )}
            maxLength={maxLength}
          />
          
          {/* Character count */}
          {characterCount > 0 && (
            <div className={cn(
              "absolute right-3 top-1/2 transform -translate-y-1/2 text-xs",
              isNearLimit ? "text-orange-500" : "text-gray-400"
            )}>
              {characterCount}/{maxLength}
            </div>
          )}
        </div>

        {/* Send button */}
        <Button
          type="submit"
          disabled={!canSend}
          className={cn(
            "px-4 py-2 transition-all duration-200",
            canSend 
              ? "bg-blue-600 hover:bg-blue-700 text-white" 
              : "bg-gray-200 text-gray-400 cursor-not-allowed"
          )}
        >
          {isSending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </div>

      {/* Helper text */}
      <div className="flex justify-between items-center text-xs text-gray-500">
        <div>
          {!isAuthenticated ? (
            <span className="text-red-500">Please sign in to send messages</span>
          ) : (
            <span>Press Enter to send, Shift+Enter for new line</span>
          )}
        </div>
        
        {isNearLimit && (
          <div className="text-orange-500">
            {maxLength - characterCount} characters remaining
          </div>
        )}
      </div>
    </form>
  );
};