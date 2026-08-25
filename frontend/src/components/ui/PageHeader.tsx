import React from 'react'
import { Bell, Search } from 'lucide-react'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { ThemeToggle } from './ThemeToggle'

export interface PageHeaderProps {
  title: string
  description?: string
  badge?: React.ReactNode
  breadcrumbs?: React.ReactNode
  actions?: React.ReactNode
  showQuickActions?: boolean
  className?: string
}

export function PageHeader({
  title,
  description,
  badge,
  breadcrumbs,
  actions,
  showQuickActions = true,
  className,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        'w-full flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2',
        className,
      )}
    >
      <div className="space-y-1 text-left flex-1 min-w-0">
        {breadcrumbs && (
          <div className="text-xs text-[#9A9187] dark:text-zinc-500 font-medium mb-1">
            {breadcrumbs}
          </div>
        )}
        <div className="flex items-center gap-3">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-[#211C17] dark:text-[#F5F5F5]">
            {title}
          </h1>
          {badge && <div className="shrink-0">{badge}</div>}
        </div>
        {description && (
          <p className="text-xs md:text-sm text-[#71695F] dark:text-[#A1A1AA] max-w-2xl leading-relaxed">
            {description}
          </p>
        )}
      </div>

      <div className="flex items-center gap-3 shrink-0 self-start md:self-center">
        {actions}

        {showQuickActions && (
          <div className="hidden sm:flex items-center gap-2.5">
            {/* Search Input Bar */}
            <div className="relative flex items-center">
              <Search className="absolute left-3 w-3.5 h-3.5 text-[#9A9187] dark:text-zinc-400 pointer-events-none" />
              <input
                type="text"
                placeholder="Search..."
                className="h-8.5 w-40 md:w-48 pl-8.5 pr-3 rounded-xl text-xs bg-[rgba(255,255,255,0.60)] dark:bg-white/[0.05] border border-[rgba(90,70,50,0.14)] dark:border-white/[0.1] text-[#211C17] dark:text-zinc-100 placeholder:text-[#9A9187] dark:placeholder:text-zinc-500 focus:outline-none focus:ring-1 focus:ring-[#886F4E]/40 dark:focus:ring-white/30 backdrop-blur-md transition-all"
              />
            </div>

            <button
              type="button"
              aria-label="Notifications"
              className="p-2 rounded-xl text-[#71695F] hover:text-[#211C17] hover:bg-[#E9E1D7]/70 dark:text-zinc-400 dark:hover:text-white dark:hover:bg-white/[0.08] transition-colors cursor-pointer"
            >
              <Bell className="w-4 h-4" />
            </button>

            <Link
              to="/account"
              aria-label="User Account"
              className="w-8 h-8 rounded-full bg-[#E9E1D7] text-[#211C17] dark:bg-white/[0.1] dark:text-zinc-200 flex items-center justify-center text-xs font-semibold hover:ring-2 hover:ring-[#886F4E]/30 dark:hover:ring-white/30 transition-all"
            >
              U
            </Link>

            <ThemeToggle />
          </div>
        )}
      </div>
    </div>
  )
}
