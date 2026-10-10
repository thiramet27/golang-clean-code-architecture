import { useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { formatValue } from '../features/data/format'

export function ProfilePage() {
  const { state, logout } = useAuth()
  const [loggingOut, setLoggingOut] = useState(false)

  if (state.status !== 'authenticated') return null
  const { user } = state

  async function handleLogout() {
    setLoggingOut(true)
    await logout()
  }

  return (
    <section className="card narrow">
      <h1>
        {user.first_name} {user.last_name}
      </h1>
      <dl className="details">
        <dt>Email</dt>
        <dd>{user.email}</dd>
        <dt>User ID</dt>
        <dd>{user.id}</dd>
        <dt>Member since</dt>
        <dd>{formatValue(user.created_at, 'datetime')}</dd>
        <dt>Last updated</dt>
        <dd>{formatValue(user.updated_at, 'datetime')}</dd>
      </dl>
      <button type="button" className="secondary" onClick={handleLogout} disabled={loggingOut}>
        {loggingOut ? 'Logging out…' : 'Log out'}
      </button>
    </section>
  )
}
