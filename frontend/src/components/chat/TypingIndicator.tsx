/**
 * TypingIndicator component - Shows when agent is processing
 * Requirements: 4.2, 4.4, 4.6, 7.2
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Bot } from 'lucide-react';

interface TypingIndicatorProps {
  className?: string;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ className }) => {
  return (
    <div className={cn("flex space-x-3 animate-fade-in", className)}>
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div className="w-8 h-8 rounded-full bg-gray-100 text-gray-600 flex items-center justify-center">
          <Bot className="w-4 h-4" />
        </div>
      </div>

      {/* Typing bubble */}
      <div className="flex-1 max-w-xs">
        <Card className="p-3 bg-white border-gray-200 shadow-sm">
          <div className="flex items-center space-x-1">
            <span className="text-sm text-gray-600">Assistant is typing</span>
            <div className="flex space-x-1 ml-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};