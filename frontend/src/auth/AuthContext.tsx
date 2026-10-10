import { createContext, use, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { setSessionExpiredHandler } from '../api/client'
import { authApi } from '../api/endpoints'
import { tokenStore } from '../api/tokens'
import type { RegisterInput, User } from '../api/types'

type AuthState = { status: 'loading' } | { status: 'anonymous' } | { status: 'authenticated'; user: User }

interface AuthContextValue {
  state: AuthState
  login: (email: string, password: string) => Promise<void>
  register: (input: RegisterInput) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(() =>
    tokenStore.get() ? { status: 'loading' } : { status: 'anonymous' },
  )

  useEffect(() => {
    setSessionExpiredHandler(() => setState({ status: 'anonymous' }))
  }, [])

  // Restore the session from stored tokens on first load.
  useEffect(() => {
    if (!tokenStore.get()) return
    authApi.profile().then(
      (user) => setState({ status: 'authenticated', user }),
      () => {
        tokenStore.clear()
        setState({ status: 'anonymous' })
      },
    )
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const session = await authApi.login(email, password)
    tokenStore.set(session.token)
    setState({ status: 'authenticated', user: session.user })
  }, [])

  const register = useCallback(
    async (input: RegisterInput) => {
      await authApi.register(input)
      await login(input.email, input.password)
    },
    [login],
  )

  const logout = useCallback(async () => {
    const refresh = tokenStore.get()?.refresh
    try {
      if (refresh) await authApi.logout(refresh)
    } catch {
      // The local session ends regardless; a failed revoke is not worth blocking the user.
    } finally {
      tokenStore.clear()
      setState({ status: 'anonymous' })
    }
  }, [])

  const value = useMemo(() => ({ state, login, register, logout }), [state, login, register, logout])
  return <AuthContext value={value}>{children}</AuthContext>
}

export function useAuth(): AuthContextValue {
  const context = use(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
