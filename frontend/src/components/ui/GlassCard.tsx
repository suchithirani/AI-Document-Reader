import React from 'react'
import { cn } from '@/lib/utils'

export interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  variant?: 'subtle' | 'default' | 'elevated' | 'interactive'
  className?: string
}

export function GlassCard({
  children,
  variant = 'default',
  className,
  ...props
}: GlassCardProps) {
  const variantStyles = {
    subtle:
      'bg-[rgba(255,255,255,0.45)] border-[rgba(90,70,50,0.10)] dark:bg-[rgba(255,255,255,0.035)] dark:border-[rgba(255,255,255,0.06)] backdrop-blur-md',
    default:
      'bg-[rgba(255,255,255,0.60)] border-[rgba(90,70,50,0.14)] dark:bg-[rgba(255,255,255,0.055)] dark:border-[rgba(255,255,255,0.10)] backdrop-blur-md shadow-sm dark:shadow-xl dark:shadow-black/40',
    elevated:
      'bg-[rgba(255,255,255,0.85)] border-[rgba(90,70,50,0.18)] dark:bg-[rgba(255,255,255,0.085)] dark:border-[rgba(255,255,255,0.14)] backdrop-blur-lg shadow-md dark:shadow-2xl dark:shadow-black/60',
    interactive:
      'bg-[rgba(255,255,255,0.60)] border-[rgba(90,70,50,0.14)] hover:bg-[rgba(255,255,255,0.85)] hover:border-[rgba(90,70,50,0.24)] dark:bg-[rgba(255,255,255,0.055)] dark:border-[rgba(255,255,255,0.10)] dark:hover:bg-[rgba(255,255,255,0.09)] dark:hover:border-[rgba(255,255,255,0.18)] backdrop-blur-md transition-all duration-150 cursor-pointer shadow-xs dark:shadow-xl dark:shadow-black/30',
  }

  return (
    <div
      className={cn(
        'rounded-2xl border text-[#211C17] dark:text-[#F5F5F5] transition-colors duration-150',
        variantStyles[variant],
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}
