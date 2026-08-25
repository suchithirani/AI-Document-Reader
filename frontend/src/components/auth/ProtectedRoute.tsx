import React from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { LoadingState } from '@/components/ui/LoadingState'

export function ProtectedRoute() {
  const isInitialized = useAuthStore((state) => state.isInitialized)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)
  const location = useLocation()

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-[#F7F3EE] dark:bg-[#08090B]">
        <LoadingState label="Checking session..." sublabel="Validating authentication tokens" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Direct unverified users to verify email screen
  if (user && !user.is_verified) {
    return <Navigate to="/verify-email" state={{ email: user.email }} replace />
  }

  return <Outlet />
}
