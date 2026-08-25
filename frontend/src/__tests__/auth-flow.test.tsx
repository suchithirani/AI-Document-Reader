import React from 'react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/authStore'
import { ProtectedRoute, PublicRoute } from '@/components/auth'
import {
  ForgotPasswordPage,
  LoginPage,
  RegisterPage,
  ResetPasswordPage,
  VerifyEmailPage,
} from '@/pages'
import * as authApi from '@/api/auth'

vi.mock('@/api/auth')

const createAuthTestRouter = (initialEntry = '/login') => {
  return createMemoryRouter(
    [
      {
        element: <PublicRoute />,
        children: [
          { path: '/login', element: <LoginPage /> },
          { path: '/register', element: <RegisterPage /> },
          { path: '/verify-email', element: <VerifyEmailPage /> },
          { path: '/forgot-password', element: <ForgotPasswordPage /> },
          { path: '/reset-password', element: <ResetPasswordPage /> },
        ],
      },
      {
        element: <ProtectedRoute />,
        children: [
          { path: '/dashboard', element: <div>Protected Dashboard Content</div> },
        ],
      },
    ],
    { initialEntries: [initialEntry] },
  )
}

const renderWithClient = (router: ReturnType<typeof createAuthTestRouter>) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
}

describe('Authentication Flow & Security Hardening', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    useAuthStore.setState({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isInitialized: true,
      isLoading: false,
    })
  })

  it('validates email format and password length in login', async () => {
    const router = createAuthTestRouter('/login')
    renderWithClient(router)

    expect(screen.getByRole('heading', { name: /sign in to your account/i })).toBeDefined()

    fireEvent.change(screen.getByPlaceholderText(/name@company\.com/i), {
      target: { value: 'not-an-email' },
    })
    fireEvent.change(screen.getByPlaceholderText(/••••••••/i), {
      target: { value: 'short' },
    })

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByText(/please enter a valid email address/i)).toBeDefined()
  })

  it('submits login payload and updates auth state on success', async () => {
    const mockUser = {
      id: 'usr_123',
      name: 'Test User',
      email: 'test@example.com',
      role: 'user' as const,
      is_active: true,
      is_verified: true,
    }

    vi.mocked(authApi.loginUser).mockResolvedValueOnce({
      access_token: 'mock_access_token',
      refresh_token: 'mock_refresh_token',
      token_type: 'Bearer',
      expires_in: 3600,
      user: mockUser,
    })

    const router = createAuthTestRouter('/login')
    renderWithClient(router)

    fireEvent.change(screen.getByPlaceholderText(/name@company\.com/i), {
      target: { value: 'test@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText(/••••••••/i), {
      target: { value: 'password123' },
    })

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(authApi.loginUser).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      })
      expect(useAuthStore.getState().isAuthenticated).toBe(true)
      expect(useAuthStore.getState().user?.email).toBe('test@example.com')
    })
  })

  it('redirects unverified user to verify email during login', async () => {
    const error403 = {
      response: {
        status: 403,
        data: { message: 'Please verify your email before logging in.' },
      },
    }
    vi.mocked(authApi.loginUser).mockRejectedValueOnce(error403)

    const router = createAuthTestRouter('/login')
    renderWithClient(router)

    fireEvent.change(screen.getByPlaceholderText(/name@company\.com/i), {
      target: { value: 'unverified@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText(/••••••••/i), {
      target: { value: 'password123' },
    })

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    expect(await screen.findByRole('heading', { name: /verify your email/i })).toBeDefined()
  })

  it('validates registration passwords match and name length', async () => {
    const router = createAuthTestRouter('/register')
    renderWithClient(router)

    expect(screen.getByRole('heading', { name: /create an account/i })).toBeDefined()

    fireEvent.change(screen.getByPlaceholderText(/jane doe/i), {
      target: { value: 'Jane Doe' },
    })
    fireEvent.change(screen.getByPlaceholderText(/name@company\.com/i), {
      target: { value: 'jane@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText(/at least 8 characters/i), {
      target: { value: 'password123' },
    })
    fireEvent.change(screen.getByPlaceholderText(/repeat password/i), {
      target: { value: 'mismatchpass' },
    })

    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByText(/passwords do not match/i)).toBeDefined()
  })

  it('handles existing email registration with security-conscious message', async () => {
    const duplicateError = {
      response: {
        status: 409,
        data: { message: 'Email already registered' },
      },
    }
    vi.mocked(authApi.registerUser).mockRejectedValueOnce(duplicateError)

    const router = createAuthTestRouter('/register')
    renderWithClient(router)

    fireEvent.change(screen.getByPlaceholderText(/jane doe/i), {
      target: { value: 'Jane Doe' },
    })
    fireEvent.change(screen.getByPlaceholderText(/name@company\.com/i), {
      target: { value: 'existing@example.com' },
    })
    fireEvent.change(screen.getByPlaceholderText(/at least 8 characters/i), {
      target: { value: 'securepassword123' },
    })
    fireEvent.change(screen.getByPlaceholderText(/repeat password/i), {
      target: { value: 'securepassword123' },
    })

    fireEvent.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByText(/it may already be registered/i)).toBeDefined()
  })

  it('validates and submits OTP on verify email page', async () => {
    vi.mocked(authApi.verifyEmail).mockResolvedValueOnce({
      success: true,
      message: 'Email verified',
      data: {},
    })

    const router = createAuthTestRouter('/verify-email')
    renderWithClient(router)

    expect(screen.getByRole('heading', { name: /verify your email/i })).toBeDefined()

    fireEvent.change(screen.getByPlaceholderText(/name@company\.com/i), {
      target: { value: 'jane@example.com' },
    })

    const digit1 = screen.getByLabelText(/digit 1 of 6/i)
    fireEvent.paste(digit1, {
      clipboardData: { getData: () => '654321' },
    })

    await waitFor(() => {
      expect(authApi.verifyEmail).toHaveBeenCalledWith({
        identifier: 'jane@example.com',
        otp: '654321',
      })
    })

    expect(await screen.findByRole('heading', { name: /email verified successfully/i })).toBeDefined()
  })

  it('submits forgot password and presents anti-enumeration confirmation state', async () => {
    vi.mocked(authApi.forgotPassword).mockResolvedValueOnce({
      success: true,
      message: 'Reset code dispatched',
      data: { message: 'Sent' },
    })

    const router = createAuthTestRouter('/forgot-password')
    renderWithClient(router)

    expect(screen.getByRole('heading', { name: /forgot your password/i })).toBeDefined()

    fireEvent.change(screen.getByPlaceholderText(/name@company\.com/i), {
      target: { value: 'user@example.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: /send reset instructions/i }))

    await waitFor(() => {
      expect(authApi.forgotPassword).toHaveBeenCalledWith({
        identifier: 'user@example.com',
      })
      expect(screen.getByRole('heading', { name: /check your email/i })).toBeDefined()
    })
  })

  it('pre-populates query parameters and submits reset password successfully', async () => {
    vi.mocked(authApi.resetPassword).mockResolvedValueOnce({
      success: true,
      message: 'Password updated',
      data: { message: 'Updated' },
    })

    const router = createAuthTestRouter('/reset-password?token=112233&email=user@example.com')
    renderWithClient(router)

    expect(screen.getByRole('heading', { name: /reset your password/i })).toBeDefined()
    expect(screen.getByDisplayValue('user@example.com')).toBeDefined()
    expect(screen.getByDisplayValue('112233')).toBeDefined()

    fireEvent.change(screen.getByPlaceholderText(/at least 8 characters/i), {
      target: { value: 'newpassword123' },
    })
    fireEvent.change(screen.getByPlaceholderText(/repeat new password/i), {
      target: { value: 'newpassword123' },
    })

    fireEvent.click(screen.getByRole('button', { name: /update password/i }))

    await waitFor(() => {
      expect(authApi.resetPassword).toHaveBeenCalledWith({
        identifier: 'user@example.com',
        otp: '112233',
        new_password: 'newpassword123',
      })
      expect(screen.getByRole('heading', { name: /password reset complete/i })).toBeDefined()
    })
  })

  it('redirects unauthenticated users from protected routes to login', () => {
    useAuthStore.setState({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isInitialized: true,
      isLoading: false,
    })

    const router = createAuthTestRouter('/dashboard')
    renderWithClient(router)

    expect(screen.getByRole('heading', { name: /sign in to your account/i })).toBeDefined()
  })

  it('allows verified authenticated users into protected routes', () => {
    useAuthStore.setState({
      user: {
        id: 'usr_1',
        name: 'Auth User',
        email: 'auth@example.com',
        role: 'user',
        is_active: true,
        is_verified: true,
      },
      tokens: {
        access_token: 'valid_access_token',
        refresh_token: 'valid_refresh_token',
        token_type: 'Bearer',
      },
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
    })

    const router = createAuthTestRouter('/dashboard')
    renderWithClient(router)

    expect(screen.getByText('Protected Dashboard Content')).toBeDefined()
  })
})
