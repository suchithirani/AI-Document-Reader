import React from 'react'
import { cn } from '@/lib/utils'

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  helperText?: string
  errorMessage?: string
  containerClassName?: string
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
      containerClassName,
      label,
      helperText,
      errorMessage,
      id,
      disabled,
      rows = 4,
      ...props
    },
    ref,
  ) => {
    const generatedId = React.useId()
    const textareaId = id || generatedId
    const helperId = `${textareaId}-helper`
    const errorId = `${textareaId}-error`

    const isInvalid = Boolean(errorMessage)

    return (
      <div className={cn('w-full space-y-1.5 text-left', containerClassName)}>
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-xs font-medium text-zinc-300 tracking-wide select-none"
          >
            {label}
          </label>
        )}

        <textarea
          ref={ref}
          id={textareaId}
          rows={rows}
          disabled={disabled}
          aria-invalid={isInvalid}
          aria-describedby={
            errorMessage ? errorId : helperText ? helperId : undefined
          }
          className={cn(
            'w-full px-3.5 py-2.5 rounded-xl text-sm text-zinc-100 placeholder:text-zinc-500',
            'bg-white/[0.04] hover:bg-white/[0.06] focus:bg-white/[0.07]',
            'border border-white/[0.1] hover:border-white/[0.16] focus:border-white/[0.3]',
            'focus:outline-none focus:ring-2 focus:ring-white/10',
            'backdrop-blur-md transition-all duration-150 resize-y min-h-[80px]',
            'disabled:opacity-40 disabled:pointer-events-none',
            isInvalid && 'border-rose-500/40 focus:border-rose-500/60 focus:ring-rose-500/10 text-rose-100',
            className,
          )}
          {...props}
        />

        {errorMessage ? (
          <p id={errorId} className="text-xs text-rose-400 font-medium">
            {errorMessage}
          </p>
        ) : helperText ? (
          <p id={helperId} className="text-xs text-zinc-500">
            {helperText}
          </p>
        ) : null}
      </div>
    )
  },
)

Textarea.displayName = 'Textarea'
