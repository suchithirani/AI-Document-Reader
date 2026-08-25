import React from 'react'
import type { DocumentStatus } from '@/types/document'
import { cn } from '@/lib/utils'

export interface DocumentProgressProps {
  status: DocumentStatus
  progress?: number
  className?: string
}

const STATUS_CONFIGS: Record<
  DocumentStatus,
  { label: string; defaultProgress: number; colorClass: string }
> = {
  UPLOADED: {
    label: 'Uploaded • Ready to Process',
    defaultProgress: 0,
    colorClass: 'bg-zinc-400 dark:bg-zinc-500',
  },
  QUEUED: {
    label: 'Queued for processing...',
    defaultProgress: 5,
    colorClass: 'bg-[#886F4E] dark:bg-[#A68A6A]',
  },
  OCR_PROCESSING: {
    label: 'Reading & extracting text (OCR)...',
    defaultProgress: 10,
    colorClass: 'bg-[#886F4E] dark:bg-[#A68A6A]',
  },
  CHUNKING: {
    label: 'Segmenting & organizing content...',
    defaultProgress: 40,
    colorClass: 'bg-[#886F4E] dark:bg-[#A68A6A]',
  },
  EMBEDDING: {
    label: 'Generating vector embeddings...',
    defaultProgress: 75,
    colorClass: 'bg-[#886F4E] dark:bg-[#A68A6A]',
  },
  READY: {
    label: 'Indexed & Ready for Intelligence Querying',
    defaultProgress: 100,
    colorClass: 'bg-emerald-500',
  },
  FAILED: {
    label: 'Processing failed',
    defaultProgress: 100,
    colorClass: 'bg-rose-500',
  },
}

export function DocumentProgress({
  status,
  progress,
  className,
}: DocumentProgressProps) {
  const config = STATUS_CONFIGS[status] || STATUS_CONFIGS.UPLOADED
  const percent = progress !== undefined && progress > 0 ? progress : config.defaultProgress

  if (status === 'READY' || status === 'UPLOADED') {
    return null
  }

  return (
    <div className={cn('space-y-1.5 w-full', className)}>
      <div className="flex items-center justify-between text-[11px]">
        <span className="font-medium text-[#71695F] dark:text-zinc-400">
          {config.label}
        </span>
        <span className="font-mono text-[#886F4E] dark:text-[#A68A6A] font-semibold">
          {percent}%
        </span>
      </div>
      <div className="h-1.5 w-full bg-[rgba(90,70,50,0.12)] dark:bg-white/[0.08] rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-300',
            config.colorClass,
            status !== 'FAILED' && 'animate-pulse',
          )}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  )
}
