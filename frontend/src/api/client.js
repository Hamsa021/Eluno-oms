import axios from 'axios'

// Point this to your deployed backend URL in production (.env: VITE_API_URL)
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL: API_URL })

export const fetchOrders = (filters = {}) =>
  api.get('/orders', { params: filters }).then(r => r.data)

export const fetchOrderHistory = (orderId) =>
  api.get(`/orders/${orderId}/history`).then(r => r.data)

export const createOrder = (payload) =>
  api.post('/orders', payload).then(r => r.data)

export const updateOrderStatus = (orderId, payload) =>
  api.patch(`/orders/${orderId}/status`, payload).then(r => r.data)

export const fetchDashboardSummary = () =>
  api.get('/dashboard/summary').then(r => r.data)

export const fetchStoreLocations = () =>
  api.get('/dashboard/locations').then(r => r.data)

export const fetchInventory = () =>
  api.get('/inventory').then(r => r.data)

export const checkInventory = (payload) =>
  api.post('/inventory/check', payload).then(r => r.data)
