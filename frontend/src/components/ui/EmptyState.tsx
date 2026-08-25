import React from 'react'
import { FileQuestion } from 'lucide-react'
import { cn } from '@/lib/utils'
import { GlassCard } from './GlassCard'

export interface EmptyStateProps {
  icon?: React.ElementType
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({
  icon: Icon = FileQuestion,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <GlassCard
      variant="subtle"
      className={cn(
        'flex flex-col items-center justify-center p-8 md:p-12 text-center space-y-4 border-dashed border-[#D6CEC2] dark:border-white/[0.1]',
        className,
      )}
    >
      <div className="p-3.5 rounded-2xl bg-[#EFE9E1] border border-[#E0D8CC] text-[#785D48] dark:bg-white/[0.04] dark:border-white/[0.08] dark:text-zinc-300 backdrop-blur-md shadow-inner">
        <Icon className="w-6 h-6" />
      </div>

      <div className="space-y-1.5 max-w-sm">
        <h4 className="text-sm md:text-base font-semibold text-[#1C1917] dark:text-zinc-100 tracking-tight">
          {title}
        </h4>
        {description && (
          <p className="text-xs md:text-sm text-[#78716C] dark:text-zinc-400 leading-relaxed">
            {description}
          </p>
        )}
      </div>

      {action && <div className="pt-2">{action}</div>}
    </GlassCard>
  )
}
