import React from 'react'
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Cpu,
  Layers,
  Sparkles,
  XCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export type DocumentProcessingStatus =
  | 'UPLOADED'
  | 'QUEUED'
  | 'OCR_PROCESSING'
  | 'CHUNKING'
  | 'EMBEDDING'
  | 'READY'
  | 'FAILED'
  | 'OCR_QUALITY_WARNING'

export interface StatusBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  status: DocumentProcessingStatus
  showIcon?: boolean
}

export function StatusBadge({
  status,
  showIcon = true,
  className,
  ...props
}: StatusBadgeProps) {
  const configs: Record<
    DocumentProcessingStatus,
    {
      label: string
      icon: React.ReactNode
      containerClass: string
      dotClass: string
    }
  > = {
    UPLOADED: {
      label: 'Uploaded',
      icon: <Clock className="w-3 h-3 text-[#71695F] dark:text-[#A1A1AA]" />,
      containerClass:
        'bg-[#EFE9E1]/80 text-[#71695F] border-[rgba(90,70,50,0.12)] dark:bg-white/[0.04] dark:text-zinc-400 dark:border-white/[0.08]',
      dotClass: 'bg-[#9A9187] dark:bg-zinc-500',
    },
    QUEUED: {
      label: 'Queued',
      icon: <Clock className="w-3 h-3 text-[#71695F] dark:text-[#A1A1AA]" />,
      containerClass:
        'bg-[#EFE9E1]/80 text-[#71695F] border-[rgba(90,70,50,0.12)] dark:bg-white/[0.04] dark:text-zinc-400 dark:border-white/[0.08]',
      dotClass: 'bg-[#71695F] dark:bg-zinc-400 animate-pulse',
    },
    OCR_PROCESSING: {
      label: 'Processing',
      icon: <Cpu className="w-3 h-3 text-[#886F4E] dark:text-[#A68A6A] animate-spin" />,
      containerClass:
        'bg-[#F5ECE0] text-[#705634] border-[rgba(136,111,78,0.25)] dark:bg-[#A68A6A]/10 dark:text-[#D4BC9F] dark:border-[#A68A6A]/25',
      dotClass: 'bg-[#886F4E] dark:bg-[#A68A6A] animate-ping',
    },
    CHUNKING: {
      label: 'Chunking',
      icon: <Layers className="w-3 h-3 text-[#886F4E] dark:text-[#A68A6A]" />,
      containerClass:
        'bg-[#F5ECE0] text-[#705634] border-[rgba(136,111,78,0.25)] dark:bg-[#A68A6A]/10 dark:text-[#D4BC9F] dark:border-[#A68A6A]/25',
      dotClass: 'bg-[#886F4E] dark:bg-[#A68A6A] animate-pulse',
    },
    EMBEDDING: {
      label: 'Embedding',
      icon: <Sparkles className="w-3 h-3 text-[#886F4E] dark:text-[#A68A6A]" />,
      containerClass:
        'bg-[#F5ECE0] text-[#705634] border-[rgba(136,111,78,0.25)] dark:bg-[#A68A6A]/10 dark:text-[#D4BC9F] dark:border-[#A68A6A]/25',
      dotClass: 'bg-[#886F4E] dark:bg-[#A68A6A] animate-pulse',
    },
    READY: {
      label: 'Ready',
      icon: <CheckCircle2 className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />,
      containerClass:
        'bg-emerald-500/10 text-emerald-800 border-emerald-500/25 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30',
      dotClass: 'bg-[#22C55E]',
    },
    FAILED: {
      label: 'Failed',
      icon: <XCircle className="w-3 h-3 text-rose-600 dark:text-rose-400" />,
      containerClass:
        'bg-rose-500/10 text-rose-800 border-rose-500/25 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30',
      dotClass: 'bg-[#EF4444]',
    },
    OCR_QUALITY_WARNING: {
      label: 'Warning',
      icon: <AlertTriangle className="w-3 h-3 text-amber-600 dark:text-amber-400" />,
      containerClass:
        'bg-amber-500/10 text-amber-800 border-amber-500/25 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30',
      dotClass: 'bg-[#F59E0B]',
    },
  }

  const config = configs[status] || configs.UPLOADED

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border backdrop-blur-md transition-colors',
        config.containerClass,
        className,
      )}
      {...props}
    >
      <span className={cn('w-2 h-2 rounded-full shrink-0', config.dotClass)} />
      <span>{config.label}</span>
      {showIcon && <span className="shrink-0">{config.icon}</span>}
    </div>
  )
}
