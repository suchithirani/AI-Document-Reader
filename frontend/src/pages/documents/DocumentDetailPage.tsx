import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Skeleton } from '@/components/ui/Skeleton'
import { ErrorState } from '@/components/ui/ErrorState'
import { Button } from '@/components/ui/Button'
import {
  DocumentDetailHeader,
  DocumentMetadataCard,
  ExtractedMetadataCard,
  DocumentProgress,
  DocumentVersionsDrawer,
} from '@/components/documents'
import { useDocument, useDocumentVersions } from '@/hooks/documents'

export function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [isVersionsOpen, setIsVersionsOpen] = useState(false)

  const {
    data: document,
    isLoading,
    isError,
    error,
    refetch,
  } = useDocument(id, { pollWhileProcessing: true })

  const { data: versions } = useDocumentVersions(id)

  if (isLoading) {
    return (
      <div className="space-y-6 text-left">
        <Skeleton className="h-6 w-32 rounded-lg" />
        <Skeleton className="h-28 w-full rounded-2xl" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80 w-full rounded-2xl" />
          <Skeleton className="h-80 w-full rounded-2xl" />
        </div>
      </div>
    )
  }

  if (isError || !document) {
    return (
      <div className="space-y-6 text-left">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => navigate('/documents')}
          leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}
        >
          Back to Documents
        </Button>

        <ErrorState
          title="Document Not Found"
          message={
            (error as Error)?.message ||
            'The requested document could not be found or you do not have permission to view it.'
          }
          onRetry={() => refetch()}
        />
      </div>
    )
  }

  const isProcessing =
    document.status !== 'READY' && document.status !== 'FAILED' && document.status !== 'UPLOADED'

  return (
    <div className="space-y-6 text-left">
      {/* Header */}
      <DocumentDetailHeader
        document={document}
        onOpenVersions={() => setIsVersionsOpen(true)}
        versionCount={versions?.length}
      />

      {/* Live Processing Pipeline Bar (if active) */}
      {isProcessing && (
        <div className="p-4 rounded-2xl bg-[rgba(255,255,255,0.60)] dark:bg-white/[0.04] border border-[rgba(90,70,50,0.14)] dark:border-white/[0.08] backdrop-blur-md space-y-2">
          <h4 className="text-xs font-semibold text-[#211C17] dark:text-white">
            Processing in progress
          </h4>
          <DocumentProgress status={document.status} progress={document.progress} />
        </div>
      )}

      {/* Main 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Standard Metadata */}
        <DocumentMetadataCard document={document} />

        {/* Right Column: Extracted Intelligence Metadata */}
        <ExtractedMetadataCard metadata={document.extracted_metadata} />
      </div>

      {/* Versions Drawer Modal */}
      <DocumentVersionsDrawer
        documentId={document.id}
        isOpen={isVersionsOpen}
        onClose={() => setIsVersionsOpen(false)}
      />
    </div>
  )
}
