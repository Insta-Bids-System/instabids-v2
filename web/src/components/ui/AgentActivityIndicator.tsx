import React from 'react';
import { cn } from '../../utils/cn';

interface AgentActivityIndicatorProps {
  isActive?: boolean;
  agentName?: string;
  message?: string;
  className?: string;
}

export const AgentActivityIndicator: React.FC<AgentActivityIndicatorProps> = ({ 
  isActive = false, 
  agentName = 'Agent',
  message = 'Processing...',
  className = '' 
}) => {
  if (!isActive) return null;

  return (
    <div className={cn(
      'flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-sm',
      className
    )}>
      <div className="flex gap-1">
        <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
        <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse animation-delay-200" />
        <span className="w-2 h-2 bg-blue-600 rounded-full animate-pulse animation-delay-400" />
      </div>
      <span className="text-blue-800 font-medium">{agentName}</span>
      <span className="text-blue-600">{message}</span>
    </div>
  );
};

interface AgentActivityWrapperProps {
  isBeingModified?: boolean;
  currentAgent?: string;
  lastChange?: string;
  className?: string;
  children: React.ReactNode;
}

export const AgentActivityWrapper: React.FC<AgentActivityWrapperProps> = ({ 
  isBeingModified = false,
  currentAgent,
  lastChange,
  className = '',
  children 
}) => {
  return (
    <div className={cn(
      'relative transition-all duration-300',
      isBeingModified && 'ring-2 ring-blue-400 ring-opacity-50',
      className
    )}>
      {children}
      {isBeingModified && currentAgent && (
        <div className="absolute -top-2 -right-2 bg-blue-600 text-white text-xs px-2 py-1 rounded-full shadow-lg animate-pulse">
          {currentAgent}
        </div>
      )}
      {lastChange && (
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-blue-50 to-transparent p-2">
          <p className="text-xs text-blue-600">{lastChange}</p>
        </div>
      )}
    </div>
  );
};