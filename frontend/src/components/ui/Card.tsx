import { cn } from '@/lib/utils'
import React from 'react'

interface CardProps {
  title?: string
  children: React.ReactNode
  className?: string
  headerAction?: React.ReactNode
  description?: string
  noPadding?: boolean
}

export default function Card({ title, children, className, headerAction, description, noPadding }: CardProps) {
  return (
    <div className={cn(
      'bg-gray-900 border border-gray-800 rounded-xl',
      !noPadding && 'p-6',
      className
    )}>
      {(title || headerAction) && (
        <div className={cn(
          'flex items-center justify-between',
          !noPadding ? 'mb-4' : 'px-6 pt-6 mb-4'
        )}>
          <div>
            {title && <h3 className="text-lg font-semibold text-gray-100">{title}</h3>}
            {description && <p className="text-sm text-gray-400 mt-0.5">{description}</p>}
          </div>
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      {noPadding ? children : children}
    </div>
  )
}

export function CardContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('', className)}>{children}</div>
}

export function CardHeader({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('flex items-center justify-between mb-4', className)}>{children}</div>
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return <h3 className={cn('text-lg font-semibold text-gray-100', className)}>{children}</h3>
}
