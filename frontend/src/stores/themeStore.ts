import { create } from 'zustand'

export type ThemeMode = 'light' | 'dark'

interface ThemeState {
  theme: ThemeMode
  setTheme: (theme: ThemeMode) => void
  toggleTheme: () => void
  initializeTheme: () => void
}

export const getInitialTheme = (): ThemeMode => {
  if (typeof window === 'undefined') return 'light'
  try {
    const saved = localStorage.getItem('ai_doc_theme') as ThemeMode | null
    if (saved === 'light' || saved === 'dark') return saved
    if (
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-color-scheme: dark)').matches
    ) {
      return 'dark'
    }
  } catch {
    // Fallback to light
  }
  return 'light'
}

export const applyThemeToDOM = (theme: ThemeMode) => {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  root.setAttribute('data-theme', theme)
  if (theme === 'dark') {
    root.classList.add('dark')
    root.classList.remove('light')
  } else {
    root.classList.add('light')
    root.classList.remove('dark')
  }
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: getInitialTheme(),

  setTheme: (theme) => {
    applyThemeToDOM(theme)
    try {
      localStorage.setItem('ai_doc_theme', theme)
    } catch {
      // Ignore
    }
    set({ theme })
  },

  toggleTheme: () => {
    const nextTheme = get().theme === 'dark' ? 'light' : 'dark'
    get().setTheme(nextTheme)
  },

  initializeTheme: () => {
    const currentTheme = getInitialTheme()
    applyThemeToDOM(currentTheme)
    set({ theme: currentTheme })
  },
}))
