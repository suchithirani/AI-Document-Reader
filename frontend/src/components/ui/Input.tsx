import React from 'react'
import { cn } from '@/lib/utils'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  helperText?: string
  errorMessage?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  containerClassName?: string
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      containerClassName,
      label,
      helperText,
      errorMessage,
      leftIcon,
      rightIcon,
      id,
      disabled,
      ...props
    },
    ref,
  ) => {
    const generatedId = React.useId()
    const inputId = id || generatedId
    const helperId = `${inputId}-helper`
    const errorId = `${inputId}-error`

    const isInvalid = Boolean(errorMessage)

    return (
      <div className={cn('w-full space-y-1.5 text-left', containerClassName)}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-medium text-[#78716C] dark:text-zinc-300 tracking-wide select-none"
          >
            {label}
          </label>
        )}

        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3 flex items-center pointer-events-none text-[#A8A29E] dark:text-zinc-400">
              {leftIcon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            aria-invalid={isInvalid}
            aria-describedby={
              errorMessage ? errorId : helperText ? helperId : undefined
            }
            className={cn(
              'w-full h-10 px-3.5 rounded-xl text-sm text-[#1C1917] dark:text-zinc-100 placeholder:text-[#A8A29E] dark:placeholder:text-zinc-500',
              'bg-[#FFFCF8] hover:bg-[#FFFFFF] focus:bg-[#FFFFFF] dark:bg-white/[0.04] dark:hover:bg-white/[0.06] dark:focus:bg-white/[0.07]',
              'border border-[#E0D8CC] hover:border-[#CFC4B4] focus:border-[#785D48] dark:border-white/[0.1] dark:hover:border-white/[0.16] dark:focus:border-white/[0.3]',
              'focus:outline-none focus:ring-2 focus:ring-[#785D48]/10 dark:focus:ring-white/10',
              'backdrop-blur-md transition-all duration-150',
              'disabled:opacity-40 disabled:pointer-events-none',
              leftIcon && 'pl-9',
              rightIcon && 'pr-9',
              isInvalid && 'border-rose-500/40 focus:border-rose-500/60 focus:ring-rose-500/10 text-rose-700 dark:text-rose-100',
              className,
            )}
            {...props}
          />

          {rightIcon && (
            <div className="absolute right-3 flex items-center text-[#A8A29E] dark:text-zinc-400">
              {rightIcon}
            </div>
          )}
        </div>

        {errorMessage ? (
          <p id={errorId} className="text-xs text-rose-500 dark:text-rose-400 font-medium">
            {errorMessage}
          </p>
        ) : helperText ? (
          <p id={helperId} className="text-xs text-[#A8A29E] dark:text-zinc-500">
            {helperText}
          </p>
        ) : null}
      </div>
    )
  },
)

Input.displayName = 'Input'
