import { STATUS_LABEL, STATUS_DOT, timeRemaining, riskColor } from '../constants'

export default function OrderTable({ orders, onSelect }) {
  if (!orders || orders.length === 0) {
    return (
      <div className="border border-line rounded-lg py-16 text-center text-slate-500 text-sm">
        No orders match these filters.
      </div>
    )
  }

  return (
    <div className="border border-line rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-panel text-left text-[11px] uppercase tracking-wider text-slate-500">
            <Th>Order</Th>
            <Th>Customer</Th>
            <Th>Lens</Th>
            <Th>Location</Th>
            <Th>Status</Th>
            <Th>SLA</Th>
            <Th>Risk</Th>
          </tr>
        </thead>
        <tbody>
          {orders.map(o => (
            <Row key={o.id} order={o} onSelect={onSelect} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Row({ order, onSelect }) {
  const sla = timeRemaining(order.sla_deadline)
  const isFinal = ['delivered', 'cancelled'].includes(order.status)

  return (
    <tr
      onClick={() => onSelect(order)}
      className="border-t border-line hover:bg-panel/70 cursor-pointer transition"
    >
      <Td className="font-mono text-xs text-slate-400">{order.order_number}</Td>
      <Td>{order.customer_name}</Td>
      <Td className="text-xs text-slate-400">
        {order.lens_type.replace('_', ' ')} · {order.lens_index} · {order.coating}
        <span className={`ml-2 text-[10px] px-1.5 py-0.5 rounded ${order.in_house ? 'bg-ok/10 text-ok' : 'bg-warn/10 text-warn'}`}>
          {order.in_house ? 'in-house' : 'procured'}
        </span>
      </Td>
      <Td className="text-xs text-slate-400">{order.store_location}</Td>
      <Td>
        <span className="inline-flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${STATUS_DOT[order.status]}`} />
          {STATUS_LABEL[order.status]}
        </span>
      </Td>
      <Td className={`text-xs ${!isFinal && sla.breached ? 'text-danger font-medium' : 'text-slate-400'}`}>
        {isFinal ? '—' : sla.label}
      </Td>
      <Td className={`font-mono text-xs ${riskColor(order.breach_risk_score)}`}>
        {(order.breach_risk_score * 100).toFixed(0)}%
      </Td>
    </tr>
  )
}

function Th({ children }) {
  return <th className="px-4 py-3 font-medium">{children}</th>
}
function Td({ children, className = '' }) {
  return <td className={`px-4 py-3 ${className}`}>{children}</td>
}
