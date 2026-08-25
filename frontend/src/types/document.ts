export type DocumentStatus =
  | 'UPLOADED'
  | 'QUEUED'
  | 'OCR_PROCESSING'
  | 'CHUNKING'
  | 'EMBEDDING'
  | 'READY'
  | 'FAILED'

export interface Document {
  id: string
  owner_id: string
  filename: string
  original_filename: string
  mime_type: string
  extension: string
  file_size: number
  file_hash?: string | null
  page_count?: number | null
  status: DocumentStatus
  progress: number
  created_at: string
  updated_at: string
  description?: string | null
  document_type?: string | null
  tags?: string[]
  extracted_metadata?: Record<string, unknown>
  version: number
  version_group_id?: string | null
  is_latest: boolean
  ocr_quality_score?: number | null
  ocr_quality_warning?: boolean
}

export interface DocumentUploadResponse {
  documents: Document[]
  count: number
  duplicate_documents?: string[]
}

export interface DocumentProcessRequest {
  document_ids: string[]
}

export interface DocumentProcessResponse {
  queued_documents: string[]
  count: number
}

export interface DocumentPaginationParams {
  skip?: number
  limit?: number
}
