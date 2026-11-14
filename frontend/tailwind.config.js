import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

// Absolute globs so the build works regardless of the process working directory.
const here = dirname(fileURLToPath(import.meta.url));

/**
 * Every palette is backed by CSS variables (see src/index.css) so the light and dark
 * themes are a variable swap on <html data-theme>, with no per-component dark: variants.
 */
const shades = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900];
const varScale = (name, steps = shades) =>
  Object.fromEntries(steps.map((s) => [s, `rgb(var(--${name}-${s}) / <alpha-value>)`]));

/** @type {import('tailwindcss').Config} */
export default {
  content: [join(here, 'index.html'), join(here, 'src/**/*.{ts,tsx}')].map((p) => p.split('\\').join('/')),
  theme: {
    extend: {
      colors: {
        surface: 'rgb(var(--surface) / <alpha-value>)',
        canvas: 'rgb(var(--canvas) / <alpha-value>)',
        slate: varScale('slate'),
        accent: varScale('accent'),
        emerald: varScale('emerald'),
        amber: varScale('amber'),
        red: varScale('red'),
        sky: varScale('sky'),
        brand: {
          navy: '#0A0A14',
          blue: '#F2A93B',
          sky: '#B9B9CC',
          lime: '#F2A93B',
          periwinkle: '#F6C66E',
          kicker: '#F2A93B',
          heading: '#0A0A14',
          table: '#1A1A28',
        },
      },
      fontFamily: {
        sans: ['"Inter"', 'Calibri', 'Arial', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      keyframes: {
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(4px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'value-pulse': {
          '0%': { opacity: '0.35' },
          '100%': { opacity: '1' },
        },
      },
      animation: {
        'fade-up': 'fade-up 240ms ease-out both',
        'value-pulse': 'value-pulse 420ms ease-out',
      },
      boxShadow: {
        card: '0 1px 2px rgb(var(--shadow) / 0.06), 0 1px 1px rgb(var(--shadow) / 0.04)',
        lift: '0 8px 24px -8px rgb(var(--shadow) / 0.18)',
      },
    },
  },
  plugins: [],
};
