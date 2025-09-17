import React from 'react';
import { cn } from '../../utils/cn';

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'warning' | 'success';
  size?: 'sm' | 'md' | 'lg';
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    const variants = {
      default: 'bg-blue-100 text-blue-800 border-blue-200',
      secondary: 'bg-gray-100 text-gray-800 border-gray-200',
      destructive: 'bg-red-100 text-red-800 border-red-200',
      warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      success: 'bg-green-100 text-green-800 border-green-200'
    };

    const sizes = {
      sm: 'px-2 py-1 text-xs',
      md: 'px-2.5 py-1.5 text-sm',
      lg: 'px-3 py-2 text-base'
    };

    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-full border font-medium transition-colors',
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);

Badge.displayName = 'Badge';

export { Badge };