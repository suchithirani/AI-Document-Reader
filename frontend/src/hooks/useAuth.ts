import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import {
  forgotPassword,
  loginUser,
  logoutUser,
  registerUser,
  resendVerificationOtp,
  resetPassword,
  verifyEmail,
} from '@/api/auth'
import type {
  ForgotPasswordPayload,
  LoginPayload,
  RegisterPayload,
  ResetPasswordPayload,
  ResendOtpPayload,
  VerifyEmailPayload,
} from '@/types/auth'
import { useToast } from '@/components/ui/useToast'
import type { AxiosError } from 'axios'
import type { ApiError } from '@/types/api'

export function useAuth() {
  const user = useAuthStore((state) => state.user)
  const tokens = useAuthStore((state) => state.tokens)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const isInitialized = useAuthStore((state) => state.isInitialized)
  const setAuth = useAuthStore((state) => state.setAuth)
  const clearAuth = useAuthStore((state) => state.clearAuth)
  const initializeAuth = useAuthStore((state) => state.initializeAuth)

  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const toast = useToast()

  const getErrorMessage = (error: unknown, fallback: string) => {
    const axiosErr = error as AxiosError<ApiError>
    return axiosErr.response?.data?.message || axiosErr.message || fallback
  }

  // Login Mutation
  const loginMutation = useMutation({
    mutationFn: (payload: LoginPayload) => loginUser(payload),
    onSuccess: (data) => {
      setAuth(data.user, {
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_type: data.token_type,
        expires_in: data.expires_in,
      })
      toast.success('Welcome back!', `Logged in as ${data.user.email}`)
    },
    onError: (error) => {
      toast.error('Login Failed', getErrorMessage(error, 'Invalid email or password.'))
    },
  })

  // Register Mutation
  const registerMutation = useMutation({
    mutationFn: (payload: RegisterPayload) => registerUser(payload),
    onSuccess: () => {
      toast.success('Account Created', 'Please verify your email with the 6-digit code sent.')
    },
    onError: (error) => {
      toast.error('Registration Failed', getErrorMessage(error, 'Could not create account.'))
    },
  })

  // Verify Email Mutation
  const verifyEmailMutation = useMutation({
    mutationFn: (payload: VerifyEmailPayload) => verifyEmail(payload),
    onSuccess: () => {
      toast.success('Email Verified', 'Your email has been verified. You may now sign in.')
    },
    onError: (error) => {
      toast.error('Verification Failed', getErrorMessage(error, 'Invalid or expired verification code.'))
    },
  })

  // Resend OTP Mutation
  const resendOtpMutation = useMutation({
    mutationFn: (payload: ResendOtpPayload) => resendVerificationOtp(payload),
    onSuccess: () => {
      toast.info('Code Sent', 'A new verification code has been dispatched.')
    },
    onError: (error) => {
      toast.error('Resend Failed', getErrorMessage(error, 'Could not send verification code.'))
    },
  })

  // Forgot Password Mutation
  const forgotPasswordMutation = useMutation({
    mutationFn: (payload: ForgotPasswordPayload) => forgotPassword(payload),
    onSuccess: () => {
      toast.info('Password Reset Code Sent', 'If an account exists, a reset code was sent.')
    },
    onError: (error) => {
      toast.error('Request Failed', getErrorMessage(error, 'Could not process password reset.'))
    },
  })

  // Reset Password Mutation
  const resetPasswordMutation = useMutation({
    mutationFn: (payload: ResetPasswordPayload) => resetPassword(payload),
    onSuccess: () => {
      toast.success('Password Updated', 'Your password has been reset. Please sign in.')
    },
    onError: (error) => {
      toast.error('Reset Failed', getErrorMessage(error, 'Could not update password.'))
    },
  })

  // Logout Mutation
  const logoutMutation = useMutation({
    mutationFn: async () => {
      if (tokens?.refresh_token) {
        try {
          await logoutUser(tokens.refresh_token)
        } catch {
          // ignore backend errors on logout to ensure local state clears
        }
      }
    },
    onSettled: () => {
      clearAuth()
      queryClient.clear()
      toast.info('Signed Out', 'You have been signed out.')
      navigate('/login')
    },
  })

  return {
    user,
    tokens,
    isAuthenticated,
    isInitialized,
    isVerified: Boolean(user?.is_verified),
    login: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error ? getErrorMessage(loginMutation.error, 'Login failed') : null,

    register: registerMutation.mutateAsync,
    isRegistering: registerMutation.isPending,
    registerError: registerMutation.error ? getErrorMessage(registerMutation.error, 'Registration failed') : null,

    verifyEmail: verifyEmailMutation.mutateAsync,
    isVerifying: verifyEmailMutation.isPending,
    verifyError: verifyEmailMutation.error ? getErrorMessage(verifyEmailMutation.error, 'Verification failed') : null,

    resendOtp: resendOtpMutation.mutateAsync,
    isResendingOtp: resendOtpMutation.isPending,

    forgotPassword: forgotPasswordMutation.mutateAsync,
    isSendingForgot: forgotPasswordMutation.isPending,
    forgotError: forgotPasswordMutation.error ? getErrorMessage(forgotPasswordMutation.error, 'Request failed') : null,

    resetPassword: resetPasswordMutation.mutateAsync,
    isResettingPassword: resetPasswordMutation.isPending,
    resetError: resetPasswordMutation.error ? getErrorMessage(resetPasswordMutation.error, 'Reset failed') : null,

    logout: logoutMutation.mutate,
    isLoggingOut: logoutMutation.isPending,

    initializeAuth,
  }
}
