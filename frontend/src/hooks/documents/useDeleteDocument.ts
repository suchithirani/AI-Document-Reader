import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deleteDocument } from '@/api/documents'
import { DOCUMENT_QUERY_KEYS } from './useDocuments'
import type { ApiResponse } from '@/types/api'

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation<ApiResponse<{ message: string }>, Error, string>({
    mutationFn: (documentId: string) => deleteDocument(documentId),
    onSuccess: (_, documentId) => {
      queryClient.invalidateQueries({ queryKey: DOCUMENT_QUERY_KEYS.all })
      queryClient.removeQueries({ queryKey: DOCUMENT_QUERY_KEYS.detail(documentId) })
    },
  })
}
