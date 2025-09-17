/**
 * ChatLayout component - Split-panel layout for chat interface
 * Requirements: 4.1, 4.8, 5.1
 */

import React, { useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, MessageSquare, BarChart3 } from 'lucide-react';

interface ChatLayoutProps {
  leftPanel: React.ReactNode;
  rightPanel: React.ReactNode;
  className?: string;
}

export const ChatLayout: React.FC<ChatLayoutProps> = ({
  leftPanel,
  rightPanel,
  className
}) => {
  const [leftPanelWidth, setLeftPanelWidth] = useState(50); // Percentage
  const [isResizing, setIsResizing] = useState(false);
  const [isMobileView, setIsMobileView] = useState(false);
  const [mobileActivePanel, setMobileActivePanel] = useState<'chat' | 'results'>('chat');

  // Handle panel resizing
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);

    const handleMouseMove = (e: MouseEvent) => {
      const container = document.getElementById('chat-container');
      if (!container) return;

      const containerRect = container.getBoundingClientRect();
      const newWidth = ((e.clientX - containerRect.left) / containerRect.width) * 100;
      
      // Constrain width between 25% and 75%
      const constrainedWidth = Math.min(Math.max(newWidth, 25), 75);
      setLeftPanelWidth(constrainedWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, []);

  // Check for mobile view
  React.useEffect(() => {
    const checkMobileView = () => {
      setIsMobileView(window.innerWidth < 768);
    };

    checkMobileView();
    window.addEventListener('resize', checkMobileView);
    return () => window.removeEventListener('resize', checkMobileView);
  }, []);

  // Mobile panel toggle
  const toggleMobilePanel = (panel: 'chat' | 'results') => {
    setMobileActivePanel(panel);
  };

  if (isMobileView) {
    return (
      <div className={cn("flex flex-col h-screen bg-gray-50", className)}>
        {/* Mobile header with panel toggles */}
        <div className="flex bg-white border-b border-gray-200 p-2">
          <Button
            variant={mobileActivePanel === 'chat' ? 'default' : 'outline'}
            size="sm"
            onClick={() => toggleMobilePanel('chat')}
            className="flex-1 mr-2"
          >
            <MessageSquare className="w-4 h-4 mr-2" />
            Chat
          </Button>
          <Button
            variant={mobileActivePanel === 'results' ? 'default' : 'outline'}
            size="sm"
            onClick={() => toggleMobilePanel('results')}
            className="flex-1"
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            Results
          </Button>
        </div>

        {/* Mobile content */}
        <div className="flex-1 overflow-hidden">
          {mobileActivePanel === 'chat' ? (
            <div className="h-full">{leftPanel}</div>
          ) : (
            <div className="h-full">{rightPanel}</div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div 
      id="chat-container"
      className={cn("flex h-screen bg-gray-50", className)}
    >
      {/* Left Panel - Chat */}
      <div 
        className="flex flex-col bg-white border-r border-gray-200 transition-all duration-200"
        style={{ width: `${leftPanelWidth}%` }}
      >
        <div className="flex-1 overflow-hidden">
          {leftPanel}
        </div>
      </div>

      {/* Resizer */}
      <div
        className={cn(
          "w-1 bg-gray-200 hover:bg-gray-300 cursor-col-resize transition-colors duration-200 relative group",
          isResizing && "bg-blue-400"
        )}
        onMouseDown={handleMouseDown}
      >
        {/* Resizer handle */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <div className="flex items-center justify-center w-6 h-12 bg-gray-400 rounded-full shadow-md">
            <ChevronLeft className="w-3 h-3 text-white" />
            <ChevronRight className="w-3 h-3 text-white -ml-1" />
          </div>
        </div>
      </div>

      {/* Right Panel - Results */}
      <div 
        className="flex flex-col bg-white transition-all duration-200"
        style={{ width: `${100 - leftPanelWidth}%` }}
      >
        <div className="flex-1 overflow-hidden">
          {rightPanel}
        </div>
      </div>
    </div>
  );
};
