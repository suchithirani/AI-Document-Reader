import apiClient from './client'
import type { ApiResponse, PaginatedApiResponse } from '@/types/api'
import type {
  Document,
  DocumentPaginationParams,
  DocumentProcessRequest,
  DocumentProcessResponse,
  DocumentUploadResponse,
} from '@/types/document'
import { normalizeEntity } from '@/lib/utils'
import { validateDocumentFiles } from '@/lib/fileValidation'

/**
 * Upload one or more document files.
 * Validates files on client-side before dispatching multipart/form-data.
 * Endpoint: POST /documents/upload
 */
export async function uploadDocuments(files: File[]): Promise<DocumentUploadResponse> {
  const validation = validateDocumentFiles(files)
  if (!validation.isValid) {
    const errorMessages = validation.errors.map((e) => e.error).join(' ')
    throw new Error(errorMessages || 'File validation failed.')
  }

  const formData = new FormData()
  for (const file of validation.validFiles) {
    formData.append('files', file)
  }

  // Axios will automatically set the appropriate Content-Type with multipart boundary
  const response = await apiClient.post<ApiResponse<{ documents: Record<string, unknown>[]; count: number; duplicate_documents?: string[] }>>(
    '/documents/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    },
  )

  const rawData = response.data.data
  return {
    ...rawData,
    documents: (rawData.documents || []).map(
      (doc) => normalizeEntity(doc) as unknown as Document,
    ),
  }
}

/**
 * Fetch paginated document list for the authenticated user.
 * Endpoint: GET /documents?skip={skip}&limit={limit}
 */
export async function getDocuments(
  params: DocumentPaginationParams = {},
): Promise<PaginatedApiResponse<Document>> {
  const { skip = 0, limit = 20 } = params

  const response = await apiClient.get<PaginatedApiResponse<Record<string, unknown>>>('/documents', {
    params: { skip, limit },
  })

  return {
    ...response.data,
    data: (response.data.data || []).map(
      (doc) => normalizeEntity(doc) as unknown as Document,
    ),
  }
}

/**
 * Fetch a single document by ID.
 * Endpoint: GET /documents/{id}
 */
export async function getDocument(documentId: string): Promise<Document> {
  if (!documentId) {
    throw new Error('documentId is required.')
  }

  const response = await apiClient.get<ApiResponse<Record<string, unknown>>>(`/documents/${documentId}`)
  return normalizeEntity(response.data.data) as unknown as Document
}

/**
 * Download a document file binary.
 * Endpoint: GET /documents/{id}/download
 */
export async function downloadDocument(documentId: string): Promise<Blob> {
  if (!documentId) {
    throw new Error('documentId is required.')
  }

  const response = await apiClient.get<Blob>(`/documents/${documentId}/download`, {
    responseType: 'blob',
  })
  return response.data
}

/**
 * Delete a document by ID.
 * Endpoint: DELETE /documents/{id}
 */
export async function deleteDocument(documentId: string): Promise<ApiResponse<{ message: string }>> {
  if (!documentId) {
    throw new Error('documentId is required.')
  }

  const response = await apiClient.delete<ApiResponse<{ message: string }>>(`/documents/${documentId}`)
  return response.data
}

/**
 * Trigger background OCR/chunking/embedding pipeline for document IDs.
 * Endpoint: POST /documents/process
 */
export async function processDocuments(
  documentIds: string[],
): Promise<DocumentProcessResponse> {
  if (!documentIds || documentIds.length === 0) {
    throw new Error('document_ids are required.')
  }

  const payload: DocumentProcessRequest = { document_ids: documentIds }
  const response = await apiClient.post<ApiResponse<DocumentProcessResponse>>('/documents/process', payload)
  return response.data.data
}

/**
 * Fetch historical versions for a document.
 * Endpoint: GET /documents/{id}/versions
 */
export async function getDocumentVersions(documentId: string): Promise<Document[]> {
  if (!documentId) {
    throw new Error('documentId is required.')
  }

  const response = await apiClient.get<ApiResponse<Record<string, unknown>[]>>(`/documents/${documentId}/versions`)
  return (response.data.data || []).map(
    (doc) => normalizeEntity(doc) as unknown as Document,
  )
}
