import React from 'react'
import { FileText, MoreVertical, MessageSquare } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { StatusBadge, type DocumentProcessingStatus } from '@/components/ui/StatusBadge'
import { Button } from '@/components/ui/Button'
import { formatFileSize, formatDate } from '@/lib/utils'

export interface DocumentCardProps {
  id: string
  title: string
  fileType: string
  fileSizeBytes: number
  status: DocumentProcessingStatus
  pageCount?: number
  createdAt: string
  onChatClick?: (id: string) => void
  onSelect?: (id: string) => void
  className?: string
}

export function DocumentCard({
  id,
  title,
  fileType,
  fileSizeBytes,
  status,
  pageCount,
  createdAt,
  onChatClick,
  onSelect,
  className,
}: DocumentCardProps) {
  return (
    <GlassCard
      variant="default"
      className={className}
      onClick={() => onSelect?.(id)}
    >
      <div className="p-5 flex flex-col justify-between space-y-4">
        {/* Top header */}
        <div className="flex items-start justify-between gap-3 text-left">
          <div className="flex items-start gap-3 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-[#EFE9E1] text-[#886F4E] dark:bg-white/[0.08] dark:text-[#A68A6A] flex items-center justify-center shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0 space-y-0.5">
              <h4 className="text-sm font-semibold text-[#211C17] dark:text-white truncate">
                {title}
              </h4>
              <p className="text-xs text-[#71695F] dark:text-zinc-400">
                {fileType.toUpperCase()} • {formatFileSize(fileSizeBytes)}
                {pageCount !== undefined && ` • ${pageCount} pages`}
              </p>
            </div>
          </div>

          <button
            type="button"
            aria-label="Document options"
            className="p-1 rounded-lg text-[#71695F] hover:text-[#211C17] hover:bg-[#E9E1D7] dark:text-zinc-400 dark:hover:text-white dark:hover:bg-white/[0.08] transition-colors"
          >
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>

        {/* Status + Metadata */}
        <div className="flex items-center justify-between text-xs pt-1 border-t border-[rgba(90,70,50,0.08)] dark:border-white/[0.06]">
          <StatusBadge status={status} />
          <span className="text-[#9A9187] dark:text-zinc-500 font-mono text-[11px]">
            {formatDate(createdAt)}
          </span>
        </div>

        {/* Action Button */}
        {status === 'READY' && onChatClick && (
          <Button
            variant="secondary"
            size="sm"
            className="w-full justify-center"
            leftIcon={<MessageSquare className="w-3.5 h-3.5" />}
            onClick={(e) => {
              e.stopPropagation()
              onChatClick(id)
            }}
          >
            Chat with this document
          </Button>
        )}
      </div>
    </GlassCard>
  )
}
