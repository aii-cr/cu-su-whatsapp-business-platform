# Frontend Development Rules - Professional Next.js/React Standards

## 🎨 **Design System & UI/UX Principles**

### **Professional Component Structure**
```typescript
/**
 * Professional ComponentName component - brief description
 * Features: key features, light/dark theme support, accessibility
 */

import * as React from 'react';
import { Icon1, Icon2, Icon3 } from 'lucide-react'; // Always use Lucide icons
import { cn } from '@/lib/utils';
import { ComponentProps } from './types';

export interface ComponentNameProps {
  // Props with proper TypeScript types
  children?: React.ReactNode;
  className?: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'outline' | 'ghost';
}

export function ComponentName({
  children,
  className,
  disabled = false,
  size = 'md',
  variant = 'default',
  ...props
}: ComponentNameProps) {
  // State management with useCallback for performance
  const [isOpen, setIsOpen] = React.useState(false);
  
  const handleClick = React.useCallback(() => {
    if (!disabled) {
      setIsOpen(true);
    }
  }, [disabled]);

  // Size classes for responsive design
  const sizeClasses = {
    sm: 'h-8 text-sm px-2',
    md: 'h-10 text-sm px-3', 
    lg: 'h-12 text-base px-4',
  };

  return (
    <div className={cn('relative w-full', className)}>
      {/* Component content with proper semantic HTML */}
    </div>
  );
}
```

### **Light/Dark Theme Compatibility**
```typescript
// ✅ CORRECT - Use CSS variables for theme compatibility
className={cn(
  'bg-background text-foreground border-border',
  'hover:bg-accent hover:text-accent-foreground',
  'focus:ring-2 focus:ring-ring focus:border-transparent',
  'disabled:opacity-50 disabled:cursor-not-allowed'
)}

// ❌ WRONG - Hard-coded colors
className="bg-white text-black border-gray-300"
```

### **Icon Usage Standards**
```typescript
// ✅ ALWAYS use Lucide React icons for consistency
import { 
  Search, Plus, X, Tag, Check, 
  ChevronDown, ChevronUp, ArrowRight,
  Settings, User, Bell, Home, Calendar,
  FileText, Image, Video, Music, Download,
  Upload, Edit, Trash, Copy, Share, Lock,
  Eye, EyeOff, Heart, Star, Flag, Bookmark
} from 'lucide-react';

// Icon placement patterns
<Search className="h-4 w-4 text-muted-foreground" />
<Plus className="h-4 w-4 text-primary" />
<X className="h-4 w-4 text-destructive" />

// Icon with text alignment
<div className="flex items-center gap-2">
  <Tag className="h-4 w-4" />
  <span>Tag Management</span>
</div>
```

## 🏗️ **Component Architecture**

### **Professional Modal/Dialog Structure**
```typescript
export function ProfessionalModal({ open, onOpenChange, children }: ModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className={cn(
          'sm:max-w-3xl lg:max-w-4xl w-full max-h-[95vh]',
          'overflow-hidden flex flex-col relative z-[1000]'
        )}
      >
        {/* Header - Always fixed */}
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>Modal Title</DialogTitle>
          <DialogDescription>Modal description</DialogDescription>
        </DialogHeader>

        {/* Content - Scrollable */}
        <div className="flex-1 overflow-y-auto flex flex-col space-y-6 p-6">
          {children}
        </div>

        {/* Footer - Always fixed */}
        <div className="flex-shrink-0 flex items-center justify-end gap-3 pt-4 border-t p-6">
          <Button variant="outline" onClick={onCancel}>Cancel</Button>
          <Button onClick={onConfirm}>Confirm</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

### **Professional Dropdown/Typeahead Structure**
```typescript
export function ProfessionalTypeahead({ ... }: TypeaheadProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  return (
    <div className="relative w-full">
      {/* Input with icon */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          ref={inputRef}
          className="pl-10 pr-10"
          placeholder="Search..."
        />
        {query && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 transform -translate-y-1/2"
          >
            <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
          </button>
        )}
      </div>

      {/* Dropdown with proper z-index */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute z-[9999] w-full mt-2 bg-background border border-border rounded-lg shadow-lg max-h-80 overflow-hidden"
        >
          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center justify-center py-6">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
              <span className="ml-3 text-sm text-muted-foreground">Loading...</span>
            </div>
          )}

          {/* Content */}
          <div className="max-h-80 overflow-y-auto">
            {/* Header */}
            <div className="px-4 py-2 text-xs font-medium text-muted-foreground border-b border-border bg-muted/30">
              Results
            </div>

            {/* Items */}
            {items.map((item) => (
              <button
                key={item.id}
                className="w-full px-4 py-3 text-left hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none flex items-center gap-3 transition-colors border-b border-border/50 last:border-b-0"
              >
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{item.name}</div>
                  <div className="text-xs text-muted-foreground">{item.description}</div>
                </div>
                <Check className="h-4 w-4 text-primary opacity-0 group-hover:opacity-100 transition-opacity" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

## 🎯 **Interactive Elements**

### **Professional Button Patterns**
```typescript
// Primary action button
<Button 
  onClick={handleAction}
  disabled={isLoading}
  className="flex items-center gap-2"
>
  {isLoading ? (
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
  ) : (
    <Plus className="h-4 w-4" />
  )}
  Create New
</Button>

// Secondary action button
<Button 
  variant="outline" 
  onClick={handleCancel}
  className="flex items-center gap-2"
>
  <X className="h-4 w-4" />
  Cancel
</Button>

// Destructive action button
<Button 
  variant="destructive" 
  onClick={handleDelete}
  className="flex items-center gap-2"
>
  <Trash className="h-4 w-4" />
  Delete
</Button>
```

### **Professional Form Patterns**
```typescript
export function ProfessionalForm() {
  const [formData, setFormData] = React.useState({
    name: '',
    description: '',
    category: 'general',
    color: '#2563eb'
  });

  const handleSubmit = React.useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) return;
    
    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Form submission failed:', error);
    }
  }, [formData, onSubmit]);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">
          Name *
        </label>
        <Input
          value={formData.name}
          onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
          placeholder="Enter name"
          required
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">
          Color
        </label>
        <div className="grid grid-cols-8 gap-2">
          {colors.map((color) => (
            <button
              key={color}
              type="button"
              onClick={() => setFormData(prev => ({ ...prev, color }))}
              className={cn(
                'w-8 h-8 rounded-full border-2 transition-all',
                formData.color === color
                  ? 'border-foreground scale-110'
                  : 'border-transparent hover:scale-105'
              )}
              style={{ backgroundColor: color }}
            />
          ))}
        </div>
      </div>

      <div className="flex gap-3 pt-4">
        <Button type="submit" className="flex-1">
          <Check className="h-4 w-4 mr-2" />
          Save
        </Button>
        <Button type="button" variant="outline" onClick={onCancel}>
          <X className="h-4 w-4 mr-2" />
          Cancel
        </Button>
      </div>
    </form>
  );
}
```

## 🎨 **Visual Design Patterns**

### **Professional Tag/Chip Design**
```typescript
export function ProfessionalTag({ tag, onRemove }: TagProps) {
  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary/10 text-primary text-sm border border-primary/20">
      <div 
        className="w-2 h-2 rounded-full flex-shrink-0"
        style={{ backgroundColor: tag.color }}
      />
      <span className="font-medium">{tag.name}</span>
      {onRemove && (
        <button
          onClick={() => onRemove(tag.id)}
          className="hover:bg-primary/20 rounded-full p-0.5 transition-colors ml-1"
          aria-label={`Remove ${tag.name}`}
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </div>
  );
}
```

### **Professional Loading States**
```typescript
// Inline loading
{isLoading && (
  <div className="flex items-center justify-center py-4">
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
    <span className="ml-2 text-sm text-muted-foreground">Loading...</span>
  </div>
)}

// Button loading
<Button disabled={isLoading}>
  {isLoading ? (
    <>
      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
      Loading...
    </>
  ) : (
    <>
      <Plus className="h-4 w-4 mr-2" />
      Create
    </>
  )}
</Button>

// Skeleton loading
<div className="space-y-3">
  <div className="h-4 bg-muted rounded animate-pulse"></div>
  <div className="h-4 bg-muted rounded animate-pulse w-3/4"></div>
  <div className="h-4 bg-muted rounded animate-pulse w-1/2"></div>
</div>
```

### **Professional Empty States**
```typescript
export function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action 
}: EmptyStateProps) {
  return (
    <div className="text-center py-8">
      <Icon className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
      <h3 className="text-lg font-medium text-foreground mb-2">{title}</h3>
      <p className="text-sm text-muted-foreground mb-4">{description}</p>
      {action && (
        <Button onClick={action.onClick} className="flex items-center gap-2">
          <action.icon className="h-4 w-4" />
          {action.label}
        </Button>
      )}
    </div>
  );
}

// Usage
<EmptyState
  icon={Tag}
  title="No tags found"
  description="Create your first tag to get started"
  action={{
    label: "Create Tag",
    icon: Plus,
    onClick: handleCreateTag
  }}
/>
```

## 🔧 **Performance & Best Practices**

### **State Management Patterns**
```typescript
// ✅ Use useCallback for event handlers
const handleClick = React.useCallback(() => {
  if (!disabled) {
    setIsOpen(true);
  }
}, [disabled]);

// ✅ Use useMemo for expensive computations
const filteredItems = React.useMemo(() => {
  return items.filter(item => 
    item.name.toLowerCase().includes(query.toLowerCase())
  );
}, [items, query]);

// ✅ Debounce search queries
const [debouncedQuery, setDebouncedQuery] = React.useState('');
React.useEffect(() => {
  const timer = setTimeout(() => {
    setDebouncedQuery(query);
  }, 300);
  return () => clearTimeout(timer);
}, [query]);
```

### **Accessibility Patterns**
```typescript
// ✅ Always include proper ARIA labels
<button
  aria-label={`Remove ${item.name}`}
  onClick={() => onRemove(item.id)}
>
  <X className="h-4 w-4" />
</button>

// ✅ Keyboard navigation support
const handleKeyDown = React.useCallback((e: React.KeyboardEvent) => {
  if (e.key === 'Escape') {
    setIsOpen(false);
  } else if (e.key === 'Enter') {
    e.preventDefault();
    handleSelect();
  }
}, [handleSelect]);

// ✅ Focus management
React.useEffect(() => {
  if (isOpen) {
    inputRef.current?.focus();
  }
}, [isOpen]);
```

## 📱 **Responsive Design Patterns**

### **Size Classes Pattern**
```typescript
const sizeClasses = {
  sm: {
    input: 'h-8 text-sm',
    button: 'h-8 px-2 text-sm',
    icon: 'h-3 w-3',
    spacing: 'gap-1.5',
  },
  md: {
    input: 'h-10 text-sm',
    button: 'h-10 px-3 text-sm',
    icon: 'h-4 w-4',
    spacing: 'gap-2',
  },
  lg: {
    input: 'h-12 text-base',
    button: 'h-12 px-4 text-base',
    icon: 'h-5 w-5',
    spacing: 'gap-3',
  },
};

const currentSize = sizeClasses[size];
```

### **Modal Responsive Patterns**
```typescript
<DialogContent 
  className={cn(
    'w-full max-h-[95vh] overflow-hidden flex flex-col',
    'sm:max-w-lg md:max-w-2xl lg:max-w-3xl xl:max-w-4xl',
    'relative z-[1000]'
  )}
>
  {/* Content */}
  <div className="flex-1 overflow-y-auto flex flex-col space-y-6 p-4 sm:p-6">
    {children}
  </div>
</DialogContent>
```

## 🎯 **File Organization Standards**

### **Component File Structure**
```
src/features/feature-name/
├── components/
│   ├── ComponentName.tsx          # Main component
│   ├── ComponentNameItem.tsx      # Sub-components
│   └── index.ts                   # Exports
├── hooks/
│   ├── useComponentName.ts        # Custom hooks
│   └── index.ts
├── api/
│   ├── componentNameApi.ts        # API functions
│   └── index.ts
├── models/
│   ├── componentName.ts           # Types & schemas
│   └── index.ts
└── index.ts                       # Feature exports
```

### **Import Order Standards**
```typescript
// 1. React and core libraries
import * as React from 'react';
import { useState, useCallback, useEffect } from 'react';

// 2. Third-party libraries
import { cn } from '@/lib/utils';
import { useQuery } from '@tanstack/react-query';

// 3. UI components
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

// 4. Icons
import { Plus, X, Search } from 'lucide-react';

// 5. Local imports
import { ComponentProps } from './types';
import { useComponentHook } from '../hooks/useComponentHook';
```

## 🚀 **Implementation Checklist**

When creating new components, ensure:

- [ ] ✅ Uses proper TypeScript interfaces
- [ ] ✅ Implements light/dark theme compatibility
- [ ] ✅ Includes proper loading states
- [ ] ✅ Has error handling
- [ ] ✅ Uses Lucide React icons
- [ ] ✅ Implements keyboard navigation
- [ ] ✅ Has proper ARIA labels
- [ ] ✅ Uses useCallback for event handlers
- [ ] ✅ Implements responsive design
- [ ] ✅ Has proper z-index management
- [ ] ✅ Uses CSS variables for theming
- [ ] ✅ Includes proper focus management
- [ ] ✅ Has smooth transitions/animations
- [ ] ✅ Implements proper empty states
- [ ] ✅ Uses semantic HTML structure

## 🎨 **Color Palette Standards**

### **Theme Colors (CSS Variables)**
```css
/* Always use these CSS variables for theming */
--background: #ffffff / #0a0a0a
--foreground: #0a0a0a / #ffffff
--primary: #2563eb
--primary-foreground: #ffffff
--secondary: #f1f5f9 / #1e293b
--secondary-foreground: #0f172a / #f8fafc
--muted: #f8fafc / #1e293b
--muted-foreground: #64748b / #94a3b8
--accent: #f1f5f9 / #1e293b
--accent-foreground: #0f172a / #f8fafc
--destructive: #ef4444
--destructive-foreground: #ffffff
--border: #e2e8f0 / #334155
--input: #ffffff / #1e293b
--ring: #2563eb
```

### **Tag Color Palette**
```typescript
const TAG_COLORS = [
  '#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d',
  '#ea580c', '#be185d', '#7c2d12', '#1e40af', '#991b1b', '#166534', '#92400e', '#581c87',
];
```

This rule set ensures consistent, professional, and accessible frontend development across the entire project! 🎯
