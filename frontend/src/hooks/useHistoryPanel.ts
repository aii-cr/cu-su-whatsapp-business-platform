/**
 * Hook to access history panel state from any component within the conversation layout
 */

import { createContext, useContext } from 'react';

interface HistoryPanelContextType {
  isHistoryVisible: boolean;
  setHistoryVisible: (visible: boolean) => void;
}

export const HistoryPanelContext = createContext<HistoryPanelContextType>({
  isHistoryVisible: true,
  setHistoryVisible: () => {},
});

export const useHistoryPanel = () => {
  return useContext(HistoryPanelContext);
};





