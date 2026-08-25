import React, { useState } from 'react'
import { cn } from '@/lib/utils'

interface TabsContextType {
  activeTab: string
  setActiveTab: (value: string) => void
}

const TabsContext = React.createContext<TabsContextType | null>(null)

export function Tabs({
  defaultValue,
  value,
  onValueChange,
  children,
  className,
}: {
  defaultValue?: string
  value?: string
  onValueChange?: (value: string) => void
  children: React.ReactNode
  className?: string
}) {
  const [internalTab, setInternalTab] = useState(defaultValue || '')
  const activeTab = value !== undefined ? value : internalTab

  const setActiveTab = (val: string) => {
    if (value === undefined) {
      setInternalTab(val)
    }
    onValueChange?.(val)
  }

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={cn('w-full space-y-4', className)}>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabList({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div
      role="tablist"
      className={cn(
        'inline-flex items-center gap-1 p-1 rounded-xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-md',
        className,
      )}
    >
      {children}
    </div>
  )
}

export function TabTrigger({
  value,
  children,
  icon,
  className,
}: {
  value: string
  children: React.ReactNode
  icon?: React.ReactNode
  className?: string
}) {
  const context = React.useContext(TabsContext)
  if (!context) throw new Error('TabTrigger must be used within Tabs')

  const isActive = context.activeTab === value

  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      onClick={() => context.setActiveTab(value)}
      className={cn(
        'inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 cursor-pointer select-none',
        isActive
          ? 'bg-white/[0.1] text-white shadow-sm border border-white/[0.12] backdrop-blur-md'
          : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]',
        className,
      )}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </button>
  )
}

export function TabContent({
  value,
  children,
  className,
}: {
  value: string
  children: React.ReactNode
  className?: string
}) {
  const context = React.useContext(TabsContext)
  if (!context) throw new Error('TabContent must be used within Tabs')

  if (context.activeTab !== value) return null

  return (
    <div
      role="tabpanel"
      className={cn('animate-in fade-in duration-150', className)}
    >
      {children}
    </div>
  )
}
