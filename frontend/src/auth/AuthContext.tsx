import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type { AuthUser } from '../api/types'

type AuthState = {
  enabled: boolean
  loading: boolean
  user: AuthUser | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  canOperate: boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [enabled, setEnabled] = useState(true)
  const [loading, setLoading] = useState(true)
  const [user, setUser] = useState<AuthUser | null>(null)

  useEffect(() => {
    api.authConfig().then(async ({ enabled: active }) => {
      setEnabled(active)
      if (active) setUser(await api.me().catch(() => null))
      else setUser({ username: 'local-admin', role: 'admin', kind: 'user' })
    }).finally(() => setLoading(false))
  }, [])

  const login = async (username: string, password: string) => setUser(await api.login(username, password))
  const logout = async () => { await api.logout(); setUser(null) }
  return <AuthContext.Provider value={{ enabled, loading, user, login, logout, canOperate: user?.role === 'analyst' || user?.role === 'admin', isAdmin: user?.role === 'admin' }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used within AuthProvider')
  return value
}
