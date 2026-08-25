/**
 * Standard Backend Response Envelope
 */
export interface ApiResponse<T = unknown> {
  success: boolean
  message: string
  data: T
}

/**
 * Standard Backend Error Envelope
 */
export interface ApiError {
  success: false
  message: string
  path?: string
  timestamp?: string
  errors?: Record<string, string[]> | string[]
}

/**
 * Pagination metadata format matching backend paginated_response
 */
export interface PaginationMeta {
  total: number
  page: number
  limit: number
  pages: number
}

/**
 * Paginated API Response Envelope
 */
export interface PaginatedApiResponse<T> {
  success: boolean
  data: T[]
  pagination: PaginationMeta
}

/**
 * Health check response data
 */
export interface HealthStatusData {
  status: string
  application: string
  version: string
  redis?: string
}
