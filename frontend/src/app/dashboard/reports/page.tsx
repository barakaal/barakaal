'use client'
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { reportsApi } from '@/lib/api'
import { BarChart3, Play, TrendingUp, Bot } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

const MOCK_AGENT_ACTIVITY = [
  { name: 'CEO Alpha', tasks: 24, decisions: 18 },
  { name: 'Chef Recherche', tasks: 52, decisions: 31 },
  { name: 'Chef Sourcing', tasks: 38, decisions: 22 },
  { name: 'Chef Marketing', tasks: 29, decisions: 15 },
  { name: 'Chef Commandes', tasks: 71, decisions: 8 },
  { name: 'Directeur Fin.', tasks: 16, decisions: 12 },
]

const MOCK_WEEKLY = {
  period: '19 mai 2026 → 25 mai 2026',
  products_analyzed: 47,
  products_validated: 8,
  orders_processed: 54,
  revenue_usd: 4820.50,
  profit_usd: 1446.15,
  approvals_pending: 3,
  top_products: [
    { name: 'Masque LED Anti-Âge', score: 88.2, orders: 21 },
    { name: 'Lampe LED Tactile', score: 82.5, orders: 18 },
    { name: 'Organisateur Bambou', score: 74.3, orders: 15 },
  ],
}

export default function ReportsPage() {
  const [triggered, setTriggered] = useState(false)

  const { data: weeklyData, isLoading: loadingWeekly } = useQuery({
    queryKey: ['reports-weekly'],
    queryFn: () => reportsApi.weekly(),
  })

  const { data: activityData, isLoading: loadingActivity } = useQuery({
    queryKey: ['reports-agent-activity'],
    queryFn: () => reportsApi.agentActivity(),
  })

  const triggerMutation = useMutation({
    mutationFn: () => reportsApi.triggerWeekly(),
    onSuccess: () => setTriggered(true),
  })

  const weekly = weeklyData?.data || MOCK_WEEKLY
  const agentActivity = activityData?.data || MOCK_AGENT_ACTIVITY

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart3 size={24} className="text-indigo-400" />
          <h1 className="text-2xl font-bold text-white">Rapports & Analyses</h1>
        </div>
        <button
          onClick={() => !triggered && triggerMutation.mutate()}
          disabled={triggered || triggerMutation.isPending}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Play size={14} />
          {triggerMutation.isPending ? 'Démarrage...' : triggered ? 'Workflow lancé ✓' : 'Lancer workflow hebdomadaire'}
        </button>
      </div>

      {/* Weekly Summary */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp size={18} className="text-indigo-400" />
          <h2 className="text-lg font-semibold text-white">Rapport hebdomadaire</h2>
          <span className="text-gray-500 text-sm">({weekly.period})</span>
        </div>
        {loadingWeekly ? <LoadingSpinner /> : (
          <div className="grid grid-cols-2 gap-6">
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: 'Produits analysés', value: weekly.products_analyzed, color: 'text-blue-400' },
                { label: 'Produits validés', value: weekly.products_validated, color: 'text-green-400' },
                { label: 'Commandes traitées', value: weekly.orders_processed, color: 'text-indigo-400' },
                { label: 'Validations en attente', value: weekly.approvals_pending, color: 'text-yellow-400' },
              ].map((item) => (
                <div key={item.label} className="bg-gray-800 rounded-lg p-4">
                  <div className="text-gray-400 text-xs mb-1">{item.label}</div>
                  <div className={`text-2xl font-bold ${item.color}`}>{item.value}</div>
                </div>
              ))}
            </div>
            <div>
              <div className="text-gray-400 text-sm mb-3">Top produits de la semaine</div>
              <div className="space-y-2">
                {weekly.top_products?.map((p: any, i: number) => (
                  <div key={i} className="flex items-center justify-between bg-gray-800 rounded-lg px-4 py-2.5">
                    <div>
                      <div className="text-white text-sm">{p.name}</div>
                      <div className="text-gray-500 text-xs">{p.orders} commandes</div>
                    </div>
                    <div className="text-green-400 font-bold">{p.score}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Agent Activity */}
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Bot size={18} className="text-indigo-400" />
          <h2 className="text-lg font-semibold text-white">Activité des agents</h2>
        </div>
        {loadingActivity ? <LoadingSpinner /> : (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={agentActivity}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
              <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }} />
              <Bar dataKey="tasks" name="Tâches" fill="#6366F1" radius={[2, 2, 0, 0]} />
              <Bar dataKey="decisions" name="Décisions" fill="#10B981" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
