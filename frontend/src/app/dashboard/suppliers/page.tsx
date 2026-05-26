'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { suppliersApi } from '@/lib/api'
import { Truck, Star, CheckCircle, XCircle } from 'lucide-react'
import Badge from '@/components/ui/Badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

const MOCK_SUPPLIERS = [
  { id: 1, name: 'ShenZhen Electronics Co.', platform: 'ALIEXPRESS', country: 'CN', rating: 4.8, response_time_hours: 12, min_order_qty: 1, is_verified: true, is_active: true, products_count: 24 },
  { id: 2, name: 'EcoHome Supply', platform: 'ALIBABA', country: 'CN', rating: 4.6, response_time_hours: 24, min_order_qty: 5, is_verified: true, is_active: true, products_count: 11 },
  { id: 3, name: 'BeautyTech Manufacturing', platform: 'ALIEXPRESS', country: 'CN', rating: 4.9, response_time_hours: 8, min_order_qty: 1, is_verified: true, is_active: true, products_count: 8 },
  { id: 4, name: 'SportGear Wholesale', platform: 'ALIBABA', country: 'KR', rating: 4.2, response_time_hours: 36, min_order_qty: 10, is_verified: false, is_active: true, products_count: 5 },
]

const PLATFORM_BADGES: Record<string, string> = {
  ALIEXPRESS: 'bg-orange-900 text-orange-300',
  ALIBABA: 'bg-yellow-900 text-yellow-300',
  EBAY: 'bg-blue-900 text-blue-300',
}

export default function SuppliersPage() {
  const [platformFilter, setPlatformFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['suppliers', platformFilter],
    queryFn: () => suppliersApi.list({ platform: platformFilter || undefined }),
  })

  const suppliers = data?.data?.items || MOCK_SUPPLIERS
  const filtered = suppliers.filter((s: any) => !platformFilter || s.platform === platformFilter)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Truck size={24} className="text-indigo-400" />
          <h1 className="text-2xl font-bold text-white">Fournisseurs</h1>
        </div>
        <select
          value={platformFilter}
          onChange={(e) => setPlatformFilter(e.target.value)}
          className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:border-indigo-500"
        >
          <option value="">Toutes plateformes</option>
          <option value="ALIEXPRESS">AliExpress</option>
          <option value="ALIBABA">Alibaba</option>
          <option value="EBAY">eBay</option>
        </select>
      </div>

      {isLoading ? <LoadingSpinner /> : (
        <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 border-b border-gray-800 bg-gray-900/80">
                <th className="px-6 py-4">Fournisseur</th>
                <th className="px-6 py-4">Plateforme</th>
                <th className="px-6 py-4">Pays</th>
                <th className="px-6 py-4">Note</th>
                <th className="px-6 py-4">Délai réponse</th>
                <th className="px-6 py-4">MOQ</th>
                <th className="px-6 py-4">Produits</th>
                <th className="px-6 py-4">Vérifié</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s: any) => (
                <tr key={s.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                  <td className="px-6 py-4">
                    <div className="text-white font-medium">{s.name}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${PLATFORM_BADGES[s.platform] || 'bg-gray-800 text-gray-300'}`}>
                      {s.platform}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-300">{s.country}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1">
                      <Star size={14} className="text-yellow-400 fill-yellow-400" />
                      <span className="text-white">{s.rating}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-gray-300">{s.response_time_hours}h</td>
                  <td className="px-6 py-4 text-gray-300">{s.min_order_qty} unité(s)</td>
                  <td className="px-6 py-4 text-gray-300">{s.products_count}</td>
                  <td className="px-6 py-4">
                    {s.is_verified
                      ? <CheckCircle size={18} className="text-green-400" />
                      : <XCircle size={18} className="text-gray-600" />
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
