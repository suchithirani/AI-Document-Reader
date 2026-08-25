import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  ChevronLeft,
  ChevronRight,
  FileText,
  FolderKanban,
  LayoutDashboard,
  LogOut,
  MessageSquareQuote,
  Settings,
  Sparkles,
  User,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Tooltip } from '@/components/ui/Tooltip'
import { useAuth } from '@/hooks/useAuth'

export interface SidebarProps {
  isCollapsed?: boolean
  onToggleCollapse?: () => void
  onCloseMobile?: () => void
  className?: string
}

const navItems = [
  {
    name: 'Dashboard',
    path: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    name: 'Documents',
    path: '/documents',
    icon: FileText,
  },
  {
    name: 'Collections',
    path: '/collections',
    icon: FolderKanban,
  },
  {
    name: 'Chat & RAG',
    path: '/chat',
    icon: MessageSquareQuote,
  },
  {
    name: 'Account',
    path: '/account',
    icon: User,
  },
]

export function Sidebar({
  isCollapsed = false,
  onToggleCollapse,
  onCloseMobile,
  className,
}: SidebarProps) {
  const { user, logout, isLoggingOut } = useAuth()

  const userInitial = user?.name ? user.name.charAt(0).toUpperCase() : user?.email ? user.email.charAt(0).toUpperCase() : 'U'
  const userRole = user?.role ? `${user.role.toUpperCase()} Plan` : 'Standard Plan'
  const userEmail = user?.email || 'user@workspace.ai'

  return (
    <aside
      className={cn(
        'h-full flex flex-col justify-between p-3 select-none transition-[width] duration-200 ease-in-out',
        'bg-[#FAF7F2]/95 border-r border-[rgba(90,70,50,0.12)] text-[#211C17]',
        'dark:bg-[#08090B]/95 dark:border-r dark:border-white/[0.08] dark:text-[#F5F5F5]',
        'backdrop-blur-xl',
        isCollapsed ? 'w-[72px]' : 'w-64',
        className,
      )}
    >
      {/* Top section: Brand & Navigation */}
      <div className="space-y-5">
        {/* Brand & Collapse Header Area */}
        {isCollapsed ? (
          <div className="flex flex-col items-center gap-2 pt-1 pb-1">
            <Tooltip content="AI Document Reader (Enterprise)" position="right">
              <div className="w-8 h-8 rounded-xl bg-[#886F4E] text-white dark:bg-[#A68A6A] dark:text-[#08090B] flex items-center justify-center font-bold text-xs shrink-0 shadow-xs">
                <Sparkles className="w-4 h-4" />
              </div>
            </Tooltip>

            {onToggleCollapse && (
              <Tooltip content="Expand sidebar" position="right">
                <button
                  type="button"
                  onClick={onToggleCollapse}
                  aria-label="Expand sidebar"
                  className="p-1.5 rounded-lg text-[#71695F] hover:text-[#211C17] hover:bg-[#E9E1D7] dark:text-zinc-400 dark:hover:text-white dark:hover:bg-white/[0.08] transition-colors cursor-pointer"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </Tooltip>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-between px-1.5 pt-1 pb-1">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-xl bg-[#886F4E] text-white dark:bg-[#A68A6A] dark:text-[#08090B] flex items-center justify-center font-bold text-xs shrink-0 shadow-xs">
                <Sparkles className="w-4 h-4" />
              </div>
              <div className="space-y-0.5 min-w-0 truncate text-left">
                <span className="text-sm font-semibold tracking-tight text-[#211C17] dark:text-[#F5F5F5] block truncate">
                  AI Doc Reader
                </span>
                <span className="text-[10px] font-sans text-[#9A9187] dark:text-zinc-500 block">
                  Enterprise
                </span>
              </div>
            </div>

            {/* Desktop collapse toggle */}
            {onToggleCollapse && !onCloseMobile && (
              <button
                type="button"
                onClick={onToggleCollapse}
                aria-label="Collapse sidebar"
                className="hidden lg:flex p-1.5 rounded-lg text-[#71695F] hover:text-[#211C17] hover:bg-[#E9E1D7] dark:text-zinc-400 dark:hover:text-white dark:hover:bg-white/[0.08] transition-colors cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            )}

            {/* Mobile close button */}
            {onCloseMobile && (
              <button
                type="button"
                onClick={onCloseMobile}
                aria-label="Close navigation"
                className="lg:hidden p-1.5 rounded-lg text-[#71695F] hover:text-[#211C17] hover:bg-[#EFE9E1] dark:text-zinc-400 dark:hover:text-white dark:hover:bg-white/[0.08] transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        )}

        {/* Navigation Links */}
        <nav aria-label="Main Navigation" className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const linkContent = (
              <NavLink
                to={item.path}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-xl text-xs md:text-sm font-medium transition-colors duration-150',
                    isCollapsed
                      ? 'justify-center p-2.5 w-11 h-11 mx-auto'
                      : 'px-3 py-2.5 w-full',
                    isActive
                      ? 'bg-[#E9E1D7] text-[#211C17] border border-[#C8BBA6] dark:bg-[#1A1C20] dark:text-[#F5F5F5] dark:border-[#2A2D33] font-semibold shadow-2xs'
                      : 'text-[#71695F] hover:text-[#211C17] hover:bg-[#EFE9E1]/70 dark:text-[#A1A1AA] dark:hover:text-[#F5F5F5] dark:hover:bg-white/[0.04] border border-transparent',
                  )
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                {!isCollapsed && <span className="truncate">{item.name}</span>}
              </NavLink>
            )

            if (isCollapsed) {
              return (
                <Tooltip key={item.path} content={item.name} position="right">
                  {linkContent}
                </Tooltip>
              )
            }

            return <React.Fragment key={item.path}>{linkContent}</React.Fragment>
          })}
        </nav>
      </div>

      {/* Bottom section: User Card & Sign Out */}
      <div className="pt-3 border-t border-[rgba(90,70,50,0.12)] dark:border-white/[0.08] space-y-2">
        {/* User preview card */}
        {isCollapsed ? (
          <div className="flex flex-col items-center gap-2">
            <Tooltip content={`${userEmail} (${userRole})`} position="right">
              <div className="w-8 h-8 rounded-full bg-[#E9E1D7] text-[#211C17] dark:bg-white/[0.08] dark:text-zinc-200 dark:border dark:border-white/[0.12] flex items-center justify-center text-xs font-semibold cursor-pointer">
                {userInitial}
              </div>
            </Tooltip>

            <Tooltip content="Sign Out" position="right">
              <button
                type="button"
                onClick={() => logout()}
                disabled={isLoggingOut}
                aria-label="Sign Out"
                className="p-1.5 rounded-lg text-[#71695F] hover:text-rose-600 hover:bg-rose-500/[0.08] dark:text-zinc-400 dark:hover:text-rose-300 dark:hover:bg-rose-500/[0.06] transition-colors cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </Tooltip>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between p-2 rounded-xl border bg-[rgba(255,255,255,0.60)] border-[rgba(90,70,50,0.14)] dark:bg-[rgba(255,255,255,0.05)] dark:border-white/[0.08] transition-colors">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-full bg-[#E9E1D7] text-[#211C17] dark:bg-white/[0.08] dark:text-zinc-200 dark:border dark:border-white/[0.12] flex items-center justify-center text-xs font-semibold shrink-0">
                  {userInitial}
                </div>
                <div className="flex-1 min-w-0 truncate text-left">
                  <p className="text-xs font-medium text-[#211C17] dark:text-[#F5F5F5] truncate">
                    {userEmail}
                  </p>
                  <p className="text-[10px] text-[#9A9187] dark:text-zinc-500 font-sans">
                    {userRole}
                  </p>
                </div>
              </div>

              <NavLink
                to="/account"
                aria-label="Account Settings"
                className="p-1 rounded-lg text-[#71695F] hover:text-[#211C17] hover:bg-[#EFE9E1] dark:text-zinc-400 dark:hover:text-white dark:hover:bg-white/[0.08] transition-colors"
              >
                <Settings className="w-3.5 h-3.5" />
              </NavLink>
            </div>

            <button
              type="button"
              onClick={() => logout()}
              disabled={isLoggingOut}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium transition-colors text-[#71695F] hover:text-rose-600 hover:bg-rose-500/[0.08] dark:text-zinc-400 dark:hover:text-rose-300 dark:hover:bg-rose-500/[0.06] cursor-pointer select-none"
            >
              <LogOut className="w-3.5 h-3.5 shrink-0" />
              <span>{isLoggingOut ? 'Signing out...' : 'Sign Out'}</span>
            </button>
          </>
        )}
      </div>
    </aside>
  )
}
