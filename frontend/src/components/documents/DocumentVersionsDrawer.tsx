import React from 'react'
import {
  Download,
  FileText,
  History,
  Image as ImageIcon,
  Loader2,
} from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/Dialog'
import { StatusBadge } from '@/components/ui/StatusBadge'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { useDocumentVersions } from '@/hooks/documents'
import { downloadDocument } from '@/api/documents'
import { useToast } from '@/components/ui/useToast'
import { formatFileSize, formatDate, cn } from '@/lib/utils'

export interface DocumentVersionsDrawerProps {
  documentId: string
  isOpen: boolean
  onClose: () => void
}

export function DocumentVersionsDrawer({
  documentId,
  isOpen,
  onClose,
}: DocumentVersionsDrawerProps) {
  const { data: versions, isLoading, isError } = useDocumentVersions(
    isOpen ? documentId : null,
  )
  const { toast } = useToast()
  const [downloadingId, setDownloadingId] = React.useState<string | null>(null)

  const handleDownload = async (id: string, filename: string) => {
    if (downloadingId) return
    setDownloadingId(id)

    try {
      const blob = await downloadDocument(id)
      const url = window.URL.createObjectURL(blob)
      const link = window.document.createElement('a')
      link.href = url
      link.download = filename || `version-${id}`
      window.document.body.appendChild(link)
      link.click()
      window.document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      toast({
        title: 'Download started',
        description: `Downloading version "${filename}"...`,
        variant: 'success',
      })
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ||
        (err as Error).message ||
        'Failed to download version.'
      toast({
        title: 'Download failed',
        description: msg,
        variant: 'error',
      })
    } finally {
      setDownloadingId(null)
    }
  }

  const getFileIcon = (ext?: string) => {
    if (ext?.toLowerCase() === 'pdf') {
      return <FileText className="w-4 h-4 text-rose-500 shrink-0" />
    }
    return <ImageIcon className="w-4 h-4 text-blue-500 shrink-0" />
  }

  return (
    <Dialog isOpen={isOpen} onClose={onClose}>
      <DialogHeader onClose={onClose}>
        <DialogTitle className="flex items-center gap-2">
          <History className="w-4 h-4 text-[#886F4E] dark:text-[#A68A6A]" />
          <span>Document Version History</span>
        </DialogTitle>
        <DialogDescription>
          View and download previous revisions and indexed checkpoints.
        </DialogDescription>
      </DialogHeader>

      <DialogContent className="max-h-[60vh] overflow-y-auto space-y-3 p-1">
        {isLoading ? (
          <div className="space-y-2.5 p-4">
            <Skeleton className="h-16 w-full rounded-xl" />
            <Skeleton className="h-16 w-full rounded-xl" />
            <Skeleton className="h-16 w-full rounded-xl" />
          </div>
        ) : isError || !versions || versions.length === 0 ? (
          <div className="py-8 text-center space-y-2 text-xs text-[#71695F] dark:text-zinc-400">
            <History className="w-8 h-8 mx-auto text-[#9A9187] dark:text-zinc-500 opacity-50" />
            <p className="font-medium">No previous versions available.</p>
            <p className="text-[11px] text-[#9A9187] dark:text-zinc-500">
              When you upload a file with the same name, new revisions will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-2.5 p-2">
            {versions.map((ver) => {
              const isCurrent = ver.is_latest
              return (
                <div
                  key={ver.id}
                  className={cn(
                    'p-3.5 rounded-xl border flex items-center justify-between gap-3 text-xs transition-all',
                    isCurrent
                      ? 'bg-[#886F4E]/8 border-[#886F4E]/30 dark:bg-white/[0.06] dark:border-white/20'
                      : 'bg-[#FFFCF8] dark:bg-white/[0.02] border-[rgba(90,70,50,0.10)] dark:border-white/[0.06]',
                  )}
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-[rgba(90,70,50,0.08)] dark:bg-white/[0.06] flex items-center justify-center shrink-0 mt-0.5">
                      {getFileIcon(ver.extension)}
                    </div>

                    <div className="min-w-0 space-y-1 text-left">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-[#211C17] dark:text-white">
                          Version {ver.version || 1}
                        </span>
                        {isCurrent && (
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
                            Current
                          </span>
                        )}
                      </div>

                      <p className="text-[11px] text-[#71695F] dark:text-zinc-400">
                        {formatFileSize(ver.file_size)} • {formatDate(ver.created_at)}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <StatusBadge status={ver.status} />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      isLoading={downloadingId === ver.id}
                      disabled={downloadingId === ver.id}
                      onClick={() => handleDownload(ver.id, ver.original_filename)}
                      aria-label={`Download version ${ver.version}`}
                    >
                      {downloadingId === ver.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Download className="w-3.5 h-3.5" />
                      )}
                    </Button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
