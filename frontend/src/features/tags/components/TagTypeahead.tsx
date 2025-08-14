/**
 * Professional TagTypeahead component inspired by ClickUp
 * Features: Search suggestions, create new tags, light/dark theme support
 */

import * as React from 'react';
import { Search, Plus, X, Tag as TagIcon, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import { TagSummary } from '../models/tag';
import { TagChip } from './TagChip';
import { useTagSuggestions } from '../hooks/useTagSuggestions';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';

export interface TagTypeaheadProps {
  selectedTags: TagSummary[];
  onTagsChange: (tags: TagSummary[]) => void;
  excludeTagIds?: string[];
  maxTags?: number;
  placeholder?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onNewTagCreated?: (tag: TagSummary) => void;
  disabled?: boolean;
}

export function TagTypeahead({
  selectedTags,
  onTagsChange,
  excludeTagIds = [],
  maxTags = 10,
  placeholder = "Search or create tags...",
  size = 'md',
  className,
  onNewTagCreated,
  disabled = false,
}: TagTypeaheadProps) {
  const [query, setQuery] = React.useState('');
  const [isOpen, setIsOpen] = React.useState(false);
  const [showCreateForm, setShowCreateForm] = React.useState(false);
  const [createFormData, setCreateFormData] = React.useState({
    name: '',
    color: '#2563eb'
  });

  const inputRef = React.useRef<HTMLInputElement>(null);
  const dropdownRef = React.useRef<HTMLDivElement>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Debounce query for API calls
  const [debouncedQuery, setDebouncedQuery] = React.useState('');
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  // Get tag suggestions
  const {
    data: suggestionsResponse,
    isLoading: isSuggestionsLoading,
    error: suggestionsError,
  } = useTagSuggestions({
    query: debouncedQuery,
    excludeIds: excludeTagIds,
    limit: 10,
    enabled: !disabled && isOpen,
  });

  const suggestions = suggestionsResponse?.suggestions || [];
  const isPopular = !debouncedQuery.trim();

  // Logic checks
  const queryLength = query.trim().length;
  const hasExactMatch = suggestions.some(tag => 
    tag.name.toLowerCase() === query.trim().toLowerCase()
  );
  const canCreateNew = queryLength >= 2 && !hasExactMatch && !showCreateForm;

  // Handle input focus/blur
  const handleInputFocus = React.useCallback(() => {
    if (!disabled) {
      setIsOpen(true);
    }
  }, [disabled]);

  const handleInputBlur = React.useCallback((e: React.FocusEvent) => {
    // Check if the focus is moving to the dropdown
    if (dropdownRef.current?.contains(e.relatedTarget as Node)) {
      return;
    }
    // Small delay to allow for dropdown clicks
    setTimeout(() => {
      setIsOpen(false);
      setShowCreateForm(false);
    }, 150);
  }, []);

  // Handle tag selection
  const handleTagSelect = React.useCallback((tag: TagSummary) => {
    if (selectedTags.length >= maxTags) {
      return;
    }
    
    if (!selectedTags.find(t => t.id === tag.id)) {
      onTagsChange([...selectedTags, tag]);
    }
    
    setQuery('');
    setIsOpen(false);
    setShowCreateForm(false);
    inputRef.current?.focus();
  }, [selectedTags, maxTags, onTagsChange]);

  // Handle tag removal from selection
  const handleRemoveSelectedTag = React.useCallback((tagId: string) => {
    onTagsChange(selectedTags.filter(t => t.id !== tagId));
  }, [selectedTags, onTagsChange]);

  // Handle new tag creation
  const handleCreateTag = React.useCallback(async () => {
    if (!createFormData.name.trim()) return;

    try {
      const newTag: TagSummary = {
        id: `temp-${Date.now()}`,
        name: createFormData.name.trim(),
        slug: createFormData.name.trim().toLowerCase().replace(/\s+/g, '-'),
        display_name: createFormData.name.trim(),
        category: 'general',
        color: createFormData.color,
        usage_count: 0,
      };
      
      onNewTagCreated?.(newTag);
      setShowCreateForm(false);
      setCreateFormData({ name: '', color: '#2563eb' });
      setQuery('');
      setIsOpen(false);
    } catch (error) {
      console.error('Failed to create tag:', error);
    }
  }, [createFormData, onNewTagCreated]);

  // Handle input change
  const handleInputChange = React.useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    
    if (value.trim()) {
      setIsOpen(true);
      setShowCreateForm(false);
    } else {
      setIsOpen(true);
      setShowCreateForm(false);
    }
  }, []);

  // Handle clear input
  const handleClearInput = React.useCallback(() => {
    setQuery('');
    setIsOpen(true);
    setShowCreateForm(false);
    inputRef.current?.focus();
  }, []);

  // Handle keyboard navigation
  const handleKeyDown = React.useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      setShowCreateForm(false);
      inputRef.current?.blur();
    } else if (e.key === 'Enter' && !showCreateForm) {
      e.preventDefault();
      if (canCreateNew) {
        setCreateFormData(prev => ({ ...prev, name: query.trim() }));
        setShowCreateForm(true);
      }
    }
  }, [query, canCreateNew, showCreateForm]);

  // Size classes
  const sizeClasses = {
    sm: {
      input: 'h-8 text-sm',
      chip: 'text-xs px-1.5 py-0.5',
      dropdown: 'text-sm',
    },
    md: {
      input: 'h-10 text-sm',
      chip: 'text-sm px-2 py-1',
      dropdown: 'text-sm',
    },
    lg: {
      input: 'h-12 text-base',
      chip: 'text-base px-3 py-1.5',
      dropdown: 'text-base',
    },
  };

  const currentSize = sizeClasses[size];

  // Tag colors for creation
  const tagColors = [
    '#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d',
    '#ea580c', '#be185d', '#7c2d12', '#1e40af', '#991b1b', '#166534', '#92400e', '#581c87',
  ];

  return (
    <div ref={containerRef} className={cn('relative w-full', className)}>
      {/* Selected tags display */}
      {selectedTags.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {selectedTags.map((tag) => (
            <div
              key={tag.id}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary/10 text-primary text-sm border border-primary/20"
            >
              <div 
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: tag.color }}
              />
              <span className="font-medium">{tag.display_name || tag.name}</span>
              <button
                type="button"
                onClick={() => handleRemoveSelectedTag(tag.id)}
                className="hover:bg-primary/20 rounded-full p-0.5 transition-colors ml-1"
                aria-label={`Remove ${tag.display_name || tag.name}`}
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input container */}
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            onBlur={handleInputBlur}
            onKeyDown={handleKeyDown}
            placeholder={selectedTags.length >= maxTags ? "Maximum tags reached" : placeholder}
            disabled={disabled || selectedTags.length >= maxTags}
            className={cn(
              'w-full pl-10 pr-10',
              currentSize.input
            )}
          />
          {query && (
            <button
              type="button"
              onClick={handleClearInput}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Clear input"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Dropdown */}
        {isOpen && (
          <div
            ref={dropdownRef}
            className="absolute z-[9999] w-full mt-2 bg-background border border-border rounded-lg shadow-lg max-h-80 overflow-hidden"
            style={{ 
              position: 'absolute',
              top: '100%',
              left: 0,
              right: 0,
              zIndex: 99999,
              maxHeight: '20rem',
            }}
          >
            {/* Loading state */}
            {isSuggestionsLoading && (
              <div className="flex items-center justify-center py-6">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
                <span className="ml-3 text-sm text-muted-foreground">Loading suggestions...</span>
              </div>
            )}

            {/* Error state */}
            {suggestionsError && (
              <div className="px-4 py-3 text-sm text-destructive bg-destructive/10 border-b border-border">
                Error loading suggestions. Please try again.
              </div>
            )}

            {/* Content */}
            {!isSuggestionsLoading && !suggestionsError && (
              <div className="max-h-80 overflow-y-auto">
                {/* Header */}
                {suggestions.length > 0 && (
                  <div className="px-4 py-2 text-xs font-medium text-muted-foreground border-b border-border bg-muted/30">
                    {isPopular ? 'Popular Tags' : `Search Results (${suggestions.length})`}
                  </div>
                )}
                
                {/* Tag suggestions */}
                {suggestions.map((tag) => (
                  <button
                    key={tag.id}
                    type="button"
                    onClick={() => handleTagSelect(tag)}
                    className="w-full px-4 py-3 text-left hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none flex items-center gap-3 transition-colors border-b border-border/50 last:border-b-0"
                  >
                    <div 
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: tag.color }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{tag.display_name || tag.name}</div>
                      {tag.category && (
                        <div className="text-xs text-muted-foreground capitalize">{tag.category}</div>
                      )}
                    </div>
                    <Check className="h-4 w-4 text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                ))}
                
                {/* Create new tag option */}
                {canCreateNew && (
                  <button
                    type="button"
                    onClick={() => {
                      setCreateFormData(prev => ({ ...prev, name: query.trim() }));
                      setShowCreateForm(true);
                    }}
                    className="w-full px-4 py-3 text-left hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none flex items-center gap-3 border-t border-border transition-colors"
                  >
                    <Plus className="h-4 w-4 text-muted-foreground" />
                    <div className="flex-1">
                      <div className="font-medium">Create "{query.trim()}"</div>
                      <div className="text-xs text-muted-foreground">New tag</div>
                    </div>
                  </button>
                )}
                
                {/* Create tag form */}
                {showCreateForm && (
                  <div className="border-t border-border p-4 bg-muted/20">
                    <div className="space-y-4">
                      <div className="flex items-center gap-2">
                        <Plus className="h-4 w-4 text-primary" />
                        <span className="font-medium text-sm">Create new tag</span>
                      </div>
                      
                      <div className="space-y-3">
                        <div>
                          <label className="text-xs font-medium text-muted-foreground mb-1 block">
                            Tag Name
                          </label>
                          <Input
                            type="text"
                            value={createFormData.name}
                            onChange={(e) => setCreateFormData(prev => ({ ...prev, name: e.target.value }))}
                            placeholder="Enter tag name"
                            maxLength={40}
                            className="text-sm"
                            autoFocus
                          />
                        </div>
                        
                        <div>
                          <label className="text-xs font-medium text-muted-foreground mb-2 block">
                            Color
                          </label>
                          <div className="grid grid-cols-8 gap-1">
                            {tagColors.map((color) => (
                              <button
                                key={color}
                                type="button"
                                onClick={() => setCreateFormData(prev => ({ ...prev, color }))}
                                className={cn(
                                  'w-6 h-6 rounded-full border-2 transition-all',
                                  createFormData.color === color
                                    ? 'border-foreground scale-110'
                                    : 'border-transparent hover:scale-105'
                                )}
                                style={{ backgroundColor: color }}
                                aria-label={`Select color ${color}`}
                              />
                            ))}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex gap-2 pt-2">
                        <Button
                          type="button"
                          size="sm"
                          onClick={handleCreateTag}
                          disabled={!createFormData.name.trim()}
                          className="flex-1"
                        >
                          Create & Add
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setShowCreateForm(false);
                            setCreateFormData({ name: '', color: '#2563eb' });
                          }}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Helpful tip */}
                {isPopular && suggestions.length > 0 && (
                  <div className="px-4 py-2 text-xs text-muted-foreground border-t border-border bg-muted/30">
                    💡 Type to search or create new tags
                  </div>
                )}
                
                {/* No results */}
                {!isPopular && suggestions.length === 0 && query.trim() && (
                  <div className="px-4 py-6 text-center text-sm text-muted-foreground">
                    <TagIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No tags found for "{query.trim()}"</p>
                    <p className="text-xs mt-1">Try a different search term or create a new tag</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default TagTypeahead;
