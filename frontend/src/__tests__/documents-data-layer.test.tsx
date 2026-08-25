import { describe, expect, it, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import {
  validateDocumentFile,
  validateDocumentFiles,
  MAX_DOCUMENT_FILE_SIZE_BYTES,
} from '@/lib/fileValidation'
import {
  deleteDocument,
  downloadDocument,
  getDocument,
  getDocuments,
  getDocumentVersions,
  processDocuments,
  uploadDocuments,
} from '@/api/documents'
import {
  useDeleteDocument,
  useDocument,
  useDocuments,
  useDocumentVersions,
  useProcessDocuments,
  useUploadDocuments,
} from '@/hooks/documents'
import apiClient from '@/api/client'

vi.mock('@/api/client')

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('Document File Validation', () => {
  it('accepts valid PDF, PNG, and JPG files within 20MB', () => {
    const validPdf = new File(['%PDF-1.4 test content'], 'report.pdf', {
      type: 'application/pdf',
    })
    const validPng = new File(['dummy png data'], 'diagram.png', {
      type: 'image/png',
    })
    const validJpg = new File(['dummy jpg data'], 'photo.jpg', {
      type: 'image/jpeg',
    })

    expect(validateDocumentFile(validPdf).isValid).toBe(true)
    expect(validateDocumentFile(validPng).isValid).toBe(true)
    expect(validateDocumentFile(validJpg).isValid).toBe(true)
  })

  it('rejects unsupported file formats', () => {
    const textFile = new File(['hello'], 'document.txt', {
      type: 'text/plain',
    })
    const exeFile = new File(['binary'], 'installer.exe', {
      type: 'application/x-msdownload',
    })

    const textRes = validateDocumentFile(textFile)
    expect(textRes.isValid).toBe(false)
    expect(textRes.error).toContain('unsupported format')

    const exeRes = validateDocumentFile(exeFile)
    expect(exeRes.isValid).toBe(false)
  })

  it('rejects files larger than 20MB', () => {
    const largeFile = new File(['dummy'], 'giant.pdf', {
      type: 'application/pdf',
    })
    Object.defineProperty(largeFile, 'size', {
      value: MAX_DOCUMENT_FILE_SIZE_BYTES + 1024,
    })

    const res = validateDocumentFile(largeFile)
    expect(res.isValid).toBe(false)
    expect(res.error).toContain('exceeds the maximum upload size')
  })

  it('validates batches of files correctly', () => {
    const valid = new File(['content'], 'valid.pdf', { type: 'application/pdf' })
    const invalid = new File(['content'], 'invalid.zip', { type: 'application/zip' })

    const result = validateDocumentFiles([valid, invalid])
    expect(result.isValid).toBe(false)
    expect(result.validFiles).toHaveLength(1)
    expect(result.errors).toHaveLength(1)
    expect(result.errors[0].file.name).toBe('invalid.zip')
  })
})

describe('Document API Functions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('uploadDocuments constructs FormData and sends files to /documents/upload', async () => {
    const file1 = new File(['content1'], 'doc1.pdf', { type: 'application/pdf' })
    const file2 = new File(['content2'], 'doc2.png', { type: 'image/png' })

    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: {
        success: true,
        message: 'Document uploaded successfully.',
        data: {
          documents: [
            { _id: 'doc_1', filename: 'doc1.pdf', status: 'UPLOADED' },
            { _id: 'doc_2', filename: 'doc2.png', status: 'UPLOADED' },
          ],
          count: 2,
        },
      },
    })

    const response = await uploadDocuments([file1, file2])

    expect(apiClient.post).toHaveBeenCalledWith(
      '/documents/upload',
      expect.any(FormData),
      expect.objectContaining({
        headers: { 'Content-Type': 'multipart/form-data' },
      }),
    )

    expect(response.documents).toHaveLength(2)
    expect(response.documents[0].id).toBe('doc_1')
    expect(response.documents[1].id).toBe('doc_2')
  })

  it('getDocuments calls GET /documents with pagination parameters and normalizes IDs', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        success: true,
        data: [
          { _id: 'doc_101', filename: 'invoice.pdf', status: 'READY' },
        ],
        pagination: { total: 1, page: 1, limit: 10, pages: 1 },
      },
    })

    const result = await getDocuments({ skip: 0, limit: 10 })

    expect(apiClient.get).toHaveBeenCalledWith('/documents', {
      params: { skip: 0, limit: 10 },
    })
    expect(result.data[0].id).toBe('doc_101')
    expect(result.pagination.total).toBe(1)
  })

  it('getDocument calls GET /documents/{id} and normalizes entity', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        success: true,
        message: 'Fetched',
        data: { _id: 'doc_abc', filename: 'paper.pdf', status: 'READY' },
      },
    })

    const doc = await getDocument('doc_abc')

    expect(apiClient.get).toHaveBeenCalledWith('/documents/doc_abc')
    expect(doc.id).toBe('doc_abc')
  })

  it('downloadDocument requests binary FileResponse blob', async () => {
    const mockBlob = new Blob(['sample pdf stream'], { type: 'application/pdf' })
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockBlob })

    const blob = await downloadDocument('doc_xyz')

    expect(apiClient.get).toHaveBeenCalledWith('/documents/doc_xyz/download', {
      responseType: 'blob',
    })
    expect(blob).toBe(mockBlob)
  })

  it('deleteDocument calls DELETE /documents/{id}', async () => {
    vi.mocked(apiClient.delete).mockResolvedValueOnce({
      data: { success: true, message: 'Document deleted successfully.' },
    })

    const result = await deleteDocument('doc_123')

    expect(apiClient.delete).toHaveBeenCalledWith('/documents/doc_123')
    expect(result.message).toBe('Document deleted successfully.')
  })

  it('processDocuments sends document_ids payload to /documents/process', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: {
        success: true,
        message: 'Documents queued for processing.',
        data: { queued_documents: ['doc_1', 'doc_2'], count: 2 },
      },
    })

    const result = await processDocuments(['doc_1', 'doc_2'])

    expect(apiClient.post).toHaveBeenCalledWith('/documents/process', {
      document_ids: ['doc_1', 'doc_2'],
    })
    expect(result.queued_documents).toEqual(['doc_1', 'doc_2'])
  })

  it('getDocumentVersions fetches historical versions', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        success: true,
        message: 'Retrieved',
        data: [
          { _id: 'doc_v1', version: 1, filename: 'spec_v1.pdf' },
          { _id: 'doc_v2', version: 2, filename: 'spec_v2.pdf' },
        ],
      },
    })

    const versions = await getDocumentVersions('doc_v2')

    expect(apiClient.get).toHaveBeenCalledWith('/documents/doc_v2/versions')
    expect(versions).toHaveLength(2)
    expect(versions[0].id).toBe('doc_v1')
  })
})

describe('Document React Query Hooks', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('useDocuments fetches and returns document query state', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        success: true,
        data: [{ _id: 'doc_1', filename: 'file.pdf', status: 'READY' }],
        pagination: { total: 1, page: 1, limit: 20, pages: 1 },
      },
    })

    const { result } = renderHook(() => useDocuments(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.data[0].id).toBe('doc_1')
  })

  it('useDocument fetches single document detail', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        success: true,
        message: 'Fetched',
        data: { _id: 'doc_single', filename: 'contract.pdf', status: 'READY' },
      },
    })

    const { result } = renderHook(() => useDocument('doc_single'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.id).toBe('doc_single')
  })

  it('useUploadDocuments triggers upload and invalidates cache', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: {
        success: true,
        data: { documents: [{ _id: 'doc_up' }], count: 1 },
      },
    })

    const { result } = renderHook(() => useUploadDocuments(), {
      wrapper: createWrapper(),
    })

    const file = new File(['data'], 'test.pdf', { type: 'application/pdf' })
    await result.current.mutateAsync([file])

    expect(apiClient.post).toHaveBeenCalled()
  })

  it('useProcessDocuments triggers batch processing', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: {
        success: true,
        data: { queued_documents: ['doc_1'], count: 1 },
      },
    })

    const { result } = renderHook(() => useProcessDocuments(), {
      wrapper: createWrapper(),
    })

    await result.current.mutateAsync(['doc_1'])

    expect(apiClient.post).toHaveBeenCalledWith('/documents/process', {
      document_ids: ['doc_1'],
    })
  })

  it('useDeleteDocument deletes document by id', async () => {
    vi.mocked(apiClient.delete).mockResolvedValueOnce({
      data: { success: true, message: 'Deleted' },
    })

    const { result } = renderHook(() => useDeleteDocument(), {
      wrapper: createWrapper(),
    })

    await result.current.mutateAsync('doc_del')

    expect(apiClient.delete).toHaveBeenCalledWith('/documents/doc_del')
  })

  it('useDocumentVersions fetches document versions', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        success: true,
        data: [{ _id: 'doc_v1', version: 1 }],
      },
    })

    const { result } = renderHook(() => useDocumentVersions('doc_v1'), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.[0].id).toBe('doc_v1')
  })
})
