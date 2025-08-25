'use client';

/**
 * Dialog component for modal interactions.
 * Built on top of Headless UI for accessibility.
 */

import React, { Fragment, ReactNode } from 'react';
import { Dialog as HeadlessDialog, Transition } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';
import { Button } from './Button';

interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: ReactNode;
  className?: string;
}

// Dialog context for compound components
interface DialogContextValue {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const DialogContext = React.createContext<DialogContextValue | undefined>(undefined);

const useDialogContext = () => {
  const context = React.useContext(DialogContext);
  if (!context) {
    throw new Error('Dialog compound components must be used within Dialog');
  }
  return context;
};

// Main Dialog component for compound usage
interface DialogRootProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
}

const Dialog: React.FC<DialogRootProps> = ({ open, onOpenChange, children }) => {
  return (
    <DialogContext.Provider value={{ open, onOpenChange }}>
      <Transition appear show={open} as={Fragment}>
        <HeadlessDialog as="div" className="relative z-50" onClose={() => onOpenChange(false)}>
          {children}
        </HeadlessDialog>
      </Transition>
    </DialogContext.Provider>
  );
};

// DialogContent component
interface DialogContentProps {
  children: ReactNode;
  className?: string;
}

const DialogContent: React.FC<DialogContentProps> = ({ children, className }) => {
  return (
    <>
      <Transition.Child
        as={Fragment}
        enter="ease-out duration-300"
        enterFrom="opacity-0"
        enterTo="opacity-100"
        leave="ease-in duration-200"
        leaveFrom="opacity-100"
        leaveTo="opacity-0"
      >
        <div className="fixed inset-0 bg-black bg-opacity-25" />
      </Transition.Child>

      <div className="fixed inset-0 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4 text-center">
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <HeadlessDialog.Panel
              className={cn(
                'w-full max-w-md transform overflow-hidden rounded-lg bg-background border border-border p-6 text-left align-middle shadow-xl transition-all',
                className
              )}
            >
              {children}
            </HeadlessDialog.Panel>
          </Transition.Child>
        </div>
      </div>
    </>
  );
};

// DialogHeader component
interface DialogHeaderProps {
  children: ReactNode;
  className?: string;
}

const DialogHeader: React.FC<DialogHeaderProps> = ({ children, className }) => {
  return (
    <div className={cn('flex flex-col space-y-1.5 text-center sm:text-left', className)}>
      {children}
    </div>
  );
};

// DialogTitle component
interface DialogTitleProps {
  children: ReactNode;
  className?: string;
}

const DialogTitle: React.FC<DialogTitleProps> = ({ children, className }) => {
  return (
    <HeadlessDialog.Title
      as="h3"
      className={cn('text-lg font-semibold leading-none tracking-tight', className)}
    >
      {children}
    </HeadlessDialog.Title>
  );
};

// DialogDescription component
interface DialogDescriptionProps {
  children: ReactNode;
  className?: string;
}

const DialogDescription: React.FC<DialogDescriptionProps> = ({ children, className }) => {
  return (
    <HeadlessDialog.Description className={cn('text-sm text-muted-foreground', className)}>
      {children}
    </HeadlessDialog.Description>
  );
};

// Legacy Dialog component for backward compatibility
function LegacyDialog({
  isOpen,
  onClose,
  title,
  description,
  children,
  className
}: DialogProps) {
  return (
    <Transition appear show={isOpen} as={Fragment}>
      <HeadlessDialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <HeadlessDialog.Panel
                className={cn(
                  'w-full max-w-md transform overflow-hidden rounded-lg bg-surface p-6 text-left align-middle shadow-xl transition-all',
                  className
                )}
              >
                <div className="flex items-center justify-between mb-4">
                  <div>
                    {title && (
                      <HeadlessDialog.Title
                        as="h3"
                        className="text-lg font-medium leading-6 text-foreground"
                      >
                        {title}
                      </HeadlessDialog.Title>
                    )}
                    {description && (
                      <HeadlessDialog.Description className="text-sm text-muted-foreground mt-1">
                        {description}
                      </HeadlessDialog.Description>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={onClose}
                    className="h-8 w-8"
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </Button>
                </div>
                {children}
              </HeadlessDialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </HeadlessDialog>
    </Transition>
  );
}

export { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogDescription,
  LegacyDialog 
};