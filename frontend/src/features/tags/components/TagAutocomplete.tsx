/**
 * TagAutocomplete component - searchable tag selector with create functionality
 * Supports keyboard navigation, debounced search, and RBAC
 */

import * as React from 'react';
import { Search, Plus, Loader2, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useDebounce } from '@/hooks/useDebounce';
import { TagSummary, TagCreate, TagCategory, TagColor } from '../models/tag';
import { useTagSuggestions, useCreateTag } from '../hooks/useTags';
import { TagChip } from './TagChip';

export interface TagAutocompleteProps {
  selectedTags: TagSummary[];
  onTagsChange: (tags: TagSummary[]) => void;
  onTagCreate?: (tagData: TagCreate) => Promise<TagSummary>;
  placeholder?: string;
  disabled?: boolean;
  maxTags?: number;
  allowCreate?: boolean;
  categoryFilter?: TagCategory;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function TagAutocomplete({
  selectedTags,
  onTagsChange,
  onTagCreate,
  placeholder = "Search tags...",
  disabled = false,
  maxTags,
  allowCreate = true,
  categoryFilter,
  size = 'md',
  className,
}: TagAutocompleteProps) {
  const [query, setQuery] = React.useState('');
  const [isOpen, setIsOpen] = React.useState(false);
  const [highlightedIndex, setHighlightedIndex] = React.useState(-1);
  const [isCreating, setIsCreating] = React.useState(false);
  
  const debouncedQuery = useDebounce(query, 300);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const listRef = React.useRef<HTMLUListElement>(null);
  
  const createTagMutation = useCreateTag();
  
  // Get tag suggestions
  const excludeIds = selectedTags.map(tag => tag.id);
  const { 
    data: suggestions, 
    isLoading: isLoadingSuggestions,
    error: suggestionsError 
  } = useTagSuggestions(
    {
      query: debouncedQuery,
      category: categoryFilter,
      limit: 10,
      exclude_ids: excludeIds,
    },
    debouncedQuery.length > 0 && isOpen
  );

  const availableSuggestions = suggestions?.tags || [];
  const canCreateNew = allowCreate && 
    debouncedQuery.length > 0 && 
    !availableSuggestions.some(tag => tag.name.toLowerCase() === debouncedQuery.toLowerCase()) &&
    !selectedTags.some(tag => tag.name.toLowerCase() === debouncedQuery.toLowerCase());

  const allOptions = [
    ...availableSuggestions,
    ...(canCreateNew ? [{ 
      id: '__create_new__', 
      name: `Create "${debouncedQuery}"`,
      slug: '',
      category: categoryFilter || TagCategory.GENERAL,
      color: TagColor.BLUE,
      usage_count: 0,
      isCreateOption: true 
    } as TagSummary & { isCreateOption: boolean }] : [])
  ];

  // Handle tag selection
  const handleTagSelect = React.useCallback(async (tag: TagSummary & { isCreateOption?: boolean }) => {
    if (disabled || (maxTags && selectedTags.length >= maxTags)) return;

    if (tag.isCreateOption) {
      if (!onTagCreate && !createTagMutation) return;
      
      try {
        setIsCreating(true);
        
        const newTagData: TagCreate = {
          name: debouncedQuery,
          category: categoryFilter || TagCategory.GENERAL,
          color: TagColor.BLUE,
        };

        let newTag: TagSummary;
        if (onTagCreate) {
          newTag = await onTagCreate(newTagData);
        } else {
          const createdTag = await createTagMutation.mutateAsync(newTagData);
          newTag = {
            id: createdTag.id,
            name: createdTag.name,
            slug: createdTag.slug,
            display_name: createdTag.display_name,
            category: createdTag.category,
            color: createdTag.color,
            usage_count: createdTag.usage_count,
          };
        }
        
        onTagsChange([...selectedTags, newTag]);
      } catch (error) {
        console.error('Failed to create tag:', error);
      } finally {
        setIsCreating(false);
      }
    } else {
      onTagsChange([...selectedTags, tag]);
    }

    setQuery('');
    setIsOpen(false);
    setHighlightedIndex(-1);
    inputRef.current?.focus();
  }, [
    disabled, 
    maxTags, 
    selectedTags, 
    onTagCreate, 
    createTagMutation, 
    categoryFilter, 
    debouncedQuery, 
    onTagsChange
  ]);

  // Handle tag removal
  const handleTagRemove = React.useCallback((tagToRemove: TagSummary) => {
    if (disabled) return;
    
    onTagsChange(selectedTags.filter(tag => tag.id !== tagToRemove.id));
    inputRef.current?.focus();
  }, [disabled, selectedTags, onTagsChange]);

  // Keyboard navigation
  const handleKeyDown = React.useCallback((e: React.KeyboardEvent) => {
    if (disabled) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex(prev => 
            prev < allOptions.length - 1 ? prev + 1 : 0
          );
        }
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        if (isOpen) {
          setHighlightedIndex(prev => 
            prev > 0 ? prev - 1 : allOptions.length - 1
          );
        }
        break;
        
      case 'Enter':
        e.preventDefault();
        if (isOpen && highlightedIndex >= 0 && allOptions[highlightedIndex]) {
          handleTagSelect(allOptions[highlightedIndex] as any);
        } else if (canCreateNew && debouncedQuery.length > 0) {
          handleTagSelect({ 
            id: '__create_new__', 
            name: `Create "${debouncedQuery}"`,
            isCreateOption: true 
          } as any);
        }
        break;
        
      case 'Escape':
        setIsOpen(false);
        setHighlightedIndex(-1);
        inputRef.current?.blur();
        break;
        
      case 'Backspace':
        if (query === '' && selectedTags.length > 0) {
          e.preventDefault();
          handleTagRemove(selectedTags[selectedTags.length - 1]);
        }
        break;
    }
  }, [
    disabled, 
    isOpen, 
    highlightedIndex, 
    allOptions, 
    canCreateNew, 
    debouncedQuery, 
    query, 
    selectedTags, 
    handleTagSelect, 
    handleTagRemove
  ]);

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (inputRef.current && !inputRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Reset highlighted index when suggestions change
  React.useEffect(() => {
    setHighlightedIndex(-1);
  }, [allOptions.length]);

  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  };

  const inputSizeClasses = {
    sm: 'h-8 px-3',
    md: 'h-10 px-4',
    lg: 'h-12 px-5',
  };

  return (
    <div className={cn('relative w-full', className)}>
      {/* Input area with selected tags */}
      <div
        className={cn(
          'flex flex-wrap items-center gap-2 rounded-lg border border-border bg-background transition-colors',
          'focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2',
          disabled && 'opacity-50 cursor-not-allowed',
          inputSizeClasses[size],
          'min-h-[2.5rem]', // Ensure minimum height
          'p-2'
        )}
      >
        {/* Selected tags */}
        {selectedTags.map((tag) => (
          <TagChip
            key={tag.id}
            tag={tag}
            size={size === 'lg' ? 'md' : 'sm'}
            removable
            onRemove={() => handleTagRemove(tag)}
            disabled={disabled}
          />
        ))}
        
        {/* Input */}
        <div className="flex items-center flex-1 min-w-[120px]">
          <Search className={cn(
            'text-muted-foreground mr-2 flex-shrink-0',
            size === 'sm' ? 'h-3 w-3' : size === 'lg' ? 'h-5 w-5' : 'h-4 w-4'
          )} />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
            onKeyDown={handleKeyDown}
            placeholder={selectedTags.length === 0 ? placeholder : ''}
            disabled={disabled || (maxTags ? selectedTags.length >= maxTags : false)}
            className={cn(
              'flex-1 bg-transparent outline-none placeholder:text-muted-foreground',
              sizeClasses[size],
              disabled && 'cursor-not-allowed'
            )}
          />
          
          {(isLoadingSuggestions || isCreating) && (
            <Loader2 className={cn(
              'animate-spin text-muted-foreground ml-2',
              size === 'sm' ? 'h-3 w-3' : size === 'lg' ? 'h-5 w-5' : 'h-4 w-4'
            )} />
          )}
        </div>
      </div>

      {/* Dropdown with suggestions */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 z-50 mt-1 max-h-60 overflow-auto rounded-lg border border-border bg-popover shadow-lg">
          {suggestionsError ? (
            <div className="px-4 py-3 text-sm text-destructive">
              Failed to load suggestions
            </div>
          ) : allOptions.length === 0 && !isLoadingSuggestions ? (
            <div className="px-4 py-3 text-sm text-muted-foreground">
              {debouncedQuery ? 'No tags found' : 'Start typing to search tags'}
            </div>
          ) : (
            <ul ref={listRef} className="py-1">
              {allOptions.map((option, index) => (
                <li key={option.id}>
                  <button
                    type="button"
                    className={cn(
                      'w-full px-4 py-2 text-left transition-colors hover:bg-accent hover:text-accent-foreground focus:outline-none',
                      index === highlightedIndex && 'bg-accent text-accent-foreground',
                      sizeClasses[size]
                    )}
                    onClick={() => handleTagSelect(option as any)}
                    disabled={disabled || isCreating}
                  >
                    {(option as any).isCreateOption ? (
                      <div className="flex items-center gap-2">
                        <Plus className="h-4 w-4 text-muted-foreground" />
                        <span>{option.name}</span>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div
                            className={cn(
                              'h-3 w-3 rounded-full border',
                              `bg-${option.color}-100 border-${option.color}-300`
                            )}
                          />
                          <span>{option.display_name || option.name}</span>
                        </div>
                        {option.usage_count > 0 && (
                          <span className="text-xs text-muted-foreground">
                            {option.usage_count}
                          </span>
                        )}
                      </div>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}



