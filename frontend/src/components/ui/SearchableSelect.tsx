/**
 * Searchable Select component with server-side search functionality.
 * Used for agent selection in conversation filters.
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { ChevronDownIcon, MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { cn } from '@/lib/utils';

export interface SearchableSelectOption {
  value: string;
  label: string;
  email?: string;
  [key: string]: any;
}

interface SearchableSelectProps {
  options: SearchableSelectOption[];
  value?: string;
  onChange: (value: string) => void;
  onSearch: (searchTerm: string) => void;
  placeholder?: string;
  label?: string;
  disabled?: boolean;
  loading?: boolean;
  className?: string;
  searchPlaceholder?: string;
  noOptionsMessage?: string;
  maxHeight?: string;
}

export function SearchableSelect({
  options,
  value,
  onChange,
  onSearch,
  placeholder = "Select an option...",
  label,
  disabled = false,
  loading = false,
  className,
  searchPlaceholder = "Search...",
  noOptionsMessage = "No options found",
  maxHeight = "200px"
}: SearchableSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const selectedOption = options.find(option => option.value === value);

  // Handle keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightedIndex(prev => 
            prev < options.length - 1 ? prev + 1 : 0
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex(prev => 
            prev > 0 ? prev - 1 : options.length - 1
          );
          break;
        case 'Enter':
          e.preventDefault();
          if (highlightedIndex >= 0 && options[highlightedIndex]) {
            handleSelect(options[highlightedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          setIsOpen(false);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, options, highlightedIndex]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when opening
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  const handleSelect = (option: SearchableSelectOption) => {
    onChange(option.value);
    setIsOpen(false);
    setSearchTerm('');
    setHighlightedIndex(-1);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newSearchTerm = e.target.value;
    setSearchTerm(newSearchTerm);
    onSearch(newSearchTerm);
    setHighlightedIndex(-1);
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange('');
    setSearchTerm('');
    setHighlightedIndex(-1);
  };

  const toggleDropdown = () => {
    if (!disabled) {
      setIsOpen(!isOpen);
      if (!isOpen) {
        setSearchTerm('');
        setHighlightedIndex(-1);
      }
    }
  };

  return (
    <div className={cn("relative", className)} ref={containerRef}>
      {label && (
        <label className="text-sm font-medium text-foreground mb-1 block">
          {label}
        </label>
      )}
      
      <div className="relative">
        <button
          type="button"
          onClick={toggleDropdown}
          disabled={disabled}
          className={cn(
            "w-full flex items-center justify-between px-3 py-2 text-left",
            "border border-border rounded-md bg-background",
            "focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "hover:border-primary/50 transition-colors"
          )}
        >
          <span className={cn(
            "truncate",
            !selectedOption && "text-muted-foreground"
          )}>
            {selectedOption ? selectedOption.label : placeholder}
          </span>
          
          <div className="flex items-center gap-1">
            {value && (
              <div
                role="button"
                tabIndex={0}
                onClick={handleClear}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleClear(e as any);
                  }
                }}
                className="p-1 hover:bg-muted rounded-sm cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary"
                aria-label="Clear selection"
              >
                <XMarkIcon className="w-3 h-3" />
              </div>
            )}
            <ChevronDownIcon 
              className={cn(
                "w-4 h-4 transition-transform",
                isOpen && "rotate-180"
              )} 
            />
          </div>
        </button>
      </div>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-background border border-border rounded-md shadow-lg">
          {/* Search input */}
          <div className="p-2 border-b border-border">
            <div className="relative">
              <MagnifyingGlassIcon className="w-4 h-4 absolute left-2 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchTerm}
                onChange={handleSearchChange}
                placeholder={searchPlaceholder}
                className="w-full pl-8 pr-2 py-1 text-sm border border-border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
          </div>

          {/* Options list */}
          <div 
            className="overflow-y-auto"
            style={{ maxHeight }}
          >
            {loading ? (
              <div className="p-3 text-center text-sm text-muted-foreground">
                Searching...
              </div>
            ) : options.length === 0 ? (
              <div className="p-3 text-center text-sm text-muted-foreground">
                {noOptionsMessage}
              </div>
            ) : (
              options.map((option, index) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleSelect(option)}
                  className={cn(
                    "w-full text-left px-3 py-2 text-sm hover:bg-muted transition-colors",
                    "focus:outline-none focus:bg-muted",
                    highlightedIndex === index && "bg-muted",
                    option.value === value && "bg-primary/10 text-primary"
                  )}
                >
                  <div className="font-medium">{option.label}</div>
                  {option.email && (
                    <div className="text-xs text-muted-foreground truncate">
                      {option.email}
                    </div>
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
