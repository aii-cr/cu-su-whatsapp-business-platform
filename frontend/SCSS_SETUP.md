# SCSS + Tailwind CSS Integration

This project uses SCSS alongside Tailwind CSS to provide the best of both worlds: Tailwind's utility-first approach for layout and responsive design, and SCSS for complex styling patterns and component-specific styles.

## 📁 Directory Structure

```
src/
├── app/
│   └── globals.scss          # Main SCSS file with Tailwind directives
├── styles/                   # SCSS partials and utilities
│   ├── _variables.scss       # Design tokens and variables
│   ├── _mixins.scss          # Reusable SCSS mixins
│   ├── _animations.scss      # Custom keyframes and animations
│   └── _typography.scss      # Typography utilities
└── components/
    └── ui/
        ├── EnhancedButton.tsx
        └── EnhancedButton.module.scss  # Component-specific SCSS module
```

## 🎯 Usage Guidelines

### When to Use Tailwind
- **Layout**: Flexbox, Grid, positioning
- **Spacing**: Margins, padding, gaps
- **Responsive design**: Breakpoints, responsive utilities
- **Basic styling**: Colors, typography, borders
- **Simple interactions**: Hover, focus states

### When to Use SCSS
- **Complex animations**: Keyframes, transforms
- **Component-specific styling**: Unique visual effects
- **Reusable patterns**: Mixins for common patterns
- **Advanced CSS features**: Custom properties, complex selectors
- **Design system tokens**: Variables for consistent theming

## 🔧 Setup

### 1. Dependencies
```bash
npm install sass --save-dev
```

### 2. File Structure
- **Global styles**: `src/app/globals.scss` (imports Tailwind + SCSS partials)
- **SCSS partials**: `src/styles/` (variables, mixins, animations, typography)
- **Component styles**: `*.module.scss` files co-located with components

### 3. Import Order
```scss
// globals.scss
@tailwind base;
@tailwind components;
@tailwind utilities;

// Then import SCSS partials
@import '../styles/variables';
@import '../styles/mixins';
@import '../styles/animations';
@import '../styles/typography';
```

## 📝 Best Practices

### ✅ Do's
- Use Tailwind for layout, spacing, and responsive design
- Use SCSS modules for complex component-specific styling
- Keep SCSS variables in sync with Tailwind design tokens
- Use `@apply` sparingly for repetitive utility combinations
- Create reusable SCSS mixins for complex patterns
- Use CSS modules to prevent style leaks

### ❌ Don'ts
- Don't duplicate Tailwind utilities in SCSS
- Don't create global SCSS styles for components
- Don't override Tailwind's responsive breakpoints
- Don't use SCSS for simple layout tasks
- Don't forget to use CSS modules to prevent style leaks

## 🎨 Examples

### Component with SCSS Module
```tsx
// EnhancedButton.tsx
import styles from './EnhancedButton.module.scss';

const EnhancedButton = ({ effect, ...props }) => {
  const buttonClasses = cn(
    buttonVariants({ variant, size }),
    styles.button,
    {
      [styles.gradient]: effect === 'gradient',
      [styles.neon]: effect === 'neon',
    }
  );
  
  return <button className={buttonClasses} {...props} />;
};
```

```scss
// EnhancedButton.module.scss
@import '../../styles/variables';
@import '../../styles/mixins';

.button {
  @include button-base;
  
  &.gradient {
    background: linear-gradient(135deg, rgb(var(--primary)), rgb(var(--primary) / 0.8));
    // Complex gradient effects...
  }
  
  &.neon {
    box-shadow: 0 0 5px rgb(var(--primary)), 0 0 10px rgb(var(--primary));
    animation: neon-pulse 2s infinite;
  }
}
```

### Using SCSS Mixins with Tailwind
```scss
// In globals.scss
@layer utilities {
  .chat-container {
    @apply flex flex-col h-full;
  }
  
  .chat-input {
    @apply flex-1 px-3 py-2 border rounded-lg;
    @include focus-ring; // SCSS mixin
  }
}
```

## 🚀 Available Features

### SCSS Variables
- Design tokens (spacing, typography, colors)
- Breakpoints and responsive values
- Animation durations and easing
- Z-index scale

### SCSS Mixins
- `@mixin focus-ring()` - Accessible focus states
- `@mixin button-base()` - Base button styles
- `@mixin chat-bubble()` - WhatsApp-style bubbles
- `@mixin glass-effect()` - Glass morphism
- `@mixin skeleton-loading()` - Loading states
- `@mixin custom-scrollbar()` - Custom scrollbars

### SCSS Animations
- `fadeIn`, `slideUp`, `slideDown`, `scaleIn`
- `bounce`, `pulse`, `spin`, `typing`
- `shake`, `neon-pulse`, `skeleton-pulse`

### Utility Classes
- `.glass`, `.glass-light`, `.glass-heavy`
- `.skeleton`, `.focus-ring`
- `.animate-*` classes for animations
- `.chat-*` classes for chat interface

## 🧪 Testing

Visit `/scss-demo` to see the SCSS + Tailwind integration in action, including:
- Enhanced button effects
- WhatsApp-style chat interface
- Glass morphism effects
- Loading states
- Custom animations

## 🔄 Migration from CSS

If you have existing CSS files:
1. Rename `.css` to `.scss`
2. Import SCSS partials as needed
3. Use `@apply` to incorporate Tailwind utilities
4. Convert to CSS modules for component-specific styles

## 📚 Resources

- [Sass Documentation](https://sass-lang.com/documentation)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [CSS Modules](https://github.com/css-modules/css-modules)
- [Next.js Styling](https://nextjs.org/docs/basic-features/built-in-css-support)
