/** Light / dark / system theme, applied as <html data-theme> with a brief cross-fade. */
import { create } from 'zustand';

export type ThemePref = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

const KEY = 'hallplan.theme';

function systemTheme(): ResolvedTheme {
  try {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}

function readPref(): ThemePref {
  try {
    const v = localStorage.getItem(KEY);
    return v === 'light' || v === 'dark' || v === 'system' ? v : 'system';
  } catch {
    return 'system';
  }
}

let fadeTimer: ReturnType<typeof setTimeout> | undefined;

function apply(theme: ResolvedTheme, animate: boolean) {
  const root = document.documentElement;
  if (animate) {
    root.classList.add('theme-transition');
    clearTimeout(fadeTimer);
    fadeTimer = setTimeout(() => root.classList.remove('theme-transition'), 320);
  }
  root.setAttribute('data-theme', theme);
}

interface ThemeState {
  pref: ThemePref;
  resolved: ResolvedTheme;
  setPref: (pref: ThemePref) => void;
  toggle: () => void;
}

const initialPref = readPref();
const initialResolved = initialPref === 'system' ? systemTheme() : initialPref;

export const useThemeStore = create<ThemeState>((set, get) => ({
  pref: initialPref,
  resolved: initialResolved,
  setPref: (pref) => {
    const resolved = pref === 'system' ? systemTheme() : pref;
    try {
      localStorage.setItem(KEY, pref);
    } catch {
      /* ignore */
    }
    apply(resolved, true);
    set({ pref, resolved });
  },
  toggle: () => get().setPref(get().resolved === 'dark' ? 'light' : 'dark'),
}));

if (typeof window !== 'undefined') {
  apply(initialResolved, false);
  try {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (useThemeStore.getState().pref === 'system') useThemeStore.getState().setPref('system');
    });
  } catch {
    /* older browsers */
  }
}

/** Chart colours that cannot use CSS variables (SVG presentation attributes). */
export function chartTheme(theme: ResolvedTheme) {
  return theme === 'dark'
    ? {
        grid: '#223054',
        axis: '#33436b',
        tick: '#93a1c0',
        label: '#dde4f2',
        link: '#2a4c9c',
        cursor: '#16223f',
      }
    : {
        grid: '#dce3ef',
        axis: '#c4d2e8',
        tick: '#5b6478',
        label: '#182036',
        link: '#adc8ff',
        cursor: '#eaeff9',
      };
}
