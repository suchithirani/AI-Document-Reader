import apiClient from './client'
import type { ApiResponse } from '@/types/api'
import type {
  AuthResponseData,
  AuthTokens,
  ForgotPasswordPayload,
  LoginPayload,
  RegisterPayload,
  ResetPasswordPayload,
  ResendOtpPayload,
  User,
  VerifyEmailPayload,
} from '@/types/auth'
import { normalizeEntity } from '@/lib/utils'

/**
 * Login with email and password
 * Endpoint: POST /auth/login
 */
export async function loginUser(payload: LoginPayload): Promise<AuthResponseData> {
  const response = await apiClient.post<ApiResponse<AuthResponseData>>('/auth/login', payload)
  const data = response.data.data
  return {
    ...data,
    user: normalizeEntity(data.user as unknown as Record<string, unknown>) as unknown as User,
  }
}

/**
 * Register a new user account
 * Endpoint: POST /auth/register
 */
export async function registerUser(payload: RegisterPayload): Promise<ApiResponse<unknown>> {
  const response = await apiClient.post<ApiResponse<unknown>>('/auth/register', payload)
  return response.data
}

/**
 * Verify user email with 6-digit OTP
 * Endpoint: POST /auth/verify-email
 */
export async function verifyEmail(payload: VerifyEmailPayload): Promise<ApiResponse<unknown>> {
  const response = await apiClient.post<ApiResponse<unknown>>('/auth/verify-email', payload)
  return response.data
}

/**
 * Resend verification OTP code
 * Endpoint: POST /auth/resend-verification-otp
 */
export async function resendVerificationOtp(payload: ResendOtpPayload): Promise<ApiResponse<{ message: string }>> {
  const response = await apiClient.post<ApiResponse<{ message: string }>>('/auth/resend-verification-otp', payload)
  return response.data
}

/**
 * Request forgot password OTP code
 * Endpoint: POST /auth/forgot-password
 */
export async function forgotPassword(payload: ForgotPasswordPayload): Promise<ApiResponse<{ message: string }>> {
  const response = await apiClient.post<ApiResponse<{ message: string }>>('/auth/forgot-password', payload)
  return response.data
}

/**
 * Reset password using OTP code
 * Endpoint: POST /auth/reset-password
 */
export async function resetPassword(payload: ResetPasswordPayload): Promise<ApiResponse<{ message: string }>> {
  const response = await apiClient.post<ApiResponse<{ message: string }>>('/auth/reset-password', payload)
  return response.data
}

/**
 * Get current authenticated user profile
 * Endpoint: GET /auth/me
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<ApiResponse<User>>('/auth/me')
  const user = response.data.data
  return normalizeEntity(user as unknown as Record<string, unknown>) as unknown as User
}

/**
 * Refresh access token
 * Endpoint: POST /auth/refresh
 */
export async function refreshAuthToken(refreshToken: string): Promise<AuthTokens> {
  const response = await apiClient.post<ApiResponse<AuthTokens>>('/auth/refresh', {
    refresh_token: refreshToken,
  })
  return response.data.data
}

/**
 * Logout user session
 * Endpoint: POST /auth/logout
 */
export async function logoutUser(refreshToken: string): Promise<ApiResponse<{ message: string }>> {
  const response = await apiClient.post<ApiResponse<{ message: string }>>('/auth/logout', {
    refresh_token: refreshToken,
  })
  return response.data
}
