import { useContext } from 'react'
import { ToastContext } from './ToastContext'

export interface ToastOptions {
  title: string
  description?: string
  variant?: 'default' | 'success' | 'error' | 'warning' | 'info'
}

export function useToast() {
  const context = useContext(ToastContext)

  const toastFn = (options: ToastOptions) => {
    const type = options.variant === 'default' ? 'info' : (options.variant || 'info')
    if (context?.addToast) {
      return context.addToast({
        title: options.title,
        description: options.description,
        type,
      })
    }
    return ''
  }

  return {
    toast: toastFn,
    addToast: context?.addToast || (() => ''),
    removeToast: context?.removeToast || (() => {}),
    success: context?.success || (() => ''),
    error: context?.error || (() => ''),
    warning: context?.warning || (() => ''),
    info: context?.info || (() => ''),
    toasts: context?.toasts || [],
  }
}
