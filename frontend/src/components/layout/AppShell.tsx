import React, { useEffect, useState } from 'react'
import { Link, Outlet } from 'react-router-dom'
import { Bell, Menu } from 'lucide-react'
import { Sidebar } from './Sidebar'
import { MobileBottomNav } from './MobileBottomNav'

export function AppShell() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // Prevent background scrolling when mobile drawer is open & handle Escape
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && mobileMenuOpen) {
        setMobileMenuOpen(false)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [mobileMenuOpen])

  return (
    <div className="min-h-screen bg-[#F7F3EE] dark:bg-[#08090B] text-[#211C17] dark:text-[#F5F5F5] flex flex-col lg:flex-row relative selection:bg-[#886F4E]/20 dark:selection:bg-white/20">
      {/* Background ambient lighting */}
      <div className="fixed top-[-10%] left-[20%] w-[500px] h-[500px] bg-[#886F4E]/[0.03] dark:bg-white/[0.015] rounded-full blur-[160px] pointer-events-none" />
      <div className="fixed bottom-[-10%] right-[10%] w-[600px] h-[600px] bg-[#A68A6A]/[0.02] dark:bg-zinc-500/[0.015] rounded-full blur-[180px] pointer-events-none" />

      {/* Desktop Persistent Sidebar with smooth width transition */}
      <div className="hidden lg:flex shrink-0 h-screen sticky top-0 z-30">
        <Sidebar
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        />
      </div>

      {/* Mobile Top Header */}
      <header className="lg:hidden sticky top-0 z-40 w-full flex items-center justify-between px-4 py-3 bg-[#FAF7F2]/90 dark:bg-[#08090B]/90 border-b border-[rgba(90,70,50,0.12)] dark:border-white/[0.08] backdrop-blur-xl">
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(true)}
            aria-label="Open mobile menu"
            className="p-1.5 rounded-xl text-[#71695F] hover:text-[#211C17] hover:bg-[#EFE9E1] dark:text-zinc-300 dark:hover:text-white dark:hover:bg-white/[0.08] transition-colors border border-[rgba(90,70,50,0.14)] dark:border-white/[0.08] cursor-pointer"
          >
            <Menu className="w-4 h-4" />
          </button>
          <span className="text-sm font-semibold tracking-tight text-[#211C17] dark:text-[#F5F5F5]">
            AI Document Reader
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            aria-label="Notifications"
            className="p-1.5 rounded-xl text-[#71695F] hover:text-[#211C17] dark:text-zinc-400 dark:hover:text-white transition-colors"
          >
            <Bell className="w-4 h-4" />
          </button>
          <Link
            to="/account"
            aria-label="Account profile"
            className="w-7 h-7 rounded-full bg-[#E9E1D7] text-[#211C17] dark:bg-white/[0.1] dark:text-zinc-200 flex items-center justify-center text-xs font-semibold"
          >
            U
          </Link>
        </div>
      </header>

      {/* Mobile Drawer Overlay & Sheet */}
      {mobileMenuOpen && (
        <div role="presentation" className="lg:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-xs transition-opacity duration-200 animate-in fade-in"
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          />

          {/* Sliding Sheet */}
          <div className="relative z-10 w-72 max-w-[85vw] h-full shadow-2xl transition-transform duration-200 ease-out animate-in slide-in-from-left">
            <Sidebar onCloseMobile={() => setMobileMenuOpen(false)} className="w-full" />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen z-10 overflow-x-hidden">
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-6 pb-20 lg:pb-8">
          <Outlet />
        </main>

        {/* Global Footer */}
        <footer className="text-center py-4 text-xs text-[#9A9187] dark:text-zinc-500 border-t border-[rgba(90,70,50,0.10)] dark:border-white/[0.06] mt-auto">
          © 2026 AI Document Reader. All rights reserved.
        </footer>
      </div>

      {/* Mobile Bottom Navigation Bar */}
      <MobileBottomNav />
    </div>
  )
}
