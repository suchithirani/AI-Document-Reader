import React, { useEffect, useRef, useState } from 'react'
import { cn } from '@/lib/utils'

interface DropdownContextType {
  isOpen: boolean
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>
  close: () => void
}

const DropdownContext = React.createContext<DropdownContextType | null>(null)

export function Dropdown({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const close = () => setIsOpen(false)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      document.addEventListener('keydown', handleKeyDown)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen])

  return (
    <DropdownContext.Provider value={{ isOpen, setIsOpen, close }}>
      <div ref={dropdownRef} className={cn('relative inline-block text-left', className)}>
        {children}
      </div>
    </DropdownContext.Provider>
  )
}

export function DropdownTrigger({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  const context = React.useContext(DropdownContext)
  if (!context) throw new Error('DropdownTrigger must be used within Dropdown')

  return (
    <div
      onClick={() => context.setIsOpen((prev) => !prev)}
      aria-haspopup="menu"
      aria-expanded={context.isOpen}
      className={cn('inline-flex items-center cursor-pointer select-none', className)}
    >
      {children}
    </div>
  )
}

export function DropdownMenu({
  children,
  align = 'right',
  className,
}: {
  children: React.ReactNode
  align?: 'left' | 'right' | 'center'
  className?: string
}) {
  const context = React.useContext(DropdownContext)
  if (!context) throw new Error('DropdownMenu must be used within Dropdown')

  if (!context.isOpen) return null

  const alignStyles = {
    left: 'left-0 origin-top-left',
    right: 'right-0 origin-top-right',
    center: 'left-1/2 -translate-x-1/2 origin-top',
  }

  return (
    <div
      role="menu"
      className={cn(
        'absolute z-50 mt-2 min-w-[180px] rounded-xl bg-[#0e0f16]/95 border border-white/[0.12]',
        'p-1.5 text-zinc-100 backdrop-blur-2xl shadow-2xl shadow-black/80',
        'animate-in fade-in zoom-in-95 duration-150',
        alignStyles[align],
        className,
      )}
    >
      {children}
    </div>
  )
}

export function DropdownItem({
  children,
  icon,
  destructive = false,
  disabled = false,
  onClick,
  className,
}: {
  children: React.ReactNode
  icon?: React.ReactNode
  destructive?: boolean
  disabled?: boolean
  onClick?: () => void
  className?: string
}) {
  const context = React.useContext(DropdownContext)

  const handleClick = () => {
    if (disabled) return
    onClick?.()
    context?.close()
  }

  return (
    <button
      type="button"
      role="menuitem"
      disabled={disabled}
      onClick={handleClick}
      className={cn(
        'w-full flex items-center gap-2 px-3 py-2 text-xs font-medium rounded-lg text-left transition-colors cursor-pointer select-none',
        destructive
          ? 'text-rose-300 hover:bg-rose-500/[0.12] hover:text-rose-200'
          : 'text-zinc-200 hover:bg-white/[0.08] hover:text-white',
        disabled && 'opacity-40 pointer-events-none',
        className,
      )}
    >
      {icon && <span className="shrink-0 text-current">{icon}</span>}
      <span className="truncate">{children}</span>
    </button>
  )
}

export function DropdownSeparator({ className }: { className?: string }) {
  return <div className={cn('my-1 h-px bg-white/[0.08]', className)} />
}
