import React, { useState } from 'react'
import { Eye, EyeOff, Lock } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface PasswordInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string
  error?: string
  helperText?: string
  showStrengthMeter?: boolean
}

export const PasswordInput = React.forwardRef<HTMLInputElement, PasswordInputProps>(
  (
    {
      label,
      error,
      helperText,
      showStrengthMeter = false,
      value = '',
      className,
      id,
      ...props
    },
    ref,
  ) => {
    const [showPassword, setShowPassword] = useState(false)
    const generatedId = React.useId()
    const inputId = id || generatedId

    const passwordStr = String(value)
    const hasMinLength = passwordStr.length >= 8
    const hasNumberOrSpecial = /[0-9!@#$%^&*(),.?":{}|<>]/.test(passwordStr)
    const hasUpperLower = /[a-z]/.test(passwordStr) && /[A-Z]/.test(passwordStr)

    let strengthScore = 0
    if (hasMinLength) strengthScore += 1
    if (hasNumberOrSpecial) strengthScore += 1
    if (hasUpperLower) strengthScore += 1

    return (
      <div className="w-full space-y-1.5 text-left">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-medium text-[#71695F] dark:text-zinc-300 tracking-wide select-none"
          >
            {label}
          </label>
        )}

        <div className="relative flex items-center">
          <div className="absolute left-3 flex items-center pointer-events-none text-[#9A9187] dark:text-zinc-500">
            <Lock className="w-4 h-4" />
          </div>

          <input
            ref={ref}
            id={inputId}
            type={showPassword ? 'text' : 'password'}
            value={value}
            className={cn(
              'w-full h-10 pl-9.5 pr-10 rounded-xl text-sm font-medium transition-all duration-150',
              'bg-[#FFFCF8] hover:bg-[#FFFFFF] focus:bg-[#FFFFFF] dark:bg-white/[0.04] dark:hover:bg-white/[0.06] dark:focus:bg-white/[0.07]',
              'border border-[rgba(90,70,50,0.18)] hover:border-[rgba(90,70,50,0.28)] focus:border-[#886F4E] dark:border-white/[0.1] dark:hover:border-white/[0.16] dark:focus:border-white/[0.3]',
              'text-[#211C17] dark:text-zinc-100 placeholder:text-[#9A9187] dark:placeholder:text-zinc-500',
              'focus:outline-none focus:ring-2 focus:ring-[#886F4E]/20 dark:focus:ring-white/10 backdrop-blur-md',
              'disabled:opacity-40 disabled:pointer-events-none',
              error && 'border-rose-500/50 focus:border-rose-500 focus:ring-rose-500/10',
              className,
            )}
            {...props}
          />

          <button
            type="button"
            onClick={() => setShowPassword((prev) => !prev)}
            tabIndex={-1}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            className="absolute right-2.5 p-1 rounded-lg text-[#9A9187] hover:text-[#211C17] dark:text-zinc-400 dark:hover:text-white transition-colors cursor-pointer"
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>

        {/* Password Strength Meter */}
        {showStrengthMeter && passwordStr.length > 0 && (
          <div className="pt-1 space-y-1">
            <div className="grid grid-cols-3 gap-1.5 h-1">
              <div
                className={cn(
                  'rounded-full transition-all duration-200',
                  strengthScore >= 1 ? 'bg-amber-500' : 'bg-zinc-200 dark:bg-zinc-800',
                )}
              />
              <div
                className={cn(
                  'rounded-full transition-all duration-200',
                  strengthScore >= 2 ? 'bg-amber-500' : 'bg-zinc-200 dark:bg-zinc-800',
                )}
              />
              <div
                className={cn(
                  'rounded-full transition-all duration-200',
                  strengthScore >= 3 ? 'bg-emerald-500' : 'bg-zinc-200 dark:bg-zinc-800',
                )}
              />
            </div>
            <p className="text-[10px] text-[#9A9187] dark:text-zinc-500">
              {strengthScore === 3
                ? 'Strong password'
                : strengthScore === 2
                  ? 'Moderate (add numbers or symbols)'
                  : 'Weak (must be at least 8 characters)'}
            </p>
          </div>
        )}

        {error && <p className="text-xs text-rose-500 text-left">{error}</p>}
        {!error && helperText && (
          <p className="text-xs text-[#9A9187] dark:text-zinc-500 text-left">{helperText}</p>
        )}
      </div>
    )
  },
)

PasswordInput.displayName = 'PasswordInput'
