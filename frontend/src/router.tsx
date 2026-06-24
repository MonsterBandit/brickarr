import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { SetsGrid } from './pages/sets/SetsGrid';
import { SetDetail } from './pages/sets/SetDetail';
import { AddNew } from './pages/sets/AddNew';
import { Import as SetsImport } from './pages/sets/Import';
import { Discover } from './pages/sets/Discover';
import { Themes } from './pages/sets/Themes';
import { Minifigs } from './pages/sets/Minifigs';
import { Parts } from './pages/sets/Parts';
import { Calendar } from './pages/Calendar';
import { Activity } from './pages/Activity';
import { Wanted } from './pages/Wanted';
import { SettingsLayout } from './pages/settings/SettingsLayout';
import { General } from './pages/settings/General';
import { UI } from './pages/settings/UI';
import { Tags } from './pages/settings/Tags';
import { Connect } from './pages/settings/Connect';
import { MediaManagement } from './pages/settings/MediaManagement';
import { Pricing } from './pages/settings/Pricing';
import { DataSources } from './pages/settings/DataSources';
import { ImportLists } from './pages/settings/ImportLists';
import { SystemLayout } from './pages/system/SystemLayout';
import { Status } from './pages/system/Status';
import { Tasks } from './pages/system/Tasks';
import { Backup } from './pages/system/Backup';
import { Updates } from './pages/system/Updates';
import { Events } from './pages/system/Events';
import { LogFiles } from './pages/system/LogFiles';

export const router = createBrowserRouter([
  { path: '/login', element: <Login /> },
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/sets" replace /> },
      { path: 'sets', element: <SetsGrid /> },
      { path: 'sets/add', element: <AddNew /> },
      { path: 'sets/import', element: <SetsImport /> },
      { path: 'sets/discover', element: <Discover /> },
      { path: 'sets/themes', element: <Themes /> },
      { path: 'sets/minifigs', element: <Minifigs /> },
      { path: 'sets/parts', element: <Parts /> },
      { path: 'sets/:id', element: <SetDetail /> },
      { path: 'calendar', element: <Calendar /> },
      { path: 'activity', element: <Activity /> },
      { path: 'wanted', element: <Wanted /> },
      {
        path: 'settings',
        element: <SettingsLayout />,
        children: [
          { index: true, element: <Navigate to="/settings/general" replace /> },
          { path: 'general', element: <General /> },
          { path: 'ui', element: <UI /> },
          { path: 'tags', element: <Tags /> },
          { path: 'connect', element: <Connect /> },
          { path: 'media-management', element: <MediaManagement /> },
          { path: 'pricing', element: <Pricing /> },
          { path: 'data-sources', element: <DataSources /> },
          { path: 'import-lists', element: <ImportLists /> },
        ],
      },
      {
        path: 'system',
        element: <SystemLayout />,
        children: [
          { index: true, element: <Navigate to="/system/status" replace /> },
          { path: 'status', element: <Status /> },
          { path: 'tasks', element: <Tasks /> },
          { path: 'backup', element: <Backup /> },
          { path: 'updates', element: <Updates /> },
          { path: 'events', element: <Events /> },
          { path: 'log-files', element: <LogFiles /> },
        ],
      },
    ],
  },
]);
