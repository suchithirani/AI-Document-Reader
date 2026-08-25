export type MessageRole = 'user' | 'assistant' | 'system'

export interface CitationSource {
  document_id: string
  document_title?: string
  page_number?: number
  chunk_id?: string
  snippet?: string
  similarity_score?: number
}

export interface ChatMessage {
  id: string
  session_id: string
  role: MessageRole
  content: string
  sources?: CitationSource[]
  tokens_used?: number
  created_at: string
}

export interface ChatSession {
  id: string
  user_id: string
  title: string
  collection_id?: string | null
  document_ids?: string[]
  created_at: string
  updated_at?: string
}

export type SSEEventType = 'chunk' | 'sources' | 'done' | 'error'

export interface SSEChunkPayload {
  chunk?: string
  sources?: CitationSource[]
  message_id?: string
  session_id?: string
  error?: string
}
