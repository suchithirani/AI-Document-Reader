import { useMutation, useQueryClient } from '@tanstack/react-query'
import { processDocuments } from '@/api/documents'
import { DOCUMENT_QUERY_KEYS } from './useDocuments'
import type { DocumentProcessResponse } from '@/types/document'

export function useProcessDocuments() {
  const queryClient = useQueryClient()

  return useMutation<DocumentProcessResponse, Error, string[]>({
    mutationFn: (documentIds: string[]) => processDocuments(documentIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENT_QUERY_KEYS.all })
    },
  })
}
