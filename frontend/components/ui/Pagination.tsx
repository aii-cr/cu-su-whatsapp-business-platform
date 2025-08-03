/**
 * Reusable pagination component with optional chaining for safety.
 */

import * as React from 'react';
import { Button } from './Button';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
  disabled?: boolean;
  showInfo?: boolean;
  className?: string;
}

const Pagination = React.forwardRef<HTMLDivElement, PaginationProps>(
  ({ 
    currentPage, 
    totalPages, 
    totalItems, 
    itemsPerPage, 
    onPageChange, 
    disabled = false,
    showInfo = true,
    className = '' 
  }, ref) => {
    const startItem = Math.max(1, (currentPage - 1) * itemsPerPage + 1);
    const endItem = Math.min(currentPage * itemsPerPage, totalItems);
    
    const hasPrev = currentPage > 1;
    const hasNext = currentPage < totalPages;

    return (
      <div 
        ref={ref}
        className={`flex items-center justify-between ${className}`}
      >
        {showInfo && (
          <p className="text-sm text-muted-foreground">
            Showing {startItem} to {endItem} of {totalItems} items
          </p>
        )}
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            disabled={disabled || !hasPrev}
            onClick={() => onPageChange(currentPage - 1)}
            className="flex items-center"
          >
            <ChevronLeftIcon className="w-4 h-4 mr-1" />
            Previous
          </Button>
          
          <span className="text-sm text-muted-foreground px-2">
            Page {currentPage} of {totalPages}
          </span>
          
          <Button
            variant="outline"
            size="sm"
            disabled={disabled || !hasNext}
            onClick={() => onPageChange(currentPage + 1)}
            className="flex items-center"
          >
            Next
            <ChevronRightIcon className="w-4 h-4 ml-1" />
          </Button>
        </div>
      </div>
    );
  }
);
Pagination.displayName = 'Pagination';

export { Pagination };