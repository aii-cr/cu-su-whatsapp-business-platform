/**
 * Conversation filters component with all supported filter options.
 * Provides comprehensive filtering based on the backend list_conversations endpoint.
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LegacySelect as Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent } from '@/components/ui/Card';
import { SearchableSelect } from '@/components/ui/SearchableSelect';
import { ConversationFilters as IConversationFilters, ConversationStatus, ConversationPriority } from '../models/conversation';
import { useAgentOptions } from '@/features/users/hooks/useAgentSearch';
import { useDebounce } from '@/hooks/useDebounce';
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  XMarkIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline';
import React from 'react'; // Added missing import for React

interface ConversationFiltersProps {
  filters: IConversationFilters;
  onFiltersChange: (filters: IConversationFilters) => void;
  onClearFilters: () => void;
  loading?: boolean;
}

export function ConversationFilters({ 
  filters, 
  onFiltersChange, 
  onClearFilters,
  loading = false 
}: ConversationFiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [localSearch, setLocalSearch] = useState(filters.search || '');
  const [agentSearchTerm, setAgentSearchTerm] = useState('');

  // Debounce the search to prevent excessive API calls
  const debouncedSearch = useDebounce(localSearch, 500);

  // Agent search functionality
  const { options: agentOptions, isLoading: agentSearchLoading } = useAgentOptions(agentSearchTerm);

  // Status options
  const statusOptions = [
    { value: 'active', label: 'Active' },
    { value: 'pending', label: 'Pending' },
    { value: 'waiting', label: 'Waiting' },
    { value: 'closed', label: 'Closed' },
    { value: 'transferred', label: 'Transferred' },
  ];

  // Priority options
  const priorityOptions = [
    { value: 'low', label: 'Low' },
    { value: 'medium', label: 'Medium' },
    { value: 'high', label: 'High' },
    { value: 'urgent', label: 'Urgent' },
  ];

  // Channel options
  const channelOptions = [
    { value: 'whatsapp', label: 'WhatsApp' },
    { value: 'web', label: 'Web Chat' },
    { value: 'email', label: 'Email' },
    { value: 'phone', label: 'Phone' },
  ];

  // Sort options
  const sortOptions = [
    { value: 'updated_at:desc', label: 'Most Recent' },
    { value: 'updated_at:asc', label: 'Oldest First' },
    { value: 'created_at:desc', label: 'Newest Created' },
    { value: 'created_at:asc', label: 'Oldest Created' },
    { value: 'priority:desc', label: 'High Priority First' },
    { value: 'status:asc', label: 'Status (A-Z)' },
  ];

  const handleFilterChange = (key: keyof IConversationFilters, value: string | boolean | undefined) => {
    onFiltersChange({
      ...filters,
      [key]: (value as any) || undefined,
      page: 1,
    });
  };

  // Handle search with debouncing
  const handleSearchChange = (value: string) => {
    setLocalSearch(value);
  };

  // Apply debounced search to filters
  React.useEffect(() => {
    handleFilterChange('search', debouncedSearch);
  }, [debouncedSearch]);

  const handleSortChange = (value: string) => {
    const [sort_by, sort_order] = value.split(':');
    onFiltersChange({
      ...filters,
      sort_by,
      sort_order: sort_order as 'asc' | 'desc',
      page: 1,
    });
  };

  const handleAgentSearch = (searchTerm: string) => {
    setAgentSearchTerm(searchTerm);
  };

  const hasActiveFilters = Boolean(
    filters.search ||
    filters.status ||
    filters.priority ||
    filters.channel ||
    filters.assigned_agent_id ||
    filters.has_unread !== undefined
  );

  const activeFilterCount = [
    filters.search,
    filters.status,
    filters.priority,
    filters.channel,
    filters.assigned_agent_id,
    filters.has_unread !== undefined ? 'unread' : null,
  ].filter(Boolean).length;

  return (
    <div className="space-y-3 sm:space-y-4">
      {/* Main search and quick filters */}
      <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
        {/* Search */}
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search by customer phone or name..."
            value={localSearch}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-10"
            disabled={loading}
          />
        </div>

        {/* Quick filters row */}
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          {/* Quick status filter */}
          <Select
            options={statusOptions}
            value={filters.status}
            onChange={(value) => handleFilterChange('status', value)}
            placeholder="All Statuses"
            className="w-full sm:w-40"
            disabled={loading}
          />

          {/* Sort */}
          <Select
            options={sortOptions}
            value={`${filters.sort_by || 'updated_at'}:${filters.sort_order || 'desc'}`}
            onChange={handleSortChange}
            placeholder="Sort by..."
            className="w-full sm:w-44"
            disabled={loading}
          />

          {/* Advanced filters toggle */}
          <Button
            variant="outline"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="whitespace-nowrap w-full sm:w-auto"
            disabled={loading}
            size="sm"
          >
            <AdjustmentsHorizontalIcon className="w-4 h-4 mr-2" />
            <span className="hidden sm:inline">Filters</span>
            <span className="sm:hidden">More</span>
            {activeFilterCount > 0 && (
              <Badge variant="default" className="ml-2 text-xs">
                {activeFilterCount}
              </Badge>
            )}
          </Button>
        </div>
      </div>

      {/* Advanced filters */}
      {showAdvanced && (
        <Card>
          <CardContent className="p-3 sm:p-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4">
              {/* Priority filter */}
              <Select
                label="Priority"
                options={priorityOptions}
                value={filters.priority}
                onChange={(value) => handleFilterChange('priority', value)}
                placeholder="All Priorities"
                disabled={loading}
              />

              {/* Channel filter */}
              <Select
                label="Channel"
                options={channelOptions}
                value={filters.channel}
                onChange={(value) => handleFilterChange('channel', value)}
                placeholder="All Channels"
                disabled={loading}
              />

              {/* Unread filter */}
              <Select
                label="Unread Messages"
                options={[
                  { value: 'true', label: 'Has Unread' },
                  { value: 'false', label: 'All Read' },
                ]}
                value={filters.has_unread !== undefined ? String(filters.has_unread) : ''}
                onChange={(value) => handleFilterChange('has_unread', value ? value === 'true' : undefined)}
                placeholder="All Conversations"
                disabled={loading}
              />

              {/* Agent filter - Searchable dropdown */}
              <SearchableSelect
                label="Assigned Agent"
                options={agentOptions}
                value={filters.assigned_agent_id || ''}
                onChange={(value) => handleFilterChange('assigned_agent_id', value)}
                onSearch={handleAgentSearch}
                placeholder="Search agents..."
                searchPlaceholder="Search by name or email..."
                disabled={loading}
                loading={agentSearchLoading}
                noOptionsMessage="No agents found"
              />
            </div>

            {/* Filter actions */}
            <div className="flex justify-between items-center mt-4 pt-4 border-t border-border">
              <div className="text-sm text-muted-foreground">
                {hasActiveFilters && `${activeFilterCount} filter${activeFilterCount === 1 ? '' : 's'} applied`}
              </div>
              
              <div className="flex space-x-2">
                {hasActiveFilters && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={onClearFilters}
                    disabled={loading}
                  >
                    <XMarkIcon className="w-4 h-4 mr-1" />
                    Clear All
                  </Button>
                )}
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowAdvanced(false)}
                  disabled={loading}
                >
                  Done
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active filters display */}
      {hasActiveFilters && !showAdvanced && (
        <div className="flex flex-wrap gap-2">
          {filters.search && (
            <Badge variant="secondary" className="text-xs">
              Search: "{filters.search}"
              <button
                onClick={() => handleFilterChange('search', '')}
                className="ml-1 hover:text-destructive"
                disabled={loading}
              >
                <XMarkIcon className="w-3 h-3" />
              </button>
            </Badge>
          )}
          
          {filters.status && (
            <Badge variant="secondary" className="text-xs">
              Status: {filters.status}
              <button
                onClick={() => handleFilterChange('status', '')}
                className="ml-1 hover:text-destructive"
                disabled={loading}
              >
                <XMarkIcon className="w-3 h-3" />
              </button>
            </Badge>
          )}
          
          {filters.priority && (
            <Badge variant="secondary" className="text-xs">
              Priority: {filters.priority}
              <button
                onClick={() => handleFilterChange('priority', '')}
                className="ml-1 hover:text-destructive"
                disabled={loading}
              >
                <XMarkIcon className="w-3 h-3" />
              </button>
            </Badge>
          )}

          {filters.channel && (
            <Badge variant="secondary" className="text-xs">
              Channel: {filters.channel}
              <button
                onClick={() => handleFilterChange('channel', '')}
                className="ml-1 hover:text-destructive"
                disabled={loading}
              >
                <XMarkIcon className="w-3 h-3" />
              </button>
            </Badge>
          )}

          {filters.assigned_agent_id && (
            <Badge variant="secondary" className="text-xs">
              Agent: {agentOptions.find(opt => opt.value === filters.assigned_agent_id)?.label || filters.assigned_agent_id}
              <button
                onClick={() => handleFilterChange('assigned_agent_id', '')}
                className="ml-1 hover:text-destructive"
                disabled={loading}
              >
                <XMarkIcon className="w-3 h-3" />
              </button>
            </Badge>
          )}

          {filters.has_unread !== undefined && (
            <Badge variant="secondary" className="text-xs">
              {filters.has_unread ? 'Has Unread' : 'All Read'}
              <button
                onClick={() => handleFilterChange('has_unread', undefined)}
                className="ml-1 hover:text-destructive"
                disabled={loading}
              >
                <XMarkIcon className="w-3 h-3" />
              </button>
            </Badge>
          )}
        </div>
      )}
    </div>
  );
}