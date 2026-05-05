import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        charcoal: '#1A1A2E',
        'specifio-blue': '#2B6CB0',
        'clean-white': '#FAFAFA',
        'warm-grey': '#E2E0DC',
        slate: '#4A5568',
        forest: '#276749',
        ember: '#C53030',
      },
      fontFamily: {
        satoshi: ['Satoshi', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '6px',
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.08)',
        'card-hover': '0 1px 3px rgba(0,0,0,0.1)',
      },
      fontSize: {
        label: ['13px', { lineHeight: '1.3', fontWeight: '500', letterSpacing: '0.02em' }],
        body: ['16px', { lineHeight: '1.6' }],
        tech: ['14px', { lineHeight: '1.5' }],
        'spec-badge': ['11px', { lineHeight: '1.4' }],
      },
    },
  },
  plugins: [],
} satisfies Config
