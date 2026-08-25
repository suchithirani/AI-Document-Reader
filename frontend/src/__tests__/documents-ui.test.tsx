import { describe, expect, it, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'
import { MemoryRouter } from 'react-router-dom'
import { DocumentsPage } from '@/pages/documents/DocumentsPage'
import * as docsApi from '@/api/documents'
import type { Document } from '@/types/document'

vi.mock('@/api/documents')

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

const mockDoc1: Document = {
  id: 'doc_1',
  owner_id: 'usr_1',
  filename: 'financial_report_2025.pdf',
  original_filename: 'financial_report_2025.pdf',
  mime_type: 'application/pdf',
  extension: 'pdf',
  file_size: 1024 * 1024 * 2.5, // 2.5 MB
  status: 'UPLOADED',
  progress: 0,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  version: 1,
  is_latest: true,
}

const mockDoc2: Document = {
  id: 'doc_2',
  owner_id: 'usr_1',
  filename: 'receipt_scan.png',
  original_filename: 'receipt_scan.png',
  mime_type: 'image/png',
  extension: 'png',
  file_size: 512 * 1024,
  status: 'READY',
  progress: 100,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  version: 1,
  is_latest: true,
  ocr_quality_warning: true,
}

describe('Documents Page & UI Components', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Documents page with header and empty state when no documents exist', async () => {
    vi.mocked(docsApi.getDocuments).mockResolvedValueOnce({
      success: true,
      data: [],
      pagination: { total: 0, page: 1, limit: 20, pages: 0 },
    })

    render(<DocumentsPage />, { wrapper: createWrapper() })

    expect(screen.getByRole('heading', { name: /^documents$/i })).toBeDefined()
    expect(
      screen.getByText(/upload, inspect, ocr process, and manage intelligence documents/i),
    ).toBeDefined()

    expect(await screen.findByText(/no documents yet/i)).toBeDefined()
  })

  it('renders document items with status badges, metadata, and OCR warnings', async () => {
    vi.mocked(docsApi.getDocuments).mockResolvedValueOnce({
      success: true,
      data: [mockDoc1, mockDoc2],
      pagination: { total: 2, page: 1, limit: 20, pages: 1 },
    })

    render(<DocumentsPage />, { wrapper: createWrapper() })

    expect(await screen.findByText('financial_report_2025.pdf')).toBeDefined()
    expect(screen.getByText('receipt_scan.png')).toBeDefined()
    expect(screen.getByText(/low ocr quality/i)).toBeDefined()
    expect(screen.getByText('Uploaded')).toBeDefined()
    expect(screen.getByText('Ready')).toBeDefined()
  })

  it('triggers process action when single document Process button is clicked', async () => {
    vi.mocked(docsApi.getDocuments).mockResolvedValueOnce({
      success: true,
      data: [mockDoc1],
      pagination: { total: 1, page: 1, limit: 20, pages: 1 },
    })
    vi.mocked(docsApi.processDocuments).mockResolvedValueOnce({
      queued_documents: ['doc_1'],
      count: 1,
    })

    render(<DocumentsPage />, { wrapper: createWrapper() })

    const processBtn = await screen.findByRole('button', { name: /^process$/i })
    fireEvent.click(processBtn)

    await waitFor(() => {
      expect(docsApi.processDocuments).toHaveBeenCalledWith(['doc_1'])
    })
  })

  it('supports selecting documents and running bulk processing', async () => {
    vi.mocked(docsApi.getDocuments).mockResolvedValueOnce({
      success: true,
      data: [mockDoc1, mockDoc2],
      pagination: { total: 2, page: 1, limit: 20, pages: 1 },
    })
    vi.mocked(docsApi.processDocuments).mockResolvedValueOnce({
      queued_documents: ['doc_1'],
      count: 1,
    })

    render(<DocumentsPage />, { wrapper: createWrapper() })

    const selectCheckbox = await screen.findByLabelText(/select financial_report_2025\.pdf/i)
    fireEvent.click(selectCheckbox)

    const bulkProcessBtn = await screen.findByRole('button', { name: /process selected \(1\)/i })
    fireEvent.click(bulkProcessBtn)

    await waitFor(() => {
      expect(docsApi.processDocuments).toHaveBeenCalledWith(['doc_1'])
    })
  })

  it('opens delete confirmation modal and calls deleteDocument on confirm', async () => {
    vi.mocked(docsApi.getDocuments).mockResolvedValueOnce({
      success: true,
      data: [mockDoc1],
      pagination: { total: 1, page: 1, limit: 20, pages: 1 },
    })
    vi.mocked(docsApi.deleteDocument).mockResolvedValueOnce({
      success: true,
      message: 'Deleted',
      data: { message: 'Deleted' },
    })

    render(<DocumentsPage />, { wrapper: createWrapper() })

    const deleteBtn = await screen.findByRole('button', { name: /delete/i })
    fireEvent.click(deleteBtn)

    expect(screen.getByRole('heading', { name: /delete document/i })).toBeDefined()

    const confirmDeleteBtn = screen.getByRole('button', { name: /confirm delete/i })
    fireEvent.click(confirmDeleteBtn)

    await waitFor(() => {
      expect(docsApi.deleteDocument).toHaveBeenCalledWith('doc_1')
    })
  })
})
