import React from 'react'
import { Moon, Sun } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'

export function ThemeToggle({ className }: { className?: string }) {
  const { isDark, setTheme } = useTheme()

  return (
    <div
      role="group"
      aria-label="Color theme toggle"
      className={cn(
        'inline-flex items-center p-0.5 rounded-full border transition-all select-none',
        'bg-[#E9E1D7] border-[#C8BBA6] text-[#71695F]',
        'dark:bg-[#1A1C20] dark:border-[#2A2D33] dark:text-[#A1A1AA]',
        className,
      )}
    >
      <button
        type="button"
        onClick={() => setTheme('light')}
        aria-pressed={!isDark}
        className={cn(
          'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all duration-150 cursor-pointer',
          !isDark
            ? 'bg-[#FFFCF8] text-[#211C17] shadow-xs font-semibold'
            : 'hover:text-[#211C17] dark:hover:text-[#F5F5F5]',
        )}
      >
        <Sun className="w-3.5 h-3.5" />
        <span>Light</span>
      </button>

      <button
        type="button"
        onClick={() => setTheme('dark')}
        aria-pressed={isDark}
        className={cn(
          'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all duration-150 cursor-pointer',
          isDark
            ? 'bg-white/[0.14] text-[#F5F5F5] shadow-xs font-semibold'
            : 'hover:text-[#211C17] dark:hover:text-[#F5F5F5]',
        )}
      >
        <Moon className="w-3.5 h-3.5" />
        <span>Dark</span>
      </button>
    </div>
  )
}
