import { useQuery } from '@tanstack/react-query'
import { getDocumentVersions } from '@/api/documents'
import { DOCUMENT_QUERY_KEYS } from './useDocuments'

export function useDocumentVersions(documentId: string | undefined | null) {
  return useQuery({
    queryKey: DOCUMENT_QUERY_KEYS.versions(documentId || ''),
    queryFn: () => getDocumentVersions(documentId as string),
    enabled: Boolean(documentId),
    staleTime: 1000 * 60, // 1 minute
  })
}
