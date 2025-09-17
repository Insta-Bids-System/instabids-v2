import React from 'react';
import { useIris } from '@/contexts/IrisContext';
import { useAuth } from '@/contexts/AuthContext';
import FloatingIrisChat from './FloatingIrisChat';

/**
 * Global IRIS Manager - Provides floating IRIS chat across all pages
 * 
 * This component should be included at the app level (in main App component)
 * to provide persistent IRIS chat functionality across all routes and tabs.
 */
const GlobalIrisManager: React.FC = () => {
  const { user } = useAuth();
  const { 
    isIrisOpen, 
    setIsIrisOpen, 
    currentPropertyId, 
    currentBoardId 
  } = useIris();

  // Only render if user is authenticated
  if (!user) {
    return null;
  }

  return (
    <>
      {/* Always render FloatingIrisChat - it handles its own open/closed state */}
      <FloatingIrisChat
        propertyId={currentPropertyId}
        boardId={currentBoardId}
        initialContext="auto"
        onClose={() => setIsIrisOpen(false)}
      />
    </>
  );
};

export default GlobalIrisManager;