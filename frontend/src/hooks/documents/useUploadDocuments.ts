import { useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadDocuments } from '@/api/documents'
import { DOCUMENT_QUERY_KEYS } from './useDocuments'
import type { DocumentUploadResponse } from '@/types/document'

export function useUploadDocuments() {
  const queryClient = useQueryClient()

  return useMutation<DocumentUploadResponse, Error, File[]>({
    mutationFn: (files: File[]) => uploadDocuments(files),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: DOCUMENT_QUERY_KEYS.all })
    },
  })
}
