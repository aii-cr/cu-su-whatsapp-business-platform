/**
 * Select component for dropdowns with consistent styling.
 * Provides accessible dropdown functionality with proper theming.
 * Includes compound components for flexible composition.
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { ChevronDownIcon, CheckIcon } from '@heroicons/react/24/outline';

// Context for Select state
interface SelectContextValue {
  value?: string;
  displayText?: string;
  onValueChange?: (value: string, displayText?: string) => void;
  open: boolean;
  setOpen: (open: boolean) => void;
}

const SelectContext = React.createContext<SelectContextValue | undefined>(undefined);

const useSelectContext = () => {
  const context = React.useContext(SelectContext);
  if (!context) {
    throw new Error('Select compound components must be used within Select');
  }
  return context;
};

// Main Select component
interface SelectProps {
  value?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
  defaultValue?: string;
}

const Select: React.FC<SelectProps> = ({ 
  value, 
  onValueChange, 
  children,
  defaultValue 
}) => {
  const [open, setOpen] = React.useState(false);
  const [internalValue, setInternalValue] = React.useState(defaultValue || '');
  const [displayText, setDisplayText] = React.useState('');
  
  const currentValue = value !== undefined ? value : internalValue;
  
  const handleValueChange = React.useCallback((newValue: string, newDisplayText?: string) => {
    if (value === undefined) {
      setInternalValue(newValue);
    }
    if (newDisplayText) {
      setDisplayText(newDisplayText);
    }
    onValueChange?.(newValue);
    setOpen(false);
  }, [value, onValueChange]);

  return (
    <SelectContext.Provider
      value={{
        value: currentValue,
        displayText,
        onValueChange: handleValueChange,
        open,
        setOpen,
      }}
    >
      <div className="relative">
        {children}
      </div>
    </SelectContext.Provider>
  );
};

// SelectTrigger component
interface SelectTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  className?: string;
}

const SelectTrigger = React.forwardRef<HTMLButtonElement, SelectTriggerProps>(
  ({ children, className, ...props }, ref) => {
    const { open, setOpen } = useSelectContext();

    return (
      <button
        ref={ref}
        type="button"
        role="combobox"
        aria-expanded={open}
        className={cn(
          'flex h-10 w-full items-center justify-between rounded-lg border border-border bg-background px-3 py-2 text-sm',
          'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'hover:bg-accent hover:text-accent-foreground',
          className
        )}
        onClick={() => setOpen(!open)}
        {...props}
      >
        {children}
        <ChevronDownIcon 
          className={cn(
            'h-4 w-4 opacity-50 transition-transform duration-200',
            open && 'rotate-180'
          )} 
        />
      </button>
    );
  }
);
SelectTrigger.displayName = 'SelectTrigger';

// SelectValue component
interface SelectValueProps {
  placeholder?: string;
  className?: string;
}

const SelectValue: React.FC<SelectValueProps> = ({ placeholder, className }) => {
  const { value, displayText } = useSelectContext();
  
  return (
    <span className={cn('block truncate', className)}>
      {value ? (displayText || value) : (
        <span className="text-muted-foreground">
          {placeholder || 'Select...'}
        </span>
      )}
    </span>
  );
};
SelectValue.displayName = 'SelectValue';

// SelectContent component
interface SelectContentProps {
  children: React.ReactNode;
  className?: string;
}

const SelectContent: React.FC<SelectContentProps> = ({ children, className }) => {
  const { open, setOpen } = useSelectContext();
  const contentRef = React.useRef<HTMLDivElement>(null);

  // Close on outside click
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (contentRef.current && !contentRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [open, setOpen]);

  // Close on escape key
  React.useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [open, setOpen]);

  if (!open) {
    return null;
  }

  return (
    <div
      ref={contentRef}
      className={cn(
        'absolute z-50 mt-1 w-full overflow-auto rounded-lg border border-border bg-background shadow-lg',
        'max-h-60 min-w-[8rem] animate-in fade-in-0 zoom-in-95',
        className
      )}
    >
      <div className="p-1">
        {children}
      </div>
    </div>
  );
};
SelectContent.displayName = 'SelectContent';

// SelectItem component
interface SelectItemProps {
  value: string;
  children: React.ReactNode;
  className?: string;
}

const SelectItem: React.FC<SelectItemProps> = ({ value, children, className }) => {
  const { value: selectedValue, onValueChange } = useSelectContext();
  const isSelected = selectedValue === value;

  const handleClick = () => {
    // Extract text content from children for display
    const displayText = typeof children === 'string' ? children : value;
    onValueChange?.(value, displayText);
  };

  return (
    <div
      className={cn(
        'relative flex w-full cursor-pointer select-none items-center rounded-md py-2 pl-8 pr-2 text-sm',
        'hover:bg-accent hover:text-accent-foreground',
        'focus:bg-accent focus:text-accent-foreground',
        isSelected && 'bg-accent text-accent-foreground',
        className
      )}
      onClick={handleClick}
    >
      <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
        {isSelected && <CheckIcon className="h-4 w-4" />}
      </span>
      <span className="block truncate">{children}</span>
    </div>
  );
};
SelectItem.displayName = 'SelectItem';

// Legacy Select for backward compatibility
export interface SelectOption {
  value: string;
  label: string;
}

export interface LegacySelectProps {
  options: SelectOption[];
  value?: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  label?: string;
  error?: string;
}

const LegacySelect = React.forwardRef<HTMLSelectElement, LegacySelectProps>(
  ({ 
    options, 
    value, 
    onChange, 
    placeholder = "Select...", 
    disabled = false, 
    className,
    label,
    error,
    ...props 
  }, ref) => {
    return (
      <div className="space-y-1">
        {label && (
          <label className="text-sm font-medium text-foreground">
            {label}
          </label>
        )}
        
        <div className="relative">
          <select
            ref={ref}
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className={cn(
              'w-full h-10 px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground',
              'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background',
              'disabled:cursor-not-allowed disabled:opacity-50',
              'appearance-none cursor-pointer',
              error && 'border-destructive focus:ring-destructive',
              className
            )}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          
          {/* Dropdown arrow */}
          <ChevronDownIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        </div>
        
        {error && (
          <p className="text-sm text-destructive">
            {error}
          </p>
        )}
      </div>
    );
  }
);

LegacySelect.displayName = 'LegacySelect';

export { 
  Select, 
  SelectTrigger, 
  SelectValue, 
  SelectContent, 
  SelectItem,
  LegacySelect 
};