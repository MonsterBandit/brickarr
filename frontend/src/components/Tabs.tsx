import { NavLink } from 'react-router-dom';

interface Tab {
  to: string;
  label: string;
  end?: boolean;
}

interface Props {
  tabs: Tab[];
}

export function Tabs({ tabs }: Props) {
  return (
    <div className="tabs">
      {tabs.map((t) => (
        <NavLink
          key={t.to}
          to={t.to}
          end={t.end}
          className={({ isActive }) => `tab${isActive ? ' active' : ''}`}
        >
          {t.label}
        </NavLink>
      ))}
    </div>
  );
}
