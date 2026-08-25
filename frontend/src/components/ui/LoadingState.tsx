import React from 'react'
import { cn } from '@/lib/utils'
import { Spinner } from './Spinner'

export interface LoadingStateProps {
  label?: string
  sublabel?: string
  fullPage?: boolean
  className?: string
}

export function LoadingState({
  label = 'Loading AI Intelligence...',
  sublabel = 'Please wait while resources are processed',
  fullPage = false,
  className,
}: LoadingStateProps) {
  const content = (
    <div className="flex flex-col items-center justify-center text-center space-y-3.5 p-6">
      <div className="relative flex items-center justify-center">
        <div className="w-12 h-12 rounded-2xl bg-white/[0.04] border border-white/[0.08] backdrop-blur-md flex items-center justify-center">
          <Spinner size="lg" className="text-zinc-200" />
        </div>
      </div>
      <div className="space-y-1">
        <p className="text-sm font-medium text-zinc-200 tracking-tight">
          {label}
        </p>
        {sublabel && (
          <p className="text-xs text-zinc-500 max-w-xs">{sublabel}</p>
        )}
      </div>
    </div>
  )

  if (fullPage) {
    return (
      <div
        role="status"
        className={cn(
          'fixed inset-0 z-50 flex items-center justify-center bg-[#07080c]/80 backdrop-blur-md',
          className,
        )}
      >
        {content}
      </div>
    )
  }

  return (
    <div
      role="status"
      className={cn('w-full flex items-center justify-center py-12', className)}
    >
      {content}
    </div>
  )
}
