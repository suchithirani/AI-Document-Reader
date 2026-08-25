import { create } from 'zustand'
import type { AuthTokens, User } from '@/types/auth'
import { normalizeEntity } from '@/lib/utils'
import { getCurrentUser } from '@/api/auth'

interface AuthState {
  user: User | null
  tokens: AuthTokens | null
  isAuthenticated: boolean
  isInitialized: boolean
  isLoading: boolean
  setAuth: (user: User, tokens: AuthTokens) => void
  setTokens: (tokens: AuthTokens) => void
  clearAuth: () => void
  updateUser: (partialUser: Partial<User>) => void
  initializeAuth: () => Promise<void>
}

const getStoredTokens = (): AuthTokens | null => {
  try {
    const raw = localStorage.getItem('ai_doc_tokens')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

const getStoredUser = (): User | null => {
  try {
    const raw = localStorage.getItem('ai_doc_user')
    return raw ? (normalizeEntity(JSON.parse(raw)) as unknown as User) : null
  } catch {
    return null
  }
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: getStoredUser(),
  tokens: getStoredTokens(),
  isAuthenticated: Boolean(getStoredTokens()?.access_token),
  isInitialized: false,
  isLoading: false,

  setAuth: (user, tokens) => {
    const normalizedUser = normalizeEntity(user as unknown as Record<string, unknown>) as unknown as User
    try {
      localStorage.setItem('ai_doc_user', JSON.stringify(normalizedUser))
      localStorage.setItem('ai_doc_tokens', JSON.stringify(tokens))
    } catch {
      // Storage error ignored
    }
    set({
      user: normalizedUser,
      tokens,
      isAuthenticated: true,
      isInitialized: true,
      isLoading: false,
    })
  },

  setTokens: (tokens) => {
    try {
      localStorage.setItem('ai_doc_tokens', JSON.stringify(tokens))
    } catch {
      // Storage error ignored
    }
    set({
      tokens,
      isAuthenticated: Boolean(tokens?.access_token),
    })
  },

  clearAuth: () => {
    try {
      localStorage.removeItem('ai_doc_user')
      localStorage.removeItem('ai_doc_tokens')
    } catch {
      // Storage error ignored
    }
    set({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isInitialized: true,
      isLoading: false,
    })
  },

  updateUser: (partialUser) => {
    set((state) => {
      if (!state.user) return state
      const updated = { ...state.user, ...partialUser }
      const normalizedUser = normalizeEntity(updated as unknown as Record<string, unknown>) as unknown as User
      try {
        localStorage.setItem('ai_doc_user', JSON.stringify(normalizedUser))
      } catch {
        // Storage error ignored
      }
      return { user: normalizedUser }
    })
  },

  initializeAuth: async () => {
    const tokens = getStoredTokens()
    if (!tokens?.access_token) {
      set({
        user: null,
        tokens: null,
        isAuthenticated: false,
        isInitialized: true,
        isLoading: false,
      })
      return
    }

    set({ isLoading: true })

    try {
      const user = await getCurrentUser()
      set({
        user,
        tokens,
        isAuthenticated: true,
        isInitialized: true,
        isLoading: false,
      })
    } catch {
      get().clearAuth()
    }
  },
}))
