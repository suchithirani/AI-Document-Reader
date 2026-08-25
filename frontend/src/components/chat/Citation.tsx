import React from 'react'
import { FileText } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface CitationProps {
  documentName: string
  pageNumber?: number
  score?: number
  onClick?: () => void
  className?: string
}

export function Citation({
  documentName,
  pageNumber,
  score,
  onClick,
  className,
}: CitationProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all select-none',
        'bg-[#EFE9E1]/80 hover:bg-[#E9E1D7] text-[#211C17] border border-[rgba(90,70,50,0.14)]',
        'dark:bg-white/[0.06] dark:hover:bg-white/[0.1] dark:text-[#F5F5F5] dark:border-white/[0.1]',
        'cursor-pointer active:scale-95',
        className,
      )}
    >
      <FileText className="w-3 h-3 text-[#886F4E] dark:text-[#A68A6A] shrink-0" />
      <span className="truncate max-w-[120px]">{documentName}</span>
      {pageNumber !== undefined && (
        <span className="text-[10px] text-[#71695F] dark:text-zinc-400 font-mono">
          p.{pageNumber}
        </span>
      )}
      {score !== undefined && (
        <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-mono">
          {Math.round(score * 100)}%
        </span>
      )}
    </button>
  )
}
