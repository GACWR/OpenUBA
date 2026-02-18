'use client'

import * as React from 'react'
import { useUIStore, CurrentUser } from '@/lib/state/ui-store'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface AuthContextValue {
  user: CurrentUser | null
  token: string | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  hasPermission: (page: string, access?: 'read' | 'write') => boolean
  authFetch: (url: string, init?: RequestInit) => Promise<Response>
}

const AuthContext = React.createContext<AuthContextValue | null>(null)

export function useAuth() {
  const ctx = React.useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { token, currentUser, setAuth, logout: storeLogout, hasPermission } = useUIStore()
  const [isLoading, setIsLoading] = React.useState(true)

  // validate token on mount
  React.useEffect(() => {
    if (!token) {
      setIsLoading(false)
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) {
          storeLogout()
        } else {
          const data = await res.json()
          setAuth(token, {
            id: data.id,
            username: data.username,
            role: data.role,
            email: data.email,
            display_name: data.display_name,
            permissions: data.permissions || {},
          })
        }
      } catch {
        storeLogout()
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const login = React.useCallback(async (username: string, password: string) => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)

    const res = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form.toString(),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'login failed' }))
      throw new Error(err.detail || 'login failed')
    }

    const data = await res.json()
    const newToken = data.access_token

    // fetch full user info with permissions
    const meRes = await fetch(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${newToken}` },
    })
    if (!meRes.ok) throw new Error('failed to fetch user info')
    const me = await meRes.json()

    setAuth(newToken, {
      id: me.id,
      username: me.username,
      role: me.role,
      email: me.email,
      display_name: me.display_name,
      permissions: me.permissions || {},
    })
  }, [setAuth])

  const logout = React.useCallback(() => {
    storeLogout()
  }, [storeLogout])

  const authFetch = React.useCallback(async (url: string, init?: RequestInit) => {
    const currentToken = useUIStore.getState().token
    const headers = new Headers(init?.headers)
    if (currentToken) {
      headers.set('Authorization', `Bearer ${currentToken}`)
    }
    const res = await fetch(url, { ...init, headers })
    if (res.status === 401) {
      storeLogout()
    }
    return res
  }, [storeLogout])

  const value = React.useMemo(() => ({
    user: currentUser,
    token,
    isLoading,
    login,
    logout,
    hasPermission,
    authFetch,
  }), [currentUser, token, isLoading, login, logout, hasPermission, authFetch])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
