'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  LayoutDashboard, Building2, Bot, Package, Truck,
  ShoppingCart, CheckCircle, DollarSign, ScrollText,
  BarChart3, Plug, LogOut, Zap
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { removeToken } from '@/lib/auth'
import { useQuery } from '@tanstack/react-query'
import { approvalsApi } from '@/lib/api'

interface NavItem {
  href: string
  label: string
  icon: React.ReactNode
  badge?: number
}

export default function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()

  const { data: approvalStats } = useQuery({
    queryKey: ['approval-stats'],
    queryFn: async () => {
      try {
        const res = await approvalsApi.stats()
        return res.data
      } catch {
        return { pending: 3 }
      }
    },
    refetchInterval: 60000,
  })

  const pendingCount = approvalStats?.pending || 0

  const navItems: NavItem[] = [
    { href: '/dashboard', label: 'Vue CEO', icon: <LayoutDashboard className="w-5 h-5" /> },
    { href: '/dashboard/departments', label: 'Départements', icon: <Building2 className="w-5 h-5" /> },
    { href: '/dashboard/agents', label: 'Agents IA', icon: <Bot className="w-5 h-5" /> },
    { href: '/dashboard/products', label: 'Produits', icon: <Package className="w-5 h-5" /> },
    { href: '/dashboard/suppliers', label: 'Fournisseurs', icon: <Truck className="w-5 h-5" /> },
    { href: '/dashboard/orders', label: 'Commandes', icon: <ShoppingCart className="w-5 h-5" /> },
    {
      href: '/dashboard/approvals',
      label: 'Validations',
      icon: <CheckCircle className="w-5 h-5" />,
      badge: pendingCount || undefined,
    },
    { href: '/dashboard/finance', label: 'Finance', icon: <DollarSign className="w-5 h-5" /> },
    { href: '/dashboard/logs', label: 'Logs d\'audit', icon: <ScrollText className="w-5 h-5" /> },
    { href: '/dashboard/reports', label: 'Rapports', icon: <BarChart3 className="w-5 h-5" /> },
    { href: '/dashboard/connectors', label: 'Connecteurs', icon: <Plug className="w-5 h-5" /> },
  ]

  const handleLogout = () => {
    removeToken()
    router.push('/login')
  }

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard'
    }
    return pathname.startsWith(href)
  }

  return (
    <div className="w-60 flex-shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col h-screen fixed left-0 top-0 z-40">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-gray-800">
        <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center flex-shrink-0">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-white leading-none">AI Dropship</p>
          <p className="text-xs text-indigo-400 mt-0.5">Company OS</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 scrollbar-dark">
        <ul className="space-y-0.5 px-2">
          {navItems.map((item) => {
            const active = isActive(item.href)
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                    active
                      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-900/30'
                      : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'
                  )}
                >
                  <span className={cn('flex-shrink-0', active ? 'text-white' : 'text-gray-500')}>
                    {item.icon}
                  </span>
                  <span className="flex-1 truncate">{item.label}</span>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span className="flex-shrink-0 bg-red-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                      {item.badge > 9 ? '9+' : item.badge}
                    </span>
                  )}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-800 p-3">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-400 hover:text-red-400 hover:bg-red-900/20 transition-all duration-150"
        >
          <LogOut className="w-5 h-5" />
          <span>Déconnexion</span>
        </button>
      </div>
    </div>
  )
}
