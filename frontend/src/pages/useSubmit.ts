import { useState } from 'react'
import { toApiError, type ApiError } from '../api/client'

/** Tracks the pending/error state of a form submission. */
export function useSubmit() {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  async function run(action: () => Promise<void>): Promise<void> {
    setPending(true)
    setError(null)
    try {
      await action()
    } catch (err) {
      setError(toApiError(err))
    } finally {
      setPending(false)
    }
  }

  return { pending, error, run }
}
