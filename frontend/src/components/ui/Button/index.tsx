/**
 * Enhanced Button component with SCSS + Tailwind integration.
 * Supports complex effects while maintaining accessibility and theming.
 */

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import styles from './Button.module.scss';

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
        gradient: 'text-white border-0',
        neon: 'text-white border-0',
        threeD: 'text-white border-0',
        ripple: 'text-white border-0',
        whatsapp: 'text-white border-0',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-8 rounded-md px-3 text-xs',
        lg: 'h-12 rounded-xl px-6 text-base',
        icon: 'h-10 w-10',
        md: 'h-10 px-4 py-2',
        xl: 'h-14 px-8 py-3 text-lg',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
  effect?: 'gradient' | 'neon' | 'threeD' | 'ripple' | 'whatsapp' | 'none';
  icon?: React.ReactNode;
  iconOnly?: boolean;
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant, 
    size, 
    loading, 
    effect = 'none',
    icon,
    iconOnly = false,
    asChild = false,
    children, 
    disabled, 
    ...props 
  }, ref) => {
    // Combine Tailwind classes with SCSS module classes
    const buttonClasses = cn(
      buttonVariants({ variant, size, className }),
      styles.button,
      {
        [styles.gradient]: effect === 'gradient' || variant === 'gradient',
        [styles.neon]: effect === 'neon' || variant === 'neon',
        [styles.threeD]: effect === 'threeD' || variant === 'threeD',
        [styles.ripple]: effect === 'ripple' || variant === 'ripple',
        [styles.whatsapp]: effect === 'whatsapp' || variant === 'whatsapp',
        [styles.loading]: loading,
        [styles.disabled]: disabled,
        [styles.iconOnly]: iconOnly,
        [styles.ghostGradient]: variant === 'ghost' && effect === 'gradient',
        [styles.ghost]: variant === 'ghost',
        [styles.outline]: variant === 'outline',
      }
    );

    const iconClasses = cn(
      styles.icon,
      {
        [styles.iconOnly]: iconOnly,
      }
    );

    const Comp = asChild ? 'div' : 'button';
    
    return (
      <Comp
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
      </Comp>
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };
