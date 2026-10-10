import { useEffect, useState } from 'react'
import { toApiError, type ApiError } from './api/client'

export type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: ApiError }

type Settled<T> = { load: () => Promise<T> } & ({ status: 'success'; data: T } | { status: 'error'; error: ApiError })

/**
 * Runs `load` whenever its identity changes (memoize it with useCallback/useMemo).
 * Pass null to skip. Results from a stale `load` are discarded.
 */
export function useAsync<T>(load: (() => Promise<T>) | null): AsyncState<T> {
  const [settled, setSettled] = useState<Settled<T> | null>(null)

  useEffect(() => {
    if (!load) return
    let active = true
    load().then(
      (data) => active && setSettled({ load, status: 'success', data }),
      (error: unknown) => active && setSettled({ load, status: 'error', error: toApiError(error) }),
    )
    return () => {
      active = false
    }
  }, [load])

  if (!load) return { status: 'idle' }
  if (settled?.load !== load) return { status: 'loading' }
  return settled
}
