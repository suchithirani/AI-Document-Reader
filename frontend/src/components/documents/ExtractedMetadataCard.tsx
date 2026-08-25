import React from 'react'
import { Sparkles, FileSearch } from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'

export interface ExtractedMetadataCardProps {
  metadata?: Record<string, unknown> | null
  className?: string
}

export function ExtractedMetadataCard({ metadata, className }: ExtractedMetadataCardProps) {
  const hasMetadata = metadata && Object.keys(metadata).length > 0

  const formatKey = (key: string) => {
    return key
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, (str) => str.toUpperCase())
      .trim()
  }

  const renderValue = (val: unknown): React.ReactNode => {
    if (val === null || val === undefined) {
      return <span className="text-zinc-400 italic">None</span>
    }
    if (typeof val === 'boolean') {
      return val ? 'Yes' : 'No'
    }
    if (typeof val === 'number') {
      return val.toLocaleString()
    }
    if (typeof val === 'string') {
      return val
    }
    if (Array.isArray(val)) {
      if (val.length === 0) return <span className="text-zinc-400 italic">Empty array</span>
      return (
        <ul className="list-disc list-inside space-y-1 pl-1">
          {val.map((item, idx) => (
            <li key={idx} className="text-xs">
              {typeof item === 'object' ? JSON.stringify(item) : String(item)}
            </li>
          ))}
        </ul>
      )
    }
    if (typeof val === 'object') {
      return (
        <div className="space-y-1.5 p-2 rounded-lg bg-[rgba(90,70,50,0.05)] dark:bg-white/[0.03] border border-[rgba(90,70,50,0.08)] dark:border-white/[0.04]">
          {Object.entries(val as Record<string, unknown>).map(([nestedKey, nestedVal]) => (
            <div key={nestedKey} className="text-xs flex flex-col sm:flex-row sm:items-baseline gap-1">
              <span className="font-medium text-[#71695F] dark:text-zinc-400">{formatKey(nestedKey)}:</span>
              <span className="text-[#211C17] dark:text-zinc-100 font-semibold">{renderValue(nestedVal)}</span>
            </div>
          ))}
        </div>
      )
    }
    return String(val)
  }

  return (
    <GlassCard variant="default" className={className}>
      <div className="p-5 space-y-4 text-left">
        <div className="flex items-center justify-between pb-3 border-b border-[rgba(90,70,50,0.10)] dark:border-white/[0.08]">
          <h3 className="text-sm font-semibold text-[#211C17] dark:text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#886F4E] dark:text-[#A68A6A]" />
            <span>Extracted Intelligence Metadata</span>
          </h3>
        </div>

        {!hasMetadata ? (
          <div className="py-6 flex flex-col items-center justify-center text-center space-y-2 text-xs text-[#71695F] dark:text-zinc-400">
            <FileSearch className="w-8 h-8 text-[#9A9187] dark:text-zinc-500 opacity-60" />
            <p className="font-medium">No extracted metadata available.</p>
            <p className="text-[11px] text-[#9A9187] dark:text-zinc-500 max-w-xs">
              Extracted entities, summaries, and domain attributes will appear once the OCR pipeline processes the document.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3">
            {Object.entries(metadata).map(([key, val]) => (
              <div
                key={key}
                className="p-3 rounded-xl bg-[rgba(255,255,255,0.40)] dark:bg-white/[0.02] border border-[rgba(90,70,50,0.08)] dark:border-white/[0.04] space-y-1"
              >
                <span className="text-[11px] font-medium text-[#71695F] dark:text-zinc-400">
                  {formatKey(key)}
                </span>
                <div className="text-xs font-semibold text-[#211C17] dark:text-zinc-100 break-words">
                  {renderValue(val)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </GlassCard>
  )
}
