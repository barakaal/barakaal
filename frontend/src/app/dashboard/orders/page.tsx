'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ordersApi } from '@/lib/api'
import { formatCurrency, formatDateTime, getStatusColor } from '@/lib/utils'
import { ShoppingCart, Search, Eye } from 'lucide-react'
import Badge from '@/components/ui/Badge'
import StatCard from '@/components/ui/StatCard'
import Modal from '@/components/ui/Modal'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

const MOCK_ORDERS = [
  { id: 1, order_number: 'ORD-2026-001', customer_name: 'Marie Dupont', customer_email: 'marie@example.com', status: 'DELIVERED', total_usd: 89.97, items_count: 3, created_at: '2026-05-24T10:30:00Z', tracking_number: 'TRK123456789', shipping_address: '12 Rue de la Paix, Paris 75001' },
  { id: 2, order_number: 'ORD-2026-002', customer_name: 'Jean Martin', customer_email: 'jean@example.com', status: 'SHIPPED', total_usd: 44.99, items_count: 1, created_at: '2026-05-25T14:15:00Z', tracking_number: 'TRK987654321', shipping_address: '5 Avenue Victor Hugo, Lyon 69001' },
  { id: 3, order_number: 'ORD-2026-003', customer_name: 'Sophie Bernard', customer_email: 'sophie@example.com', status: 'PROCESSING', total_usd: 129.95, items_count: 4, created_at: '2026-05-26T08:00:00Z', tracking_number: null, shipping_address: '8 Rue du Commerce, Bordeaux 33000' },
  { id: 4, order_number: 'ORD-2026-004', customer_name: 'Pierre Moreau', customer_email: 'pierre@example.com', status: 'PENDING', total_usd: 29.99, items_count: 1, created_at: '2026-05-26T09:30:00Z', tracking_number: null, shipping_address: '22 Boulevard Haussmann, Paris 75009' },
  { id: 5, order_number: 'ORD-2026-005', customer_name: 'Claire Petit', customer_email: 'claire@example.com', status: 'REFUNDED', total_usd: 59.99, items_count: 2, created_at: '2026-05-20T16:00:00Z', tracking_number: 'TRK111222333', shipping_address: '3 Rue Nationale, Lille 59000' },
]

const STATUS_LABELS: Record<string, string> = {
  PENDING: 'En attente', PROCESSING: 'En traitement', SHIPPED: 'Expédié',
  DELIVERED: 'Livré', CANCELLED: 'Annulé', REFUNDED: 'Remboursé',
}

export default function OrdersPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedOrder, setSelectedOrder] = useState<any>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['orders', { search, status: statusFilter }],
    queryFn: () => ordersApi.list({ search, status: statusFilter || undefined }),
  })

  const orders = data?.data?.items || MOCK_ORDERS

  const stats = {
    total: orders.length,
    processing: orders.filter((o: any) => ['PENDING', 'PROCESSING'].includes(o.status)).length,
    delivered: orders.filter((o: any) => o.status === 'DELIVERED').length,
    refunded: orders.filter((o: any) => o.status === 'REFUNDED').length,
  }

  const filtered = orders.filter((o: any) => {
    const matchSearch = !search || o.order_number.includes(search) || o.customer_name.toLowerCase().includes(search.toLowerCase())
    const matchStatus = !statusFilter || o.status === statusFilter
    return matchSearch && matchStatus
  })

  const getVariant = (status: string) => {
    if (['DELIVERED'].includes(status)) return 'success'
    if (['PENDING', 'PROCESSING'].includes(status)) return 'warning'
    if (['CANCELLED', 'REFUNDED'].includes(status)) return 'danger'
    if (['SHIPPED'].includes(status)) return 'info'
    return 'default'
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Gestion des Commandes</h1>

      <div className="grid grid-cols-4 gap-4">
        <StatCard title="Total commandes" value={stats.total} icon={<ShoppingCart size={20} />} />
        <StatCard title="En cours" value={stats.processing} icon={<ShoppingCart size={20} />} variant="warning" />
        <StatCard title="Livrées" value={stats.delivered} icon={<ShoppingCart size={20} />} variant="success" />
        <StatCard title="Remboursées" value={stats.refunded} icon={<ShoppingCart size={20} />} variant="danger" />
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <div className="flex gap-4 mb-6">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher commande ou client..."
              className="w-full pl-9 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
          >
            <option value="">Tous les statuts</option>
            {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </div>

        {isLoading ? <LoadingSpinner /> : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 border-b border-gray-800">
                <th className="pb-3">Commande</th>
                <th className="pb-3">Client</th>
                <th className="pb-3">Statut</th>
                <th className="pb-3">Articles</th>
                <th className="pb-3">Total</th>
                <th className="pb-3">Date</th>
                <th className="pb-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((order: any) => (
                <tr key={order.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="py-3 font-mono text-indigo-400">{order.order_number}</td>
                  <td className="py-3">
                    <div className="text-white">{order.customer_name}</div>
                    <div className="text-gray-400 text-xs">{order.customer_email}</div>
                  </td>
                  <td className="py-3">
                    <Badge variant={getVariant(order.status)}>{STATUS_LABELS[order.status] || order.status}</Badge>
                  </td>
                  <td className="py-3 text-gray-300">{order.items_count} article(s)</td>
                  <td className="py-3 text-white font-medium">{formatCurrency(order.total_usd)}</td>
                  <td className="py-3 text-gray-400">{formatDateTime(order.created_at)}</td>
                  <td className="py-3">
                    <button onClick={() => setSelectedOrder(order)} className="p-1.5 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white">
                      <Eye size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <Modal isOpen={!!selectedOrder} onClose={() => setSelectedOrder(null)} title={`Commande ${selectedOrder?.order_number}`} size="lg">
        {selectedOrder && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-gray-400 text-xs mb-1">Client</div>
                <div className="text-white font-medium">{selectedOrder.customer_name}</div>
                <div className="text-gray-400 text-sm">{selectedOrder.customer_email}</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-gray-400 text-xs mb-1">Livraison</div>
                <div className="text-white text-sm">{selectedOrder.shipping_address}</div>
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4 flex justify-between items-center">
              <div>
                <div className="text-gray-400 text-xs">Statut</div>
                <Badge variant={getVariant(selectedOrder.status)} className="mt-1">{STATUS_LABELS[selectedOrder.status]}</Badge>
              </div>
              <div>
                <div className="text-gray-400 text-xs">Tracking</div>
                <div className="text-white font-mono text-sm mt-1">{selectedOrder.tracking_number || 'Non disponible'}</div>
              </div>
              <div>
                <div className="text-gray-400 text-xs">Total</div>
                <div className="text-white text-xl font-bold mt-1">{formatCurrency(selectedOrder.total_usd)}</div>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
