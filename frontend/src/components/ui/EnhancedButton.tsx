/**
 * EnhancedButton component demonstrating SCSS modules + Tailwind integration.
 * Shows how to use SCSS for complex styling while keeping Tailwind for layout.
 */

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import styles from './EnhancedButton.module.scss';

const buttonVariants = cva(
  // Base Tailwind classes for layout and basic styling
  'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-150 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 active:scale-95 select-none',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-border bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline hover:text-primary/80',
        success: 'bg-success text-white hover:bg-success/90',
        warning: 'bg-warning text-white hover:bg-warning/90',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-12 rounded-xl px-6 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface EnhancedButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  effect?: 'gradient' | 'neon' | 'threeD' | 'ripple' | 'whatsapp' | 'none';
  icon?: React.ReactNode;
  iconOnly?: boolean;
}

const EnhancedButton = React.forwardRef<HTMLButtonElement, EnhancedButtonProps>(
  ({ 
    className, 
    variant, 
    size, 
    loading, 
    effect = 'none',
    icon,
    iconOnly = false,
    children, 
    disabled, 
    ...props 
  }, ref) => {
    // Combine Tailwind classes with SCSS module classes
    const buttonClasses = cn(
      buttonVariants({ variant, size, className }),
      styles.button,
      {
        [styles.gradient]: effect === 'gradient',
        [styles.neon]: effect === 'neon',
        [styles.threeD]: effect === 'threeD',
        [styles.ripple]: effect === 'ripple',
        [styles.whatsapp]: effect === 'whatsapp',
        [styles.loading]: loading,
        [styles.disabled]: disabled,
        [styles.sizeSm]: size === 'sm',
        [styles.sizeMd]: size === 'md',
        [styles.sizeLg]: size === 'lg',
        [styles.sizeXl]: size === 'xl',
      }
    );

    const iconClasses = cn(
      styles.icon,
      {
        [styles.iconOnly]: iconOnly,
      }
    );

    return (
      <button
        className={buttonClasses}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {icon && (
          <span className={iconClasses}>
            {icon}
          </span>
        )}
        {!iconOnly && children}
      </button>
    );
  }
);

EnhancedButton.displayName = 'EnhancedButton';

export { EnhancedButton, buttonVariants };
