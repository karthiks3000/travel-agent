/**
 * ChatPanel component - Main chat container with message list
 * Requirements: 4.2, 4.4, 4.6, 7.2
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Card, CardHeader } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { TypingIndicator } from './TypingIndicator';
import { useChatStore } from '@/stores/chatStore';
import { MessageSquare } from 'lucide-react';

interface ChatPanelProps {
  className?: string;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ className }) => {
  const { messages, isSending, error } = useChatStore();
  // const { user } = useAuthStore(); // Removed unused variable

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Chat Header */}
      <Card className="rounded-none border-0 border-b">
        <CardHeader className="pb-3">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-full">
              <MessageSquare className="w-5 h-5 text-blue-600" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-500">
                How can I help you plan your trip?
              </p>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Messages Area */}
      <div className="flex-1 flex flex-col min-h-0">
        <ScrollArea className="flex-1 p-4">
          <MessageList messages={messages} />
          {isSending && <TypingIndicator />}
        </ScrollArea>

        {/* Error Display */}
        {error && (
          <div className="px-4 py-2 bg-red-50 border-t border-red-200">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Message Input */}
        <div className="border-t border-gray-200 p-4">
          <MessageInput />
        </div>
      </div>
    </div>
  );
};
