import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from './Button'
import { GlassCard } from './GlassCard'

export interface ErrorStateProps {
  title?: string
  message: string
  onRetry?: () => void
  isRetrying?: boolean
  className?: string
}

export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  isRetrying = false,
  className,
}: ErrorStateProps) {
  return (
    <GlassCard
      variant="default"
      className={cn(
        'flex flex-col items-center justify-center p-6 md:p-8 text-center space-y-4 border-rose-500/20 bg-rose-500/[0.03]',
        className,
      )}
    >
      <div className="p-3 rounded-2xl bg-rose-500/8 border border-rose-500/25 text-rose-400">
        <AlertCircle className="w-6 h-6" />
      </div>

      <div className="space-y-1.5 max-w-md">
        <h4 className="text-sm md:text-base font-semibold text-rose-200 tracking-tight">
          {title}
        </h4>
        <p className="text-xs md:text-sm text-zinc-400 leading-relaxed font-mono">
          {message}
        </p>
      </div>

      {onRetry && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onRetry}
          isLoading={isRetrying}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          className="mt-2 border-white/[0.12] hover:border-white/[0.2]"
        >
          Try Again
        </Button>
      )}
    </GlassCard>
  )
}
