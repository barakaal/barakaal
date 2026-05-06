import { cn } from '@/lib/utils'
import { TrendingDown, TrendingUp } from 'lucide-react'
import React from 'react'

interface StatCardProps {
  title: string
  value: string | number
  change?: number
  changeLabel?: string
  icon: React.ReactNode
  variant?: 'default' | 'warning' | 'danger' | 'success'
  subtitle?: string
}

const variantStyles: Record<string, { card: string; icon: string }> = {
  default: {
    card: 'border-gray-800',
    icon: 'bg-indigo-900/40 text-indigo-400',
  },
  success: {
    card: 'border-green-900/50',
    icon: 'bg-green-900/40 text-green-400',
  },
  warning: {
    card: 'border-yellow-900/50',
    icon: 'bg-yellow-900/40 text-yellow-400',
  },
  danger: {
    card: 'border-red-900/50',
    icon: 'bg-red-900/40 text-red-400',
  },
}

export default function StatCard({
  title,
  value,
  change,
  changeLabel,
  icon,
  variant = 'default',
  subtitle,
}: StatCardProps) {
  const styles = variantStyles[variant]
  const isPositive = change !== undefined && change >= 0

  return (
    <div className={cn(
      'bg-gray-900 border rounded-xl p-6 flex flex-col gap-4',
      styles.card
    )}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-400">{title}</p>
          <p className={cn(
            'text-3xl font-bold mt-1',
            variant === 'danger' ? 'text-red-400' :
            variant === 'warning' ? 'text-yellow-400' :
            variant === 'success' ? 'text-green-400' :
            'text-gray-100'
          )}>
            {value}
          </p>
          {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
        <div className={cn('p-3 rounded-xl', styles.icon)}>
          {icon}
        </div>
      </div>

      {change !== undefined && (
        <div className="flex items-center gap-1.5">
          {isPositive ? (
            <TrendingUp className="w-4 h-4 text-green-400" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-400" />
          )}
          <span className={cn(
            'text-sm font-medium',
            isPositive ? 'text-green-400' : 'text-red-400'
          )}>
            {isPositive ? '+' : ''}{change.toFixed(1)}%
          </span>
          {changeLabel && <span className="text-sm text-gray-500">{changeLabel}</span>}
        </div>
      )}
    </div>
  )
}
