'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { connectorsApi } from '@/lib/api'
import { Plug, CheckCircle, XCircle, RefreshCw, AlertTriangle } from 'lucide-react'
import Modal from '@/components/ui/Modal'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

const CONNECTOR_INFO: Record<string, { icon: string; color: string; description: string }> = {
  AMAZON: { icon: '🛒', color: 'text-orange-400', description: 'Amazon Product Advertising API 5.0' },
  ALIEXPRESS: { icon: '📦', color: 'text-red-400', description: 'AliExpress DS (Dropshipping) API' },
  EBAY: { icon: '🏪', color: 'text-blue-400', description: 'eBay Browse API / Finding API' },
  GOOGLE_TRENDS: { icon: '📈', color: 'text-green-400', description: 'Google Trends (via pytrends)' },
  TIKTOK: { icon: '🎵', color: 'text-pink-400', description: 'TikTok for Business API' },
  CSV_IMPORT: { icon: '📋', color: 'text-gray-400', description: 'Import de fichiers CSV' },
}

const MOCK_CONNECTORS = [
  { id: 1, name: 'Amazon PA-API', platform: 'AMAZON', is_active: true, config: { mode: 'mock' }, last_sync_at: '2026-05-26T06:00:00Z', status: 'mock' },
  { id: 2, name: 'AliExpress DS API', platform: 'ALIEXPRESS', is_active: true, config: { mode: 'mock' }, last_sync_at: '2026-05-26T06:00:00Z', status: 'mock' },
  { id: 3, name: 'eBay Browse API', platform: 'EBAY', is_active: true, config: { mode: 'mock' }, last_sync_at: '2026-05-26T06:00:00Z', status: 'mock' },
  { id: 4, name: 'Google Trends', platform: 'GOOGLE_TRENDS', is_active: true, config: { mode: 'mock', geo: 'US' }, last_sync_at: '2026-05-26T06:00:00Z', status: 'mock' },
  { id: 5, name: 'TikTok for Business', platform: 'TIKTOK', is_active: true, config: { mode: 'mock' }, last_sync_at: '2026-05-26T06:00:00Z', status: 'mock' },
  { id: 6, name: 'CSV Import', platform: 'CSV_IMPORT', is_active: true, config: { mode: 'live' }, last_sync_at: null, status: 'live' },
]

export default function ConnectorsPage() {
  const [testingId, setTestingId] = useState<number | null>(null)
  const [testResults, setTestResults] = useState<Record<number, any>>({})
  const [configModal, setConfigModal] = useState<any>(null)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['connectors'],
    queryFn: () => connectorsApi.list(),
  })

  const connectors = data?.data || MOCK_CONNECTORS

  const testMutation = useMutation({
    mutationFn: (id: number) => connectorsApi.test(id),
    onMutate: (id) => setTestingId(id),
    onSuccess: (data, id) => {
      setTestResults(prev => ({ ...prev, [id]: data?.data || { success: true, message: 'Connected (mock)', latency_ms: 12 } }))
      setTestingId(null)
    },
    onError: (_, id) => {
      setTestResults(prev => ({ ...prev, [id]: { success: false, message: 'Test failed' } }))
      setTestingId(null)
    },
  })

  const syncMutation = useMutation({
    mutationFn: (id: number) => connectorsApi.sync(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['connectors'] }),
  })

  if (isLoading) return <LoadingSpinner />

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Plug size={24} className="text-indigo-400" />
        <h1 className="text-2xl font-bold text-white">Connecteurs Marketplace</h1>
      </div>

      <div className="bg-gray-800/50 border border-yellow-800/50 rounded-xl p-4 flex items-start gap-3">
        <AlertTriangle size={18} className="text-yellow-400 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-yellow-200">
          <strong>Mode Mock actif</strong> — Les connecteurs sans clé API configurée utilisent des données de démonstration.
          Configurez vos clés dans le fichier <code className="bg-gray-800 px-1 rounded">.env</code> pour activer les données réelles.
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {connectors.map((c: any) => {
          const info = CONNECTOR_INFO[c.platform] || { icon: '🔌', color: 'text-gray-400', description: c.name }
          const isMock = c.config?.mode === 'mock'
          const testResult = testResults[c.id]

          return (
            <div key={c.id} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{info.icon}</span>
                  <div>
                    <h3 className={`font-semibold ${info.color}`}>{c.name}</h3>
                    <p className="text-gray-500 text-xs">{info.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isMock && (
                    <span className="px-2 py-0.5 bg-yellow-900/50 text-yellow-400 text-xs rounded border border-yellow-800">MOCK</span>
                  )}
                  {c.is_active
                    ? <CheckCircle size={18} className="text-green-400" />
                    : <XCircle size={18} className="text-red-400" />
                  }
                </div>
              </div>

              {testResult && (
                <div className={`mb-3 px-3 py-2 rounded-lg text-xs ${testResult.success ? 'bg-green-900/30 text-green-300' : 'bg-red-900/30 text-red-300'}`}>
                  {testResult.success ? '✓ ' : '✗ '}{testResult.message}
                  {testResult.latency_ms > 0 && ` (${testResult.latency_ms}ms)`}
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => testMutation.mutate(c.id)}
                  disabled={testingId === c.id}
                  className="flex-1 py-1.5 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-gray-300 text-xs rounded-lg transition-colors"
                >
                  {testingId === c.id ? 'Test...' : 'Tester'}
                </button>
                <button
                  onClick={() => syncMutation.mutate(c.id)}
                  disabled={syncMutation.isPending}
                  className="flex items-center gap-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded-lg transition-colors"
                >
                  <RefreshCw size={12} /> Sync
                </button>
                <button
                  onClick={() => setConfigModal(c)}
                  className="px-3 py-1.5 bg-indigo-900/50 hover:bg-indigo-900 text-indigo-300 text-xs rounded-lg transition-colors"
                >
                  Configurer
                </button>
              </div>
            </div>
          )
        })}
      </div>

      <Modal isOpen={!!configModal} onClose={() => setConfigModal(null)} title={`Configurer: ${configModal?.name}`}>
        {configModal && (
          <div className="space-y-4">
            <div className="bg-gray-800 rounded-lg p-4 text-sm text-gray-300">
              Pour configurer ce connecteur, ajoutez les clés API dans votre fichier <code className="bg-gray-700 px-1 rounded">.env</code> :
            </div>
            <div className="bg-gray-900 rounded-lg p-4 font-mono text-xs text-green-300">
              {configModal.platform === 'AMAZON' && <>AMAZON_ACCESS_KEY=your_key<br />AMAZON_SECRET_KEY=your_secret<br />AMAZON_PARTNER_TAG=your_tag</>}
              {configModal.platform === 'ALIEXPRESS' && <>ALIEXPRESS_APP_KEY=your_key<br />ALIEXPRESS_APP_SECRET=your_secret</>}
              {configModal.platform === 'EBAY' && <>EBAY_CLIENT_ID=your_client_id<br />EBAY_CLIENT_SECRET=your_secret</>}
              {configModal.platform === 'TIKTOK' && <>TIKTOK_APP_ID=your_app_id<br />TIKTOK_APP_SECRET=your_secret</>}
              {configModal.platform === 'GOOGLE_TRENDS' && <>{'# Google Trends utilise pytrends (pas de clé API requise)'}<br />{'# Activé automatiquement en production'}</>}
              {configModal.platform === 'CSV_IMPORT' && <>{'# Aucune configuration requise'}<br />{'# Import via Dashboard → Produits → Importer CSV'}</>}
            </div>
            <p className="text-gray-500 text-xs">Redémarrez le serveur backend après avoir mis à jour le fichier .env.</p>
          </div>
        )}
      </Modal>
    </div>
  )
}
