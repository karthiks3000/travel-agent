/**
 * StreamingMessageBubble - Shows real-time AI response as it streams in
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Bot } from 'lucide-react';

interface StreamingMessageBubbleProps {
  message: string;
  showAvatar?: boolean;
  className?: string;
}

export const StreamingMessageBubble: React.FC<StreamingMessageBubbleProps> = ({
  message,
  showAvatar = true,
  className
}) => {
  return (
    <div className={cn("flex space-x-3", className)}>
      {/* Avatar */}
      <div className={cn("flex-shrink-0", !showAvatar && "invisible")}>
        <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gray-100 text-gray-600">
          <Bot className="w-4 h-4" />
        </div>
      </div>

      {/* Streaming Message Content */}
      <div className="flex-1 max-w-xs sm:max-w-md">
        <Card className="p-3 shadow-sm bg-white border-gray-200 text-gray-900">
          {/* Streaming message text */}
          <div className="text-sm whitespace-pre-wrap break-words">
            {message}
            {/* Typing cursor */}
            <span className="inline-block w-2 h-4 bg-blue-500 ml-1 animate-pulse" />
          </div>

          {/* Streaming indicator */}
          <div className="mt-2 text-xs text-gray-500 flex items-center">
            <div className="flex space-x-1">
              <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" />
              <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
              <div className="w-1 h-1 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
            </div>
            <span className="ml-2">Typing...</span>
          </div>
        </Card>
      </div>
    </div>
  );
};
