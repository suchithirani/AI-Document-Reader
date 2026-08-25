import axios, {
  type AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios'
import type { ApiError, ApiResponse } from '@/types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value?: unknown) => void
  reject: (reason?: unknown) => void
}> = []

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error)
    } else {
      promise.resolve(token)
    }
  })
  failedQueue = []
}

// Request Interceptor: Attach Access Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const rawTokens = localStorage.getItem('ai_doc_tokens')
    if (rawTokens) {
      try {
        const parsed = JSON.parse(rawTokens)
        if (parsed.access_token && !config.headers.Authorization) {
          config.headers.Authorization = `Bearer ${parsed.access_token}`
        }
      } catch {
        // invalid JSON in storage, ignore
      }
    }
    return config
  },
  (error) => Promise.reject(error),
)

// Response Interceptor: Handle Envelope & Token Refresh
apiClient.interceptors.response.use(
  (response) => {
    // Return backend data envelope directly if present
    return response
  },
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // If 401 Unauthorized and not already retried
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      if (originalRequest.url?.includes('/auth/refresh') || originalRequest.url?.includes('/auth/login')) {
        return Promise.reject(error)
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            if (token && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            return apiClient(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const rawTokens = localStorage.getItem('ai_doc_tokens')
        if (!rawTokens) {
          throw new Error('No refresh token available')
        }

        const parsed = JSON.parse(rawTokens)
        if (!parsed.refresh_token) {
          throw new Error('Missing refresh_token')
        }

        // Refresh uses JSON request body: { refresh_token }
        const { data: refreshRes } = await axios.post<ApiResponse<{ access_token: string; refresh_token?: string }>>(
          `${API_BASE_URL}/auth/refresh`,
          { refresh_token: parsed.refresh_token },
        )

        const newAccessToken = refreshRes.data.access_token
        const updatedTokens = {
          ...parsed,
          access_token: newAccessToken,
          refresh_token: refreshRes.data.refresh_token || parsed.refresh_token,
        }

        localStorage.setItem('ai_doc_tokens', JSON.stringify(updatedTokens))

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        }

        processQueue(null, newAccessToken)
        return apiClient(originalRequest)
      } catch (refreshErr) {
        processQueue(refreshErr, null)
        localStorage.removeItem('ai_doc_tokens')
        localStorage.removeItem('ai_doc_user')
        return Promise.reject(refreshErr)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

export default apiClient
