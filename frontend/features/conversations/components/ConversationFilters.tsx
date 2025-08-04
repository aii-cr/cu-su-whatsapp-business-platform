/**
 * Conversation filters component with all supported filter options.
 * Provides comprehensive filtering based on the backend list_conversations endpoint.
 */

'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { Card, CardContent } from '@/components/ui/Card';
import { ConversationFilters as IConversationFilters, ConversationStatus, ConversationPriority } from '../models/conversation';
import { 
  MagnifyingGlassIcon,
  FunnelIcon,
  XMarkIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline';

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

  // Customer type options
  const customerTypeOptions = [
    { value: 'new', label: 'New Customer' },
    { value: 'returning', label: 'Returning Customer' },
    { value: 'vip', label: 'VIP Customer' },
    { value: 'premium', label: 'Premium Customer' },
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

  const handleFilterChange = (key: keyof IConversationFilters, value: any) => {
    onFiltersChange({
      ...filters,
      [key]: value || undefined,
      page: 1, // Reset to first page when filters change
    });
  };

  const handleSearchChange = (value: string) => {
    setLocalSearch(value);
    handleFilterChange('search', value);
  };

  const handleSortChange = (value: string) => {
    const [sort_by, sort_order] = value.split(':');
    onFiltersChange({
      ...filters,
      sort_by,
      sort_order: sort_order as 'asc' | 'desc',
      page: 1,
    });
  };

  const hasActiveFilters = Boolean(
    filters.search ||
    filters.status ||
    filters.priority ||
    filters.channel ||
    filters.department_id ||
    filters.assigned_agent_id ||
    filters.customer_type ||
    filters.has_unread !== undefined
  );

  const activeFilterCount = [
    filters.search,
    filters.status,
    filters.priority,
    filters.channel,
    filters.department_id,
    filters.assigned_agent_id,
    filters.customer_type,
    filters.has_unread !== undefined ? 'unread' : null,
  ].filter(Boolean).length;

  return (
    <div className="space-y-4">
      {/* Main search and quick filters */}
      <div className="flex flex-col sm:flex-row gap-4">
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

        {/* Quick status filter */}
        <Select
          options={statusOptions}
          value={filters.status}
          onChange={(value) => handleFilterChange('status', value)}
          placeholder="All Statuses"
          className="w-40"
          disabled={loading}
        />

        {/* Sort */}
        <Select
          options={sortOptions}
          value={`${filters.sort_by || 'updated_at'}:${filters.sort_order || 'desc'}`}
          onChange={handleSortChange}
          placeholder="Sort by..."
          className="w-44"
          disabled={loading}
        />

        {/* Advanced filters toggle */}
        <Button
          variant="outline"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="whitespace-nowrap"
          disabled={loading}
        >
          <AdjustmentsHorizontalIcon className="w-4 h-4 mr-2" />
          Filters
          {activeFilterCount > 0 && (
            <Badge variant="default" className="ml-2 text-xs">
              {activeFilterCount}
            </Badge>
          )}
        </Button>
      </div>

      {/* Advanced filters */}
      {showAdvanced && (
        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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

              {/* Customer type filter */}
              <Select
                label="Customer Type"
                options={customerTypeOptions}
                value={filters.customer_type}
                onChange={(value) => handleFilterChange('customer_type', value)}
                placeholder="All Types"
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

              {/* Department filter - TODO: Load from API */}
              <div className="space-y-1">
                <label className="text-sm font-medium text-foreground">
                  Department
                </label>
                <Input
                  type="text"
                  placeholder="Department ID"
                  value={filters.department_id || ''}
                  onChange={(e) => handleFilterChange('department_id', e.target.value)}
                  disabled={loading}
                />
              </div>

              {/* Agent filter - TODO: Load from API */}
              <div className="space-y-1">
                <label className="text-sm font-medium text-foreground">
                  Assigned Agent
                </label>
                <Input
                  type="text"
                  placeholder="Agent ID"
                  value={filters.assigned_agent_id || ''}
                  onChange={(e) => handleFilterChange('assigned_agent_id', e.target.value)}
                  disabled={loading}
                />
              </div>
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

          {/* Add more active filter badges as needed */}
        </div>
      )}
    </div>
  );
}