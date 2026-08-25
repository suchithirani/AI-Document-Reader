import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Download,
  FileText,
  History,
  Image as ImageIcon,
  Loader2,
  MessageSquare,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { downloadDocument } from '@/api/documents'
import { useToast } from '@/components/ui/useToast'
import type { Document } from '@/types/document'

export interface DocumentDetailHeaderProps {
  document: Document
  onOpenVersions: () => void
  versionCount?: number
}

export function DocumentDetailHeader({
  document,
  onOpenVersions,
  versionCount,
}: DocumentDetailHeaderProps) {
  const [isDownloading, setIsDownloading] = useState(false)
  const navigate = useNavigate()
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

  const handleChatClick = () => {
    if (document.status !== 'READY') return
    navigate('/chat', { state: { documentId: document.id, documentTitle: document.original_filename } })
  }

  const getFileIcon = () => {
    const ext = document.extension?.toLowerCase() || document.filename?.split('.').pop()?.toLowerCase()
    if (ext === 'pdf') {
      return <FileText className="w-6 h-6 text-rose-500 shrink-0" />
    }
    return <ImageIcon className="w-6 h-6 text-blue-500 shrink-0" />
  }

  const isReady = document.status === 'READY'

  return (
    <div className="space-y-4">
      {/* Back Link */}
      <div>
        <Link
          to="/documents"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-[#71695F] hover:text-[#211C17] dark:text-zinc-400 dark:hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Documents</span>
        </Link>
      </div>

      {/* Main Header Card */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 sm:p-6 rounded-2xl bg-[rgba(255,255,255,0.60)] dark:bg-white/[0.04] border border-[rgba(90,70,50,0.14)] dark:border-white/[0.08] backdrop-blur-md">
        {/* Title & Info */}
        <div className="flex items-start gap-3.5 min-w-0">
          <div className="w-11 h-11 rounded-2xl bg-[#EFE9E1] dark:bg-white/[0.06] flex items-center justify-center shrink-0 mt-0.5">
            {getFileIcon()}
          </div>

          <div className="min-w-0 space-y-1 text-left">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-lg sm:text-xl font-bold tracking-tight text-[#211C17] dark:text-white break-words max-w-full">
                {document.original_filename}
              </h1>
              <span className="px-2 py-0.5 text-[11px] font-mono font-medium rounded-md bg-[rgba(90,70,50,0.08)] dark:bg-white/[0.08] text-[#71695F] dark:text-zinc-300">
                v{document.version || 1}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs text-[#71695F] dark:text-zinc-400">
              <StatusBadge status={document.status} />
              <span>•</span>
              <span className="font-mono text-[11px] uppercase">
                {document.extension || 'FILE'}
              </span>
              <span>•</span>
              <span className="font-mono text-[11px]">
                ID: {document.id.slice(0, 8)}...
              </span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-[rgba(90,70,50,0.10)] dark:border-white/[0.06]">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={onOpenVersions}
            leftIcon={<History className="w-3.5 h-3.5" />}
          >
            Versions {versionCount !== undefined && versionCount > 0 ? `(${versionCount})` : ''}
          </Button>

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

          <div className="relative group">
            <Button
              type="button"
              variant="primary"
              size="sm"
              disabled={!isReady}
              onClick={handleChatClick}
              leftIcon={<MessageSquare className="w-3.5 h-3.5" />}
            >
              Chat with this document
            </Button>
            {!isReady && (
              <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 hidden group-hover:block px-2.5 py-1 text-[11px] rounded-lg bg-zinc-900 text-zinc-100 dark:bg-zinc-800 border border-zinc-700 whitespace-nowrap shadow-md z-30 pointer-events-none">
                Document must be ready before chatting
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
