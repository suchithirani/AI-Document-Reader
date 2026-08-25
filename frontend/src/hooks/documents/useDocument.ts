import { useQuery } from '@tanstack/react-query'
import { getDocument } from '@/api/documents'
import { DOCUMENT_QUERY_KEYS } from './useDocuments'
import type { Document, DocumentStatus } from '@/types/document'

const PROCESSING_STATUSES: DocumentStatus[] = [
  'UPLOADED',
  'QUEUED',
  'OCR_PROCESSING',
  'CHUNKING',
  'EMBEDDING',
]

export interface UseDocumentOptions {
  pollWhileProcessing?: boolean
  pollIntervalMs?: number
}

export function useDocument(
  documentId: string | undefined | null,
  options: UseDocumentOptions = {},
) {
  const { pollWhileProcessing = false, pollIntervalMs = 2000 } = options

  return useQuery({
    queryKey: DOCUMENT_QUERY_KEYS.detail(documentId || ''),
    queryFn: () => getDocument(documentId as string),
    enabled: Boolean(documentId),
    staleTime: 1000 * 15,
    refetchInterval: (query) => {
      if (!pollWhileProcessing) return false
      const doc = query.state.data as Document | undefined
      if (doc && PROCESSING_STATUSES.includes(doc.status)) {
        return pollIntervalMs
      }
      return false
    },
  })
}
