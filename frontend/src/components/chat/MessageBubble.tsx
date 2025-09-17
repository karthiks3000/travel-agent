/**
 * MessageBubble component - Individual message display
 * Requirements: 4.2, 4.4, 4.6, 7.2
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { User, Bot, AlertCircle } from 'lucide-react';
import type { Message } from '@/types/chat';

interface MessageBubbleProps {
  message: Message;
  showAvatar?: boolean;
  className?: string;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  showAvatar = true,
  className
}) => {
  const isUser = message.sender === 'user';
  const isError = message.metadata?.error;
  const hasResults = message.metadata?.resultType && message.metadata?.resultData;

  const formatTime = (timestamp: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(timestamp);
  };

  return (
    <div className={cn("flex space-x-3", isUser && "flex-row-reverse space-x-reverse", className)}>
      {/* Avatar */}
      <div className={cn("flex-shrink-0", !showAvatar && "invisible")}>
        <div className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center",
          isUser 
            ? "bg-blue-600 text-white" 
            : "bg-gray-100 text-gray-600"
        )}>
          {isUser ? (
            <User className="w-4 h-4" />
          ) : (
            <Bot className="w-4 h-4" />
          )}
        </div>
      </div>

      {/* Message Content */}
      <div className={cn("flex-1 max-w-xs sm:max-w-md", isUser && "flex justify-end")}>
        <Card className={cn(
          "p-3 shadow-sm",
          isUser 
            ? "bg-blue-600 text-white border-blue-600" 
            : isError
              ? "bg-red-50 border-red-200 text-red-800"
              : "bg-white border-gray-200 text-gray-900"
        )}>
          {/* Message text */}
          <div className="text-sm whitespace-pre-wrap break-words">
            {message.content}
          </div>

          {/* Error indicator */}
          {isError && (
            <div className="flex items-center mt-2 text-xs text-red-600">
              <AlertCircle className="w-3 h-3 mr-1" />
              Error occurred
            </div>
          )}

          {/* Results indicator */}
          {hasResults && (
            <div className="mt-2 text-xs opacity-75">
              <div className="flex items-center">
                <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                Results available in right panel
              </div>
            </div>
          )}

          {/* Timestamp */}
          <div className={cn(
            "text-xs mt-2 opacity-75",
            isUser ? "text-blue-100" : "text-gray-500"
          )}>
            {formatTime(message.timestamp)}
          </div>
        </Card>
      </div>
    </div>
  );
};
