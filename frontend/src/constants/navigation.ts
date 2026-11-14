import type { IconName } from '../components/layouts/icons';

export interface NavItem {
  to: string;
  label: string;
  icon: IconName;
  /** extra paths that should highlight this item */
  match?: string[];
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

export const NAV_SECTIONS: NavSection[] = [
  {
    title: 'Workspace',
    items: [
      { to: '/calculator', label: 'Calculator', icon: 'calculator' },
      { to: '/projects', label: 'Saved Projects', icon: 'folder' },
    ],
  },
  {
    title: 'Engineering tools',
    items: [
      {
        to: '/tools/kw-kva',
        label: 'Power',
        icon: 'bolt',
        match: ['/tools/circuit', '/tools/units', '/tools/rack-count'],
      },
      { to: '/tools/cooling', label: 'Cooling', icon: 'snowflake' },
      { to: '/tools/ups-sizing', label: 'UPS', icon: 'battery' },
      { to: '/tools/pdu', label: 'PDU', icon: 'plug' },
      { to: '/tools/rack-density', label: 'Rack Density', icon: 'grid' },
      { to: '/tools/transformer', label: 'Transformer', icon: 'transformer' },
      { to: '/tools/generator', label: 'Generator', icon: 'generator' },
      { to: '/tools/bess', label: 'BESS', icon: 'storage' },
      { to: '/tools/ai-rack', label: 'AI / GPU Rack', icon: 'cpu' },
    ],
  },
  {
    title: 'Knowledge',
    items: [
      { to: '/methodology', label: 'Methodology', icon: 'book' },
      { to: '/references', label: 'Reference', icon: 'library' },
      { to: '/settings', label: 'Settings', icon: 'settings' },
    ],
  },
];

export const POWER_TABS = [
  { to: '/tools/kw-kva', label: 'kW ↔ kVA' },
  { to: '/tools/circuit', label: 'Circuits' },
  { to: '/tools/units', label: 'Unit converter' },
  { to: '/tools/rack-count', label: 'Rack count' },
];

export function titleForPath(pathname: string): string {
  for (const s of NAV_SECTIONS)
    for (const i of s.items) if (i.to === pathname || i.match?.includes(pathname)) return i.label;
  return 'HallPlan';
}
