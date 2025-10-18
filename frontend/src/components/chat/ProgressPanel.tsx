/**
 * ProgressPanel component - Shows real-time tool execution progress
 * Replaces TypingIndicator with detailed streaming progress
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { 
  Bot, 
  Plane, 
  Hotel, 
  Utensils, 
  Camera, 
  MapPin,
  Brain,
  Loader2, 
  CheckCircle, 
  XCircle 
} from 'lucide-react';
import type { ToolProgress } from '@/types/chat';

interface ProgressPanelProps {
  className?: string;
  thinkingMessage?: string | null;
  toolProgress: ToolProgress[];
}

/**
 * Get appropriate icon for tool type
 */
const getToolIcon = (toolId: string): React.ReactNode => {
  const iconProps = { className: "w-4 h-4" };
  
  switch (toolId) {
    case 'search_flights':
      return <Plane {...iconProps} />;
    case 'search_accommodations':
      return <Hotel {...iconProps} />;
    case 'searchPlacesByText':
    case 'search_restaurants':
      return <Utensils {...iconProps} />;
    case 'searchNearbyPlaces':
    case 'search_attractions':
      return <Camera {...iconProps} />;
    case 'getPlaceDetails':
      return <MapPin {...iconProps} />;
    default:
      return <Bot {...iconProps} />;
  }
};

/**
 * Get status indicator icon based on tool status
 */
const getStatusIcon = (status: ToolProgress['status']): React.ReactNode => {
  switch (status) {
    case 'active':
      return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
    case 'completed':
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    case 'failed':
      return <XCircle className="w-4 h-4 text-red-500" />;
    case 'pending':
    default:
      return <div className="w-4 h-4 rounded-full border-2 border-gray-300 animate-pulse" />;
  }
};

/**
 * Individual progress item component
 */
const ProgressItem: React.FC<{
  icon: React.ReactNode;
  message: string;
  description?: string;
  status: ToolProgress['status'];
  preview?: string;
  errorMessage?: string;
}> = ({ icon, message, description, status, preview, errorMessage }) => {
  return (
    <div className={cn(
      "flex items-start space-x-3 py-2 transition-all duration-300",
      "animate-fade-in"
    )}>
      {/* Status indicator */}
      <div className="flex-shrink-0 mt-1">
        {getStatusIcon(status)}
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2">
          <span className={cn(
            "text-sm font-medium",
            status === 'completed' && "text-green-700",
            status === 'failed' && "text-red-700",
            status === 'active' && "text-blue-700",
            status === 'pending' && "text-gray-600"
          )}>
            {message}
          </span>
          <div className="flex-shrink-0">
            {icon}
          </div>
        </div>
        
        {/* Description */}
        {description && (
          <p className="text-xs text-gray-500 mt-1">
            {description}
          </p>
        )}
        
        {/* Preview or error */}
        {status === 'completed' && preview && (
          <p className="text-xs text-green-600 mt-1 font-medium">
            ✓ {preview}
          </p>
        )}
        
        {status === 'failed' && errorMessage && (
          <p className="text-xs text-red-600 mt-1">
            ✗ {errorMessage}
          </p>
        )}
      </div>
    </div>
  );
};

/**
 * Thinking indicator component
 */
const ThinkingIndicator: React.FC<{ message: string }> = ({ message }) => {
  return (
    <div className="flex items-center space-x-3 py-2 animate-fade-in">
      <div className="flex-shrink-0">
        <Loader2 className="w-4 h-4 animate-spin text-purple-500" />
      </div>
      <div className="flex-1">
        <span className="text-sm font-medium text-purple-700">{message}</span>
      </div>
      <div className="flex-shrink-0">
        <Brain className="w-4 h-4 text-purple-500" />
      </div>
    </div>
  );
};

/**
 * Main ProgressPanel component
 */
export const ProgressPanel: React.FC<ProgressPanelProps> = ({ 
  className, 
  thinkingMessage, 
  toolProgress 
}) => {
  // Add debugging
  console.log('🎯 ProgressPanel render:', {
    thinkingMessage,
    toolProgress,
    shouldRender: !(!thinkingMessage && (!toolProgress || toolProgress.length === 0))
  });

  // Don't render if no progress to show
  if (!thinkingMessage && (!toolProgress || toolProgress.length === 0)) {
    console.log('🎯 ProgressPanel: Not rendering (no data)');
    return null;
  }

  return (
    <div className={cn("flex space-x-3 animate-fade-in", className)}>
      {/* Avatar */}
      <div className="flex-shrink-0">
        <div className="w-8 h-8 rounded-full bg-gray-100 text-gray-600 flex items-center justify-center">
          <Bot className="w-4 h-4" />
        </div>
      </div>

      {/* Progress content */}
      <div className="flex-1 max-w-md">
        <Card className="p-3 bg-white border-gray-200 shadow-sm">
          <div className="space-y-2">
            {/* Thinking indicator */}
            {thinkingMessage && (
              <ThinkingIndicator message={thinkingMessage} />
            )}
            
            {/* Tool progress items */}
            {toolProgress.map((tool) => (
              <ProgressItem
                key={tool.tool_id}
                icon={getToolIcon(tool.tool_id)}
                message={tool.display_name}
                description={tool.description}
                status={tool.status}
                preview={tool.result_preview}
                errorMessage={tool.error_message}
              />
            ))}
            
            {/* Fallback if no specific progress */}
            {!thinkingMessage && toolProgress.length === 0 && (
              <div className="flex items-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
                <span className="text-sm text-gray-600">Processing your request...</span>
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};
