/**
 * Loading spinner component with different sizes and variants.
 */

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const spinnerVariants = cva(
  'animate-spin rounded-full border-solid',
  {
    variants: {
      variant: {
        default: 'border-primary-500 border-t-transparent',
        light: 'border-white border-t-transparent',
        muted: 'border-muted-foreground border-t-transparent',
      },
      size: {
        sm: 'h-4 w-4 border-2',
        md: 'h-6 w-6 border-2',
        lg: 'h-8 w-8 border-2',
        xl: 'h-12 w-12 border-4',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
    },
  }
);

export interface LoadingSpinnerProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof spinnerVariants> {
  text?: string;
}

const LoadingSpinner = React.forwardRef<HTMLDivElement, LoadingSpinnerProps>(
  ({ className, variant, size, text, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn('flex flex-col items-center justify-center', className)}
        {...props}
      >
        <div className={cn(spinnerVariants({ variant, size }))} />
        {text && (
          <p className="mt-2 text-sm text-muted-foreground">{text}</p>
        )}
      </div>
    );
  }
);
LoadingSpinner.displayName = 'LoadingSpinner';

export { LoadingSpinner, spinnerVariants };