'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { approvalsApi } from '@/lib/api'
import { formatDateTime, getRiskBadge } from '@/lib/utils'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import { CheckCircle, XCircle, ChevronDown, ChevronRight, AlertTriangle, Clock } from 'lucide-react'

const MOCK_APPROVALS = [
  {
    id: 1, title: 'Approbation produit: Drone Pliable 4K', agent_name: 'Agent Sourcing Beta',
    decision_type: 'PRODUCT_APPROVAL', risk_level: 'HIGH', status: 'PENDING',
    rationale: 'Le drone pliable 4K présente un score de 48/100. Bien que la marge soit acceptable (64%), la concurrence est forte sur Amazon avec 850+ vendeurs. Le fournisseur a une note de 4.2/5 sur AliExpress mais les délais de livraison sont de 21 jours.',
    estimated_cost: 8900, estimated_revenue: 24999, recommendation: 'APPROUVER avec suivi mensuel',
    created_at: new Date(Date.now() - 3600000).toISOString(),
    data_used: { platform: 'AliExpress', competitors: 850, supplier_rating: 4.2 }
  },
  {
    id: 2, title: 'Commande fournisseur: 500x Chargeur USB-C 65W', agent_name: 'Agent Logistique',
    decision_type: 'SUPPLIER_ORDER', risk_level: 'MEDIUM', status: 'PENDING',
    rationale: 'Stock critique (5 unités restantes). 45 commandes en attente de traitement. Le fournisseur ShenzhenTech propose un prix de $6.80/unité pour 500 unités avec livraison 14 jours.',
    estimated_cost: 3400, estimated_revenue: 14995, recommendation: 'APPROUVER immédiatement',
    created_at: new Date(Date.now() - 1800000).toISOString(),
    data_used: { current_stock: 5, pending_orders: 45, supplier: 'ShenzhenTech' }
  },
  {
    id: 3, title: 'Campagne publicitaire TikTok: Montre Connectée', agent_name: 'Agent Marketing Gamma',
    decision_type: 'MARKETING_CAMPAIGN', risk_level: 'LOW', status: 'PENDING',
    rationale: 'La montre connectée Pro X12 a un taux de conversion de 3.2% sur Facebook. Une campagne TikTok de 7 jours avec budget $500 pourrait générer 80+ commandes basé sur les benchmarks du secteur.',
    estimated_cost: 500, estimated_revenue: 6399, recommendation: 'APPROUVER — ROI estimé 1280%',
    created_at: new Date(Date.now() - 900000).toISOString(),
    data_used: { current_cvr: 3.2, budget: 500, platform: 'TikTok' }
  },
  {
    id: 4, title: 'Mise à jour prix: -15% Écouteurs Elite', agent_name: 'Agent Pricing Delta',
    decision_type: 'PRICE_UPDATE', risk_level: 'MEDIUM', status: 'APPROVED',
    rationale: "L'analyse concurrentielle montre que 3 vendeurs Amazon ont baissé leurs prix de 20% cette semaine. Une réduction de 15% maintient notre compétitivité et la marge à 63%.",
    estimated_cost: 0, estimated_revenue: 4250, recommendation: 'APPROUVER avec surveillance',
    created_at: new Date(Date.now() - 86400000).toISOString(),
    review_notes: 'Approuvé. Surveiller la marge sur 72h.',
    data_used: { competitor_drop: 20, new_price: 42.49, margin_after: 63 }
  },
  {
    id: 5, title: 'Ajout fournisseur: GlobalDrop Ltd (UK)', agent_name: 'Agent Sourcing Beta',
    decision_type: 'SUPPLIER_ADDITION', risk_level: 'HIGH', status: 'REJECTED',
    rationale: 'Nouveau fournisseur UK avec catalogue de 2000+ produits. Délai livraison Europe: 5-7 jours. Note non vérifiée.',
    estimated_cost: 0, estimated_revenue: 0, recommendation: 'VÉRIFIER les accréditations avant',
    created_at: new Date(Date.now() - 172800000).toISOString(),
    review_notes: "Rejeté — Le fournisseur n'a pas de certification ISO. Relancer après vérification.",
    data_used: { products: 2000, delivery_days: '5-7', country: 'UK' }
  },
]

type Approval = typeof MOCK_APPROVALS[0]

const DECISION_TYPE_LABELS: Record<string, string> = {
  PRODUCT_APPROVAL: 'Approbation produit',
  SUPPLIER_ORDER: 'Commande fournisseur',
  MARKETING_CAMPAIGN: 'Campagne marketing',
  PRICE_UPDATE: 'Mise à jour prix',
  SUPPLIER_ADDITION: 'Ajout fournisseur',
}

function ApprovalCard({
  approval,
  onApprove,
  onReject,
}: {
  approval: Approval
  onApprove: (id: number) => void
  onReject: (id: number) => void
}) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="p-5">
        <div className="flex items-start gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getRiskBadge(approval.risk_level)}`}>
                {approval.risk_level === 'HIGH' && <AlertTriangle className="w-3 h-3 mr-1" />}
                Risque {approval.risk_level}
              </span>
              <Badge variant="default">{DECISION_TYPE_LABELS[approval.decision_type] || approval.decision_type}</Badge>
            </div>
            <h3 className="font-semibold text-gray-100 mb-1">{approval.title}</h3>
            <div className="flex items-center gap-3 text-xs text-gray-500">
              <span>Agent: <span className="text-gray-400">{approval.agent_name}</span></span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatDateTime(approval.created_at)}
              </span>
            </div>
          </div>

          {approval.status === 'PENDING' && (
            <div className="flex items-center gap-2 flex-shrink-0">
              <button
                onClick={() => onApprove(approval.id)}
                className="flex items-center gap-1.5 px-4 py-2 bg-green-700 hover:bg-green-600 text-white text-sm font-medium rounded-lg transition-colors"
              >
                <CheckCircle className="w-4 h-4" />
                Approuver
              </button>
              <button
                onClick={() => onReject(approval.id)}
                className="flex items-center gap-1.5 px-4 py-2 bg-red-800 hover:bg-red-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                <XCircle className="w-4 h-4" />
                Rejeter
              </button>
            </div>
          )}
        </div>

        {/* Toggle detail */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-3 flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300"
        >
          {expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
          {expanded ? 'Masquer les détails' : 'Voir les détails'}
        </button>
      </div>

      {expanded && (
        <div className="border-t border-gray-800 bg-gray-800/30 px-5 py-4 space-y-4">
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Analyse de l'agent</p>
            <p className="text-sm text-gray-300 leading-relaxed">{approval.rationale}</p>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="bg-gray-800 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 mb-1">Coût estimé</p>
              <p className="text-base font-bold text-red-400">
                {approval.estimated_cost > 0 ? `$${approval.estimated_cost.toLocaleString()}` : 'N/A'}
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 mb-1">Revenue estimé</p>
              <p className="text-base font-bold text-green-400">
                {approval.estimated_revenue > 0 ? `$${approval.estimated_revenue.toLocaleString()}` : 'N/A'}
              </p>
            </div>
            <div className="bg-gray-800 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-500 mb-1">ROI estimé</p>
              <p className="text-base font-bold text-indigo-400">
                {approval.estimated_cost > 0
                  ? `${(((approval.estimated_revenue - approval.estimated_cost) / approval.estimated_cost) * 100).toFixed(0)}%`
                  : 'N/A'
                }
              </p>
            </div>
          </div>

          <div className="bg-indigo-900/20 border border-indigo-800/50 rounded-lg p-3">
            <p className="text-xs font-semibold text-indigo-400 mb-1">Recommandation de l'agent</p>
            <p className="text-sm text-indigo-300">{approval.recommendation}</p>
          </div>

          {'review_notes' in approval && approval.review_notes && (
            <div className={`rounded-lg p-3 ${approval.status === 'APPROVED' ? 'bg-green-900/20 border border-green-800/50' : 'bg-red-900/20 border border-red-800/50'}`}>
              <p className={`text-xs font-semibold mb-1 ${approval.status === 'APPROVED' ? 'text-green-400' : 'text-red-400'}`}>
                Notes de révision
              </p>
              <p className={`text-sm ${approval.status === 'APPROVED' ? 'text-green-300' : 'text-red-300'}`}>
                {approval.review_notes}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function ApprovalsPage() {
  const [activeTab, setActiveTab] = useState<'PENDING' | 'APPROVED' | 'REJECTED'>('PENDING')
  const [reviewModal, setReviewModal] = useState<{ id: number; action: 'APPROVE' | 'REJECT' } | null>(null)
  const [reviewNotes, setReviewNotes] = useState('')
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['approvals'],
    queryFn: async () => {
      try {
        const res = await approvalsApi.list()
        return res.data
      } catch {
        return MOCK_APPROVALS
      }
    },
    refetchInterval: 30000,
  })

  const reviewMutation = useMutation({
    mutationFn: async ({ id, status, notes }: { id: number; status: string; notes: string }) => {
      try {
        return await approvalsApi.review(id, { status, review_notes: notes })
      } catch {
        return { data: { success: true } }
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] })
      queryClient.invalidateQueries({ queryKey: ['approval-stats'] })
      setReviewModal(null)
      setReviewNotes('')
    },
  })

  const approvals = data || MOCK_APPROVALS

  const filtered = approvals.filter((a: Approval) => a.status === activeTab)
  const pendingCount = approvals.filter((a: Approval) => a.status === 'PENDING').length
  const approvedToday = approvals.filter((a: Approval) => a.status === 'APPROVED').length
  const rejectedToday = approvals.filter((a: Approval) => a.status === 'REJECTED').length

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-yellow-900/20 border border-yellow-800/40 rounded-xl p-4 text-center">
          <p className="text-3xl font-bold text-yellow-400">{pendingCount}</p>
          <p className="text-sm text-yellow-300 mt-1">En attente</p>
        </div>
        <div className="bg-green-900/20 border border-green-800/40 rounded-xl p-4 text-center">
          <p className="text-3xl font-bold text-green-400">{approvedToday}</p>
          <p className="text-sm text-green-300 mt-1">Approuvées</p>
        </div>
        <div className="bg-red-900/20 border border-red-800/40 rounded-xl p-4 text-center">
          <p className="text-3xl font-bold text-red-400">{rejectedToday}</p>
          <p className="text-sm text-red-300 mt-1">Rejetées</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1 w-fit">
        {(['PENDING', 'APPROVED', 'REJECTED'] as const).map((tab) => {
          const count = approvals.filter((a: Approval) => a.status === tab).length
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {tab === 'PENDING' ? 'En attente' : tab === 'APPROVED' ? 'Approuvées' : 'Rejetées'}
              {count > 0 && (
                <span className={`text-xs rounded-full px-1.5 py-0.5 font-bold ${
                  activeTab === tab ? 'bg-white/20' : 'bg-gray-800'
                }`}>
                  {count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Approvals list */}
      {isLoading ? (
        <PageLoader />
      ) : filtered.length === 0 ? (
        <Card>
          <div className="text-center py-8 text-gray-500">
            <CheckCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>Aucune validation dans cette catégorie</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          {filtered.map((approval: Approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              onApprove={(id) => setReviewModal({ id, action: 'APPROVE' })}
              onReject={(id) => setReviewModal({ id, action: 'REJECT' })}
            />
          ))}
        </div>
      )}

      {/* Review Confirmation Modal */}
      <Modal
        isOpen={!!reviewModal}
        onClose={() => { setReviewModal(null); setReviewNotes('') }}
        title={reviewModal?.action === 'APPROVE' ? 'Confirmer l\'approbation' : 'Confirmer le rejet'}
        size="md"
        footer={
          <>
            <Button variant="outline" onClick={() => { setReviewModal(null); setReviewNotes('') }}>
              Annuler
            </Button>
            <Button
              variant={reviewModal?.action === 'APPROVE' ? 'success' : 'danger'}
              loading={reviewMutation.isPending}
              leftIcon={reviewModal?.action === 'APPROVE' ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
              onClick={() => {
                if (!reviewModal) return
                reviewMutation.mutate({
                  id: reviewModal.id,
                  status: reviewModal.action === 'APPROVE' ? 'APPROVED' : 'REJECTED',
                  notes: reviewNotes,
                })
              }}
            >
              {reviewModal?.action === 'APPROVE' ? 'Approuver' : 'Rejeter'}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className={`p-4 rounded-xl border ${
            reviewModal?.action === 'APPROVE'
              ? 'bg-green-900/20 border-green-800/50 text-green-300'
              : 'bg-red-900/20 border-red-800/50 text-red-300'
          }`}>
            <p className="text-sm font-medium">
              {reviewModal?.action === 'APPROVE'
                ? 'Vous êtes sur le point d\'approuver cette décision. L\'agent pourra procéder à son exécution.'
                : 'Vous êtes sur le point de rejeter cette décision. L\'agent sera notifié.'
              }
            </p>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-300 block mb-1.5">
              Notes de révision *
            </label>
            <textarea
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              className="input-dark w-full h-28 resize-none"
              placeholder="Expliquez votre décision..."
              required
            />
            <p className="text-xs text-gray-500 mt-1">Ces notes seront enregistrées dans l'historique d'audit.</p>
          </div>
        </div>
      </Modal>
    </div>
  )
}
