import { PageHeader } from './PageHeader';

interface Props {
  title: string;
  endpoint?: string;
  note?: string;
}

export function Stub({ title, endpoint, note }: Props) {
  const subtitle = endpoint
    ? `Coming in alpha-1 — populated by ${endpoint}`
    : note ?? 'Coming in alpha-1';
  return (
    <div className="page">
      <PageHeader title={title} subtitle={subtitle} />
      <div className="card empty">Placeholder.</div>
    </div>
  );
}
