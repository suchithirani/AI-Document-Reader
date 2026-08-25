import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge Tailwind classes with clsx
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

/**
 * Normalizes backend MongoDB and Pydantic IDs.
 * Ensures `raw.id ?? raw._id` is consistently returned as a string id.
 */
export function normalizeId(raw: Record<string, unknown> | null | undefined): string {
  if (!raw || typeof raw !== 'object') return ''
  const idVal = raw.id ?? raw._id
  return idVal ? String(idVal) : ''
}

/**
 * Normalizes an entire entity object so that `id` is always present and string-typed.
 */
export function normalizeEntity<T extends Record<string, unknown>>(raw: T): T & { id: string } {
  if (!raw || typeof raw !== 'object') return raw as T & { id: string }
  const id = normalizeId(raw)
  return {
    ...raw,
    id,
  }
}

/**
 * Formats byte counts into human-readable file sizes
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

export const formatFileSize = formatBytes

/**
 * Formats ISO date string
 */
export function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  } catch {
    return dateString
  }
}
