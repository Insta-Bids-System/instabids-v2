import React from 'react';
import { cn } from '../../utils/cn';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  label?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className = '',
  label 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-2',
    lg: 'h-12 w-12 border-3',
    xl: 'h-16 w-16 border-4'
  };

  return (
    <div className={cn('flex flex-col items-center justify-center', className)}>
      <div className={cn(
        'animate-spin rounded-full border-gray-300 border-t-blue-600',
        sizeClasses[size]
      )} />
      {label && (
        <p className="mt-2 text-sm text-gray-600">{label}</p>
      )}
    </div>
  );
};

export { LoadingSpinner };
export default LoadingSpinner;