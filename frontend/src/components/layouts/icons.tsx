/* eslint-disable react-refresh/only-export-components -- icon map is a stable constant */
/** Minimal 24px stroke icon set (original artwork). */
import type { SVGProps } from 'react';

type P = SVGProps<SVGSVGElement>;

function Icon({ children, ...p }: P & { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      {...p}
    >
      {children}
    </svg>
  );
}

export const Icons = {
  calculator: (p: P) => (
    <Icon {...p}>
      <rect x="4" y="3" width="16" height="18" rx="2" />
      <path d="M8 7h8M8 12h1M12 12h1M16 12h0M8 16h1M12 16h1M16 16v0" />
    </Icon>
  ),
  folder: (p: P) => (
    <Icon {...p}>
      <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    </Icon>
  ),
  bolt: (p: P) => (
    <Icon {...p}>
      <path d="M13 2 4 14h7l-1 8 9-12h-7z" />
    </Icon>
  ),
  snowflake: (p: P) => (
    <Icon {...p}>
      <path d="M12 2v20M4.5 6.5l15 11M19.5 6.5l-15 11M9 4l3 2 3-2M9 20l3-2 3 2" />
    </Icon>
  ),
  battery: (p: P) => (
    <Icon {...p}>
      <rect x="2" y="7" width="17" height="10" rx="2" />
      <path d="M22 11v2M6 10v4M10 10v4" />
    </Icon>
  ),
  plug: (p: P) => (
    <Icon {...p}>
      <path d="M9 2v5M15 2v5M6 7h12v4a6 6 0 0 1-12 0zM12 17v5" />
    </Icon>
  ),
  grid: (p: P) => (
    <Icon {...p}>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </Icon>
  ),
  transformer: (p: P) => (
    <Icon {...p}>
      <circle cx="9" cy="12" r="5" />
      <circle cx="15" cy="12" r="5" />
      <path d="M2 12h2M20 12h2" />
    </Icon>
  ),
  generator: (p: P) => (
    <Icon {...p}>
      <rect x="3" y="6" width="18" height="12" rx="2" />
      <path d="M12 8.5 9.5 12.5h5L12 16.5M6 18v2M18 18v2" />
    </Icon>
  ),
  storage: (p: P) => (
    <Icon {...p}>
      <rect x="3" y="4" width="18" height="16" rx="2" />
      <path d="M3 9h18M3 14h18M7 6.5h.01M7 11.5h.01M7 16.5h.01" />
    </Icon>
  ),
  cpu: (p: P) => (
    <Icon {...p}>
      <rect x="6" y="6" width="12" height="12" rx="1.5" />
      <rect x="9.5" y="9.5" width="5" height="5" />
      <path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4" />
    </Icon>
  ),
  book: (p: P) => (
    <Icon {...p}>
      <path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2zM4 21V5M8 7h7" />
    </Icon>
  ),
  library: (p: P) => (
    <Icon {...p}>
      <path d="M4 4v16M9 4v16M14 5l5 15M3 20h18" />
    </Icon>
  ),
  settings: (p: P) => (
    <Icon {...p}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
    </Icon>
  ),
  sun: (p: P) => (
    <Icon {...p}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </Icon>
  ),
  moon: (p: P) => (
    <Icon {...p}>
      <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" />
    </Icon>
  ),
  menu: (p: P) => (
    <Icon {...p}>
      <path d="M4 6h16M4 12h16M4 18h16" />
    </Icon>
  ),
  close: (p: P) => (
    <Icon {...p}>
      <path d="M6 6l12 12M18 6 6 18" />
    </Icon>
  ),
  chevron: (p: P) => (
    <Icon {...p}>
      <path d="m15 18-6-6 6-6" />
    </Icon>
  ),
};

export type IconName = keyof typeof Icons;
