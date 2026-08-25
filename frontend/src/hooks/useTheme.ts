import { useThemeStore } from '@/stores/themeStore'

export function useTheme() {
  const theme = useThemeStore((state) => state.theme)
  const setTheme = useThemeStore((state) => state.setTheme)
  const toggleTheme = useThemeStore((state) => state.toggleTheme)
  const initializeTheme = useThemeStore((state) => state.initializeTheme)

  return {
    theme,
    isDark: theme === 'dark',
    isLight: theme === 'light',
    setTheme,
    toggleTheme,
    initializeTheme,
  }
}
