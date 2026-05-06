import { cn } from '@/lib/utils'

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple' | 'outline'

interface BadgeProps {
  children: React.ReactNode
  variant?: BadgeVariant
  className?: string
  size?: 'sm' | 'md'
}

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-gray-800 text-gray-300 border border-gray-700',
  success: 'bg-green-900/60 text-green-300 border border-green-800',
  warning: 'bg-yellow-900/60 text-yellow-300 border border-yellow-800',
  danger: 'bg-red-900/60 text-red-300 border border-red-800',
  info: 'bg-blue-900/60 text-blue-300 border border-blue-800',
  purple: 'bg-indigo-900/60 text-indigo-300 border border-indigo-800',
  outline: 'bg-transparent text-gray-300 border border-gray-600',
}

export default function Badge({ children, variant = 'default', className, size = 'sm' }: BadgeProps) {
  return (
    <span className={cn(
      'inline-flex items-center font-medium rounded-full',
      size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
      variantClasses[variant],
      className
    )}>
      {children}
    </span>
  )
}

export function StatusBadge({ status }: { status: string }) {
  const variantMap: Record<string, BadgeVariant> = {
    ACTIVE: 'success',
    APPROVED: 'success',
    COMPLETED: 'success',
    DELIVERED: 'success',
    PENDING: 'warning',
    PENDING_APPROVAL: 'warning',
    DRAFT: 'default',
    CANDIDATE: 'info',
    REJECTED: 'danger',
    FAILED: 'danger',
    CANCELLED: 'danger',
    DISCONTINUED: 'default',
    RUNNING: 'info',
    PROCESSING: 'info',
    SHIPPED: 'purple',
    IDLE: 'default',
    PAUSED: 'default',
    CONNECTED: 'success',
    MOCK: 'warning',
    ERROR: 'danger',
  }

  const labelMap: Record<string, string> = {
    ACTIVE: 'Actif',
    APPROVED: 'Approuvé',
    COMPLETED: 'Terminé',
    DELIVERED: 'Livré',
    PENDING: 'En attente',
    PENDING_APPROVAL: 'Validation requise',
    DRAFT: 'Brouillon',
    CANDIDATE: 'Candidat',
    REJECTED: 'Rejeté',
    FAILED: 'Échoué',
    CANCELLED: 'Annulé',
    DISCONTINUED: 'Arrêté',
    RUNNING: 'En cours',
    PROCESSING: 'Traitement',
    SHIPPED: 'Expédié',
    IDLE: 'Inactif',
    PAUSED: 'Pausé',
    CONNECTED: 'Connecté',
    MOCK: 'Mock',
    ERROR: 'Erreur',
  }

  return (
    <Badge variant={variantMap[status] || 'default'}>
      {labelMap[status] || status}
    </Badge>
  )
}
