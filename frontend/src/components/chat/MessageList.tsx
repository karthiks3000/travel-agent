/**
 * MessageList component - Scrollable conversation history
 * Requirements: 4.2, 4.4, 4.6, 7.2
 */

import React, { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { MessageBubble } from './MessageBubble';
import { StreamingMessageBubble } from './StreamingMessageBubble';
import { Skeleton } from '@/components/ui/skeleton';
import { useChatStreaming } from '@/stores/chatStore';
import type { Message } from '@/types/chat';

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  className?: string;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isLoading = false,
  className
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { streamingMessage, isStreaming } = useChatStreaming();

  // Auto-scroll to bottom when new messages arrive or streaming updates
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end'
      });
    }
  }, [messages, streamingMessage]);

  // Show welcome message if no messages
  if (messages.length === 0 && !isLoading) {
    return (
      <div className={cn("flex flex-col items-center justify-center h-full text-center p-8", className)}>
        <div className="max-w-md">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Start Your Travel Planning
          </h3>
          <p className="text-gray-600 mb-4">
            I'm here to help you plan your perfect trip! Ask me about flights, hotels, restaurants, or anything travel-related.
          </p>
          <div className="text-sm text-gray-500">
            <p className="mb-1">Try asking:</p>
            <ul className="space-y-1">
              <li>"Find flights from New York to Paris"</li>
              <li>"Show me hotels in Tokyo"</li>
              <li>"Plan a 3-day itinerary for Rome"</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className={cn("space-y-4", className)}
    >
      {/* Loading skeleton */}
      {isLoading && messages.length === 0 && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex space-x-3">
              <Skeleton variant="circular" className="w-8 h-8" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Messages */}
      {messages.map((message, index) => {
        const previousMessage = index > 0 ? messages[index - 1] : null;
        const showAvatar = !previousMessage || previousMessage.sender !== message.sender;
        
        return (
          <MessageBubble
            key={message.id}
            message={message}
            showAvatar={showAvatar}
          />
        );
      })}

      {/* Streaming message bubble */}
      {isStreaming && streamingMessage && (
        <StreamingMessageBubble
          message={streamingMessage}
          showAvatar={messages.length === 0 || messages[messages.length - 1]?.sender !== 'agent'}
        />
      )}

      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  );
};
