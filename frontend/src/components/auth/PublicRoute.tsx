import React from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { LoadingState } from '@/components/ui/LoadingState'

export function PublicRoute() {
  const isInitialized = useAuthStore((state) => state.isInitialized)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const user = useAuthStore((state) => state.user)

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-[#F7F3EE] dark:bg-[#08090B]">
        <LoadingState label="Loading..." sublabel="Checking workspace session" />
      </div>
    )
  }

  // If already authenticated and verified, redirect to dashboard
  if (isAuthenticated && user?.is_verified) {
    return <Navigate to="/dashboard" replace />
  }

  return <Outlet />
}
