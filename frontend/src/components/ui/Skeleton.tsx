import React from 'react'
import { cn } from '@/lib/utils'

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'rectangular' | 'circular' | 'rounded'
}

export function Skeleton({
  className,
  variant = 'rounded',
  ...props
}: SkeletonProps) {
  const variantStyles = {
    rectangular: 'rounded-none',
    circular: 'rounded-full',
    rounded: 'rounded-xl',
  }

  return (
    <div
      aria-hidden="true"
      className={cn(
        'bg-white/[0.04] border border-white/[0.05] animate-pulse',
        variantStyles[variant],
        className,
      )}
      {...props}
    />
  )
}
