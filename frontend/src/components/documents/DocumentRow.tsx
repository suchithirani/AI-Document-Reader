import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  Download,
  FileText,
  Image as ImageIcon,
  Loader2,
  Play,
  RotateCcw,
  Trash2,
} from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { Button } from '@/components/ui/Button'
import { formatFileSize, formatDate, cn } from '@/lib/utils'
import { DocumentProgress } from './DocumentProgress'
import { downloadDocument } from '@/api/documents'
import { useProcessDocuments } from '@/hooks/documents'
import { useToast } from '@/components/ui/useToast'
import type { Document } from '@/types/document'

export interface DocumentRowProps {
  document: Document
  isSelected: boolean
  onToggleSelect: (id: string) => void
  onDeleteClick: (document: Document) => void
  className?: string
}

export function DocumentRow({
  document,
  isSelected,
  onToggleSelect,
  onDeleteClick,
  className,
}: DocumentRowProps) {
  const [isDownloading, setIsDownloading] = useState(false)
  const { mutateAsync: processDocs, isPending: isProcessing } = useProcessDocuments()
  const { toast } = useToast()

  const handleDownload = async () => {
    if (isDownloading) return
    setIsDownloading(true)

    try {
      const blob = await downloadDocument(document.id)
      const url = window.URL.createObjectURL(blob)
      const link = window.document.createElement('a')
      link.href = url
      link.download = document.original_filename || `document-${document.id}`
      window.document.body.appendChild(link)
      link.click()
      window.document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      toast({
        title: 'Download started',
        description: `Downloading "${document.original_filename}"...`,
        variant: 'success',
      })
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ||
        (err as Error).message ||
        'Failed to download document.'
      toast({
        title: 'Download failed',
        description: msg,
        variant: 'error',
      })
    } finally {
      setIsDownloading(false)
    }
  }

  const handleProcess = async () => {
    if (isProcessing) return

    try {
      await processDocs([document.id])
      toast({
        title: 'Processing started',
        description: `Queued "${document.original_filename}" for OCR and embedding indexing.`,
        variant: 'success',
      })
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ||
        (err as Error).message ||
        'Failed to start document processing.'
      toast({
        title: 'Processing failed',
        description: msg,
        variant: 'error',
      })
    }
  }

  const getFileIcon = () => {
    const ext = document.extension?.toLowerCase() || document.filename?.split('.').pop()?.toLowerCase()
    if (ext === 'pdf') {
      return <FileText className="w-5 h-5 text-rose-500 shrink-0" />
    }
    return <ImageIcon className="w-5 h-5 text-blue-500 shrink-0" />
  }

  const canProcess = document.status === 'UPLOADED' || document.status === 'FAILED'

  return (
    <GlassCard
      variant="default"
      className={cn(
        'p-4 sm:p-5 transition-all duration-150',
        isSelected && 'border-[#886F4E] dark:border-white/30 bg-[#886F4E]/5 dark:bg-white/[0.06]',
        className,
      )}
    >
      <div className="space-y-3.5">
        {/* Top bar */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 min-w-0">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onToggleSelect(document.id)}
              aria-label={`Select ${document.original_filename}`}
              className="mt-1 w-4 h-4 rounded border-[rgba(90,70,50,0.22)] dark:border-white/20 text-[#886F4E] focus:ring-[#886F4E] cursor-pointer"
            />

            <div className="w-9 h-9 rounded-xl bg-[#EFE9E1] dark:bg-white/[0.06] flex items-center justify-center shrink-0">
              {getFileIcon()}
            </div>

            <div className="min-w-0 space-y-0.5 text-left">
              <Link
                to={`/documents/${document.id}`}
                className="text-sm font-semibold text-[#211C17] hover:text-[#886F4E] dark:text-white dark:hover:text-[#A68A6A] hover:underline transition-colors truncate max-w-xs sm:max-w-md md:max-w-lg block"
              >
                {document.original_filename}
              </Link>
              <p className="text-xs text-[#71695F] dark:text-zinc-400">
                {document.extension?.toUpperCase() || 'FILE'} • {formatFileSize(document.file_size)}
                {document.page_count !== null && document.page_count !== undefined && (
                  <> • {document.page_count} {document.page_count === 1 ? 'page' : 'pages'}</>
                )}
                {' • '}
                <span className="font-mono text-[11px] text-[#9A9187] dark:text-zinc-500">
                  {formatDate(document.created_at)}
                </span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <StatusBadge status={document.status} />
          </div>
        </div>

        {/* OCR Quality Warning Alert */}
        {document.ocr_quality_warning && (
          <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 dark:text-amber-400" />
            <span>Low OCR quality — some text may have been extracted inaccurately.</span>
          </div>
        )}

        {/* Progress Pipeline */}
        <DocumentProgress status={document.status} progress={document.progress} />

        {/* Bottom Actions */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[rgba(90,70,50,0.08)] dark:border-white/[0.06]">
          <div className="text-[11px] text-[#9A9187] dark:text-zinc-500">
            ID: <span className="font-mono">{document.id.slice(0, 8)}...</span>
          </div>

          <div className="flex items-center gap-1.5 sm:gap-2">
            {canProcess && (
              <Button
                type="button"
                variant={document.status === 'FAILED' ? 'destructive' : 'primary'}
                size="sm"
                isLoading={isProcessing}
                disabled={isProcessing}
                onClick={handleProcess}
                leftIcon={
                  document.status === 'FAILED' ? (
                    <RotateCcw className="w-3.5 h-3.5" />
                  ) : (
                    <Play className="w-3.5 h-3.5" />
                  )
                }
              >
                {document.status === 'FAILED' ? 'Retry Process' : 'Process'}
              </Button>
            )}

            <Button
              type="button"
              variant="secondary"
              size="sm"
              isLoading={isDownloading}
              disabled={isDownloading}
              onClick={handleDownload}
              leftIcon={
                isDownloading ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Download className="w-3.5 h-3.5" />
                )
              }
            >
              Download
            </Button>

            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="text-rose-600 hover:text-rose-700 dark:text-rose-400 dark:hover:text-rose-300"
              onClick={() => onDeleteClick(document)}
              leftIcon={<Trash2 className="w-3.5 h-3.5" />}
            >
              Delete
            </Button>
          </div>
        </div>
      </div>
    </GlassCard>
  )
}
