import React from 'react'
import { cn } from '@/lib/utils'

export interface IconButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'ghost' | 'glass' | 'primary'
  size?: 'sm' | 'md' | 'lg'
  icon: React.ReactNode
  'aria-label': string
}

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      className,
      variant = 'ghost',
      size = 'md',
      icon,
      disabled,
      type = 'button',
      ...props
    },
    ref,
  ) => {
    const sizeStyles = {
      sm: 'w-7 h-7 p-1 rounded-lg text-xs',
      md: 'w-8.5 h-8.5 p-1.5 rounded-xl text-sm',
      lg: 'w-10 h-10 p-2 rounded-xl text-base',
    }

    const variantStyles = {
      default:
        'bg-[#FFFCF8] text-[#211C17] border border-[rgba(90,70,50,0.14)] hover:bg-white dark:bg-white/[0.06] dark:text-zinc-100 dark:border-white/[0.1] dark:hover:bg-white/[0.1]',
      ghost:
        'bg-transparent text-[#71695F] hover:text-[#211C17] hover:bg-[#E9E1D7]/60 dark:text-zinc-400 dark:hover:text-white dark:hover:bg-white/[0.08]',
      glass:
        'bg-[rgba(255,255,255,0.60)] border border-[rgba(90,70,50,0.14)] text-[#211C17] hover:bg-[rgba(255,255,255,0.85)] dark:bg-white/[0.05] dark:border-white/[0.1] dark:text-zinc-200 dark:hover:bg-white/[0.1] backdrop-blur-md',
      primary:
        'bg-[#886F4E] text-white hover:bg-[#745B3C] dark:bg-[#A68A6A] dark:text-[#08090B] dark:hover:bg-[#B89C7D]',
    }

    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled}
        className={cn(
          'inline-flex items-center justify-center transition-all duration-150 active:scale-95 disabled:opacity-40 disabled:pointer-events-none cursor-pointer',
          sizeStyles[size],
          variantStyles[variant],
          className,
        )}
        {...props}
      >
        {icon}
      </button>
    )
  },
)

IconButton.displayName = 'IconButton'
