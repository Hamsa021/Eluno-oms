export const STATUS_OPTIONS = [
  'placed', 'inventory_check', 'processing', 'lens_fitting',
  'qc', 'qc_failed', 'dispatched', 'delivered', 'cancelled',
]

export const LENS_TYPE_OPTIONS = ['single_vision', 'bifocal', 'progressive', 'contact_lens']

export const STATUS_LABEL = {
  placed: 'Placed',
  inventory_check: 'Inventory Check',
  processing: 'Processing',
  lens_fitting: 'Lens Fitting',
  qc: 'QC',
  qc_failed: 'QC Failed',
  dispatched: 'Dispatched',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
}

export const STATUS_DOT = {
  placed: 'bg-slate-400',
  inventory_check: 'bg-sky-400',
  processing: 'bg-indigo-400',
  lens_fitting: 'bg-violet-400',
  qc: 'bg-amber-400',
  qc_failed: 'bg-danger',
  dispatched: 'bg-teal-400',
  delivered: 'bg-ok',
  cancelled: 'bg-slate-600',
}

export const ALLOWED_TRANSITIONS = {
  placed: ['inventory_check', 'cancelled'],
  inventory_check: ['processing', 'cancelled'],
  processing: ['lens_fitting', 'cancelled'],
  lens_fitting: ['qc', 'cancelled'],
  qc: ['dispatched', 'qc_failed'],
  qc_failed: ['processing'],
  dispatched: ['delivered'],
  delivered: [],
  cancelled: [],
}

export function timeRemaining(slaDeadline) {
  const now = new Date()
  const deadline = new Date(slaDeadline)
  const diffMs = deadline - now
  const breached = diffMs < 0
  const absMs = Math.abs(diffMs)
  const hours = Math.floor(absMs / 3600000)
  const mins = Math.floor((absMs % 3600000) / 60000)
  const label = hours > 0 ? `${hours}h ${mins}m` : `${mins}m`
  return { breached, label: breached ? `Breached ${label} ago` : `${label} left` }
}

export function riskColor(score) {
  if (score >= 0.6) return 'text-danger'
  if (score >= 0.35) return 'text-warn'
  return 'text-ok'
}

export function formatDate(d) {
  return new Date(d).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' })
}
