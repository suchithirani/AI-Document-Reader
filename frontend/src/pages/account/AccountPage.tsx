import React from 'react'
import { LogOut, Shield, User as UserIcon } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { GlassCard } from '@/components/ui/GlassCard'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { useAuth } from '@/hooks/useAuth'

export function AccountPage() {
  const { user, logout, isLoggingOut } = useAuth()

  return (
    <div className="space-y-6 text-left">
      <PageHeader
        title="Account & Settings"
        description="Manage your profile information, authentication credentials, and security preferences"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Card */}
        <GlassCard variant="default" className="p-6 space-y-4 lg:col-span-2">
          <div className="flex items-center gap-3 pb-3 border-b border-[rgba(90,70,50,0.12)] dark:border-white/[0.06]">
            <UserIcon className="w-4 h-4 text-[#886F4E] dark:text-[#A68A6A]" />
            <h3 className="text-sm font-semibold text-[#211C17] dark:text-white">
              Profile Information
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Full Name"
              defaultValue={user?.name || 'User'}
              disabled
            />
            <Input
              label="Email address"
              defaultValue={user?.email || 'user@workspace.ai'}
              disabled
            />
          </div>

          <div className="pt-2 flex items-center gap-3">
            <Badge variant="default" size="sm">
              Role: {user?.role ? user.role.toUpperCase() : 'USER'}
            </Badge>
            <Badge variant={user?.is_verified ? 'success' : 'warning'} size="sm">
              {user?.is_verified ? 'Email Verified' : 'Unverified'}
            </Badge>
          </div>
        </GlassCard>

        {/* Security & Session */}
        <GlassCard variant="default" className="p-6 space-y-4">
          <div className="flex items-center gap-3 pb-3 border-b border-[rgba(90,70,50,0.12)] dark:border-white/[0.06]">
            <Shield className="w-4 h-4 text-[#886F4E] dark:text-[#A68A6A]" />
            <h3 className="text-sm font-semibold text-[#211C17] dark:text-white">
              Security & Session
            </h3>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-[#71695F] dark:text-zinc-400">Auth Method</span>
              <Badge variant="default" size="sm">Bearer JWT</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#71695F] dark:text-zinc-400">Email Status</span>
              <Badge variant={user?.is_verified ? 'success' : 'warning'} size="sm">
                {user?.is_verified ? 'Verified' : 'Pending'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[#71695F] dark:text-zinc-400">Account ID</span>
              <span className="font-mono text-[10px] text-[#211C17] dark:text-zinc-300 truncate max-w-[120px]">
                {user?.id || '—'}
              </span>
            </div>
          </div>

          <div className="pt-3 border-t border-[rgba(90,70,50,0.10)] dark:border-white/[0.06]">
            <Button
              variant="destructive"
              size="sm"
              className="w-full justify-center"
              leftIcon={<LogOut className="w-3.5 h-3.5" />}
              onClick={() => logout()}
              isLoading={isLoggingOut}
            >
              Sign Out of Session
            </Button>
          </div>
        </GlassCard>
      </div>
    </div>
  )
}
