import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, expect, it, vi } from 'vitest'
import { AuthProvider } from '../auth/AuthContext'
import { json, mockFetch } from '../test/fetchMock'
import { LoginPage } from './LoginPage'

afterEach(() => vi.unstubAllGlobals())

function renderLogin() {
  render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/profile" element={<p>Profile page</p>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

async function submit(email: string, password: string) {
  await userEvent.type(screen.getByLabelText('Email'), email)
  await userEvent.type(screen.getByLabelText('Password'), password)
  await userEvent.click(screen.getByRole('button', { name: 'Log in' }))
}

it('shows the API error message on bad credentials', async () => {
  mockFetch(() => json(400, { trace_id: 'users-003', message: 'invalid email or password' }))
  renderLogin()

  await submit('a@b.co', 'wrong-password')

  expect(await screen.findByRole('alert')).toHaveTextContent('invalid email or password')
  expect(screen.getByRole('button', { name: 'Log in' })).toBeEnabled()
})

it('stores tokens and redirects to the profile on success', async () => {
  const user = { id: 1, email: 'a@b.co', first_name: 'A', last_name: 'B', created_at: '', updated_at: '' }
  mockFetch(() => json(200, { user, token: { access: 'a', refresh: 'r' } }))
  renderLogin()

  await submit('a@b.co', 'correct-password')

  expect(await screen.findByText('Profile page')).toBeInTheDocument()
  expect(JSON.parse(localStorage.getItem('khaojai.tokens') ?? 'null')).toEqual({ access: 'a', refresh: 'r' })
})
