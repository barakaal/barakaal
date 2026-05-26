'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { agentsApi } from '@/lib/api'
import { formatDateTime } from '@/lib/utils'
import Card from '@/components/ui/Card'
import Badge, { StatusBadge } from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import { Bot, Plus, Play, Clock, ChevronDown, Filter } from 'lucide-react'

const MOCK_AGENTS = [
  { id: 1, name: 'Alpha-Commercial', type: 'CEO', department_name: 'Direction', status: 'ACTIVE', role: 'CEO Agent - Supervision globale', last_activity: new Date(Date.now() - 600000).toISOString(), tasks_count: 47, success_rate: 94 },
  { id: 2, name: 'Beta-Sourcing', type: 'MANAGER', department_name: 'Sourcing', status: 'RUNNING', role: 'Recherche et évaluation produits', last_activity: new Date(Date.now() - 120000).toISOString(), tasks_count: 23, success_rate: 88 },
  { id: 3, name: 'Gamma-Marketing', type: 'EMPLOYEE', department_name: 'Marketing', status: 'ACTIVE', role: 'Campagnes publicitaires et SEO', last_activity: new Date(Date.now() - 1800000).toISOString(), tasks_count: 18, success_rate: 91 },
  { id: 4, name: 'Delta-Pricing', type: 'EMPLOYEE', department_name: 'Commercial', status: 'ACTIVE', role: 'Optimisation des prix concurrentiels', last_activity: new Date(Date.now() - 300000).toISOString(), tasks_count: 56, success_rate: 97 },
  { id: 5, name: 'Epsilon-Logistics', type: 'MANAGER', department_name: 'Logistique', status: 'IDLE', role: 'Gestion des commandes et livraisons', last_activity: new Date(Date.now() - 7200000).toISOString(), tasks_count: 34, success_rate: 86 },
  { id: 6, name: 'Zeta-Finance', type: 'EMPLOYEE', department_name: 'Finance', status: 'ACTIVE', role: 'Analyse financière et reporting', last_activity: new Date(Date.now() - 900000).toISOString(), tasks_count: 12, success_rate: 100 },
  { id: 7, name: 'Eta-Support', type: 'EMPLOYEE', department_name: 'SAV', status: 'PAUSED', role: 'Service client et remboursements', last_activity: new Date(Date.now() - 86400000).toISOString(), tasks_count: 8, success_rate: 75 },
  { id: 8, name: 'Theta-Content', type: 'EMPLOYEE', department_name: 'Marketing', status: 'ACTIVE', role: "Création de contenu et fiches produits", last_activity: new Date(Date.now() - 3600000).toISOString(), tasks_count: 29, success_rate: 93 },
]

const MOCK_TASKS = [
  { id: 1, title: 'Analyser top 10 produits tendance TikTok', status: 'COMPLETED', created_at: new Date(Date.now() - 3600000).toISOString(), duration: '4m 32s' },
  { id: 2, title: 'Calculer score dropshipping Drone 4K Pro', status: 'COMPLETED', created_at: new Date(Date.now() - 7200000).toISOString(), duration: '1m 15s' },
  { id: 3, title: 'Vérifier fournisseurs AliExpress pour LED', status: 'RUNNING', created_at: new Date(Date.now() - 180000).toISOString(), duration: '3m 02s' },
]

type Agent = typeof MOCK_AGENTS[0]

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple' | 'outline'

function AgentCard({ agent, onClick }: { agent: Agent; onClick: () => void }) {
  const typeConfig: Record<string, { variant: BadgeVariant; label: string }> = {
    CEO: { variant: 'purple', label: 'CEO' },
    MANAGER: { variant: 'info', label: 'Manager' },
    EMPLOYEE: { variant: 'default', label: 'Employé' },
  }
  const tc = typeConfig[agent.type] || typeConfig.EMPLOYEE

  const dotClass =
    agent.status === 'ACTIVE' ? 'bg-green-400 shadow-green-500' :
    agent.status === 'RUNNING' ? 'bg-blue-400 shadow-blue-500' :
    agent.status === 'IDLE' ? 'bg-gray-500' :
    'bg-gray-600'

  return (
    <div
      onClick={onClick}
      className="bg-gray-900 border border-gray-800 rounded-xl p-5 cursor-pointer hover:border-indigo-600 hover:shadow-lg hover:shadow-indigo-900/10 transition-all duration-200"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="w-10 h-10 bg-indigo-900/50 rounded-xl flex items-center justify-center">
          <Bot className="w-5 h-5 text-indigo-400" />
        </div>
        <div className={`w-2.5 h-2.5 rounded-full mt-1 ${dotClass} shadow-sm`} />
      </div>
      <h3 className="font-semibold text-gray-100 mb-1">{agent.name}</h3>
      <p className="text-xs text-gray-500 mb-3 line-clamp-2">{agent.role}</p>
      <div className="flex items-center gap-2 flex-wrap">
        <Badge variant={tc.variant}>{tc.label}</Badge>
        <span className="text-xs text-gray-500">{agent.department_name}</span>
      </div>
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-800">
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{formatDateTime(agent.last_activity)}</span>
        </div>
        <span className="text-xs text-gray-400">{agent.tasks_count} tâches</span>
      </div>
    </div>
  )
}

export default function AgentsPage() {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null)
  const [showRunTask, setShowRunTask] = useState(false)
  const [taskForm, setTaskForm] = useState({ title: '', description: '', input_data: '{}' })
  const [filterType, setFilterType] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['agents', filterType, filterStatus],
    queryFn: async () => {
      try {
        const res = await agentsApi.list({ type: filterType || undefined, status: filterStatus || undefined })
        return res.data
      } catch {
        return MOCK_AGENTS
      }
    },
  })

  const { data: tasks } = useQuery({
    queryKey: ['agent-tasks-all'],
    queryFn: async () => {
      try {
        const res = await agentsApi.allTasks({ limit: 10 })
        return res.data
      } catch {
        return MOCK_TASKS
      }
    },
  })

  const runTaskMutation = useMutation({
    mutationFn: async () => {
      if (!selectedAgent) return
      return agentsApi.runTask(selectedAgent.id, {
        ...taskForm,
        input_data: JSON.parse(taskForm.input_data || '{}'),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-tasks-all'] })
      setShowRunTask(false)
      setTaskForm({ title: '', description: '', input_data: '{}' })
    },
  })

  const agents = data || MOCK_AGENTS
  const allTasks = tasks || MOCK_TASKS

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">{agents.length} agents déployés</p>
        </div>
        <Button leftIcon={<Plus className="w-4 h-4" />} size="md">
          Nouvel Agent
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <Filter className="w-4 h-4 text-gray-500" />
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="select-dark text-sm py-1.5"
        >
          <option value="">Tous les types</option>
          <option value="CEO">CEO</option>
          <option value="MANAGER">Manager</option>
          <option value="EMPLOYEE">Employé</option>
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="select-dark text-sm py-1.5"
        >
          <option value="">Tous les statuts</option>
          <option value="ACTIVE">Actif</option>
          <option value="RUNNING">En cours</option>
          <option value="IDLE">Inactif</option>
          <option value="PAUSED">Pausé</option>
        </select>
        {(filterType || filterStatus) && (
          <button
            onClick={() => { setFilterType(''); setFilterStatus('') }}
            className="text-xs text-indigo-400 hover:text-indigo-300"
          >
            Réinitialiser
          </button>
        )}
      </div>

      {/* Agents Grid */}
      {isLoading ? (
        <PageLoader />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {agents.map((agent: Agent) => (
            <AgentCard key={agent.id} agent={agent} onClick={() => setSelectedAgent(agent)} />
          ))}
        </div>
      )}

      {/* Recent Tasks Table */}
      <Card title="Tâches récentes" headerAction={
        <span className="text-xs text-gray-400">10 dernières tâches</span>
      }>
        <div className="overflow-x-auto mt-2">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800">
                <th className="px-3 py-2.5 text-left text-xs font-medium text-gray-400 uppercase">Tâche</th>
                <th className="px-3 py-2.5 text-left text-xs font-medium text-gray-400 uppercase">Statut</th>
                <th className="px-3 py-2.5 text-left text-xs font-medium text-gray-400 uppercase">Date</th>
                <th className="px-3 py-2.5 text-left text-xs font-medium text-gray-400 uppercase">Durée</th>
              </tr>
            </thead>
            <tbody>
              {allTasks.map((task: typeof MOCK_TASKS[0]) => (
                <tr key={task.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="px-3 py-3 text-sm text-gray-200">{task.title}</td>
                  <td className="px-3 py-3"><StatusBadge status={task.status} /></td>
                  <td className="px-3 py-3 text-xs text-gray-500">{formatDateTime(task.created_at)}</td>
                  <td className="px-3 py-3 text-xs text-gray-400 font-mono">{task.duration}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Agent Detail Modal */}
      <Modal
        isOpen={!!selectedAgent && !showRunTask}
        onClose={() => setSelectedAgent(null)}
        title={selectedAgent?.name}
        size="lg"
        footer={
          <>
            <Button variant="outline" onClick={() => setSelectedAgent(null)}>Fermer</Button>
            <Button
              leftIcon={<Play className="w-4 h-4" />}
              onClick={() => setShowRunTask(true)}
            >
              Lancer une tâche
            </Button>
          </>
        }
      >
        {selectedAgent && (
          <div className="space-y-5">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-indigo-900/40 rounded-2xl flex items-center justify-center">
                <Bot className="w-7 h-7 text-indigo-400" />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <StatusBadge status={selectedAgent.status} />
                  <Badge variant={selectedAgent.type === 'CEO' ? 'purple' : selectedAgent.type === 'MANAGER' ? 'info' : 'default'}>
                    {selectedAgent.type}
                  </Badge>
                </div>
                <p className="text-sm text-gray-400">{selectedAgent.role}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-800 rounded-xl p-4">
                <p className="text-xs text-gray-500 mb-1">Département</p>
                <p className="text-sm font-semibold text-gray-200">{selectedAgent.department_name}</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-4">
                <p className="text-xs text-gray-500 mb-1">Taux de succès</p>
                <p className="text-sm font-semibold text-green-400">{selectedAgent.success_rate}%</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-4">
                <p className="text-xs text-gray-500 mb-1">Tâches total</p>
                <p className="text-sm font-semibold text-gray-200">{selectedAgent.tasks_count}</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-4">
                <p className="text-xs text-gray-500 mb-1">Dernière activité</p>
                <p className="text-sm font-semibold text-gray-200">{formatDateTime(selectedAgent.last_activity)}</p>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                <ChevronDown className="w-4 h-4" />
                Tâches récentes
              </h4>
              <div className="space-y-2">
                {MOCK_TASKS.map((task) => (
                  <div key={task.id} className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg">
                    <StatusBadge status={task.status} />
                    <span className="text-sm text-gray-300 flex-1">{task.title}</span>
                    <span className="text-xs text-gray-500 font-mono">{task.duration}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* Run Task Modal */}
      <Modal
        isOpen={showRunTask}
        onClose={() => setShowRunTask(false)}
        title={`Lancer une tâche — ${selectedAgent?.name}`}
        size="md"
        footer={
          <>
            <Button variant="outline" onClick={() => setShowRunTask(false)}>Annuler</Button>
            <Button
              loading={runTaskMutation.isPending}
              leftIcon={<Play className="w-4 h-4" />}
              onClick={() => runTaskMutation.mutate()}
            >
              Lancer
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-300 block mb-1.5">Titre de la tâche *</label>
            <input
              value={taskForm.title}
              onChange={(e) => setTaskForm(f => ({ ...f, title: e.target.value }))}
              className="input-dark w-full"
              placeholder="Ex: Analyser les tendances du marché LED..."
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-300 block mb-1.5">Description</label>
            <textarea
              value={taskForm.description}
              onChange={(e) => setTaskForm(f => ({ ...f, description: e.target.value }))}
              className="input-dark w-full h-24 resize-none"
              placeholder="Description détaillée de la tâche..."
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-300 block mb-1.5">Données d'entrée (JSON)</label>
            <textarea
              value={taskForm.input_data}
              onChange={(e) => setTaskForm(f => ({ ...f, input_data: e.target.value }))}
              className="input-dark w-full h-32 resize-none font-mono text-xs"
              placeholder='{"key": "value"}'
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}
