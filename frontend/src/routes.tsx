import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { ProtectedRoute, PublicRoute } from '@/components/auth'
import {
  AccountPage,
  ChatPage,
  CollectionsPage,
  DashboardPage,
  DocumentsPage,
  DocumentDetailPage,
  ForgotPasswordPage,
  LoginPage,
  RegisterPage,
  ResendVerificationPage,
  ResetPasswordPage,
  ScaffoldStatusPage,
  VerifyEmailPage,
} from '@/pages'

export const router = createBrowserRouter([
  // Root Redirect
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },

  // Public Authentication Routes (Guarded: redirect to /dashboard if logged in and verified)
  {
    element: <PublicRoute />,
    children: [
      {
        element: <AuthLayout />,
        children: [
          {
            path: '/login',
            element: <LoginPage />,
          },
          {
            path: '/register',
            element: <RegisterPage />,
          },
          {
            path: '/verify-email',
            element: <VerifyEmailPage />,
          },
          {
            path: '/resend-verification',
            element: <ResendVerificationPage />,
          },
          {
            path: '/forgot-password',
            element: <ForgotPasswordPage />,
          },
          {
            path: '/reset-password',
            element: <ResetPasswordPage />,
          },
        ],
      },
    ],
  },

  // Authenticated Feature Routes (Guarded: require authentication and verified email)
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppShell />,
        children: [
          {
            path: '/dashboard',
            element: <DashboardPage />,
          },
          {
            path: '/documents',
            element: <DocumentsPage />,
          },
          {
            path: '/documents/:id',
            element: <DocumentDetailPage />,
          },
          {
            path: '/collections',
            element: <CollectionsPage />,
          },
          {
            path: '/chat',
            element: <ChatPage />,
          },
          {
            path: '/account',
            element: <AccountPage />,
          },
          {
            path: '/dev-status',
            element: <ScaffoldStatusPage />,
          },
        ],
      },
    ],
  },

  // Catch-all 404 redirect
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
])
