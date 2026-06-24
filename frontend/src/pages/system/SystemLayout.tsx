import { Outlet } from 'react-router-dom';
import { PageHeader } from '../../components/PageHeader';
import { Tabs } from '../../components/Tabs';

const tabs = [
  { to: '/system/status', label: 'Status' },
  { to: '/system/tasks', label: 'Tasks' },
  { to: '/system/backup', label: 'Backup' },
  { to: '/system/updates', label: 'Updates' },
  { to: '/system/events', label: 'Events' },
  { to: '/system/log-files', label: 'Log Files' },
];

export function SystemLayout() {
  return (
    <div className="page">
      <PageHeader title="System" />
      <Tabs tabs={tabs} />
      <Outlet />
    </div>
  );
}
