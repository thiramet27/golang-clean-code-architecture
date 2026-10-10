import type { FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { ErrorMessage } from '../components/ErrorMessage'
import { TextField } from '../components/TextField'
import { useSubmit } from './useSubmit'

export function RegisterPage() {
  const { state, register } = useAuth()
  const { pending, error, run } = useSubmit()

  if (state.status === 'authenticated') return <Navigate to="/profile" replace />

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const field = (name: string) => String(form.get(name)).trim()
    void run(() =>
      register({
        email: field('email'),
        password: String(form.get('password')),
        first_name: field('first_name'),
        last_name: field('last_name'),
      }),
    )
  }

  return (
    <section className="card narrow">
      <h1>Create an account</h1>
      <form onSubmit={handleSubmit} className="stack">
        <div className="row">
          <TextField label="First name" name="first_name" autoComplete="given-name" required />
          <TextField label="Last name" name="last_name" autoComplete="family-name" required />
        </div>
        <TextField label="Email" name="email" type="email" autoComplete="email" required />
        <TextField
          label="Password (min. 8 characters)"
          name="password"
          type="password"
          autoComplete="new-password"
          minLength={8}
          required
        />
        <ErrorMessage error={error} />
        <button type="submit" disabled={pending}>
          {pending ? 'Creating account…' : 'Register'}
        </button>
      </form>
      <p className="muted">
        Already registered? <Link to="/login">Log in</Link>
      </p>
    </section>
  )
}
