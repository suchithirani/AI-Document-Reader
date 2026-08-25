import React from 'react'
import { cn } from '@/lib/utils'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'glass' | 'solid' | 'subtle' | 'outline' | 'interactive'
}

export function Card({
  className,
  variant = 'glass',
  children,
  ...props
}: CardProps) {
  const variantStyles = {
    glass:
      'bg-[#FFFCF8]/90 border border-[#E8E2D9] dark:bg-white/[0.04] dark:border-white/[0.08] backdrop-blur-xl shadow-xl shadow-stone-900/5 dark:shadow-2xl dark:shadow-black/40',
    solid:
      'bg-[#FFFCF8] border border-[#E8E2D9] dark:bg-[#0d0e14] dark:border-white/[0.08] shadow-md dark:shadow-2xl dark:shadow-black/60',
    subtle:
      'bg-[#FFFCF8]/60 border border-[#EFE9E1] dark:bg-white/[0.02] dark:border-white/[0.05] backdrop-blur-md',
    outline:
      'bg-transparent border border-[#E8E2D9] dark:border-white/[0.12]',
    interactive:
      'bg-[#FFFCF8]/90 border border-[#E8E2D9] hover:bg-[#FFFFFF] hover:border-[#D6CEC2] dark:bg-white/[0.04] dark:border-white/[0.08] dark:hover:bg-white/[0.07] dark:hover:border-white/[0.16] backdrop-blur-xl transition-all duration-200 cursor-pointer shadow-sm dark:shadow-xl dark:shadow-black/30',
  }

  return (
    <div
      className={cn(
        'rounded-2xl text-[#1C1917] dark:text-zinc-100 overflow-hidden transition-colors duration-150',
        variantStyles[variant],
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex flex-col space-y-1.5 p-6 pb-4', className)}
      {...props}
    />
  )
}

export function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        'text-base md:text-lg font-semibold tracking-tight text-[#1C1917] dark:text-zinc-100',
        className,
      )}
      {...props}
    />
  )
}

export function CardDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn('text-xs md:text-sm text-[#78716C] dark:text-zinc-400 leading-relaxed', className)}
      {...props}
    />
  )
}

export function CardContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('p-6 pt-0', className)} {...props} />
}

export function CardFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex items-center p-6 pt-0 border-t border-[#E8E2D9] dark:border-white/[0.06] mt-4 pt-4', className)}
      {...props}
    />
  )
}
