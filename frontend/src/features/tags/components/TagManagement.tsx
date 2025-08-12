/**
 * TagManagement component - administrative interface for managing tags
 * Supports CRUD operations, filtering, and bulk actions
 */

import * as React from 'react';
import { Plus, Search, Filter, MoreHorizontal, Edit, Trash2, Eye, EyeOff } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Select } from '@/components/ui/Select';
import { Card } from '@/components/ui/Card';
import { 
  Tag, 
  TagCreate, 
  TagUpdate, 
  TagCategory, 
  TagStatus,
  formatTagCategory,
  getTagColorClasses,
  getTagDisplayName 
} from '../models/tag';
import { useTags, useCreateTag, useUpdateTag, useDeleteTag } from '../hooks/useTags';
import { TagChip } from './TagChip';

export interface TagManagementProps {
  className?: string;
}

export function TagManagement({ className }: TagManagementProps) {
  const [search, setSearch] = React.useState('');
  const [categoryFilter, setCategoryFilter] = React.useState<TagCategory | 'all'>('all');
  const [statusFilter, setStatusFilter] = React.useState<TagStatus | 'all'>('all');
  const [sortBy, setSortBy] = React.useState<'name' | 'usage_count' | 'created_at'>('name');
  const [sortOrder, setSortOrder] = React.useState<'asc' | 'desc'>('asc');
  const [page, setPage] = React.useState(0);
  const [editingTag, setEditingTag] = React.useState<Tag | null>(null);
  const [creatingTag, setCreatingTag] = React.useState(false);

  // Build query parameters
  const queryParams = React.useMemo(() => ({
    search: search || undefined,
    category: categoryFilter !== 'all' ? categoryFilter : undefined,
    status: statusFilter !== 'all' ? statusFilter : undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
    limit: 20,
    offset: page * 20,
  }), [search, categoryFilter, statusFilter, sortBy, sortOrder, page]);

  // Fetch tags
  const { data: tagsResponse, isLoading, error } = useTags(queryParams);
  const createTagMutation = useCreateTag();
  const updateTagMutation = useUpdateTag();
  const deleteTagMutation = useDeleteTag();

  const tags = tagsResponse?.tags || [];
  const total = tagsResponse?.total || 0;
  const hasMore = tagsResponse?.has_more || false;

  // Handle tag creation
  const handleCreateTag = React.useCallback(async (tagData: TagCreate) => {
    try {
      await createTagMutation.mutateAsync(tagData);
      setCreatingTag(false);
    } catch (error) {
      console.error('Failed to create tag:', error);
    }
  }, [createTagMutation]);

  // Handle tag update
  const handleUpdateTag = React.useCallback(async (tagId: string, tagData: TagUpdate) => {
    try {
      await updateTagMutation.mutateAsync({ tagId, tagData });
      setEditingTag(null);
    } catch (error) {
      console.error('Failed to update tag:', error);
    }
  }, [updateTagMutation]);

  // Handle tag deletion
  const handleDeleteTag = React.useCallback(async (tagId: string) => {
    if (!confirm('Are you sure you want to delete this tag? This action cannot be undone.')) {
      return;
    }

    try {
      await deleteTagMutation.mutateAsync(tagId);
    } catch (error) {
      console.error('Failed to delete tag:', error);
    }
  }, [deleteTagMutation]);

  // Handle tag status toggle
  const handleToggleStatus = React.useCallback(async (tag: Tag) => {
    const newStatus = tag.status === TagStatus.ACTIVE ? TagStatus.INACTIVE : TagStatus.ACTIVE;
    await handleUpdateTag(tag.id, { status: newStatus });
  }, [handleUpdateTag]);

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Tag Management</h1>
          <p className="text-muted-foreground">
            Manage conversation tags and categories
          </p>
        </div>
        
        <Button
          onClick={() => setCreatingTag(true)}
          className="flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Create Tag
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search tags..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Category Filter */}
          <Select
            value={categoryFilter}
            onValueChange={(value) => setCategoryFilter(value as TagCategory | 'all')}
          >
            <option value="all">All Categories</option>
            {Object.values(TagCategory).map((category) => (
              <option key={category} value={category}>
                {formatTagCategory(category)}
              </option>
            ))}
          </Select>

          {/* Status Filter */}
          <Select
            value={statusFilter}
            onValueChange={(value) => setStatusFilter(value as TagStatus | 'all')}
          >
            <option value="all">All Statuses</option>
            <option value={TagStatus.ACTIVE}>Active</option>
            <option value={TagStatus.INACTIVE}>Inactive</option>
          </Select>

          {/* Sort */}
          <Select
            value={`${sortBy}-${sortOrder}`}
            onValueChange={(value) => {
              const [field, order] = value.split('-');
              setSortBy(field as 'name' | 'usage_count' | 'created_at');
              setSortOrder(order as 'asc' | 'desc');
            }}
          >
            <option value="name-asc">Name A-Z</option>
            <option value="name-desc">Name Z-A</option>
            <option value="usage_count-desc">Most Used</option>
            <option value="usage_count-asc">Least Used</option>
            <option value="created_at-desc">Newest</option>
            <option value="created_at-asc">Oldest</option>
          </Select>
        </div>
      </Card>

      {/* Results */}
      <div className="space-y-4">
        {/* Summary */}
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Showing {tags.length} of {total} tags
          </span>
          {page > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.max(0, p - 1))}
            >
              Previous
            </Button>
          )}
          {hasMore && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => p + 1)}
            >
              Next
            </Button>
          )}
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} className="p-4">
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-muted rounded w-3/4"></div>
                  <div className="h-3 bg-muted rounded w-1/2"></div>
                  <div className="h-6 bg-muted rounded w-16"></div>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Error state */}
        {error && (
          <Card className="p-8 text-center">
            <p className="text-destructive">Failed to load tags</p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.location.reload()}
              className="mt-2"
            >
              Retry
            </Button>
          </Card>
        )}

        {/* Empty state */}
        {!isLoading && !error && tags.length === 0 && (
          <Card className="p-8 text-center">
            <p className="text-muted-foreground">
              {search || categoryFilter !== 'all' || statusFilter !== 'all'
                ? 'No tags match your filters'
                : 'No tags created yet'
              }
            </p>
            {!search && categoryFilter === 'all' && statusFilter === 'all' && (
              <Button
                onClick={() => setCreatingTag(true)}
                className="mt-2"
              >
                Create First Tag
              </Button>
            )}
          </Card>
        )}

        {/* Tag cards */}
        {!isLoading && !error && tags.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {tags.map((tag) => (
              <Card key={tag.id} className="p-4 hover:shadow-md transition-shadow">
                <div className="space-y-3">
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <TagChip tag={tag} size="md" />
                      {tag.display_name && tag.display_name !== tag.name && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Display: {tag.display_name}
                        </p>
                      )}
                    </div>
                    
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 -mt-1 -mr-1"
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Description */}
                  {tag.description && (
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {tag.description}
                    </p>
                  )}

                  {/* Metadata */}
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {formatTagCategory(tag.category)}
                      </Badge>
                      {tag.is_system_tag && (
                        <Badge variant="secondary" className="text-xs">
                          System
                        </Badge>
                      )}
                    </div>
                    
                    <span>
                      Used {tag.usage_count} times
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 pt-2 border-t border-border">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setEditingTag(tag)}
                      disabled={tag.is_system_tag}
                      className="flex-1"
                    >
                      <Edit className="h-3 w-3 mr-1" />
                      Edit
                    </Button>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleStatus(tag)}
                      disabled={tag.is_system_tag}
                      className="flex-1"
                    >
                      {tag.status === TagStatus.ACTIVE ? (
                        <>
                          <EyeOff className="h-3 w-3 mr-1" />
                          Hide
                        </>
                      ) : (
                        <>
                          <Eye className="h-3 w-3 mr-1" />
                          Show
                        </>
                      )}
                    </Button>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteTag(tag.id)}
                      disabled={tag.is_system_tag || tag.usage_count > 0}
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* TODO: Add TagCreateModal and TagEditModal components */}
      {creatingTag && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4 p-6">
            <h3 className="text-lg font-semibold mb-4">Create Tag</h3>
            <p className="text-sm text-muted-foreground">
              Tag creation form would go here
            </p>
            <div className="flex gap-2 mt-4">
              <Button size="sm" disabled>
                Create
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCreatingTag(false)}
              >
                Cancel
              </Button>
            </div>
          </Card>
        </div>
      )}

      {editingTag && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-md mx-4 p-6">
            <h3 className="text-lg font-semibold mb-4">Edit Tag</h3>
            <p className="text-sm text-muted-foreground">
              Tag editing form would go here for: {getTagDisplayName(editingTag)}
            </p>
            <div className="flex gap-2 mt-4">
              <Button size="sm" disabled>
                Save
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setEditingTag(null)}
              >
                Cancel
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}



