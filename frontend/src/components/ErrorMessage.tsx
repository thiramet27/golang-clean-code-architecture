import type { ApiError } from '../api/client'

const FRIENDLY: Record<number, string> = {
  403: 'You do not have permission to view this.',
  404: 'Not found.',
}

export function ErrorMessage({ error }: { error: ApiError | null }) {
  if (!error) return null
  const hint = FRIENDLY[error.status]
  return (
    <p className="error" role="alert">
      {hint ? `${hint} ` : ''}
      <span className="error-detail">{error.message}</span>
    </p>
  )
}
