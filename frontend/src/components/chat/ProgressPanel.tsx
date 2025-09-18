/**
 * ProgressPanel component - Shows real-time tool execution progress
 * Requirements: Status communication, progress tracking, user feedback
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { CheckCircle2, Circle, Loader2, XCircle, Clock } from 'lucide-react';
import type { ToolProgress, ResponseStatus } from '@/types/chat';

interface ProgressPanelProps {
  toolProgress: ToolProgress[];
  overallProgressMessage: string;
  responseStatus: ResponseStatus;
  className?: string;
}

export const ProgressPanel: React.FC<ProgressPanelProps> = ({
  toolProgress,
  overallProgressMessage,
  responseStatus,
  className
}) => {
  // Get status icon based on tool status
  const getStatusIcon = (status: ToolProgress['status']) => {
    switch (status) {
      case 'pending':
        return <Circle className="w-5 h-5 text-gray-400" />;
      case 'active':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Circle className="w-5 h-5 text-gray-400" />;
    }
  };

  // Get status color for text
  const getStatusColor = (status: ToolProgress['status']) => {
    switch (status) {
      case 'pending':
        return 'text-gray-500';
      case 'active':
        return 'text-blue-600';
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-gray-500';
    }
  };

  // Get response status indicator
  const getResponseStatusIcon = () => {
    switch (responseStatus) {
      case 'requesting_info':
      case 'validating':
        return <Clock className="w-4 h-4 text-blue-500" />;
      case 'thinking':
      case 'calling_tools':
      case 'tool_in_progress':
      case 'processing_results':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'complete_success':
      case 'complete_with_recommendations':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'partial_results':
        return <CheckCircle2 className="w-4 h-4 text-yellow-500" />;
      case 'tool_error':
      case 'validation_error':
      case 'system_error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Circle className="w-4 h-4 text-gray-400" />;
    }
  };

  // If no progress data, don't render
  if (!toolProgress || toolProgress.length === 0) {
    return null;
  }

  return (
    <Card className={cn("p-4 space-y-4", className)}>
      {/* Overall Status */}
      <div className="flex items-center space-x-2 pb-3 border-b border-gray-200">
        {getResponseStatusIcon()}
        <div className="flex-1">
          <h3 className="font-medium text-gray-900">Progress</h3>
          <p className="text-sm text-gray-600">{overallProgressMessage}</p>
        </div>
      </div>

      {/* Tool Progress List */}
      <div className="space-y-3">
        {toolProgress.map((tool, index) => (
          <div key={`${tool.tool_id}-${index}`} className="flex items-start space-x-3">
            {/* Status Icon */}
            <div className="flex-shrink-0 mt-0.5">
              {getStatusIcon(tool.status)}
            </div>

            {/* Tool Details */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <h4 className={cn(
                  "text-sm font-medium",
                  getStatusColor(tool.status)
                )}>
                  {tool.display_name}
                </h4>
                <span className={cn(
                  "text-xs px-2 py-1 rounded-full capitalize",
                  tool.status === 'pending' && "bg-gray-100 text-gray-600",
                  tool.status === 'active' && "bg-blue-100 text-blue-700",
                  tool.status === 'completed' && "bg-green-100 text-green-700",
                  tool.status === 'failed' && "bg-red-100 text-red-700"
                )}>
                  {tool.status}
                </span>
              </div>

              {/* Tool Description */}
              <p className="text-xs text-gray-500 mt-1">
                {tool.description}
              </p>

              {/* Result Preview or Error */}
              {tool.result_preview && (
                <div className="mt-2 p-2 bg-green-50 rounded text-xs text-green-700 border border-green-200">
                  <span className="font-medium">Result: </span>
                  {tool.result_preview}
                </div>
              )}

              {tool.error_message && (
                <div className="mt-2 p-2 bg-red-50 rounded text-xs text-red-700 border border-red-200">
                  <span className="font-medium">Error: </span>
                  {tool.error_message}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Progress Summary */}
      <div className="pt-3 border-t border-gray-200">
        <div className="flex justify-between text-xs text-gray-500">
          <span>
            {toolProgress.filter(t => t.status === 'completed').length} completed
          </span>
          <span>
            {toolProgress.filter(t => t.status === 'failed').length} failed
          </span>
          <span>
            {toolProgress.filter(t => t.status === 'active').length} active
          </span>
        </div>
      </div>
    </Card>
  );
};
