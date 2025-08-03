/**
 * Badge component for displaying status indicators and labels.
 * Supports different variants and sizes.
 */

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-primary-500 text-primary-foreground hover:bg-primary-600',
        secondary: 'border-transparent bg-surface text-foreground hover:bg-muted',
        destructive: 'border-transparent bg-error text-white hover:bg-red-700',
        success: 'border-transparent bg-success text-white hover:bg-emerald-700',
        warning: 'border-transparent bg-warning text-white hover:bg-amber-700',
        outline: 'text-foreground border-border',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };