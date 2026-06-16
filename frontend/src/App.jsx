import { useEffect, useState, useCallback } from 'react'
import Header from './components/Header'
import FilterBar from './components/FilterBar'
import OrderTable from './components/OrderTable'
import OrderDetail from './components/OrderDetail'
import NewOrderModal from './components/NewOrderModal'
import { fetchOrders, fetchDashboardSummary, fetchStoreLocations } from './api/client'

export default function App() {
  const [orders, setOrders] = useState([])
  const [summary, setSummary] = useState(null)
  const [locations, setLocations] = useState([])
  const [filters, setFilters] = useState({})
  const [selected, setSelected] = useState(null)
  const [showNewOrder, setShowNewOrder] = useState(false)
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')

  const load = useCallback(async () => {
    try {
      const [o, s, l] = await Promise.all([
        fetchOrders(filters),
        fetchDashboardSummary(),
        fetchStoreLocations(),
      ])
      setOrders(o)
      setSummary(s)
      setLocations(l)
      setErr('')
    } catch (e) {
      setErr('Could not reach the backend. Is it running and is VITE_API_URL set correctly?')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    load()
    const interval = setInterval(load, 30000) // poll every 30s for SLA countdowns / new alerts
    return () => clearInterval(interval)
  }, [load])

  function handleUpdated(updatedOrder) {
    setOrders(prev => prev.map(o => o.id === updatedOrder.id ? updatedOrder : o))
    setSelected(updatedOrder)
    fetchDashboardSummary().then(setSummary)
  }

  function handleCreated(newOrder) {
    setShowNewOrder(false)
    load()
  }

  return (
    <div className="min-h-screen">
      <Header summary={summary} />

      <main className="max-w-7xl mx-auto px-6 py-6">
        {err && (
          <div className="bg-danger/10 text-danger text-sm rounded px-4 py-3 mb-4">{err}</div>
        )}

        <FilterBar
          filters={filters}
          setFilters={setFilters}
          locations={locations}
          onNewOrder={() => setShowNewOrder(true)}
        />

        {loading ? (
          <div className="text-slate-500 text-sm py-10 text-center">Loading orders…</div>
        ) : (
          <OrderTable orders={orders} onSelect={setSelected} />
        )}
      </main>

      <OrderDetail
        order={selected}
        onClose={() => setSelected(null)}
        onUpdated={handleUpdated}
      />

      {showNewOrder && (
        <NewOrderModal
          onClose={() => setShowNewOrder(false)}
          onCreated={handleCreated}
        />
      )}
    </div>
  )
}
