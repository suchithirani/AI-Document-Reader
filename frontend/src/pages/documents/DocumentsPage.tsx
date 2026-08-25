import React, { useState } from 'react'
import { FileUp, RefreshCw, Upload } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import {
  DocumentList,
  UploadDropzone,
  DeleteDocumentModal,
} from '@/components/documents'
import { useDocuments } from '@/hooks/documents'
import type { Document } from '@/types/document'

export function DocumentsPage() {
  const [page, setPage] = useState(1)
  const limit = 20
  const skip = (page - 1) * limit

  const [isUploadOpen, setIsUploadOpen] = useState(true)
  const [docToDelete, setDocToDelete] = useState<Document | null>(null)

  const {
    data: response,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useDocuments({ skip, limit })

  const documents = response?.data || []
  const pagination = response?.pagination

  return (
    <div className="space-y-6 text-left">
      <PageHeader
        title="Documents"
        description="Upload, inspect, OCR process, and manage intelligence documents"
        actions={
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
              leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />}
            >
              Refresh
            </Button>
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={() => setIsUploadOpen((prev) => !prev)}
              leftIcon={isUploadOpen ? <FileUp className="w-3.5 h-3.5" /> : <Upload className="w-3.5 h-3.5" />}
            >
              {isUploadOpen ? 'Hide Upload' : 'Upload Documents'}
            </Button>
          </div>
        }
      />

      {/* Upload Dropzone Section */}
      {isUploadOpen && (
        <div className="animate-in fade-in duration-200">
          <UploadDropzone
            onUploadSuccess={() => {
              refetch()
            }}
          />
        </div>
      )}

      {/* Main Content Area */}
      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-16 w-full rounded-2xl" />
          <Skeleton className="h-28 w-full rounded-2xl" />
          <Skeleton className="h-28 w-full rounded-2xl" />
          <Skeleton className="h-28 w-full rounded-2xl" />
        </div>
      ) : isError ? (
        <ErrorState
          title="Failed to load documents"
          message={
            (error as Error)?.message ||
            'An error occurred while fetching your documents. Please verify your network connection and try again.'
          }
          onRetry={() => refetch()}
        />
      ) : (
        <DocumentList
          documents={documents}
          pagination={pagination}
          onPageChange={(newPage) => setPage(newPage)}
          onDeleteClick={(doc) => setDocToDelete(doc)}
          onUploadClick={() => setIsUploadOpen(true)}
        />
      )}

      {/* Delete Confirmation Modal */}
      <DeleteDocumentModal
        document={docToDelete}
        isOpen={Boolean(docToDelete)}
        onClose={() => setDocToDelete(null)}
        onDeleted={() => {
          setDocToDelete(null)
          refetch()
        }}
      />
    </div>
  )
}
