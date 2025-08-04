/**
 * Reusable form field component with validation support.
 */

import * as React from 'react';
import { Input } from '@/components/ui/Input';
import { cn } from '@/lib/utils';

export interface FormFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  required?: boolean;
}

const FormField = React.forwardRef<HTMLInputElement, FormFieldProps>(
  ({ className, label, error, helperText, required, id, ...props }, ref) => {
    const fieldId = id || `field-${Math.random().toString(36).substring(2)}`;

    return (
      <div className={cn('space-y-2', className)}>
        {label && (
          <label
            htmlFor={fieldId}
            className="block text-sm font-medium text-foreground"
          >
            {label}
            {required && <span className="text-error ml-1">*</span>}
          </label>
        )}
        
        <Input
          ref={ref}
          id={fieldId}
          error={!!error}
          helperText={error || helperText}
          aria-invalid={!!error}
          aria-describedby={error ? `${fieldId}-error` : undefined}
          {...props}
        />
      </div>
    );
  }
);
FormField.displayName = 'FormField';

export { FormField };