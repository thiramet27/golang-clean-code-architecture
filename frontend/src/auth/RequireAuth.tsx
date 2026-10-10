import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

export function RequireAuth({ children }: { children: ReactNode }) {
  const { state } = useAuth()
  const location = useLocation()

  if (state.status === 'loading') return <p className="muted">Loading…</p>
  if (state.status === 'anonymous') return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return children
}
