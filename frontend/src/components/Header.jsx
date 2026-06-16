export default function Header({ summary }) {
  return (
    <header className="border-b border-line bg-panel/60 backdrop-blur sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-accent flex items-center justify-center font-mono font-bold text-ink text-sm">
            E
          </div>
          <div>
            <h1 className="text-sm font-semibold tracking-wide">ELUNO ORDER CONTROL</h1>
            <p className="text-xs text-slate-500">Eyewear fulfilment — intake to delivery</p>
          </div>
        </div>

        {summary && (
          <div className="flex gap-6 font-mono text-sm">
            <Stat label="Active" value={summary.total_active} />
            <Stat label="At Risk" value={summary.at_risk_count} tone="warn" />
            <Stat label="Breached" value={summary.breached_count} tone="danger" />
          </div>
        )}
      </div>
    </header>
  )
}

function Stat({ label, value, tone }) {
  const color = tone === 'warn' ? 'text-warn' : tone === 'danger' ? 'text-danger' : 'text-slate-100'
  return (
    <div className="text-right">
      <div className={`text-lg font-semibold ${color}`}>{value ?? '—'}</div>
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
    </div>
  )
}
