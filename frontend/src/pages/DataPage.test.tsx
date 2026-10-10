import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { tokenStore } from '../api/tokens'
import { json, mockFetch } from '../test/fetchMock'
import { DataPage } from './DataPage'

const schema = {
  type: 'record',
  name: 'UserModel',
  fields: [
    { name: 'id', type: 'int' },
    { name: 'email', type: 'string' },
    { name: 'is_active', type: 'boolean' },
  ],
}

beforeEach(() => tokenStore.set({ access: 'a', refresh: 'r' }))
afterEach(() => vi.unstubAllGlobals())

it('renders columns from the schema and sends filters as query params', async () => {
  const calls = mockFetch((call) => {
    const url = new URL(call.url)
    if (url.pathname.endsWith('/describe')) return json(200, schema)
    return json(200, {
      code: 200,
      data: [{ id: 1, email: 'a@b.co', is_active: true }],
      page: 1,
      page_size: 10,
      total_page: 1,
      total_data: 1,
      message: 'ok',
      data_schema: schema,
    })
  })

  render(<DataPage />)

  const table = await screen.findByRole('table')
  const headers = within(table).getAllByRole('columnheader').map((th) => th.textContent)
  expect(headers).toEqual(['id', 'email', 'is_active'])
  expect(within(table).getByText('✓')).toBeInTheDocument()
  expect(screen.getByText('Page 1 of 1, 1 record')).toBeInTheDocument()

  await userEvent.selectOptions(screen.getByLabelText('Field'), 'email')
  await userEvent.type(screen.getByLabelText('Equals'), 'a@b.co')
  await userEvent.click(screen.getByRole('button', { name: 'Add filter' }))

  await screen.findByText('email=a@b.co')
  const lastList = new URL(calls.at(-1)?.url ?? '')
  expect(lastList.searchParams.get('email')).toBe('a@b.co')
  expect(lastList.searchParams.get('_page')).toBe('1')
})

it('shows a friendly message when the model is forbidden', async () => {
  mockFetch(() => json(403, { trace_id: 'data-001', message: 'permission denied' }))

  render(<DataPage />)
  await userEvent.selectOptions(await screen.findByLabelText('Model'), 'user-permissions')

  expect(await screen.findByRole('alert')).toHaveTextContent('You do not have permission to view this.')
})
