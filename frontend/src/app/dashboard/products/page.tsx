'use client'
import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { productsApi } from '@/lib/api'
import { formatCurrency, formatDateTime, getScoreColor } from '@/lib/utils'
import Card from '@/components/ui/Card'
import Badge, { StatusBadge } from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Modal from '@/components/ui/Modal'
import ScoreBar from '@/components/ui/ScoreBar'
import { PageLoader } from '@/components/ui/LoadingSpinner'
import {
  Plus, Upload, Filter, RefreshCw, Package,
  BarChart2, Star, ShoppingBag
} from 'lucide-react'
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer
} from 'recharts'

const MOCK_PRODUCTS = [
  { id: 1, name: 'Montre Connectée Pro X12', category: 'Électronique', score: 87, status: 'ACTIVE', supplier_price: 18.50, selling_price: 79.99, margin_pct: 76.9, stock: 45, orders_30d: 124 },
  { id: 2, name: 'Écouteurs Sans Fil Elite', category: 'Audio', score: 82, status: 'ACTIVE', supplier_price: 12.30, selling_price: 49.99, margin_pct: 75.4, stock: 0, orders_30d: 89 },
  { id: 3, name: 'Lampe LED Bureau Smart', category: 'Maison', score: 76, status: 'ACTIVE', supplier_price: 8.90, selling_price: 34.99, margin_pct: 74.6, stock: 128, orders_30d: 67 },
  { id: 4, name: 'Support Téléphone Voiture', category: 'Auto', score: 71, status: 'ACTIVE', supplier_price: 3.20, selling_price: 19.99, margin_pct: 84.0, stock: 312, orders_30d: 203 },
  { id: 5, name: 'Chargeur Rapide USB-C 65W', category: 'Électronique', score: 68, status: 'PENDING_APPROVAL', supplier_price: 6.80, selling_price: 29.99, margin_pct: 77.3, stock: 5, orders_30d: 45 },
  { id: 6, name: 'Sac à Dos Étanche 40L', category: 'Sport', score: 61, status: 'CANDIDATE', supplier_price: 22.00, selling_price: 69.99, margin_pct: 68.6, stock: 0, orders_30d: 0 },
  { id: 7, name: 'Robot Aspirateur Auto', category: 'Maison', score: 55, status: 'DRAFT', supplier_price: 45.00, selling_price: 149.99, margin_pct: 70.0, stock: 0, orders_30d: 0 },
  { id: 8, name: 'Drone Pliable 4K', category: 'Tech', score: 48, status: 'PENDING_APPROVAL', supplier_price: 89.00, selling_price: 249.99, margin_pct: 64.4, stock: 0, orders_30d: 0 },
  { id: 9, name: 'Ceinture Fitness Smart', category: 'Sport', score: 39, status: 'REJECTED', supplier_price: 15.00, selling_price: 39.99, margin_pct: 62.5, stock: 0, orders_30d: 0 },
  { id: 10, name: 'Câble HDMI Ultra HD', category: 'Électronique', score: 35, status: 'DISCONTINUED', supplier_price: 2.50, selling_price: 12.99, margin_pct: 80.8, stock: 8, orders_30d: 5 },
]

const SCORE_CRITERIA = [
  { criterion: 'Demande marché', score: 88 },
  { criterion: 'Marge', score: 77 },
  { criterion: 'Concurrence', score: 65 },
  { criterion: 'Fiabilité fournisseur', score: 90 },
  { criterion: 'Tendance', score: 72 },
  { criterion: 'Facilité livraison', score: 85 },
]

type Product = typeof MOCK_PRODUCTS[0]

export default function ProductsPage() {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [showImport, setShowImport] = useState(false)
  const [filterStatus, setFilterStatus] = useState('')
  const [filterCategory, setFilterCategory] = useState('')
  const [filterMinScore, setFilterMinScore] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['products', filterStatus, filterCategory, filterMinScore],
    queryFn: async () => {
      try {
        const res = await productsApi.list({
          status: filterStatus || undefined,
          category: filterCategory || undefined,
          min_score: filterMinScore || undefined,
        })
        return res.data
      } catch {
        return MOCK_PRODUCTS
      }
    },
  })

  const scoreMutation = useMutation({
    mutationFn: (id: number) => productsApi.score(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['products'] }),
  })

  const importMutation = useMutation({
    mutationFn: (file: File) => productsApi.importCSV(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] })
      setShowImport(false)
    },
  })

  const products = (data || MOCK_PRODUCTS).filter((p: Product) => {
    if (searchQuery && !p.name.toLowerCase().includes(searchQuery.toLowerCase())) return false
    if (filterMinScore && p.score < filterMinScore) return false
    return true
  })

  const categories = [...new Set(MOCK_PRODUCTS.map((p) => p.category))]

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file && file.name.endsWith('.csv')) {
      importMutation.mutate(file)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <p className="text-gray-400 text-sm">{products.length} produits</p>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            leftIcon={<Upload className="w-4 h-4" />}
            onClick={() => setShowImport(true)}
            size="md"
          >
            Importer CSV
          </Button>
          <Button leftIcon={<Plus className="w-4 h-4" />} size="md">
            Ajouter produit
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <Filter className="w-4 h-4 text-gray-500 flex-shrink-0" />
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Rechercher un produit..."
          className="input-dark text-sm py-1.5 w-48"
        />
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="select-dark text-sm py-1.5">
          <option value="">Tous les statuts</option>
          <option value="ACTIVE">Actif</option>
          <option value="PENDING_APPROVAL">En attente</option>
          <option value="CANDIDATE">Candidat</option>
          <option value="DRAFT">Brouillon</option>
          <option value="REJECTED">Rejeté</option>
        </select>
        <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)} className="select-dark text-sm py-1.5">
          <option value="">Toutes catégories</option>
          {categories.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select value={filterMinScore} onChange={(e) => setFilterMinScore(Number(e.target.value))} className="select-dark text-sm py-1.5">
          <option value={0}>Score min: tous</option>
          <option value={70}>Score ≥ 70</option>
          <option value={60}>Score ≥ 60</option>
          <option value={50}>Score ≥ 50</option>
        </select>
      </div>

      {/* Products Table */}
      <Card noPadding>
        {isLoading ? (
          <PageLoader />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Produit</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Catégorie</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Score</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Statut</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Prix fournisseur</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Prix vente</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-400 uppercase">Marge %</th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product: Product, idx: number) => (
                  <tr
                    key={product.id}
                    className={`border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors cursor-pointer ${idx % 2 === 1 ? 'bg-gray-900/30' : ''}`}
                    onClick={() => setSelectedProduct(product)}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-gray-800 rounded-lg flex items-center justify-center flex-shrink-0">
                          <Package className="w-4 h-4 text-gray-500" />
                        </div>
                        <span className="text-sm font-medium text-gray-200">{product.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="default">{product.category}</Badge>
                    </td>
                    <td className="px-4 py-3 w-36">
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-bold w-8 ${getScoreColor(product.score)}`}>{product.score}</span>
                        <div className="flex-1">
                          <ScoreBar score={product.score} showValue={false} height="sm" />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={product.status} />
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-gray-300">{formatCurrency(product.supplier_price)}</td>
                    <td className="px-4 py-3 text-right text-sm text-gray-300">{formatCurrency(product.selling_price)}</td>
                    <td className="px-4 py-3 text-right">
                      <span className={`text-sm font-semibold ${product.margin_pct >= 70 ? 'text-green-400' : product.margin_pct >= 50 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {product.margin_pct.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={() => scoreMutation.mutate(product.id)}
                        className="p-1.5 rounded-lg hover:bg-gray-700 text-gray-400 hover:text-indigo-400 transition-colors"
                        title="Recalculer le score"
                      >
                        <RefreshCw className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Product Detail Modal */}
      <Modal
        isOpen={!!selectedProduct}
        onClose={() => setSelectedProduct(null)}
        title={selectedProduct?.name}
        size="2xl"
        footer={
          <>
            <Button variant="outline" onClick={() => setSelectedProduct(null)}>Fermer</Button>
            <Button
              leftIcon={<RefreshCw className="w-4 h-4" />}
              loading={scoreMutation.isPending}
              onClick={() => selectedProduct && scoreMutation.mutate(selectedProduct.id)}
              variant="secondary"
            >
              Recalculer score
            </Button>
          </>
        }
      >
        {selectedProduct && (
          <div className="space-y-5">
            {/* Header */}
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 bg-gray-800 rounded-xl flex items-center justify-center flex-shrink-0">
                <Package className="w-8 h-8 text-gray-500" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <Badge variant="default">{selectedProduct.category}</Badge>
                  <StatusBadge status={selectedProduct.status} />
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center">
                    <p className="text-xs text-gray-500">Prix fournisseur</p>
                    <p className="text-sm font-semibold text-gray-200">{formatCurrency(selectedProduct.supplier_price)}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500">Prix vente</p>
                    <p className="text-sm font-semibold text-gray-200">{formatCurrency(selectedProduct.selling_price)}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500">Marge</p>
                    <p className="text-sm font-semibold text-green-400">{selectedProduct.margin_pct.toFixed(1)}%</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Score Section */}
            <div className="bg-gray-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-semibold text-gray-200 flex items-center gap-2">
                  <Star className="w-4 h-4 text-yellow-400" />
                  Score Dropshipping
                </h4>
                <span className={`text-3xl font-bold ${getScoreColor(selectedProduct.score)}`}>
                  {selectedProduct.score}/100
                </span>
              </div>

              {/* Radar Chart */}
              <div className="h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={SCORE_CRITERIA}>
                    <PolarGrid stroke="rgba(55,65,81,0.8)" />
                    <PolarAngleAxis dataKey="criterion" tick={{ fontSize: 10, fill: '#9ca3af' }} />
                    <Radar name="Score" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              <div className="space-y-2 mt-3">
                {SCORE_CRITERIA.map((c) => (
                  <div key={c.criterion} className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 w-36 flex-shrink-0">{c.criterion}</span>
                    <ScoreBar score={c.score} showValue={true} height="sm" className="flex-1" />
                  </div>
                ))}
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-800 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-1">
                  <ShoppingBag className="w-4 h-4 text-gray-500" />
                  <p className="text-xs text-gray-500">Commandes 30j</p>
                </div>
                <p className="text-xl font-bold text-gray-200">{selectedProduct.orders_30d}</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-1">
                  <BarChart2 className="w-4 h-4 text-gray-500" />
                  <p className="text-xs text-gray-500">Stock</p>
                </div>
                <p className={`text-xl font-bold ${selectedProduct.stock === 0 ? 'text-red-400' : selectedProduct.stock < 10 ? 'text-yellow-400' : 'text-gray-200'}`}>
                  {selectedProduct.stock} unités
                </p>
              </div>
            </div>
          </div>
        )}
      </Modal>

      {/* Import CSV Modal */}
      <Modal
        isOpen={showImport}
        onClose={() => setShowImport(false)}
        title="Importer des produits via CSV"
        size="md"
        footer={
          <>
            <Button variant="outline" onClick={() => setShowImport(false)}>Annuler</Button>
            <Button onClick={() => fileRef.current?.click()} loading={importMutation.isPending}>
              Sélectionner un fichier
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              isDragging ? 'border-indigo-500 bg-indigo-900/20' : 'border-gray-700 hover:border-gray-600'
            }`}
          >
            <Upload className="w-10 h-10 text-gray-500 mx-auto mb-3" />
            <p className="text-gray-300 font-medium">Glissez-déposez votre fichier CSV</p>
            <p className="text-sm text-gray-500 mt-1">ou cliquez pour sélectionner</p>
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) importMutation.mutate(file)
              }}
            />
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-xs font-semibold text-gray-400 mb-2">Format attendu:</p>
            <code className="text-xs text-green-400 font-mono block">
              name,category,supplier_price,selling_price,description,supplier_url
            </code>
          </div>
        </div>
      </Modal>
    </div>
  )
}
