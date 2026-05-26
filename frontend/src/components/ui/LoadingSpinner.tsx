import { cn } from '@/lib/utils'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeClasses = {
  sm: 'w-4 h-4 border-2',
  md: 'w-8 h-8 border-3',
  lg: 'w-12 h-12 border-4',
}

export default function LoadingSpinner({ size = 'md', className }: SpinnerProps) {
  return (
    <div className={cn(
      'border-indigo-500 border-t-transparent rounded-full animate-spin',
      sizeClasses[size],
      className
    )} />
  )
}

export function PageLoader() {
  return (
    <div className="flex items-center justify-center min-h-64">
      <div className="flex flex-col items-center gap-4">
        <LoadingSpinner size="lg" />
        <p className="text-gray-400 text-sm">Chargement...</p>
      </div>
    </div>
  )
}

interface SkeletonProps {
  className?: string
  lines?: number
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn('skeleton rounded', className)} />
  )
}

export function SkeletonCard() {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
      <Skeleton className="h-8 w-24" />
      <Skeleton className="h-3 w-full" />
    </div>
  )
}

export function SkeletonRow() {
  return (
    <tr className="border-b border-gray-800/50">
      {Array.from({ length: 6 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton className="h-4" style={{ width: `${50 + Math.random() * 50}%` } as React.CSSProperties} />
        </td>
      ))}
    </tr>
  )
}

export function SkeletonTable({ rows = 5, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {Array.from({ length: cols }).map((_, j) => (
            <Skeleton key={j} className="h-10 flex-1" />
          ))}
        </div>
      ))}
    </div>
  )
}

export function SkeletonStats() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  )
}
