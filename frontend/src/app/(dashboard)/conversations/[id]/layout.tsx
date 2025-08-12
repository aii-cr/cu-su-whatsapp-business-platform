'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { ClockIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { HistoryPanelContext } from '@/hooks/useHistoryPanel';

export default function ConversationLayout({
  children,
  side,
}: {
  children: React.ReactNode;
  side: React.ReactNode;
}) {
  const [showHistoryMobile, setShowHistoryMobile] = useState(false);
  const [isHistoryVisible, setHistoryVisible] = useState(true);

  return (
    <HistoryPanelContext.Provider value={{ isHistoryVisible, setHistoryVisible }}>
      <div className={`h-[calc(100vh-4rem)] grid grid-cols-1 gap-0 relative transition-all duration-300 ${
        isHistoryVisible ? 'xl:grid-cols-[1fr_360px]' : 'xl:grid-cols-1'
      }`}>
        {/* Main conversation area */}
        <div className="min-h-0 overflow-hidden relative">
          {children}
          
          {/* Mobile history toggle button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowHistoryMobile(true)}
            className="xl:hidden fixed bottom-20 right-4 z-30 shadow-lg bg-background border-border"
          >
            <ClockIcon className="w-4 h-4 mr-2" />
            History
          </Button>
        </div>
        
        {/* Desktop sidebar - conditionally rendered */}
        {isHistoryVisible && (
          <aside className="hidden xl:block min-h-0 overflow-hidden border-l border-border bg-surface transition-all duration-300">
            <div className="h-full overflow-y-auto p-3">
              {side}
            </div>
          </aside>
        )}
        
        {/* Mobile history overlay */}
        {showHistoryMobile && (
          <div className="xl:hidden fixed inset-0 z-50 bg-black/50">
            <div className="absolute right-0 top-0 h-full w-full max-w-sm bg-surface border-l border-border">
              <div className="flex items-center justify-between p-4 border-b border-border">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <ClockIcon className="w-5 h-5 text-primary" />
                  History Timeline
                </h2>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowHistoryMobile(false)}
                >
                  <XMarkIcon className="w-5 h-5" />
                </Button>
              </div>
              <div className="p-3 h-[calc(100%-80px)] overflow-y-auto">
                {side}
              </div>
            </div>
          </div>
        )}
      </div>
    </HistoryPanelContext.Provider>
  );
}


