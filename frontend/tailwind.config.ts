import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './features/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        border: 'rgb(var(--border))',
        input: 'rgb(var(--input))',
        ring: 'rgb(var(--ring))',
        background: 'rgb(var(--background))',
        foreground: 'rgb(var(--foreground))',
        primary: {
          DEFAULT: 'rgb(var(--primary))',
          foreground: 'rgb(var(--primary-foreground))',
          50: 'rgb(var(--primary) / 0.05)',
          100: 'rgb(var(--primary) / 0.1)',
          500: 'rgb(var(--primary))',
          600: 'rgb(var(--secondary))',
          700: 'rgb(var(--secondary) / 0.8)',
        },
        secondary: {
          DEFAULT: 'rgb(var(--secondary))',
          foreground: 'rgb(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'rgb(var(--error))',
          foreground: 'rgb(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'rgb(var(--muted))',
          foreground: 'rgb(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'rgb(var(--accent))',
          foreground: 'rgb(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'rgb(var(--popover))',
          foreground: 'rgb(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'rgb(var(--card))',
          foreground: 'rgb(var(--card-foreground))',
        },
        surface: 'rgb(var(--surface))',
        success: 'rgb(var(--success))',
        warning: 'rgb(var(--warning))',
        error: 'rgb(var(--error))',
      },
      borderRadius: {
        lg: '8px',
        xl: '12px',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'typing': 'typing 1.4s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        typing: {
          '0%, 20%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
          '80%, 100%': { transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}

export default config