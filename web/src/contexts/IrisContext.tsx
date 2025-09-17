import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth } from './AuthContext';

interface IrisContextType {
  // Chat state
  isIrisOpen: boolean;
  setIsIrisOpen: (open: boolean) => void;
  
  // Context passing
  currentPropertyId?: string;
  currentBoardId?: string;
  setPropertyContext: (propertyId: string) => void;
  setBoardContext: (boardId: string) => void;
  clearContext: () => void;
  
  // Cross-tab persistence
  sessionData: any;
  updateSession: (data: any) => void;
}

const IrisContext = createContext<IrisContextType | undefined>(undefined);

interface IrisProviderProps {
  children: ReactNode;
}

export const IrisProvider: React.FC<IrisProviderProps> = ({ children }) => {
  const { user } = useAuth();
  const [isIrisOpen, setIsIrisOpen] = useState(false);
  const [currentPropertyId, setCurrentPropertyId] = useState<string>();
  const [currentBoardId, setCurrentBoardId] = useState<string>();
  const [sessionData, setSessionData] = useState<any>(null);

  // Load persisted state when user changes
  useEffect(() => {
    if (user) {
      loadPersistedState();
      setupStorageListener();
    } else {
      clearAllState();
    }
  }, [user]);

  const loadPersistedState = () => {
    if (!user) return;
    
    try {
      // Load IRIS open state
      const irisState = localStorage.getItem(`iris_open_${user.id}`);
      if (irisState) {
        setIsIrisOpen(JSON.parse(irisState));
      }
      
      // Load context state
      const contextState = localStorage.getItem(`iris_context_${user.id}`);
      if (contextState) {
        const context = JSON.parse(contextState);
        setCurrentPropertyId(context.propertyId);
        setCurrentBoardId(context.boardId);
      }
      
      // Load session data
      const sessionState = localStorage.getItem(`iris_session_${user.id}`);
      if (sessionState) {
        setSessionData(JSON.parse(sessionState));
      }
    } catch (error) {
      console.error('Error loading IRIS state:', error);
    }
  };

  const setupStorageListener = () => {
    // Listen for storage changes from other tabs
    const handleStorageChange = (e: StorageEvent) => {
      if (!user) return;
      
      if (e.key === `iris_open_${user.id}` && e.newValue) {
        setIsIrisOpen(JSON.parse(e.newValue));
      }
      
      if (e.key === `iris_context_${user.id}` && e.newValue) {
        const context = JSON.parse(e.newValue);
        setCurrentPropertyId(context.propertyId);
        setCurrentBoardId(context.boardId);
      }
      
      if (e.key === `iris_session_${user.id}` && e.newValue) {
        setSessionData(JSON.parse(e.newValue));
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  };

  const clearAllState = () => {
    setIsIrisOpen(false);
    setCurrentPropertyId(undefined);
    setCurrentBoardId(undefined);
    setSessionData(null);
  };

  const setPropertyContext = (propertyId: string) => {
    setCurrentPropertyId(propertyId);
    setCurrentBoardId(undefined); // Clear board context when setting property
    persistContext({ propertyId, boardId: undefined });
  };

  const setBoardContext = (boardId: string) => {
    setCurrentBoardId(boardId);
    setCurrentPropertyId(undefined); // Clear property context when setting board
    persistContext({ propertyId: undefined, boardId });
  };

  const clearContext = () => {
    setCurrentPropertyId(undefined);
    setCurrentBoardId(undefined);
    persistContext({ propertyId: undefined, boardId: undefined });
  };

  const persistContext = (context: { propertyId?: string; boardId?: string }) => {
    if (!user) return;
    
    try {
      localStorage.setItem(`iris_context_${user.id}`, JSON.stringify(context));
    } catch (error) {
      console.error('Error persisting IRIS context:', error);
    }
  };

  const handleSetIsIrisOpen = (open: boolean) => {
    setIsIrisOpen(open);
    
    if (user) {
      try {
        localStorage.setItem(`iris_open_${user.id}`, JSON.stringify(open));
      } catch (error) {
        console.error('Error persisting IRIS open state:', error);
      }
    }
  };

  const updateSession = (data: any) => {
    setSessionData(data);
    
    if (user) {
      try {
        localStorage.setItem(`iris_session_${user.id}`, JSON.stringify(data));
      } catch (error) {
        console.error('Error persisting IRIS session:', error);
      }
    }
  };

  const value: IrisContextType = {
    isIrisOpen,
    setIsIrisOpen: handleSetIsIrisOpen,
    currentPropertyId,
    currentBoardId,
    setPropertyContext,
    setBoardContext,
    clearContext,
    sessionData,
    updateSession
  };

  return (
    <IrisContext.Provider value={value}>
      {children}
    </IrisContext.Provider>
  );
};

export const useIris = (): IrisContextType => {
  const context = useContext(IrisContext);
  if (!context) {
    throw new Error('useIris must be used within an IrisProvider');
  }
  return context;
};