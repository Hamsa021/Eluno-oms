import { useState } from 'react'
import { createOrder, checkInventory } from '../api/client'
import { LENS_TYPE_OPTIONS } from '../constants'

const empty = {
  customer_name: '', customer_phone: '', customer_email: '',
  store_location: '', source: 'store',
  sphere_power: 0, cylinder_power: 0,
  lens_type: 'single_vision', lens_index: '1.50', coating: 'None', frame_sku: '',
}

export default function NewOrderModal({ onClose, onCreated }) {
  const [form, setForm] = useState(empty)
  const [preview, setPreview] = useState(null)
  const [checking, setChecking] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }))

  async function runPreview() {
    setChecking(true)
    try {
      const result = await checkInventory({
        lens_type: form.lens_type,
        lens_index: form.lens_index,
        coating: form.coating,
        sphere_power: Number(form.sphere_power),
      })
      setPreview(result)
    } catch {
      setPreview(null)
    } finally {
      setChecking(false)
    }
  }

  async function submit() {
    if (!form.customer_name || !form.customer_phone || !form.store_location) {
      setError('Customer name, phone, and store location are required.')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      const order = await createOrder({
        ...form,
        sphere_power: Number(form.sphere_power),
        cylinder_power: Number(form.cylinder_power),
      })
      onCreated(order)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Could not create order.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-30 p-4" onClick={onClose}>
      <div
        className="bg-ink border border-line rounded-lg w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-5">
          <h2 className="text-base font-semibold">New order</h2>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-200">✕</button>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <Input label="Customer name" value={form.customer_name} onChange={v => set('customer_name', v)} />
          <Input label="Phone" value={form.customer_phone} onChange={v => set('customer_phone', v)} />
          <Input label="Email (optional)" value={form.customer_email} onChange={v => set('customer_email', v)} />
          <Input label="Store location" value={form.store_location} onChange={v => set('store_location', v)} />
          <Select label="Source" value={form.source} onChange={v => set('source', v)}
            options={['store', 'website', 'app', 'partner']} />
          <Input label="Frame SKU (optional)" value={form.frame_sku} onChange={v => set('frame_sku', v)} />
        </div>

        <div className="border-t border-line pt-4 mb-4">
          <h3 className="text-xs uppercase tracking-wider text-slate-500 mb-3">Prescription</h3>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Sphere power" type="number" step="0.25" value={form.sphere_power} onChange={v => set('sphere_power', v)} />
            <Input label="Cylinder power" type="number" step="0.25" value={form.cylinder_power} onChange={v => set('cylinder_power', v)} />
            <Select label="Lens type" value={form.lens_type} onChange={v => set('lens_type', v)} options={LENS_TYPE_OPTIONS} />
            <Input label="Lens index" value={form.lens_index} onChange={v => set('lens_index', v)} />
            <Input label="Coating" value={form.coating} onChange={v => set('coating', v)} />
          </div>

          <button
            onClick={runPreview}
            disabled={checking}
            className="mt-3 text-xs border border-line rounded px-3 py-1.5 text-slate-300 hover:border-accent transition"
          >
            {checking ? 'Checking…' : 'Preview inventory match'}
          </button>

          {preview && (
            <div className={`mt-2 text-xs rounded px-3 py-2 ${preview.in_house ? 'bg-ok/10 text-ok' : 'bg-warn/10 text-warn'}`}>
              {preview.in_house
                ? `In-house · ${preview.available_qty} units available · ready in ~${preview.estimated_ready_hours}h`
                : `Needs procurement · est. ready in ~${preview.estimated_ready_hours}h`}
            </div>
          )}
        </div>

        {error && <p className="text-xs text-danger mb-3">{error}</p>}

        <button
          onClick={submit}
          disabled={submitting}
          className="w-full bg-accent text-ink font-medium text-sm py-2.5 rounded disabled:opacity-40 hover:brightness-110 transition"
        >
          {submitting ? 'Creating…' : 'Create order'}
        </button>
      </div>
    </div>
  )
}

function Input({ label, value, onChange, type = 'text', step }) {
  return (
    <label className="block text-xs">
      <span className="text-slate-500 mb-1 block">{label}</span>
      <input
        type={type}
        step={step}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full bg-panel border border-line rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-accent"
      />
    </label>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <label className="block text-xs">
      <span className="text-slate-500 mb-1 block">{label}</span>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full bg-panel border border-line rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-accent"
      >
        {options.map(o => <option key={o} value={o}>{o.replace('_', ' ')}</option>)}
      </select>
    </label>
  )
}
