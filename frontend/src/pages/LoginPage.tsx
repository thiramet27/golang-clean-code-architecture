import type { FormEvent } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ErrorMessage } from '../components/ErrorMessage'
import { TextField } from '../components/TextField'
import { useSubmit } from './useSubmit'

export function LoginPage() {
  const { state, login } = useAuth()
  const { pending, error, run } = useSubmit()
  const location = useLocation()

  if (state.status === 'authenticated') {
    const from = (location.state as { from?: string } | null)?.from ?? '/profile'
    return <Navigate to={from} replace />
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    void run(() => login(String(form.get('email')), String(form.get('password'))))
  }

  return (
    <section className="card narrow">
      <h1>Log in</h1>
      <form onSubmit={handleSubmit} className="stack">
        <TextField label="Email" name="email" type="email" autoComplete="email" required />
        <TextField label="Password" name="password" type="password" autoComplete="current-password" required />
        <ErrorMessage error={error} />
        <button type="submit" disabled={pending}>
          {pending ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p className="muted">
        No account? <Link to="/register">Register</Link>
      </p>
    </section>
  )
}
