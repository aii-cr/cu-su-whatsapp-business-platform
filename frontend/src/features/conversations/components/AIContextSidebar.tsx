/**
 * AI Context Sidebar Component
 * Responsive sidebar for AI context that can be toggled on larger screens
 * and displayed as a modal on mobile devices
 */

'use client';

import React from 'react';
import { Button } from '@/components/ui/Button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog';
import { ConversationContext } from './ConversationContext';
import { useAIContext } from '../context/AIContextProvider';
import { 
  CpuChipIcon
} from '@heroicons/react/24/outline';
import styles from './AIContextSidebar.module.scss';

interface AIContextSidebarProps {
  conversationId: string;
  className?: string;
}

export const AIContextSidebar: React.FC<AIContextSidebarProps> = ({
  conversationId,
  className = ''
}) => {
  const {
    isModalOpen,
    closeModal,
  } = useAIContext();

  return (
    <>
      {/* Modal */}
      <Dialog open={isModalOpen} onOpenChange={closeModal}>
        <DialogContent className={styles.modalContent}>
          <div className={styles.modalBody}>
            <ConversationContext 
              conversationId={conversationId}
              variant="modal"
            />
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
