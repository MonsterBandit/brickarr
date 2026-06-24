import type { ReactNode, CSSProperties } from 'react';

interface Props {
  title?: string;
  actions?: ReactNode;
  children: ReactNode;
  style?: CSSProperties;
}

export function Card({ title, actions, children, style }: Props) {
  return (
    <div className="card" style={style}>
      {(title || actions) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
          {title && <h3 style={{ fontSize: 14, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{title}</h3>}
          {actions}
        </div>
      )}
      {children}
    </div>
  );
}
