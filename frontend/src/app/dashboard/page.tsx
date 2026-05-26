'use client'
import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '@/lib/api'
import { formatCurrency, formatNumber, formatDateTime } from '@/lib/utils'
import StatCard from '@/components/ui/StatCard'
import Card from '@/components/ui/Card'
import { SkeletonStats } from '@/components/ui/LoadingSpinner'
import ScoreBar from '@/components/ui/ScoreBar'
import Badge, { StatusBadge } from '@/components/ui/Badge'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import {
  DollarSign, ShoppingCart, Package, CheckCircle,
  AlertTriangle, TrendingUp, Bot, Activity
} from 'lucide-react'

// Mock data for when API is unavailable
const MOCK_STATS = {
  revenue_today: 12847.50,
  orders_today: 47,
  active_products: 234,
  pending_approvals: 3,
  revenue_change: 12.5,
  orders_change: -3.2,
  revenue_7days: [
    { date: '30/04', revenue: 8200, profit: 2460 },
    { date: '01/05', revenue: 9800, profit: 2940 },
    { date: '02/05', revenue: 7600, profit: 2280 },
    { date: '03/05', revenue: 11200, profit: 3360 },
    { date: '04/05', revenue: 13500, profit: 4050 },
    { date: '05/05', revenue: 10900, profit: 3270 },
    { date: '06/05', revenue: 12847, profit: 3854 },
  ],
  top_products: [
    { id: 1, name: 'Montre Connectée Pro X12', score: 87, revenue: 3240, orders: 12, status: 'ACTIVE' },
    { id: 2, name: 'Écouteurs Sans Fil Elite', score: 82, revenue: 2890, orders: 19, status: 'ACTIVE' },
    { id: 3, name: 'Lampe LED Bureau Smart', score: 76, revenue: 1950, orders: 23, status: 'ACTIVE' },
    { id: 4, name: 'Support Téléphone Voiture', score: 71, revenue: 1420, orders: 31, status: 'ACTIVE' },
    { id: 5, name: 'Chargeur Rapide USB-C 65W', score: 68, revenue: 1180, orders: 28, status: 'PENDING_APPROVAL' },
  ],
  departments: [
    { name: 'Commercial', status: 'ACTIVE', agents: 3, tasks_today: 12 },
    { name: 'Marketing', status: 'ACTIVE', agents: 2, tasks_today: 8 },
    { name: 'Logistique', status: 'ACTIVE', agents: 2, tasks_today: 15 },
    { name: 'Finance', status: 'IDLE', agents: 1, tasks_today: 3 },
    { name: 'Sourcing', status: 'RUNNING', agents: 2, tasks_today: 7 },
  ],
  recent_decisions: [
    { id: 1, title: 'Approbation produit: Drone Pliable 4K', agent: 'Agent Commercial Alpha', type: 'PRODUCT_APPROVAL', risk: 'MEDIUM', status: 'PENDING', created_at: new Date(Date.now() - 3600000).toISOString() },
    { id: 2, title: 'Promotion -20% sur TV 4K 55"', agent: 'Agent Marketing Beta', type: 'MARKETING_CAMPAIGN', risk: 'LOW', status: 'APPROVED', created_at: new Date(Date.now() - 7200000).toISOString() },
    { id: 3, title: 'Commande fournisseur AliExpress #4521', agent: 'Agent Logistique', type: 'SUPPLIER_ORDER', risk: 'HIGH', status: 'PENDING', created_at: new Date(Date.now() - 1800000).toISOString() },
    { id: 4, title: 'Mise à jour prix concurrent Amazon', agent: 'Agent Pricing', type: 'PRICE_UPDATE', risk: 'LOW', status: 'COMPLETED', created_at: new Date(Date.now() - 9000000).toISOString() },
  ],
  alerts: [
    { id: 1, type: 'WARNING', message: '3 validations en attente depuis plus de 2h', timestamp: new Date().toISOString() },
    { id: 2, type: 'INFO', message: 'Stock critique: Chargeur USB-C 65W — 5 unités restantes', timestamp: new Date(Date.now() - 1800000).toISOString() },
  ],
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-3 shadow-xl">
        <p className="text-xs text-gray-400 mb-2">{label}</p>
        {payload.map((p) => (
          <p key={p.name} className="text-sm font-semibold" style={{ color: p.color }}>
            {p.name}: {formatCurrency(p.value)}
          </p>
        ))}
      </div>
    )
  }
  return null
}

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['ceo-stats'],
    queryFn: async () => {
      try {
        const res = await dashboardApi.getCEOStats()
        return res.data
      } catch {
        return MOCK_STATS
      }
    },
    refetchInterval: 60000,
  })

  const stats = data || MOCK_STATS

  return (
    <div className="space-y-6">
      {/* Alerts */}
      {stats.alerts && stats.alerts.length > 0 && (
        <div className="space-y-2">
          {stats.alerts.map((alert: { id: number; type: string; message: string; timestamp: string }) => (
            <div
              key={alert.id}
              className={`flex items-start gap-3 px-4 py-3 rounded-xl border ${
                alert.type === 'WARNING'
                  ? 'bg-yellow-900/20 border-yellow-800/50 text-yellow-300'
                  : 'bg-blue-900/20 border-blue-800/50 text-blue-300'
              }`}
            >
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <p className="text-sm">{alert.message}</p>
              <span className="ml-auto text-xs opacity-60 whitespace-nowrap">
                {formatDateTime(alert.timestamp)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* KPI Cards */}
      {isLoading ? (
        <SkeletonStats />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Revenue du jour"
            value={formatCurrency(stats.revenue_today)}
            change={stats.revenue_change}
            changeLabel="vs hier"
            icon={<DollarSign className="w-6 h-6" />}
            variant="success"
          />
          <StatCard
            title="Commandes du jour"
            value={formatNumber(stats.orders_today)}
            change={stats.orders_change}
            changeLabel="vs hier"
            icon={<ShoppingCart className="w-6 h-6" />}
          />
          <StatCard
            title="Produits actifs"
            value={formatNumber(stats.active_products)}
            icon={<Package className="w-6 h-6" />}
          />
          <StatCard
            title="Validations en attente"
            value={stats.pending_approvals}
            icon={<CheckCircle className="w-6 h-6" />}
            variant={stats.pending_approvals > 0 ? 'danger' : 'default'}
            subtitle={stats.pending_approvals > 0 ? 'Action requise' : 'Tout est à jour'}
          />
        </div>
      )}

      {/* Revenue Chart */}
      <Card title="Revenue des 7 derniers jours" headerAction={
        <div className="flex items-center gap-1.5 text-xs text-green-400">
          <TrendingUp className="w-3.5 h-3.5" />
          <span>+12.5% cette semaine</span>
        </div>
      }>
        <div className="h-64 mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={stats.revenue_7days} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(55,65,81,0.5)" />
              <XAxis dataKey="date" stroke="#6b7280" tick={{ fontSize: 12 }} />
              <YAxis stroke="#6b7280" tick={{ fontSize: 12 }} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
              <Line
                type="monotone"
                dataKey="revenue"
                name="Revenue"
                stroke="#6366f1"
                strokeWidth={2.5}
                dot={{ fill: '#6366f1', r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="profit"
                name="Profit"
                stroke="#22c55e"
                strokeWidth={2.5}
                dot={{ fill: '#22c55e', r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Two columns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        <Card title="Top produits" headerAction={
          <span className="text-xs text-gray-400">Par revenue aujourd'hui</span>
        }>
          <div className="space-y-3 mt-2">
            {stats.top_products?.map((product: { id: number; name: string; score: number; revenue: number; orders: number; status: string }, idx: number) => (
              <div key={product.id} className="flex items-center gap-3">
                <span className="text-sm font-bold text-gray-600 w-4 flex-shrink-0">
                  {idx + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm text-gray-200 truncate">{product.name}</p>
                    <StatusBadge status={product.status} />
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    <ScoreBar score={product.score} showValue={false} height="sm" className="flex-1" />
                    <span className="text-xs text-gray-500">{product.orders} cmd</span>
                  </div>
                </div>
                <span className="text-sm font-semibold text-gray-200 flex-shrink-0">
                  {formatCurrency(product.revenue)}
                </span>
              </div>
            ))}
          </div>
        </Card>

        {/* Department Status */}
        <Card title="Statut départements" headerAction={
          <div className="flex items-center gap-1.5 text-xs text-gray-400">
            <Activity className="w-3.5 h-3.5" />
            <span>Temps réel</span>
          </div>
        }>
          <div className="space-y-2.5 mt-2">
            {stats.departments?.map((dept: { name: string; status: string; agents: number; tasks_today: number }) => (
              <div key={dept.name} className="flex items-center gap-3 p-3 rounded-lg bg-gray-800/50">
                <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                  dept.status === 'ACTIVE' ? 'bg-green-400 shadow-sm shadow-green-500' :
                  dept.status === 'RUNNING' ? 'bg-blue-400 shadow-sm shadow-blue-500' :
                  'bg-gray-500'
                }`} />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-200">{dept.name}</p>
                  <p className="text-xs text-gray-500">{dept.agents} agents · {dept.tasks_today} tâches aujourd'hui</p>
                </div>
                <StatusBadge status={dept.status} />
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent Decisions */}
      <Card title="Décisions récentes des agents" headerAction={
        <Badge variant="info">
          <Bot className="w-3 h-3 mr-1" />
          IA Active
        </Badge>
      }>
        <div className="mt-2 space-y-2">
          {stats.recent_decisions?.map((decision: { id: number; title: string; agent: string; type: string; risk: string; status: string; created_at: string }) => (
            <div key={decision.id} className="flex items-start gap-4 p-4 rounded-xl bg-gray-800/40 border border-gray-800 hover:border-gray-700 transition-colors">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-sm font-medium text-gray-200">{decision.title}</p>
                  <Badge
                    variant={
                      decision.risk === 'HIGH' || decision.risk === 'CRITICAL' ? 'danger' :
                      decision.risk === 'MEDIUM' ? 'warning' : 'success'
                    }
                  >
                    {decision.risk}
                  </Badge>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {decision.agent} · {decision.type.replace('_', ' ')} · {formatDateTime(decision.created_at)}
                </p>
              </div>
              <StatusBadge status={decision.status} />
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
