interface Props {
  value: number;
  max: number;
}

export function ProgressBar({ value, max }: Props) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="progress" title={`${value} / ${max}`}>
      <div className="fill" style={{ width: `${pct}%` }} />
    </div>
  );
}
