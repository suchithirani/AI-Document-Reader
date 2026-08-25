import { createContext } from 'react'

export type ToastType = 'info' | 'success' | 'warning' | 'error'

export interface ToastItem {
  id: string
  type: ToastType
  title: string
  description?: string
  durationMs?: number
}

export interface ToastContextType {
  toasts: ToastItem[]
  addToast: (toast: Omit<ToastItem, 'id'>) => string
  removeToast: (id: string) => void
  success: (title: string, description?: string) => string
  error: (title: string, description?: string) => string
  info: (title: string, description?: string) => string
  warning: (title: string, description?: string) => string
}

export const ToastContext = createContext<ToastContextType | null>(null)
