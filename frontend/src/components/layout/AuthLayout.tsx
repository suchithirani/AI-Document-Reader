import React from 'react'
import { Link, Outlet } from 'react-router-dom'
import { GlassCard } from '@/components/ui/GlassCard'
import { ThemeToggle } from '@/components/ui/ThemeToggle'

export function AuthLayout() {
  return (
    <div className="min-h-screen bg-[#F7F3EE] dark:bg-[#08090B] text-[#211C17] dark:text-[#F5F5F5] flex flex-col items-center justify-center p-4 sm:p-6 relative overflow-hidden selection:bg-[#886F4E]/20 dark:selection:bg-white/20">
      {/* Top right theme toggle */}
      <div className="absolute top-4 right-4 z-20">
        <ThemeToggle />
      </div>

      {/* Background ambient lighting */}
      <div className="absolute top-[-10%] left-[20%] w-[500px] h-[500px] bg-[#886F4E]/[0.03] dark:bg-white/[0.02] rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[20%] w-[500px] h-[500px] bg-[#A68A6A]/[0.02] dark:bg-zinc-500/[0.02] rounded-full blur-[140px] pointer-events-none" />

      <div className="w-full max-w-md space-y-6 z-10">
        {/* Brand header */}
        <div className="text-center space-y-2">
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-2xl bg-[#EFE9E1] border border-[rgba(90,70,50,0.14)] dark:bg-white/[0.04] dark:border-white/[0.08] hover:bg-[#E8E0D5] dark:hover:bg-white/[0.08] transition-colors"
          >
            <div className="w-6 h-6 rounded-lg bg-[#886F4E] text-white dark:bg-[#A68A6A] dark:text-[#08090B] flex items-center justify-center font-bold text-xs">
              AI
            </div>
            <span className="text-sm font-semibold tracking-tight text-[#211C17] dark:text-white">
              AI Document Reader
            </span>
          </Link>
        </div>

        {/* Content Container */}
        <GlassCard variant="elevated" className="p-6 sm:p-8">
          <Outlet />
        </GlassCard>

        {/* Footer info */}
        <footer className="text-center text-xs text-[#9A9187] dark:text-zinc-500">
          Secure Multi-Provider Document Intelligence Platform
        </footer>
      </div>
    </div>
  )
}
