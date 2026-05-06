import { cn } from '@/lib/utils'

interface ScoreBarProps {
  score: number
  label?: string
  showValue?: boolean
  height?: 'sm' | 'md' | 'lg'
  className?: string
}

function getScoreColorClass(score: number): string {
  if (score >= 80) return 'bg-green-500'
  if (score >= 65) return 'bg-blue-500'
  if (score >= 50) return 'bg-yellow-500'
  if (score >= 35) return 'bg-orange-500'
  return 'bg-red-500'
}

function getScoreTextClass(score: number): string {
  if (score >= 80) return 'text-green-400'
  if (score >= 65) return 'text-blue-400'
  if (score >= 50) return 'text-yellow-400'
  if (score >= 35) return 'text-orange-400'
  return 'text-red-400'
}

const heightClasses = {
  sm: 'h-1.5',
  md: 'h-2',
  lg: 'h-3',
}

export default function ScoreBar({ score, label, showValue = true, height = 'md', className }: ScoreBarProps) {
  const clampedScore = Math.max(0, Math.min(100, score))

  return (
    <div className={cn('flex flex-col gap-1', className)}>
      {(label || showValue) && (
        <div className="flex items-center justify-between">
          {label && <span className="text-xs text-gray-400">{label}</span>}
          {showValue && (
            <span className={cn('text-sm font-semibold', getScoreTextClass(clampedScore))}>
              {clampedScore.toFixed(0)}
            </span>
          )}
        </div>
      )}
      <div className={cn('w-full bg-gray-800 rounded-full overflow-hidden', heightClasses[height])}>
        <div
          className={cn('h-full rounded-full transition-all duration-500', getScoreColorClass(clampedScore))}
          style={{ width: `${clampedScore}%` }}
        />
      </div>
    </div>
  )
}

interface ScoreDisplayProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
}

export function ScoreDisplay({ score, size = 'md' }: ScoreDisplayProps) {
  const textSize = size === 'sm' ? 'text-lg' : size === 'md' ? 'text-2xl' : 'text-4xl'

  return (
    <div className="flex flex-col items-center gap-1">
      <span className={cn('font-bold', textSize, getScoreTextClass(score))}>
        {score.toFixed(0)}
      </span>
      <ScoreBar score={score} showValue={false} className="w-24" />
    </div>
  )
}
