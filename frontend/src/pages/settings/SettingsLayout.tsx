import { Outlet } from 'react-router-dom';
import { PageHeader } from '../../components/PageHeader';
import { Tabs } from '../../components/Tabs';

const tabs = [
  { to: '/settings/general', label: 'General' },
  { to: '/settings/ui', label: 'UI' },
  { to: '/settings/tags', label: 'Tags' },
  { to: '/settings/connect', label: 'Connect' },
  { to: '/settings/media-management', label: 'Media Management' },
  { to: '/settings/pricing', label: 'Pricing' },
  { to: '/settings/data-sources', label: 'Data Sources' },
  { to: '/settings/import-lists', label: 'Import Lists' },
];

export function SettingsLayout() {
  return (
    <div className="page">
      <PageHeader title="Settings" />
      <Tabs tabs={tabs} />
      <Outlet />
    </div>
  );
}
