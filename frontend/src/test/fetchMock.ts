import { vi } from 'vitest'

export interface MockCall {
  url: string
  method: string
  authorization: string | null
  body: unknown
}

type Handler = (call: MockCall) => Response | Promise<Response>

export function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

/** Replaces global fetch with `handler` and records every call. */
export function mockFetch(handler: Handler): MockCall[] {
  const calls: MockCall[] = []
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      const headers = new Headers(init.headers)
      const call: MockCall = {
        url: String(input),
        method: init.method ?? 'GET',
        authorization: headers.get('Authorization'),
        body: typeof init.body === 'string' ? JSON.parse(init.body) : undefined,
      }
      calls.push(call)
      return handler(call)
    }),
  )
  return calls
}
