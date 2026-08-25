import React, { useState } from 'react'
import { cn } from '@/lib/utils'

export interface TooltipProps {
  content: React.ReactNode
  children: React.ReactNode
  position?: 'top' | 'bottom' | 'left' | 'right'
  className?: string
  delayMs?: number
}

export function Tooltip({
  content,
  children,
  position = 'top',
  className,
  delayMs = 150,
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [timeoutId, setTimeoutId] = useState<number | null>(null)

  const show = () => {
    const id = window.setTimeout(() => setIsVisible(true), delayMs)
    setTimeoutId(id)
  }

  const hide = () => {
    if (timeoutId) clearTimeout(timeoutId)
    setIsVisible(false)
  }

  const positionStyles = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  }

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {isVisible && (
        <div
          role="tooltip"
          className={cn(
            'absolute z-50 px-2.5 py-1 text-[11px] font-medium text-zinc-200 whitespace-nowrap',
            'bg-[#12131b]/90 border border-white/[0.12] rounded-lg backdrop-blur-xl shadow-xl shadow-black/60',
            'pointer-events-none animate-in fade-in zoom-in-95 duration-150',
            positionStyles[position],
            className,
          )}
        >
          {content}
        </div>
      )}
    </div>
  )
}
