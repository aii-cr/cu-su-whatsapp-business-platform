/**
 * CreateTagForm component - form for creating new tags
 */

import * as React from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { cn } from '@/lib/utils';

export interface CreateTagFormData {
  name: string;
  description: string;
  category: string;
  color: string;
}

export interface CreateTagFormProps {
  initialData: CreateTagFormData;
  onSubmit: (data: CreateTagFormData) => void;
  onCancel: () => void;
  className?: string;
}

const TAG_CATEGORIES = [
  { value: 'general', label: 'General' },
  { value: 'department', label: 'Department' },
  { value: 'priority', label: 'Priority' },
  { value: 'status', label: 'Status' },
  { value: 'billing', label: 'Billing' },
  { value: 'technical', label: 'Technical' },
  { value: 'product', label: 'Product' },
  { value: 'onboarding', label: 'Onboarding' },
];

const TAG_COLORS = [
  '#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d',
  '#ea580c', '#be185d', '#7c2d12', '#1e40af', '#991b1b', '#166534', '#92400e', '#581c87',
];

export function CreateTagForm({
  initialData,
  onSubmit,
  onCancel,
  className,
}: CreateTagFormProps) {
  const [formData, setFormData] = React.useState<CreateTagFormData>(initialData);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const handleSubmit = React.useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;

    setIsSubmitting(true);
    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Failed to create tag:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, onSubmit]);

  const handleInputChange = React.useCallback((field: keyof CreateTagFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  }, []);

  return (
    <form onSubmit={handleSubmit} className={cn('space-y-3', className)}>
      <div className="flex items-center gap-2 text-sm font-medium mb-2">
        <span>Create new tag</span>
      </div>

      {/* Tag Name */}
      <div className="space-y-1">
        <Label htmlFor="tag-name" className="text-xs font-medium">
          Tag Name *
        </Label>
        <Input
          id="tag-name"
          type="text"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          placeholder="Enter tag name"
          maxLength={40}
          className="text-sm"
          autoFocus
          required
        />
      </div>

      {/* Category */}
      <div className="space-y-1">
        <Label htmlFor="tag-category" className="text-xs font-medium">
          Category
        </Label>
        <Select
          value={formData.category}
          onValueChange={(value) => handleInputChange('category', value)}
        >
          <SelectTrigger className="text-sm">
            <SelectValue placeholder="Select category" />
          </SelectTrigger>
          <SelectContent>
            {TAG_CATEGORIES.map((category) => (
              <SelectItem key={category.value} value={category.value}>
                {category.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Color */}
      <div className="space-y-1">
        <Label className="text-xs font-medium">Color</Label>
        <div className="grid grid-cols-8 gap-1">
          {TAG_COLORS.map((color) => (
            <button
              key={color}
              type="button"
              onClick={() => handleInputChange('color', color)}
              className={cn(
                'w-6 h-6 rounded-full border-2 transition-all',
                formData.color === color
                  ? 'border-foreground scale-110'
                  : 'border-transparent hover:scale-105'
              )}
              style={{ backgroundColor: color }}
              aria-label={`Select color ${color}`}
            />
          ))}
        </div>
      </div>

      {/* Description */}
      <div className="space-y-1">
        <Label htmlFor="tag-description" className="text-xs font-medium">
          Description (optional)
        </Label>
        <Input
          id="tag-description"
          type="text"
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          placeholder="Brief description of the tag"
          maxLength={100}
          className="text-sm"
        />
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-2">
        <Button
          type="submit"
          size="sm"
          disabled={!formData.name.trim() || isSubmitting}
          className="flex-1"
        >
          {isSubmitting ? 'Creating...' : 'Create & Add'}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}

export default CreateTagForm;
