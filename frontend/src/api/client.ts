import { tokenStore } from './tokens'
import type { ErrorBody, Session } from './types'

export const API_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:3000/api/v1').replace(/\/$/, '')
/** Swagger UI served by FastAPI next to the API. */
export const DOCS_URL = `${API_URL.replace(/\/api\/v1$/, '')}/swagger`

export class ApiError extends Error {
  readonly status: number
  readonly traceId: string | null

  constructor(status: number, message: string, traceId: string | null = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.traceId = traceId
  }
}

export interface RequestOptions {
  method?: 'GET' | 'POST'
  body?: unknown
  query?: Record<string, string | number>
  /** Send the access token and refresh it on 401. */
  auth?: boolean
}

let onSessionExpired: () => void = () => {}

/** Called after a failed refresh, once tokens have been cleared. */
export function setSessionExpiredHandler(handler: () => void): void {
  onSessionExpired = handler
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const sentToken = options.auth ? tokenStore.get()?.access : undefined
  let response = await send(path, options, sentToken)

  if (response.status === 401 && options.auth) {
    // Another request may have refreshed while this one was in flight; only refresh if the token is unchanged.
    const tokenChanged = tokenStore.get()?.access !== sentToken
    const canRetry = tokenChanged ? tokenStore.get() !== null : await refreshTokens()
    if (canRetry) {
      response = await send(path, options, tokenStore.get()?.access)
    }
    if (!canRetry || response.status === 401) {
      tokenStore.clear()
      onSessionExpired()
    }
  }

  return parse<T>(response)
}

let refreshInFlight: Promise<boolean> | null = null

/** Rotates both tokens. Concurrent callers share one request, because the old refresh token is single-use. */
export function refreshTokens(): Promise<boolean> {
  refreshInFlight ??= doRefresh().finally(() => {
    refreshInFlight = null
  })
  return refreshInFlight
}

async function doRefresh(): Promise<boolean> {
  const refresh = tokenStore.get()?.refresh
  if (!refresh) return false
  try {
    const session = await request<Session>('/users/refresh-token', {
      method: 'POST',
      body: { refresh_token: refresh },
    })
    tokenStore.set(session.token)
    return true
  } catch {
    return false
  }
}

async function send(path: string, options: RequestOptions, accessToken: string | undefined): Promise<Response> {
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`

  try {
    return await fetch(buildUrl(path, options.query), {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
    })
  } catch {
    throw new ApiError(0, 'Cannot reach the server. Is the API running?')
  }
}

function buildUrl(path: string, query: RequestOptions['query']): string {
  const url = `${API_URL}${path}`
  if (!query) return url
  const params = new URLSearchParams(Object.entries(query).map(([key, value]) => [key, String(value)]))
  return `${url}?${params}`
}

async function parse<T>(response: Response): Promise<T> {
  const body: unknown = await response.json().catch(() => null)
  if (response.ok) return body as T

  const error = (body ?? {}) as ErrorBody
  throw new ApiError(
    response.status,
    error.message ?? `Request failed with status ${response.status}`,
    error.trace_id ?? null,
  )
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error
  return new ApiError(0, error instanceof Error ? error.message : 'Unexpected error')
}
