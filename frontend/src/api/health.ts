import apiClient from './client'
import type { ApiResponse, HealthStatusData } from '@/types/api'

/**
 * Fetches the backend system health status
 * Endpoint: GET /health (relative to baseURL /api/v1)
 */
export async function getHealthStatus(): Promise<HealthStatusData> {
  const response = await apiClient.get<ApiResponse<HealthStatusData>>('/health')
  return response.data.data
}
