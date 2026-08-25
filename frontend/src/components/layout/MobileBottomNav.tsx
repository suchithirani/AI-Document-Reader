import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  FileText,
  FolderKanban,
  LayoutDashboard,
  MessageSquareQuote,
  User,
} from 'lucide-react'
import { cn } from '@/lib/utils'

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
    name: 'Chat',
    path: '/chat',
    icon: MessageSquareQuote,
  },
  {
    name: 'Account',
    path: '/account',
    icon: User,
  },
]

export function MobileBottomNav() {
  const location = useLocation()

  // On the chat page, hide or minimize the bottom bar so it never covers the composer
  const isChat = location.pathname === '/chat'

  if (isChat) return null

  return (
    <nav
      aria-label="Mobile Navigation"
      className="lg:hidden fixed bottom-0 left-0 right-0 z-30 px-3 py-2 bg-[#FAF7F2]/95 dark:bg-[#08090e]/95 border-t border-[#E8E2D9] dark:border-white/[0.08] backdrop-blur-xl"
    >
      <div className="flex items-center justify-around max-w-md mx-auto">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  'flex flex-col items-center gap-1 py-1 px-2.5 rounded-xl text-[10px] font-medium transition-all select-none',
                  isActive
                    ? 'bg-[#231F1C] text-white dark:bg-white/[0.15] dark:text-white shadow-sm'
                    : 'text-[#78716C] hover:text-[#1C1917] dark:text-zinc-400 dark:hover:text-white',
                )
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="truncate">{item.name}</span>
            </NavLink>
          )
        })}
      </div>
    </nav>
  )
}
