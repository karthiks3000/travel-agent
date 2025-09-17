/**
 * Skeleton component for Aceternity UI
 * Loading placeholders with shimmer effects
 */

import * as React from "react";
import { cn } from "@/lib/utils";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "circular" | "rectangular" | "text";
  animation?: "pulse" | "wave" | "none";
}

const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className, variant = "default", animation = "pulse", ...props }, ref) => {
    const variantClasses = {
      default: "rounded-md",
      circular: "rounded-full",
      rectangular: "rounded-none",
      text: "rounded-sm h-4"
    };

    const animationClasses = {
      pulse: "animate-pulse",
      wave: "animate-shimmer bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 bg-[length:200%_100%]",
      none: ""
    };

    return (
      <div
        ref={ref}
        className={cn(
          "bg-gray-200 dark:bg-gray-700",
          variantClasses[variant],
          animationClasses[animation],
          className
        )}
        {...props}
      />
    );
  }
);

Skeleton.displayName = "Skeleton";

export { Skeleton };