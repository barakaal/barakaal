import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount)
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat('en-US').format(n)
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' })
}

export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('fr-FR')
}

export function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    ACTIVE: 'text-green-400', APPROVED: 'text-green-400', COMPLETED: 'text-green-400', DELIVERED: 'text-green-400',
    PENDING: 'text-yellow-400', PENDING_APPROVAL: 'text-yellow-400', DRAFT: 'text-yellow-400', CANDIDATE: 'text-yellow-400',
    REJECTED: 'text-red-400', FAILED: 'text-red-400', CANCELLED: 'text-red-400', DISCONTINUED: 'text-red-400',
    RUNNING: 'text-blue-400', PROCESSING: 'text-blue-400', SHIPPED: 'text-blue-400',
    IDLE: 'text-gray-400', PAUSED: 'text-gray-400',
    CRITICAL: 'text-red-500', HIGH: 'text-orange-400', MEDIUM: 'text-yellow-400', LOW: 'text-green-400',
  }
  return map[status] || 'text-gray-400'
}

export function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-400'
  if (score >= 65) return 'text-blue-400'
  if (score >= 50) return 'text-yellow-400'
  if (score >= 35) return 'text-orange-400'
  return 'text-red-400'
}

export function getRiskBadge(level: string): string {
  const map: Record<string, string> = {
    LOW: 'bg-green-900 text-green-300',
    MEDIUM: 'bg-yellow-900 text-yellow-300',
    HIGH: 'bg-orange-900 text-orange-300',
    CRITICAL: 'bg-red-900 text-red-300',
  }
  return map[level] || 'bg-gray-800 text-gray-300'
}

export function getStatusBadgeClass(status: string): string {
  const map: Record<string, string> = {
    ACTIVE: 'bg-green-900 text-green-300',
    APPROVED: 'bg-green-900 text-green-300',
    COMPLETED: 'bg-green-900 text-green-300',
    DELIVERED: 'bg-green-900 text-green-300',
    PENDING: 'bg-yellow-900 text-yellow-300',
    PENDING_APPROVAL: 'bg-yellow-900 text-yellow-300',
    DRAFT: 'bg-gray-800 text-gray-300',
    CANDIDATE: 'bg-blue-900 text-blue-300',
    REJECTED: 'bg-red-900 text-red-300',
    FAILED: 'bg-red-900 text-red-300',
    CANCELLED: 'bg-red-900 text-red-300',
    DISCONTINUED: 'bg-gray-800 text-gray-300',
    RUNNING: 'bg-blue-900 text-blue-300',
    PROCESSING: 'bg-blue-900 text-blue-300',
    SHIPPED: 'bg-indigo-900 text-indigo-300',
    IDLE: 'bg-gray-800 text-gray-300',
    PAUSED: 'bg-gray-800 text-gray-400',
  }
  return map[status] || 'bg-gray-800 text-gray-300'
}
