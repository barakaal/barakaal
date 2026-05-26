'use client'
import { useQuery } from '@tanstack/react-query'
import { financeApi } from '@/lib/api'
import { formatCurrency, formatDate } from '@/lib/utils'
import { DollarSign, TrendingUp, BarChart3, FileText } from 'lucide-react'
import StatCard from '@/components/ui/StatCard'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const MOCK_CHART = Array.from({ length: 30 }, (_, i) => ({
  day: `J${i + 1}`,
  revenue: Math.floor(Math.random() * 800 + 200),
  profit: Math.floor(Math.random() * 300 + 50),
}))

const MOCK_REPORTS = [
  { id: 1, title: 'Rapport hebdomadaire S21', period_start: '2026-05-18', period_end: '2026-05-24', revenue_usd: 4820.50, profit_usd: 1446.15, margin_pct: 30.0, orders_count: 54 },
  { id: 2, title: 'Rapport hebdomadaire S20', period_start: '2026-05-11', period_end: '2026-05-17', revenue_usd: 3960.00, profit_usd: 1188.00, margin_pct: 30.0, orders_count: 42 },
  { id: 3, title: 'Rapport hebdomadaire S19', period_start: '2026-05-04', period_end: '2026-05-10', revenue_usd: 5100.75, profit_usd: 1530.23, margin_pct: 30.0, orders_count: 61 },
]

export default function FinancePage() {
  const { data: summaryData } = useQuery({
    queryKey: ['finance-summary'],
    queryFn: () => financeApi.summary(),
  })

  const { data: reportsData } = useQuery({
    queryKey: ['finance-reports'],
    queryFn: () => financeApi.reports(),
  })

  const summary = summaryData?.data || {
    revenue_mtd: 12345.67,
    profit_mtd: 3703.70,
    margin_pct: 30.0,
    orders_mtd: 142,
  }

  const reports = reportsData?.data?.items || MOCK_REPORTS

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Finance & Comptabilité</h1>

      <div className="grid grid-cols-4 gap-4">
        <StatCard title="Revenue MTD" value={formatCurrency(summary.revenue_mtd)} icon={<DollarSign size={20} />} variant="success" />
        <StatCard title="Profit MTD" value={formatCurrency(summary.profit_mtd)} icon={<TrendingUp size={20} />} variant="success" />
        <StatCard title="Marge nette" value={`${summary.margin_pct?.toFixed(1)}%`} icon={<BarChart3 size={20} />} />
        <StatCard title="Commandes MTD" value={summary.orders_mtd} icon={<FileText size={20} />} />
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Revenue vs Profit — 30 derniers jours</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={MOCK_CHART}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="day" tick={{ fill: '#9CA3AF', fontSize: 11 }} interval={4} />
            <YAxis tick={{ fill: '#9CA3AF', fontSize: 11 }} />
            <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151', borderRadius: '8px' }} />
            <Legend />
            <Bar dataKey="revenue" name="Revenue ($)" fill="#6366F1" radius={[2, 2, 0, 0]} />
            <Bar dataKey="profit" name="Profit ($)" fill="#10B981" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Rapports financiers</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-400 border-b border-gray-800">
              <th className="pb-3">Rapport</th>
              <th className="pb-3">Période</th>
              <th className="pb-3">Revenue</th>
              <th className="pb-3">Profit</th>
              <th className="pb-3">Marge</th>
              <th className="pb-3">Commandes</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((r: any) => (
              <tr key={r.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                <td className="py-3 text-white">{r.title}</td>
                <td className="py-3 text-gray-400">{formatDate(r.period_start)} → {formatDate(r.period_end)}</td>
                <td className="py-3 text-green-400 font-medium">{formatCurrency(r.revenue_usd)}</td>
                <td className="py-3 text-emerald-400 font-medium">{formatCurrency(r.profit_usd)}</td>
                <td className="py-3 text-blue-400">{r.margin_pct?.toFixed(1)}%</td>
                <td className="py-3 text-gray-300">{r.orders_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
