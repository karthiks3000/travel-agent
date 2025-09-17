/**
 * ScrollArea component for Aceternity UI
 * Provides custom scrollbars with smooth scrolling
 */

import * as React from "react";
import { cn } from "@/lib/utils";

export interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  orientation?: "vertical" | "horizontal" | "both";
}

const ScrollArea = React.forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ className, children, orientation = "vertical", ...props }, ref) => {
    const scrollbarClasses = {
      vertical: "overflow-y-auto overflow-x-hidden",
      horizontal: "overflow-x-auto overflow-y-hidden", 
      both: "overflow-auto"
    };

    return (
      <div
        ref={ref}
        className={cn(
          "relative",
          scrollbarClasses[orientation],
          // Custom scrollbar styling
          "scrollbar-thin scrollbar-track-transparent scrollbar-thumb-gray-300 hover:scrollbar-thumb-gray-400",
          "dark:scrollbar-thumb-gray-600 dark:hover:scrollbar-thumb-gray-500",
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

ScrollArea.displayName = "ScrollArea";

export { ScrollArea };