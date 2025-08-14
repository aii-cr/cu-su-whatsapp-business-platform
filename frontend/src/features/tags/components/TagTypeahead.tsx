/**
 * TagTypeahead component - autocomplete input for tag search and creation
 * Supports suggestion fetching, create-on-the-fly, color picker, and assigned tag management
 */

import * as React from 'react';
import { Search, Plus, Loader2, X, Tag } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { TagSummary, TagCreate, DEFAULT_TAG_COLORS, validateHexColor } from '../models/tag';
import { TagChip } from './TagChip';
import { TagColorPicker } from './TagColorPicker';
import { useTagSuggestions } from '../hooks/useTagSuggestions';
import { useCreateTag } from '../hooks/useTags';
import { useDebounce } from '@/hooks/useDebounce';

export interface TagTypeaheadProps {
  selectedTags: TagSummary[];
  onTagsChange: (tags: TagSummary[]) => void;
  excludeTagIds?: string[];
  maxTags?: number;
  placeholder?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onNewTagCreated?: (tag: TagSummary) => void | Promise<void>;
}

export function TagTypeahead({
  selectedTags,
  onTagsChange,
  excludeTagIds = [],
  maxTags,
  placeholder = "Search tags...",
  size = 'md',
  className,
  onNewTagCreated,
}: TagTypeaheadProps) {
  const [query, setQuery] = React.useState('');
  const [isOpen, setIsOpen] = React.useState(false);
  const [showCreateForm, setShowCreateForm] = React.useState(false);
  const [createFormData, setCreateFormData] = React.useState({
    name: '',
    color: DEFAULT_TAG_COLORS[0] as string,
  });

  const inputRef = React.useRef<HTMLInputElement>(null);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  // Debounce search query
  const debouncedQuery = useDebounce(query, 300);

  // Get tag suggestions or popular tags
  const {
    data: suggestionsResponse,
    isLoading: isSuggestionsLoading,
    error: suggestionsError,
  } = useTagSuggestions({
    query: debouncedQuery,
    excludeIds: [...excludeTagIds, ...selectedTags.map(t => t.id)],
    enabled: isOpen,
  });

  // Extract tags and check if it's popular tags
  const suggestions = suggestionsResponse?.suggestions || [];
  const isPopular = !query.trim(); // If no query, show popular tags

  // Create tag mutation
  const createTagMutation = useCreateTag();

  // Handle input change
  const handleInputChange = React.useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    setIsOpen(true); // Always open when typing
    setShowCreateForm(false);
  }, []);

  // Handle tag selection
  const handleTagSelect = React.useCallback((tag: TagSummary) => {
    const isAlreadySelected = selectedTags.some(t => t.id === tag.id);
    if (isAlreadySelected) return;

    if (maxTags && selectedTags.length >= maxTags) return;

    onTagsChange([...selectedTags, tag]);
    setQuery('');
    setIsOpen(false);
  }, [selectedTags, onTagsChange, maxTags]);

  // Handle tag removal
  const handleTagRemove = React.useCallback((tagId: string) => {
    onTagsChange(selectedTags.filter(t => t.id !== tagId));
  }, [selectedTags, onTagsChange]);

  // Handle create new tag
  const handleCreateTag = React.useCallback(async () => {
    if (!createFormData.name.trim()) return;

    try {
      const tagData: TagCreate = {
        name: createFormData.name.trim(),
        color: createFormData.color,
        category: 'general' as const,
      };

      const createdTag = await createTagMutation.mutateAsync(tagData);
      
      // Convert to TagSummary format
      const tagSummary: TagSummary = {
        id: createdTag.id,
        name: createdTag.name,
        slug: createdTag.slug,
        display_name: createdTag.display_name,
        category: createdTag.category,
        color: createdTag.color,
        usage_count: 0,
      };

      if (onNewTagCreated) {
        await onNewTagCreated(tagSummary);
      } else {
        handleTagSelect(tagSummary);
      }
      setShowCreateForm(false);
      setCreateFormData({ name: '', color: DEFAULT_TAG_COLORS[0] });
    } catch (error) {
      console.error('Failed to create tag:', error);
    }
  }, [createFormData, createTagMutation, handleTagSelect, onNewTagCreated]);

  // Handle keyboard navigation
  const handleKeyDown = React.useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      setShowCreateForm(false);
      inputRef.current?.blur();
    } else if (e.key === 'Enter' && !showCreateForm) {
      e.preventDefault();
      // If there's a query and no exact match, show create form
      if (query.trim() && !suggestions.some(tag => tag.name.toLowerCase() === query.toLowerCase())) {
        setCreateFormData(prev => ({ ...prev, name: query.trim() }));
        setShowCreateForm(true);
      }
    }
  }, [query, suggestions, showCreateForm]);

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setShowCreateForm(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus input when component mounts
  React.useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const hasExactMatch = suggestions?.some((tag: any) => 
    tag.name.toLowerCase() === query.toLowerCase()
  );

  const canCreateNew = query.trim().length > 0 && !hasExactMatch && query.trim().length <= 40;

  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-sm',
    lg: 'text-base',
  };

  return (
    <div className={cn('relative w-full', className)}>
      {/* Selected tags */}
      {selectedTags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {selectedTags.map((tag) => (
            <TagChip
              key={tag.id}
              tag={tag}
              size={size}
              variant="default"
              removable
              onRemove={() => handleTagRemove(tag.id)}
            />
          ))}
        </div>
      )}

      {/* Search input */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-muted-foreground" />
        </div>
        
        <Input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className={cn(
            'pl-10 pr-4',
            sizeClasses[size]
          )}
          disabled={maxTags ? selectedTags.length >= maxTags : false}
        />

        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              setIsOpen(false);
              inputRef.current?.focus();
            }}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 bg-popover border border-border rounded-md shadow-lg max-h-60 overflow-auto"
        >
          {showCreateForm ? (
            /* Create new tag form */
            <div className="p-4 space-y-4 border-b">
              <div className="flex items-center gap-2 text-sm font-medium">
                <Plus className="h-4 w-4" />
                Create new tag
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
                  <TagColorPicker
                    selectedColor={createFormData.color}
                    onColorChange={(color) => setCreateFormData(prev => ({ ...prev, color }))}
                    size="sm"
                  />
                </div>
              </div>
              
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  onClick={handleCreateTag}
                  disabled={!createFormData.name.trim() || createTagMutation.isPending}
                  className="flex-1"
                >
                  {createTagMutation.isPending ? (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin mr-1" />
                      Creating...
                    </>
                  ) : (
                    'Create & Add'
                  )}
                </Button>
                
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCreateForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            /* Suggestions list */
            <div className="py-1">
              {isSuggestionsLoading && (
                <div key="loading" className="flex items-center justify-center py-4">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  <span className="text-sm text-muted-foreground">
                    {query.trim() ? 'Searching...' : 'Loading popular tags...'}
                  </span>
                </div>
              )}
              
              {!isSuggestionsLoading && (
                <React.Fragment>
                  {/* Header for popular tags or search results */}
                  {suggestions.length > 0 && (
                    <div key="header" className="px-3 py-2 text-xs font-medium text-muted-foreground border-b">
                      {isPopular ? 'Popular Tags' : `Search Results (${suggestions.length})`}
                    </div>
                  )}
                  
                  {/* Tag suggestions */}
                  {suggestions.map((tag: any) => (
                    <button
                      key={tag.id}
                      type="button"
                      onClick={() => handleTagSelect(tag)}
                      className="w-full px-3 py-2 text-left hover:bg-accent focus:bg-accent focus:outline-none flex items-center gap-2"
                    >
                      <TagChip
                        tag={tag}
                        size="sm"
                        variant="outline"
                        className="pointer-events-none"
                      />
                      <span className="text-xs text-muted-foreground">
                        Used {tag.usage_count} times
                      </span>
                    </button>
                  ))}
                  
                  {/* No results message */}
                  {!isSuggestionsLoading && suggestions.length === 0 && query.trim() && (
                    <div key="no-results" className="px-3 py-3 text-sm text-muted-foreground text-center">
                      <Tag className="h-4 w-4 mx-auto mb-1 opacity-50" />
                      <p>No tags found for "{query.trim()}"</p>
                    </div>
                  )}

                  {/* Create new option - only show when searching and tag doesn't exist */}
                  {canCreateNew && query.trim() && (
                    <button
                      key="create-new"
                      type="button"
                      onClick={() => {
                        setCreateFormData(prev => ({ ...prev, name: query.trim() }));
                        setShowCreateForm(true);
                      }}
                      className="w-full px-3 py-3 text-left hover:bg-accent focus:bg-accent focus:outline-none flex items-center gap-2 border-t"
                    >
                      <Plus className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">Create new tag "{query.trim()}"</span>
                    </button>
                  )}
                  
                  {/* Helpful tip */}
                  {isPopular && suggestions.length > 0 && (
                    <div key="tip" className="px-3 py-2 text-xs text-muted-foreground border-t">
                      💡 Type to search or create new tags
                    </div>
                  )}
                </React.Fragment>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default TagTypeahead;
