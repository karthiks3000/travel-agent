/**
 * Button component with Aceternity UI styling
 */

import React from 'react';
import { cn } from '../../lib/utils';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg';
  className?: string;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center rounded-md text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none",
          {
            'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700 shadow-lg hover:shadow-xl transform hover:scale-105': variant === 'default',
            'bg-white/10 text-white border border-white/20 hover:bg-white/20 backdrop-blur-sm': variant === 'secondary',
            'border border-purple-500 text-purple-400 hover:bg-purple-500 hover:text-white': variant === 'outline',
            'text-white hover:bg-white/10': variant === 'ghost',
          },
          {
            'h-10 py-2 px-4': size === 'default',
            'h-9 px-3 text-xs': size === 'sm',
            'h-11 px-8': size === 'lg',
          },
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";

export { Button };