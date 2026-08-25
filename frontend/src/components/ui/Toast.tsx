import React, { useEffect, useState } from 'react'
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Info,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { ToastContext, type ToastItem } from './ToastContext'

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  const addToast = (toast: Omit<ToastItem, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast: ToastItem = { ...toast, id }
    setToasts((prev) => [...prev, newToast])
    return id
  }

  const success = (title: string, description?: string) =>
    addToast({ type: 'success', title, description })

  const error = (title: string, description?: string) =>
    addToast({ type: 'error', title, description })

  const info = (title: string, description?: string) =>
    addToast({ type: 'info', title, description })

  const warning = (title: string, description?: string) =>
    addToast({ type: 'warning', title, description })

  return (
    <ToastContext.Provider
      value={{
        toasts,
        addToast,
        removeToast,
        success,
        error,
        info,
        warning,
      }}
    >
      {children}
      <div
        aria-live="polite"
        className="fixed bottom-4 right-4 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none p-2 sm:p-0"
      >
        {toasts.map((toast) => (
          <ToastCard
            key={toast.id}
            toast={toast}
            onDismiss={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </ToastContext.Provider>
  )
}

function ToastCard({
  toast,
  onDismiss,
}: {
  toast: ToastItem
  onDismiss: () => void
}) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss()
    }, toast.durationMs || 4500)

    return () => clearTimeout(timer)
  }, [toast, onDismiss])

  const icons = {
    info: <Info className="w-4 h-4 text-zinc-300" />,
    success: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
    warning: <AlertTriangle className="w-4 h-4 text-amber-400" />,
    error: <AlertCircle className="w-4 h-4 text-rose-400" />,
  }

  const borders = {
    info: 'border-white/[0.12]',
    success: 'border-emerald-500/25',
    warning: 'border-amber-500/25',
    error: 'border-rose-500/25',
  }

  return (
    <div
      role="alert"
      className={cn(
        'pointer-events-auto flex items-start gap-3 p-4 rounded-xl text-zinc-100',
        'bg-[#0e1017]/95 border backdrop-blur-2xl shadow-2xl shadow-black/80',
        'transition-all duration-200 animate-in slide-in-from-bottom-2 fade-in',
        borders[toast.type],
      )}
    >
      <span className="shrink-0 mt-0.5">{icons[toast.type]}</span>
      <div className="flex-1 space-y-0.5">
        <h4 className="text-xs font-semibold text-white">{toast.title}</h4>
        {toast.description && (
          <p className="text-xs text-zinc-400 leading-relaxed">
            {toast.description}
          </p>
        )}
      </div>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss toast"
        className="shrink-0 p-1 text-zinc-400 hover:text-white rounded-md hover:bg-white/[0.08] transition-colors cursor-pointer"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}
