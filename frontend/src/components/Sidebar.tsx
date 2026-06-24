import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  IconSets, IconCalendar, IconActivity, IconWanted, IconSettings, IconSystem, IconChevron, IconBrick,
} from './icons';

interface SubItem { to: string; label: string; }

const setsSubs: SubItem[] = [
  { to: '/sets/add', label: 'Add New' },
  { to: '/sets/import', label: 'Import' },
  { to: '/sets/discover', label: 'Discover' },
  { to: '/sets/themes', label: 'Themes' },
  { to: '/sets/minifigs', label: 'Minifigs' },
  { to: '/sets/parts', label: 'Parts' },
];

interface Props { open: boolean; onClose: () => void; }

export function Sidebar({ open, onClose }: Props) {
  const location = useLocation();
  const setsActive = location.pathname.startsWith('/sets');
  const [setsExpanded, setSetsExpanded] = useState(setsActive);

  return (
    <aside className={`sidebar${open ? ' open' : ''}`}>
      <div className="sidebar-brand">
        <IconBrick />
        <span>Brickarr</span>
      </div>
      <nav className="sidebar-nav">
        <div
          className={`sidebar-item${location.pathname === '/sets' ? ' active' : ''}`}
          onClick={() => setSetsExpanded((x) => !x)}
          style={{ justifyContent: 'space-between' }}
        >
          <NavLink
            to="/sets"
            end
            onClick={(e) => { e.stopPropagation(); onClose(); }}
            style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', color: 'inherit', flex: 1 }}
          >
            <IconSets />
            <span>Sets</span>
          </NavLink>
          <IconChevron open={setsExpanded} />
        </div>
        {setsExpanded && setsSubs.map((s) => (
          <NavLink
            key={s.to}
            to={s.to}
            onClick={onClose}
            className={({ isActive }) => `sidebar-sub${isActive ? ' active' : ''}`}
          >
            {s.label}
          </NavLink>
        ))}

        <NavLink to="/calendar" onClick={onClose} className={({ isActive }) => `sidebar-item${isActive ? ' active' : ''}`}>
          <IconCalendar /><span>Calendar</span>
        </NavLink>
        <NavLink to="/activity" onClick={onClose} className={({ isActive }) => `sidebar-item${isActive ? ' active' : ''}`}>
          <IconActivity /><span>Activity</span>
        </NavLink>
        <NavLink to="/wanted" onClick={onClose} className={({ isActive }) => `sidebar-item${isActive ? ' active' : ''}`}>
          <IconWanted /><span>Wanted</span>
        </NavLink>
        <NavLink to="/settings" onClick={onClose} className={({ isActive }) => `sidebar-item${isActive ? ' active' : ''}`}>
          <IconSettings /><span>Settings</span>
        </NavLink>
        <NavLink to="/system" onClick={onClose} className={({ isActive }) => `sidebar-item${isActive ? ' active' : ''}`}>
          <IconSystem /><span>System</span>
        </NavLink>
      </nav>
    </aside>
  );
}
