import { STATUS_OPTIONS, STATUS_LABEL, LENS_TYPE_OPTIONS } from '../constants'

export default function FilterBar({ filters, setFilters, locations, onNewOrder }) {
  const update = (key, value) => setFilters(prev => ({ ...prev, [key]: value || undefined }))

  return (
    <div className="flex flex-wrap items-center gap-3 mb-5">
      <Select
        label="Status"
        value={filters.status || ''}
        onChange={v => update('status', v)}
        options={[['', 'All statuses'], ...STATUS_OPTIONS.map(s => [s, STATUS_LABEL[s]])]}
      />
      <Select
        label="Lens type"
        value={filters.lens_type || ''}
        onChange={v => update('lens_type', v)}
        options={[['', 'All lens types'], ...LENS_TYPE_OPTIONS.map(l => [l, l.replace('_', ' ')])]}
      />
      <Select
        label="Location"
        value={filters.store_location || ''}
        onChange={v => update('store_location', v)}
        options={[['', 'All locations'], ...(locations || []).map(l => [l, l])]}
      />
      <label className="flex items-center gap-2 text-xs text-slate-400 ml-1 cursor-pointer">
        <input
          type="checkbox"
          checked={!!filters.at_risk_only}
          onChange={e => update('at_risk_only', e.target.checked || undefined)}
          className="accent-accent"
        />
        At-risk only
      </label>

      <div className="flex-1" />

      <button
        onClick={onNewOrder}
        className="bg-accent text-ink text-sm font-medium px-4 py-2 rounded hover:brightness-110 transition"
      >
        + New Order
      </button>
    </div>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      aria-label={label}
      className="bg-panel border border-line text-sm text-slate-200 rounded px-3 py-2 focus:outline-none focus:border-accent"
    >
      {options.map(([val, lbl]) => (
        <option key={val} value={val}>{lbl}</option>
      ))}
    </select>
  )
}
