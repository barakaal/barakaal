'use client'
import { usePathname } from 'next/navigation'
import Sidebar from '@/components/layout/Sidebar'
import { Bell, User } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { authApi } from '@/lib/api'

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Tableau de bord CEO',
  '/dashboard/departments': 'Départements',
  '/dashboard/agents': 'Agents IA',
  '/dashboard/products': 'Produits',
  '/dashboard/suppliers': 'Fournisseurs',
  '/dashboard/orders': 'Commandes',
  '/dashboard/approvals': 'Centre de validation',
  '/dashboard/finance': 'Finance',
  '/dashboard/logs': "Logs d'audit",
  '/dashboard/reports': 'Rapports',
  '/dashboard/connectors': 'Connecteurs',
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const pageTitle = PAGE_TITLES[pathname] || 'Dashboard'

  const { data: user } = useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      try {
        const res = await authApi.me()
        return res.data
      } catch {
        return { email: 'admin@company.com', full_name: 'Admin' }
      }
    },
    staleTime: 300000,
  })

  const today = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })

  return (
    <div className="flex min-h-screen bg-gray-950">
      <Sidebar />

      {/* Main content */}
      <div className="flex-1 ml-60 flex flex-col min-h-screen">
        {/* Top Header */}
        <header className="h-16 bg-gray-900/80 backdrop-blur-sm border-b border-gray-800 flex items-center justify-between px-6 sticky top-0 z-30">
          <div>
            <h1 className="text-lg font-semibold text-gray-100">{pageTitle}</h1>
            <p className="text-xs text-gray-500 capitalize">{today}</p>
          </div>

          <div className="flex items-center gap-3">
            {/* Notifications */}
            <button className="relative p-2 rounded-lg hover:bg-gray-800 text-gray-400 hover:text-gray-200 transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            </button>

            {/* User */}
            <div className="flex items-center gap-2 pl-3 border-l border-gray-700">
              <div className="w-8 h-8 bg-indigo-700 rounded-full flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="hidden sm:block">
                <p className="text-sm font-medium text-gray-200 leading-none">
                  {user?.full_name || 'Admin'}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {user?.email || 'admin@company.com'}
                </p>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6 scrollbar-dark">
          {children}
        </main>
      </div>
    </div>
  )
}
