import React from 'react'
import {
  AlertTriangle,
  Calendar,
  FileCode,
  Files,
  HardDrive,
  Hash,
  Info,
  Layers,
  Tag,
} from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { formatFileSize, formatDate } from '@/lib/utils'
import type { Document } from '@/types/document'

export interface DocumentMetadataCardProps {
  document: Document
  className?: string
}

export function DocumentMetadataCard({ document, className }: DocumentMetadataCardProps) {
  const metadataRows = [
    {
      label: 'Original Filename',
      value: document.original_filename,
      icon: <FileCode className="w-3.5 h-3.5 text-[#886F4E] dark:text-[#A68A6A]" />,
    },
    {
      label: 'File Size',
      value: formatFileSize(document.file_size),
      icon: <HardDrive className="w-3.5 h-3.5 text-[#886F4E] dark:text-[#A68A6A]" />,
    },
    {
      label: 'MIME Type',
      value: document.mime_type || `${document.extension?.toUpperCase()} document`,
      icon: <Info className="w-3.5 h-3.5 text-[#886F4E] dark:text-[#A68A6A]" />,
    },
    {
      label: 'Page Count',
      value:
        document.page_count !== null && document.page_count !== undefined
          ? `${document.page_count} ${document.page_count === 1 ? 'page' : 'pages'}`
          : '1 page',
      icon: <Files className="w-3.5 h-3.5 text-[#886F4E] dark:text-[#A68A6A]" />,
    },
    {
      label: 'Uploaded On',
      value: formatDate(document.created_at),
      icon: <Calendar className="w-3.5 h-3.5 text-[#886F4E] dark:text-[#A68A6A]" />,
    },
    {
      label: 'Version Group ID',
      value: document.version_group_id || 'Not available',
      icon: <Layers className="w-3.5 h-3.5 text-[#886F4E] dark:text-[#A68A6A]" />,
      mono: true,
    },
    {
      label: 'File Hash (SHA-256)',
      value: document.file_hash || 'Not computed',
      icon: <Hash className="w-3.5 h-3.5 text-[#886F4E] dark:text-[#A68A6A]" />,
      mono: true,
    },
  ]

  return (
    <GlassCard variant="default" className={className}>
      <div className="p-5 space-y-4 text-left">
        <div className="flex items-center justify-between pb-3 border-b border-[rgba(90,70,50,0.10)] dark:border-white/[0.08]">
          <h3 className="text-sm font-semibold text-[#211C17] dark:text-white flex items-center gap-2">
            <Info className="w-4 h-4 text-[#886F4E] dark:text-[#A68A6A]" />
            <span>Document Information</span>
          </h3>
          <span className="text-[11px] font-mono text-[#9A9187] dark:text-zinc-500">
            v{document.version || 1}
          </span>
        </div>

        {/* OCR Quality Notice */}
        {document.ocr_quality_warning && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 text-xs flex items-start gap-2.5">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
            <div className="space-y-0.5">
              <p className="font-semibold">Low OCR Quality Warning</p>
              <p className="text-[11px] leading-relaxed text-amber-700 dark:text-amber-300/90">
                Low OCR quality detected. Some extracted text or symbols may be inaccurate.
              </p>
            </div>
          </div>
        )}

        {/* Key/Value Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          {metadataRows.map((row) => (
            <div
              key={row.label}
              className="p-3 rounded-xl bg-[rgba(255,255,255,0.40)] dark:bg-white/[0.02] border border-[rgba(90,70,50,0.08)] dark:border-white/[0.04] space-y-1"
            >
              <div className="flex items-center gap-1.5 text-[11px] font-medium text-[#71695F] dark:text-zinc-400">
                {row.icon}
                <span>{row.label}</span>
              </div>
              <p
                className={`text-xs font-semibold text-[#211C17] dark:text-zinc-100 break-words ${
                  row.mono ? 'font-mono text-[11px]' : ''
                }`}
              >
                {row.value}
              </p>
            </div>
          ))}
        </div>

        {/* Tags Section (if present) */}
        {document.tags && document.tags.length > 0 && (
          <div className="pt-2 border-t border-[rgba(90,70,50,0.08)] dark:border-white/[0.06] space-y-2">
            <span className="text-xs font-semibold text-[#71695F] dark:text-zinc-400 flex items-center gap-1.5">
              <Tag className="w-3.5 h-3.5 text-[#886F4E] dark:text-[#A68A6A]" />
              <span>Tags</span>
            </span>
            <div className="flex flex-wrap gap-1.5">
              {document.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2.5 py-1 text-xs font-medium rounded-lg bg-[#EFE9E1] text-[#705634] dark:bg-white/[0.06] dark:text-zinc-300 border border-[rgba(90,70,50,0.12)] dark:border-white/[0.08]"
                >
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </GlassCard>
  )
}
