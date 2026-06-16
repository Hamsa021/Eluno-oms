import { useEffect, useState } from 'react'
import { fetchOrderHistory, updateOrderStatus } from '../api/client'
import { STATUS_LABEL, STATUS_DOT, ALLOWED_TRANSITIONS, timeRemaining, riskColor, formatDate } from '../constants'

export default function OrderDetail({ order, onClose, onUpdated }) {
  const [history, setHistory] = useState([])
  const [newStatus, setNewStatus] = useState('')
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setHistory([])
    setNewStatus('')
    setReason('')
    setError('')
    if (order) {
      fetchOrderHistory(order.id).then(setHistory).catch(() => {})
    }
  }, [order])

  if (!order) return null

  const sla = timeRemaining(order.sla_deadline)
  const allowed = ALLOWED_TRANSITIONS[order.status] || []
  const reasonRequired = newStatus === 'qc_failed'

  async function submit() {
    if (!newStatus) return
    if (reasonRequired && !reason.trim()) {
      setError('A reason is required when logging a QC failure.')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const updated = await updateOrderStatus(order.id, {
        new_status: newStatus,
        reason: reason.trim() || null,
        changed_by: 'ops_team',
      })
      onUpdated(updated)
      setNewStatus('')
      setReason('')
      const h = await fetchOrderHistory(order.id)
      setHistory(h)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Update failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex justify-end z-30" onClick={onClose}>
      <div
        className="w-full max-w-md h-full bg-ink border-l border-line overflow-y-auto p-6"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex justify-between items-start mb-1">
          <h2 className="font-mono text-sm text-slate-400">{order.order_number}</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-200">✕</button>
        </div>
        <h3 className="text-lg font-semibold mb-4">{order.customer_name}</h3>

        <div className="grid grid-cols-2 gap-3 text-sm mb-5">
          <Field label="Phone" value={order.customer_phone} />
          <Field label="Location" value={order.store_location} />
          <Field label="Lens type" value={order.lens_type.replace('_', ' ')} />
          <Field label="Index / Coating" value={`${order.lens_index} / ${order.coating}`} />
          <Field label="Power (sphere)" value={order.sphere_power} />
          <Field label="Sourcing" value={order.in_house ? 'In-house' : 'Procured'} />
          <Field label="SLA deadline" value={formatDate(order.sla_deadline)} />
          <Field
            label="Time status"
            value={sla.label}
            valueClass={sla.breached ? 'text-danger' : 'text-slate-200'}
          />
          <Field
            label="Breach risk"
            value={`${(order.breach_risk_score * 100).toFixed(0)}%`}
            valueClass={riskColor(order.breach_risk_score)}
          />
          <Field label="QC fail count" value={order.qc_fail_count} />
        </div>

        <div className="border-t border-line pt-4 mb-5">
          <div className="flex items-center gap-2 mb-3">
            <span className={`w-2.5 h-2.5 rounded-full ${STATUS_DOT[order.status]}`} />
            <span className="text-sm font-medium">Current: {STATUS_LABEL[order.status]}</span>
          </div>

          {allowed.length > 0 ? (
            <div className="space-y-2">
              <select
                value={newStatus}
                onChange={e => setNewStatus(e.target.value)}
                className="w-full bg-panel border border-line rounded px-3 py-2 text-sm"
              >
                <option value="">Move to…</option>
                {allowed.map(s => (
                  <option key={s} value={s}>{STATUS_LABEL[s]}</option>
                ))}
              </select>

              {newStatus && (
                <textarea
                  value={reason}
                  onChange={e => setReason(e.target.value)}
                  placeholder={reasonRequired ? 'Reason for QC failure (required)' : 'Reason / note (optional)'}
                  className="w-full bg-panel border border-line rounded px-3 py-2 text-sm h-20 resize-none"
                />
              )}

              {error && <p className="text-xs text-danger">{error}</p>}

              <button
                disabled={!newStatus || submitting}
                onClick={submit}
                className="w-full bg-accent text-ink font-medium text-sm py-2 rounded disabled:opacity-40 hover:brightness-110 transition"
              >
                {submitting ? 'Updating…' : 'Update status'}
              </button>
            </div>
          ) : (
            <p className="text-xs text-slate-500">No further transitions — order is final.</p>
          )}
        </div>

        <div className="border-t border-line pt-4">
          <h4 className="text-xs uppercase tracking-wider text-slate-500 mb-3">History</h4>
          <div className="space-y-3">
            {history.map((h, i) => (
              <div key={i} className="text-xs">
                <div className="flex justify-between text-slate-300">
                  <span>
                    {h.from_status ? `${STATUS_LABEL[h.from_status] || h.from_status} → ` : ''}
                    {STATUS_LABEL[h.to_status] || h.to_status}
                  </span>
                  <span className="text-slate-500">{formatDate(h.changed_at)}</span>
                </div>
                {h.reason && <p className="text-slate-500 mt-0.5">{h.reason}</p>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function Field({ label, value, valueClass = 'text-slate-200' }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className={`text-sm ${valueClass}`}>{value}</div>
    </div>
  )
}
