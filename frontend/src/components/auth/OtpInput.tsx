import React, { useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'

export interface OtpInputProps {
  length?: number
  value: string
  onChange: (value: string) => void
  onComplete?: (value: string) => void
  disabled?: boolean
  autoFocus?: boolean
  className?: string
}

export function OtpInput({
  length = 6,
  value,
  onChange,
  onComplete,
  disabled = false,
  autoFocus = true,
  className,
}: OtpInputProps) {
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  // Ensure refs array length matches length
  useEffect(() => {
    inputRefs.current = inputRefs.current.slice(0, length)
  }, [length])

  // Autofocus first input on mount
  useEffect(() => {
    if (autoFocus && inputRefs.current[0]) {
      inputRefs.current[0].focus()
    }
  }, [autoFocus])

  const digits = value.split('').slice(0, length)
  while (digits.length < length) {
    digits.push('')
  }

  const handleChange = (index: number, e: React.ChangeEvent<HTMLInputElement>) => {
    const rawVal = e.target.value
    const char = rawVal.replace(/\D/g, '').slice(-1)

    const newDigits = [...digits]
    newDigits[index] = char
    const newValue = newDigits.join('')
    onChange(newValue)

    if (char && index < length - 1) {
      inputRefs.current[index + 1]?.focus()
    }

    if (newValue.length === length && onComplete) {
      onComplete(newValue)
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace') {
      if (!digits[index] && index > 0) {
        inputRefs.current[index - 1]?.focus()
        const newDigits = [...digits]
        newDigits[index - 1] = ''
        onChange(newDigits.join(''))
      } else {
        const newDigits = [...digits]
        newDigits[index] = ''
        onChange(newDigits.join(''))
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      e.preventDefault()
      inputRefs.current[index - 1]?.focus()
    } else if (e.key === 'ArrowRight' && index < length - 1) {
      e.preventDefault()
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, length)
    if (!pastedData) return

    onChange(pastedData)

    const focusIndex = Math.min(pastedData.length, length - 1)
    inputRefs.current[focusIndex]?.focus()

    if (pastedData.length === length && onComplete) {
      onComplete(pastedData)
    }
  }

  return (
    <div className={cn('flex items-center justify-center gap-2 sm:gap-3 select-none', className)}>
      {Array.from({ length }, (_, i) => (
        <input
          key={i}
          ref={(el) => {
            inputRefs.current[i] = el
          }}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={1}
          disabled={disabled}
          value={digits[i]}
          onChange={(e) => handleChange(i, e)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          onPaste={handlePaste}
          onFocus={(e) => e.target.select()}
          aria-label={`Digit ${i + 1} of ${length}`}
          className={cn(
            'w-10 h-12 sm:w-12 sm:h-14 text-center text-lg sm:text-xl font-bold font-mono rounded-xl border transition-all',
            'bg-[rgba(255,255,255,0.60)] border-[rgba(90,70,50,0.18)] text-[#211C17]',
            'dark:bg-white/[0.05] dark:border-white/[0.12] dark:text-white',
            'focus:outline-none focus:ring-2 focus:ring-[#886F4E]/40 focus:border-[#886F4E] dark:focus:ring-white/30 dark:focus:border-white/40',
            'disabled:opacity-40 disabled:pointer-events-none',
            digits[i] ? 'border-[#886F4E] dark:border-white/40 shadow-2xs' : '',
          )}
        />
      ))}
    </div>
  )
}
