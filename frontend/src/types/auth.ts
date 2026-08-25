export type UserRole = 'user' | 'admin' | 'superadmin'

export interface User {
  id: string
  name: string
  email: string
  phone_number?: string | null
  role: UserRole
  profile_picture?: string | null
  is_active: boolean
  is_verified: boolean
  phone_verified?: boolean
  created_at?: string
  updated_at?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in?: number
}

export interface AuthResponseData {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  name: string
  email: string
  password: string
}

export interface VerifyEmailPayload {
  identifier: string
  otp: string
}

export interface ResendOtpPayload {
  identifier: string
}

export interface ForgotPasswordPayload {
  identifier: string
}

export interface ResetPasswordPayload {
  identifier: string
  otp: string
  new_password: string
}

export interface RefreshTokenPayload {
  refresh_token: string
}
