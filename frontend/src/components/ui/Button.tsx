import React from 'react'
import { cn } from '@/lib/utils'
import { Spinner } from './Spinner'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive'
  size?: 'sm' | 'md' | 'lg' | 'icon'
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      disabled,
      children,
      type = 'button',
      ...props
    },
    ref,
  ) => {
    const baseStyles =
      'relative inline-flex items-center justify-center font-medium transition-all duration-150 active:scale-[0.98] select-none cursor-pointer rounded-xl disabled:pointer-events-none disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#886F4E]/40 dark:focus-visible:ring-white/30 focus-visible:ring-offset-2 focus-visible:ring-offset-[#F7F3EE] dark:focus-visible:ring-offset-[#08090B]'

    const variantStyles = {
      primary:
        'bg-[#886F4E] text-white hover:bg-[#745B3C] dark:bg-[#A68A6A] dark:text-[#08090B] dark:hover:bg-[#B89C7D] border border-transparent font-medium shadow-sm',
      secondary:
        'bg-[#FFFCF8] text-[#211C17] hover:bg-[#FFFFFF] border border-[rgba(90,70,50,0.18)] dark:bg-white/[0.06] dark:text-zinc-100 dark:hover:bg-white/[0.1] dark:hover:text-white dark:border-white/[0.1] backdrop-blur-md shadow-xs',
      outline:
        'bg-transparent text-[#211C17] hover:bg-[#E9E1D7]/50 border border-[rgba(90,70,50,0.18)] dark:text-zinc-200 dark:hover:bg-white/[0.05] dark:hover:text-white dark:border-white/[0.14]',
      ghost:
        'bg-transparent text-[#71695F] hover:bg-[#E9E1D7]/60 hover:text-[#211C17] dark:text-zinc-400 dark:hover:bg-white/[0.06] dark:hover:text-white',
      destructive:
        'bg-rose-500/[0.08] text-rose-600 dark:text-rose-400 hover:bg-rose-500/[0.16] border border-rose-500/20',
    }

    const sizeStyles = {
      sm: 'h-8 px-3 text-xs gap-1.5 rounded-lg',
      md: 'h-9 px-4 text-xs md:text-sm gap-2 rounded-xl',
      lg: 'h-11 px-5 text-sm md:text-base gap-2.5 rounded-xl',
      icon: 'h-9 w-9 p-0 rounded-xl',
    }

    const isDisabled = disabled || isLoading

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        aria-disabled={isDisabled}
        className={cn(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          isLoading && 'text-transparent hover:text-transparent',
          className,
        )}
        {...props}
      >
        {isLoading && (
          <span className="absolute inset-0 flex items-center justify-center text-current">
            <Spinner
              size={size === 'sm' ? 'sm' : 'md'}
              className={variant === 'primary' ? 'text-white dark:text-[#08090B]' : 'text-zinc-600 dark:text-zinc-200'}
            />
          </span>
        )}
        {!isLoading && leftIcon && <span className="shrink-0">{leftIcon}</span>}
        <span>{children}</span>
        {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    )
  },
)

Button.displayName = 'Button'
