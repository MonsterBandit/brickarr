import type { SVGProps } from 'react';

const base: SVGProps<SVGSVGElement> = {
  width: 18,
  height: 18,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.75,
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
};

export const IconSets = () => (
  <svg {...base}><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
);
export const IconCalendar = () => (
  <svg {...base}><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>
);
export const IconActivity = () => (
  <svg {...base}><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
);
export const IconWanted = () => (
  <svg {...base}><path d="M19 14V5a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v9l7 4 7-4Z"/></svg>
);
export const IconSettings = () => (
  <svg {...base}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 0 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1A2 2 0 1 1 4.3 17l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 0 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1A2 2 0 1 1 7 4.3l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 0 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9c.2.6.7 1 1.3 1H21a2 2 0 0 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z"/></svg>
);
export const IconSystem = () => (
  <svg {...base}><rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>
);
export const IconChevron = ({ open }: { open: boolean }) => (
  <svg {...base} width={14} height={14} style={{ transform: `rotate(${open ? 90 : 0}deg)`, transition: 'transform 0.12s' }}>
    <path d="M9 18l6-6-6-6"/>
  </svg>
);
export const IconMenu = () => (
  <svg {...base}><path d="M3 6h18M3 12h18M3 18h18"/></svg>
);
export const IconBrick = () => (
  <svg {...base} viewBox="0 0 24 24"><rect x="3" y="8" width="18" height="12" rx="1"/><circle cx="8" cy="6" r="1.5"/><circle cx="16" cy="6" r="1.5"/></svg>
);
