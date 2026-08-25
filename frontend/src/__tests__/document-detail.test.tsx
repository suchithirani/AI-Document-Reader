import { describe, expect, it, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import React from 'react'
import { DocumentDetailPage } from '@/pages/documents/DocumentDetailPage'
import * as docsApi from '@/api/documents'
import type { Document } from '@/types/document'

vi.mock('@/api/documents')

const mockDocReady: Document = {
  id: 'doc_ready_1',
  owner_id: 'usr_1',
  filename: 'quarterly_earnings_q4.pdf',
  original_filename: 'quarterly_earnings_q4.pdf',
  mime_type: 'application/pdf',
  extension: 'pdf',
  file_size: 1024 * 1024 * 4.2,
  status: 'READY',
  progress: 100,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  version: 2,
  version_group_id: 'vg_123',
  is_latest: true,
  ocr_quality_warning: true,
  tags: ['finance', 'quarterly', 'earnings'],
  extracted_metadata: {
    title: 'Q4 Financial Report',
    author: 'Finance Team',
    pages: 14,
    revenue: 1250000,
  },
}

const mockDocProcessing: Document = {
  id: 'doc_proc_2',
  owner_id: 'usr_1',
  filename: 'contract_draft.pdf',
  original_filename: 'contract_draft.pdf',
  mime_type: 'application/pdf',
  extension: 'pdf',
  file_size: 1024 * 512,
  status: 'OCR_PROCESSING',
  progress: 10,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  version: 1,
  is_latest: true,
}

const renderWithRouter = (documentId: string) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  const router = createMemoryRouter(
    [
      {
        path: '/documents/:id',
        element: <DocumentDetailPage />,
      },
      {
        path: '/documents',
        element: <div>Documents List Page</div>,
      },
      {
        path: '/chat',
        element: <div>Chat Page Workspace</div>,
      },
    ],
    {
      initialEntries: [`/documents/${documentId}`],
    },
  )

  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

describe('Document Detail & Versions Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders Document Detail page with metadata, tags, and extracted metadata', async () => {
    vi.mocked(docsApi.getDocument).mockResolvedValueOnce(mockDocReady)
    vi.mocked(docsApi.getDocumentVersions).mockResolvedValueOnce([mockDocReady])

    renderWithRouter('doc_ready_1')

    expect(await screen.findByRole('heading', { name: /quarterly_earnings_q4\.pdf/i })).toBeDefined()
    expect(screen.getByText('Ready')).toBeDefined()
    expect(screen.getByText(/low ocr quality warning/i)).toBeDefined()
    expect(screen.getByText('#finance')).toBeDefined()
    expect(screen.getByText('#quarterly')).toBeDefined()
    expect(screen.getByText('Q4 Financial Report')).toBeDefined()
    expect(screen.getByText('Finance Team')).toBeDefined()
  })

  it('enables Chat with this document button when status is READY', async () => {
    vi.mocked(docsApi.getDocument).mockResolvedValueOnce(mockDocReady)
    vi.mocked(docsApi.getDocumentVersions).mockResolvedValueOnce([mockDocReady])

    renderWithRouter('doc_ready_1')

    const chatBtn = await screen.findByRole('button', { name: /chat with this document/i })
    expect(chatBtn.hasAttribute('disabled')).toBe(false)

    fireEvent.click(chatBtn)
    expect(await screen.findByText('Chat Page Workspace')).toBeDefined()
  })

  it('disables Chat with this document when document is in processing state', async () => {
    vi.mocked(docsApi.getDocument).mockResolvedValueOnce(mockDocProcessing)
    vi.mocked(docsApi.getDocumentVersions).mockResolvedValueOnce([mockDocProcessing])

    renderWithRouter('doc_proc_2')

    const chatBtn = await screen.findByRole('button', { name: /chat with this document/i })
    expect(chatBtn.hasAttribute('disabled')).toBe(true)
    expect(screen.getByText(/processing in progress/i)).toBeDefined()
  })

  it('opens versions modal and displays version history', async () => {
    const version1: Document = {
      ...mockDocReady,
      id: 'doc_v1',
      version: 1,
      is_latest: false,
    }

    vi.mocked(docsApi.getDocument).mockResolvedValueOnce(mockDocReady)
    vi.mocked(docsApi.getDocumentVersions).mockResolvedValueOnce([version1, mockDocReady])

    renderWithRouter('doc_ready_1')

    const versionsBtn = await screen.findByRole('button', { name: /versions/i })
    fireEvent.click(versionsBtn)

    expect(await screen.findByRole('heading', { name: /document version history/i })).toBeDefined()
    expect(screen.getByText('Version 1')).toBeDefined()
    expect(screen.getByText('Version 2')).toBeDefined()
    expect(screen.getByText('Current')).toBeDefined()
  })

  it('displays document not found error state when ID does not exist', async () => {
    vi.mocked(docsApi.getDocument).mockRejectedValueOnce(new Error('Document not found.'))

    renderWithRouter('non_existent_id')

    expect(await screen.findByRole('heading', { name: /document not found/i })).toBeDefined()
    expect(screen.getByRole('button', { name: /back to documents/i })).toBeDefined()
  })
})
