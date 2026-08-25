import { useQuery } from '@tanstack/react-query'
import { getDocuments } from '@/api/documents'
import type { DocumentPaginationParams, DocumentStatus } from '@/types/document'

export const DOCUMENT_QUERY_KEYS = {
  all: ['documents'] as const,
  list: (params: DocumentPaginationParams) => ['documents', 'list', params] as const,
  detail: (id: string) => ['documents', 'detail', id] as const,
  versions: (id: string) => ['documents', 'versions', id] as const,
}

const ACTIVE_PROCESSING_STATUSES: DocumentStatus[] = [
  'UPLOADED',
  'QUEUED',
  'OCR_PROCESSING',
  'CHUNKING',
  'EMBEDDING',
]

export function useDocuments(
  params: DocumentPaginationParams = { skip: 0, limit: 20 },
  options: { autoPollProcessing?: boolean; pollIntervalMs?: number } = {},
) {
  const { autoPollProcessing = true, pollIntervalMs = 2000 } = options

  return useQuery({
    queryKey: DOCUMENT_QUERY_KEYS.list(params),
    queryFn: () => getDocuments(params),
    staleTime: 1000 * 15,
    refetchInterval: (query) => {
      if (!autoPollProcessing) return false
      const docs = query.state.data?.data
      if (docs && docs.some((d) => ACTIVE_PROCESSING_STATUSES.includes(d.status))) {
        return pollIntervalMs
      }
      return false
    },
  })
}
