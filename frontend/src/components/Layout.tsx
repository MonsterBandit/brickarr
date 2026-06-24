import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { IconMenu } from './icons';

export function Layout() {
  const [open, setOpen] = useState(false);
  return (
    <div className="app">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="main">
        <div className="topbar">
          <button
            className="hamburger"
            aria-label="Menu"
            onClick={() => setOpen((x) => !x)}
            style={{ background: 'transparent', border: 'none', padding: 8 }}
          >
            <IconMenu />
          </button>
        </div>
        <Outlet />
      </div>
    </div>
  );
}
