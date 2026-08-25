import React from 'react'
import { cn } from '@/lib/utils'

export interface SpinnerProps extends React.HTMLAttributes<HTMLSpanElement> {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  label?: string
  className?: string
}

export function Spinner({
  size = 'md',
  label = 'Loading...',
  className,
  ...props
}: SpinnerProps) {
  const sizeStyles = {
    xs: 'w-3 h-3 border-[1.5px]',
    sm: 'w-3.5 h-3.5 border-2',
    md: 'w-4.5 h-4.5 border-2',
    lg: 'w-6 h-6 border-2',
    xl: 'w-8 h-8 border-[2.5px]',
  }

  return (
    <span
      role="status"
      className={cn('inline-flex items-center gap-2', className)}
      {...props}
    >
      <span
        aria-hidden="true"
        className={cn(
          'rounded-full border-current border-t-transparent animate-spin inline-block',
          sizeStyles[size],
        )}
      />
      {label && <span className="sr-only">{label}</span>}
    </span>
  )
}
