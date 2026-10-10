import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { json, mockFetch, type MockCall } from '../test/fetchMock'
import { ApiError, request, setSessionExpiredHandler } from './client'
import { tokenStore } from './tokens'

const user = { id: 1, email: 'a@b.co', first_name: 'A', last_name: 'B', created_at: '', updated_at: '' }
const rotated = { access: 'access-2', refresh: 'refresh-2' }

const isRefresh = (call: MockCall) => call.url.endsWith('/users/refresh-token')

/** Backend stub: the profile endpoint only accepts `access-2`; refresh returns a new pair. */
function backend(refreshResponse: () => Response = () => json(200, { user, token: rotated })) {
  return mockFetch((call) => {
    if (isRefresh(call)) return refreshResponse()
    if (call.authorization === 'Bearer access-2') return json(200, user)
    return json(401, { trace_id: 'middlware-002', message: 'token expired' })
  })
}

describe('api client', () => {
  const onExpired = vi.fn()

  beforeEach(() => {
    tokenStore.set({ access: 'access-1', refresh: 'refresh-1' })
    setSessionExpiredHandler(onExpired)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    onExpired.mockReset()
    tokenStore.clear()
  })

  it('sends the access token and returns parsed JSON', async () => {
    tokenStore.set(rotated)
    const calls = backend()

    await expect(request('/users/profile', { auth: true })).resolves.toEqual(user)
    expect(calls).toHaveLength(1)
    expect(calls[0]?.authorization).toBe('Bearer access-2')
  })

  it('turns error bodies into ApiError', async () => {
    mockFetch(() => json(409, { trace_id: 'users-001', message: 'email already used' }))

    const error = await request('/users/register', { method: 'POST', body: {} }).catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 409, traceId: 'users-001', message: 'email already used' })
  })

  it('refreshes once on 401 and retries with the new token', async () => {
    const calls = backend()

    await expect(request('/users/profile', { auth: true })).resolves.toEqual(user)

    expect(calls.map((c) => c.url.split('/api/v1')[1])).toEqual([
      '/users/profile',
      '/users/refresh-token',
      '/users/profile',
    ])
    expect(calls[1]?.body).toEqual({ refresh_token: 'refresh-1' })
    expect(tokenStore.get()).toEqual(rotated)
    expect(onExpired).not.toHaveBeenCalled()
  })

  it('shares a single refresh between concurrent requests', async () => {
    const calls = backend()

    const results = await Promise.all([
      request('/users/profile', { auth: true }),
      request('/users/profile', { auth: true }),
      request('/users/profile', { auth: true }),
    ])

    expect(results).toEqual([user, user, user])
    expect(calls.filter(isRefresh)).toHaveLength(1)
  })

  it('clears tokens and reports expiry when the refresh fails', async () => {
    const calls = backend(() => json(400, { trace_id: 'users-005', message: 'invalid token' }))

    await expect(request('/users/profile', { auth: true })).rejects.toMatchObject({ status: 401 })

    expect(calls.filter(isRefresh)).toHaveLength(1)
    expect(tokenStore.get()).toBeNull()
    expect(onExpired).toHaveBeenCalledOnce()
  })

  it('does not try to refresh for unauthenticated requests', async () => {
    const calls = backend()

    await expect(request('/users/login', { method: 'POST', body: {} })).rejects.toMatchObject({ status: 401 })
    expect(calls).toHaveLength(1)
    expect(tokenStore.get()).not.toBeNull()
  })

  it('reports network failures as ApiError with status 0', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    await expect(request('/')).rejects.toMatchObject({ status: 0 })
  })
})
