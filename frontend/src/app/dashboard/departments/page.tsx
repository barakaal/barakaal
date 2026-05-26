'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { departmentsApi } from '@/lib/api'
import { formatCurrency } from '@/lib/utils'
import { Building2, Bot, DollarSign } from 'lucide-react'
import Modal from '@/components/ui/Modal'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

const MOCK_DEPARTMENTS = [
  { id: 1, name: 'Recherche Produits', code: 'RESEARCH', description: 'Identification et analyse des produits tendances', budget_monthly_usd: 500, agent_count: 3, is_active: true },
  { id: 2, name: 'Sourcing Fournisseurs', code: 'SOURCING', description: 'Recherche et évaluation des fournisseurs', budget_monthly_usd: 300, agent_count: 1, is_active: true },
  { id: 3, name: 'Analyse de Marché', code: 'MARKET_ANALYSIS', description: 'Analyse des tendances et de la concurrence', budget_monthly_usd: 400, agent_count: 2, is_active: true },
  { id: 4, name: 'Pricing & Marges', code: 'PRICING', description: 'Optimisation des prix et des marges', budget_monthly_usd: 200, agent_count: 1, is_active: true },
  { id: 5, name: 'Marketing', code: 'MARKETING', description: 'Campagnes publicitaires et acquisition clients', budget_monthly_usd: 2000, agent_count: 1, is_active: true },
  { id: 6, name: 'Boutique en ligne', code: 'STORE', description: 'Gestion de la boutique et des fiches produits', budget_monthly_usd: 300, agent_count: 1, is_active: true },
  { id: 7, name: 'Gestion des Commandes', code: 'ORDERS', description: 'Traitement et suivi des commandes', budget_monthly_usd: 200, agent_count: 2, is_active: true },
  { id: 8, name: 'Service Client', code: 'CUSTOMER_SUPPORT', description: 'Support et satisfaction client', budget_monthly_usd: 300, agent_count: 1, is_active: true },
  { id: 9, name: 'Finance & Comptabilité', code: 'FINANCE', description: 'Suivi financier et rapports', budget_monthly_usd: 200, agent_count: 1, is_active: true },
  { id: 10, name: 'Légal & Conformité', code: 'LEGAL', description: 'Conformité légale et réglementaire', budget_monthly_usd: 300, agent_count: 1, is_active: true },
  { id: 11, name: 'Data & Reporting', code: 'DATA', description: 'Analyses de données et tableaux de bord', budget_monthly_usd: 200, agent_count: 1, is_active: true },
  { id: 12, name: 'Technique / DevOps', code: 'TECH', description: 'Infrastructure et développement', budget_monthly_usd: 500, agent_count: 1, is_active: true },
]

const DEPT_COLORS = ['indigo', 'blue', 'violet', 'purple', 'pink', 'rose', 'orange', 'amber', 'yellow', 'green', 'teal', 'cyan']

export default function DepartmentsPage() {
  const [selected, setSelected] = useState<any>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['departments'],
    queryFn: () => departmentsApi.list(),
  })

  const departments = data?.data || MOCK_DEPARTMENTS

  if (isLoading) return <LoadingSpinner />

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Building2 size={24} className="text-indigo-400" />
        <h1 className="text-2xl font-bold text-white">Départements</h1>
        <span className="text-gray-500 text-sm">({departments.length} départements)</span>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {departments.map((dept: any, i: number) => {
          const color = DEPT_COLORS[i % DEPT_COLORS.length]
          return (
            <div
              key={dept.id}
              onClick={() => setSelected(dept)}
              className="bg-gray-900 border border-gray-800 rounded-xl p-5 cursor-pointer hover:border-gray-600 transition-colors group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`w-10 h-10 rounded-lg bg-${color}-900/50 flex items-center justify-center`}>
                  <Building2 size={20} className={`text-${color}-400`} />
                </div>
                <span className={`text-xs px-2 py-1 rounded bg-${color}-900/30 text-${color}-300`}>{dept.code}</span>
              </div>
              <h3 className="text-white font-semibold mb-1 group-hover:text-indigo-300 transition-colors">{dept.name}</h3>
              <p className="text-gray-400 text-xs mb-4 line-clamp-2">{dept.description}</p>
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-1 text-gray-400">
                  <Bot size={12} />
                  <span>{dept.agent_count} agent(s)</span>
                </div>
                <div className="flex items-center gap-1 text-gray-400">
                  <DollarSign size={12} />
                  <span>{formatCurrency(dept.budget_monthly_usd)}/mois</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <Modal isOpen={!!selected} onClose={() => setSelected(null)} title={selected?.name || ''}>
        {selected && (
          <div className="space-y-4">
            <p className="text-gray-400">{selected.description}</p>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-gray-400 text-xs mb-1">Code département</div>
                <div className="text-white font-mono">{selected.code}</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-gray-400 text-xs mb-1">Budget mensuel</div>
                <div className="text-white font-bold">{formatCurrency(selected.budget_monthly_usd)}</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-gray-400 text-xs mb-1">Agents IA</div>
                <div className="text-white">{selected.agent_count} agent(s)</div>
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-gray-400 text-xs mb-1">Statut</div>
                <div className={selected.is_active ? 'text-green-400' : 'text-red-400'}>
                  {selected.is_active ? 'Actif' : 'Inactif'}
                </div>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
