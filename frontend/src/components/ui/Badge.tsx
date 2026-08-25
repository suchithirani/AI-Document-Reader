import React from 'react'
import { cn } from '@/lib/utils'

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?:
    | 'default'
    | 'subtle'
    | 'outline'
    | 'secondary'
    | 'success'
    | 'warning'
    | 'error'
  size?: 'sm' | 'md'
  icon?: React.ReactNode
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
  icon,
  className,
  ...props
}: BadgeProps) {
  const variantStyles = {
    default:
      'bg-[#EFE9E1] text-[#785D48] border border-[#E0D8CC] dark:bg-white/[0.08] dark:text-zinc-200 dark:border-white/[0.12]',
    subtle:
      'bg-[#FAF7F2] text-[#78716C] border border-[#E8E2D9] dark:bg-white/[0.03] dark:text-zinc-400 dark:border-white/[0.06]',
    outline:
      'bg-transparent text-[#78716C] border border-[#E0D8CC] dark:text-zinc-300 dark:border-white/[0.14]',
    secondary:
      'bg-[#231F1C] text-[#FFFCF8] dark:bg-white dark:text-zinc-950 font-medium',
    success:
      'bg-emerald-50 text-emerald-800 border border-emerald-200/80 dark:bg-emerald-500/10 dark:text-emerald-300 dark:border-emerald-500/25',
    warning:
      'bg-amber-50 text-amber-800 border border-amber-200/80 dark:bg-amber-500/10 dark:text-amber-300 dark:border-amber-500/25',
    error:
      'bg-rose-50 text-rose-800 border border-rose-200/80 dark:bg-rose-500/10 dark:text-rose-300 dark:border-rose-500/25',
  }

  const sizeStyles = {
    sm: 'h-5 px-2 text-[10px] gap-1 rounded-md font-mono',
    md: 'h-6 px-2.5 text-xs gap-1.5 rounded-lg font-medium',
  }

  return (
    <div
      className={cn(
        'inline-flex items-center justify-center select-none backdrop-blur-md transition-colors duration-150',
        variantStyles[variant],
        sizeStyles[size],
        className,
      )}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </div>
  )
}
