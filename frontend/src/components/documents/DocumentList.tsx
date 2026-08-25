import React, { useState } from 'react'
import {
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  FileUp,
  Play,
  Square,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/EmptyState'
import { DocumentRow } from './DocumentRow'
import { useProcessDocuments } from '@/hooks/documents'
import { useToast } from '@/components/ui/useToast'
import type { Document } from '@/types/document'
import type { PaginationMeta } from '@/types/api'

export interface DocumentListProps {
  documents: Document[]
  pagination?: PaginationMeta
  onPageChange?: (newPage: number) => void
  onDeleteClick: (document: Document) => void
  onUploadClick?: () => void
}

export function DocumentList({
  documents,
  pagination,
  onPageChange,
  onDeleteClick,
  onUploadClick,
}: DocumentListProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const { mutateAsync: processBatch, isPending: isBatchProcessing } = useProcessDocuments()
  const { toast } = useToast()

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id],
    )
  }

  const allSelected =
    documents.length > 0 && documents.every((d) => selectedIds.includes(d.id))

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedIds([])
    } else {
      setSelectedIds(documents.map((d) => d.id))
    }
  }

  const processableSelectedIds = selectedIds.filter((id) => {
    const doc = documents.find((d) => d.id === id)
    return doc && (doc.status === 'UPLOADED' || doc.status === 'FAILED')
  })

  const handleBulkProcess = async () => {
    if (processableSelectedIds.length === 0 || isBatchProcessing) return

    try {
      const res = await processBatch(processableSelectedIds)
      toast({
        title: 'Batch processing queued',
        description: `Queued ${res.count} document(s) for OCR and embedding indexing.`,
        variant: 'success',
      })
      setSelectedIds([])
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ||
        (err as Error).message ||
        'Failed to process selected documents.'
      toast({
        title: 'Processing failed',
        description: msg,
        variant: 'error',
      })
    }
  }

  if (documents.length === 0) {
    return (
      <EmptyState
        icon={FileUp}
        title="No documents yet"
        description="Upload PDF documents or images to extract text with OCR and create vector embeddings."
        action={
          onUploadClick ? (
            <Button
              variant="primary"
              size="sm"
              onClick={onUploadClick}
              leftIcon={<FileUp className="w-3.5 h-3.5" />}
            >
              Upload Document
            </Button>
          ) : undefined
        }
      />
    )
  }

  return (
    <div className="space-y-4">
      {/* Batch Actions Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-2xl bg-[rgba(255,255,255,0.40)] dark:bg-white/[0.03] border border-[rgba(90,70,50,0.12)] dark:border-white/[0.06] backdrop-blur-md">
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={toggleSelectAll}
            className="flex items-center gap-1.5 text-xs font-medium text-[#71695F] hover:text-[#211C17] dark:text-zinc-400 dark:hover:text-white transition-colors cursor-pointer select-none"
          >
            {allSelected ? (
              <CheckSquare className="w-4 h-4 text-[#886F4E] dark:text-[#A68A6A]" />
            ) : (
              <Square className="w-4 h-4" />
            )}
            <span>{allSelected ? 'Deselect All' : 'Select All'}</span>
          </button>

          {selectedIds.length > 0 && (
            <span className="text-xs text-[#886F4E] dark:text-[#A68A6A] font-semibold">
              ({selectedIds.length} selected)
            </span>
          )}
        </div>

        {selectedIds.length > 0 && (
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="primary"
              size="sm"
              disabled={processableSelectedIds.length === 0 || isBatchProcessing}
              isLoading={isBatchProcessing}
              onClick={handleBulkProcess}
              leftIcon={<Play className="w-3.5 h-3.5" />}
            >
              Process Selected ({processableSelectedIds.length})
            </Button>
          </div>
        )}
      </div>

      {/* Document Items List */}
      <div className="space-y-3">
        {documents.map((doc) => (
          <DocumentRow
            key={doc.id}
            document={doc}
            isSelected={selectedIds.includes(doc.id)}
            onToggleSelect={toggleSelect}
            onDeleteClick={onDeleteClick}
          />
        ))}
      </div>

      {/* Pagination Controls */}
      {pagination && pagination.pages > 1 && onPageChange && (
        <div className="flex items-center justify-between pt-4 border-t border-[rgba(90,70,50,0.10)] dark:border-white/[0.06] text-xs text-[#71695F] dark:text-zinc-400">
          <div>
            Showing page <span className="font-semibold">{pagination.page}</span> of{' '}
            <span className="font-semibold">{pagination.pages}</span> ({pagination.total} total)
          </div>

          <div className="flex items-center gap-1.5">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={pagination.page <= 1}
              onClick={() => onPageChange(pagination.page - 1)}
              leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
            >
              Previous
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              disabled={pagination.page >= pagination.pages}
              onClick={() => onPageChange(pagination.page + 1)}
              rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
